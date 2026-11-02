#!/usr/bin/env bash
#
# Backup 3-2-1 do M2 Moda Masculina.
#
#   dump logico (MySQL)  ->  Borg criptografado (repokey) + prune  ->  rclone sync offsite
#                                                        ->  alerta Telegram + heartbeat
#
# AGENTS.md §4:
#  - NUNCA backup dos arquivos fisicos do banco: sempre dump logico antes.
#  - Repositorio Borg criptografado; passphrase vem do ambiente (nunca hardcoded).
#  - `borg prune` com retencao explicita (o disco nao pode lotar).
#  - `rclone sync --retries 3` imediato apos o Borg.
#  - Exit code do Borg e do Rclone capturados separadamente.
#  - Falha em QUALQUER comando => alerta CRITICO no Telegram (servidor, erro, exit codes).
#  - Sucesso => resumo com tempo de execucao e tamanho deduplicado (`borg info`).
#
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
LOG_COMPONENT="backup"

BORG_REPO="${BORG_REPO:-/backup/repo}"
STAGE_DIR="${STAGE_DIR:-/backup/stage}"
PAYLOAD_DIR="${PAYLOAD_DIR:-/backup/payload}"
MEDIA_DIR="${MEDIA_DIR:-/media}"
KEEP_DAILY="${BACKUP_KEEP_DAILY:-7}"
KEEP_WEEKLY="${BACKUP_KEEP_WEEKLY:-4}"
KEEP_MONTHLY="${BACKUP_KEEP_MONTHLY:-6}"

ARCHIVE=""
START_TS=""
BORG_RC=0
RCLONE_RC=0
DUMP_RC=0

require_env() {
    local missing=()
    local var
    for var in MYSQL_DATABASE BORG_PASSPHRASE; do
        if [ -z "${!var:-}" ]; then
            missing+=("$var")
        fi
    done
    if [ -z "${MYSQL_BACKUP_PASSWORD:-}" ] && [ -z "${MYSQL_ROOT_PASSWORD:-}" ]; then
        missing+=("MYSQL_ROOT_PASSWORD")
    fi
    if [ "${#missing[@]}" -gt 0 ]; then
        log_error "Variaveis de ambiente obrigatorias ausentes: ${missing[*]}"
        send_telegram "CRITICO" "Backup abortado antes de iniciar: variaveis ausentes: ${missing[*]}" || true
        exit 2
    fi
    if [ -z "${RCLONE_REMOTE:-}" ]; then
        log_warn "RCLONE_REMOTE vazio: o offsite (rclone sync) sera SKIPPED nesta execucao."
    fi
}

on_error() {
    local exit_code=$?
    local line="$1"
    log_error "Falha na linha ${line} (exit=${exit_code}). Borg rc=${BORG_RC} Rclone rc=${RCLONE_RC}"
    send_telegram "CRITICO" "Backup FALHOU no servidor ${SERVER_NAME:-$(hostname)}
Erro na linha ${line} (exit code ${exit_code}).
Comando: ${BASH_COMMAND}
Borg exit code: ${BORG_RC} | Rclone exit code: ${RCLONE_RC}" || true
    write_heartbeat "failed" "exit=${exit_code} line=${line}" || true
    exit "$exit_code"
}

step_dump() {
    LOG_COMPONENT="dump"
    local dump_file="${STAGE_DIR}/${ARCHIVE}-database.sql.gz"
    log_info "Gerando dump logico do banco '${MYSQL_DATABASE}' -> ${dump_file}"
    mysql_dump_file "$dump_file" || DUMP_RC=$?
    if [ "$DUMP_RC" -ne 0 ]; then
        log_error "mysqldump falhou (exit=${DUMP_RC})"
        send_telegram "CRITICO" "Backup FALHOU no dump logico do MySQL (servidor ${SERVER_NAME:-$(hostname)}), exit=${DUMP_RC}" || true
        exit "${DUMP_RC}"
    fi
    if [ ! -s "$dump_file" ]; then
        log_error "Dump gerado vazio: ${dump_file}"
        send_telegram "CRITICO" "Backup FALHOU: dump logico vazio (servidor ${SERVER_NAME:-$(hostname)})" || true
        exit 3
    fi

    # Guarda contra "backup verde" de um banco vazio/errado: um dump sem nenhuma
    # tabela significa schema ausente (banco errado, permissao ou migrate pendente).
    table_count="$(gzip -dc "$dump_file" | grep -c '^CREATE TABLE' || true)"
    if [ "${table_count:-0}" -eq 0 ]; then
        log_error "Dump sem tabelas (0 CREATE TABLE) — banco '${MYSQL_DATABASE}' parece vazio ou inacessivel."
        send_telegram "CRITICO" "Backup FALHOU: dump sem nenhuma tabela (banco '${MYSQL_DATABASE}' vazio ou sem permissao) — servidor ${SERVER_NAME:-$(hostname)}" || true
        exit 5
    fi
    log_info "Dump concluido: $(du -h "$dump_file" | cut -f1) ($(stat -c%s "$dump_file") bytes), ${table_count} tabelas"
    echo "$dump_file"
}

step_borg_init() {
    LOG_COMPONENT="borg"

    # Repositorio valido = config + manifest. Um repo parcial (init interrompido)
    # e movido para o lado (nao apagado) e reinicializado.
    if [ -f "${BORG_REPO}/config" ] && [ -f "${BORG_REPO}/manifest" ]; then
        if borg list "$BORG_REPO" >/dev/null 2>&1; then
            log_info "Repositorio Borg valido: ${BORG_REPO}"
            return 0
        fi
        # config+manifest existem mas o repo nao abre: quase sempre passphrase errada.
        # NUNCA destruir um repo valido por causa de passphrase.
        log_error "Repositorio existe mas nao pode ser aberto (passphrase incorreta ou repo corrompido). Nada foi alterado."
        send_telegram "CRITICO" "Backup FALHOU: repositorio Borg existe mas nao pode ser aberto (passphrase incorreta?) — servidor ${SERVER_NAME:-$(hostname)}. Nada foi alterado." || true
        exit 6
    fi

    if [ -e "$BORG_REPO" ]; then
        BROKEN_DIR="${BORG_REPO}.broken.$(date -u '+%Y%m%d%H%M%S')"
        log_warn "Repositorio parcial encontrado; movendo para ${BROKEN_DIR} antes de reinicializar"
        mv "$BORG_REPO" "$BROKEN_DIR"
    fi

    log_info "Inicializando repositorio Borg (encryption=repokey): ${BORG_REPO}"
    mkdir -p "$BORG_REPO"
    borg init --encryption repokey "$BORG_REPO" || {
        local rc=$?
        BORG_RC=$rc
        log_error "borg init falhou (exit=${rc})"
        send_telegram "CRITICO" "Backup FALHOU: 'borg init' falhou (servidor ${SERVER_NAME:-$(hostname)}), exit=${rc}" || true
        exit "${rc}"
    }
}

step_borg_create() {
    LOG_COMPONENT="borg"
    local payload_root="${PAYLOAD_DIR}/${ARCHIVE}"
    local media_dir="${payload_root}/media"
    rm -rf "$payload_root"
    mkdir -p "$media_dir"

    log_info "Montando payload do backup em ${payload_root}"
    cp "${STAGE_DIR}/${ARCHIVE}-database.sql.gz" "${payload_root}/database.sql.gz"
    if [ -d "$MEDIA_DIR" ] && [ -n "$(ls -A "$MEDIA_DIR" 2>/dev/null)" ]; then
        cp -a "${MEDIA_DIR}/." "$media_dir/"
        log_info "Midia incluida: $(du -sh "$media_dir" | cut -f1)"
    else
        log_info "Midia vazia ou ausente (${MEDIA_DIR}) — nenhum arquivo de upload included"
    fi

    log_info "Criando arquivo no Borg: ${BORG_REPO}::${ARCHIVE}"
    ( cd "$PAYLOAD_DIR" && borg create \
        --compression lz4 \
        --stats \
        "${BORG_REPO}::${ARCHIVE}" \
        "$ARCHIVE" ) || BORG_RC=$?

    if [ "$BORG_RC" -ne 0 ]; then
        log_error "borg create falhou (exit=${BORG_RC})"
        send_telegram "CRITICO" "Backup FALHOU no 'borg create' (servidor ${SERVER_NAME:-$(hostname)}), exit=${BORG_RC}" || true
        exit "${BORG_RC}"
    fi
    log_info "borg create concluido (exit=0)"
}

step_borg_prune() {
    LOG_COMPONENT="borg"
    log_info "Prune: mantendo ${KEEP_DAILY} diarios / ${KEEP_WEEKLY} semanais / ${KEEP_MONTHLY} mensais"
    borg prune \
        --prefix "m2-" \
        --keep-daily "$KEEP_DAILY" \
        --keep-weekly "$KEEP_WEEKLY" \
        --keep-monthly "$KEEP_MONTHLY" \
        --show-rc \
        "$BORG_REPO" || BORG_RC=$?

    if [ "$BORG_RC" -ne 0 ]; then
        log_error "borg prune falhou (exit=${BORG_RC})"
        send_telegram "CRITICO" "Backup FALHOU no 'borg prune' (servidor ${SERVER_NAME:-$(hostname)}), exit=${BORG_RC}" || true
        exit "${BORG_RC}"
    fi
    log_info "borg prune concluido (exit=0)"
}

step_rclone_sync() {
    LOG_COMPONENT="rclone"
    if [ -z "${RCLONE_REMOTE:-}" ]; then
        RCLONE_RC=0
        log_warn "RCLONE_REMOTE nao configurado: offsite NAO executado (rclone exit code registrado como 0/skip)."
        return 0
    fi
    log_info "Sincronizando repositorio Borg para o offsite: ${RCLONE_REMOTE}"
    rclone sync "$BORG_REPO" "$RCLONE_REMOTE" \
        --retries 3 \
        --transfers 4 \
        --checkers 8 \
        --stats 30s \
        --stats-one-line \
        --log-level INFO || RCLONE_RC=$?

    if [ "$RCLONE_RC" -ne 0 ]; then
        log_error "rclone sync falhou (exit=${RCLONE_RC})"
        send_telegram "CRITICO" "Backup FALHOU no offsite 'rclone sync' (servidor ${SERVER_NAME:-$(hostname)}), exit=${RCLONE_RC}" || true
        exit "${RCLONE_RC}"
    fi
    log_info "rclone sync concluido (exit=0)"
}

step_summary() {
    LOG_COMPONENT="summary"
    local duration=$(( $(date +%s) - START_TS ))
    local repo_info archive_count
    repo_info="$(borg info "$BORG_REPO" 2>/dev/null || true)"
    archive_count="$(borg list "$BORG_REPO" 2>/dev/null | wc -l | tr -d ' ')"

    log_info "Repositorio: ${BORG_REPO}"
    log_info "Arquivos no repositorio: ${archive_count}"
    log_info "Duracao: ${duration}s | dump_rc=${DUMP_RC} borg_rc=${BORG_RC} rclone_rc=${RCLONE_RC}"
    if [ -n "$repo_info" ]; then
        log_info "borg info: $(printf '%s' "$repo_info" | tr '\n' ' ')"
    fi

    write_heartbeat "ok" "archive=${ARCHIVE} duration=${duration}s"

    send_telegram "OK" "Backup concluido no servidor ${SERVER_NAME:-$(hostname)}
Arquivo: ${ARCHIVE}
Duracao: ${duration}s
Repositorio: ${BORG_REPO} (${archive_count} arquivos)
Exit codes: dump=${DUMP_RC} borg=${BORG_RC} rclone=${RCLONE_RC}" || true
}

main() {
    START_TS=$(date +%s)
    ARCHIVE="m2-$(date -u '+%Y%m%d-%H%M%S')"
    trap 'on_error $LINENO' ERR

    log_info "=== INICIO do backup (servidor=${SERVER_NAME:-$(hostname)}) arquivo=${ARCHIVE} ==="
    require_env
    step_dump >/dev/null
    step_borg_init
    step_borg_create
    step_borg_prune
    step_rclone_sync
    step_summary
    log_info "=== FIM do backup com sucesso ==="
}

main "$@"
