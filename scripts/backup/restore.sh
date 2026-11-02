#!/usr/bin/env bash
#
# Restore do backup do M2 Moda Masculina.
#
# Uso:
#   restore.sh --archive <m2-YYYYmmdd-HHMMSS> [--target-db <banco>]
#   restore.sh --latest [--target-db <banco>]
#   restore.sh --list
#
# O dump e um dump LOGICO (mysqldump) sem "CREATE DATABASE": o banco destino
# precisa existir e e criado por quem chama (ex.: verify-restore.sh).
#
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
LOG_COMPONENT="restore"

BORG_REPO="${BORG_REPO:-/backup/repo}"
RESTORE_DIR="${RESTORE_DIR:-/backup/restore}"
ARCHIVE=""
TARGET_DB=""
USE_LATEST=0
LIST_ONLY=0

usage() {
    sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit "${1:-0}"
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --archive)   ARCHIVE="$2"; shift 2 ;;
        --latest)    USE_LATEST=1; shift ;;
        --target-db) TARGET_DB="$2"; shift 2 ;;
        --list)      LIST_ONLY=1; shift ;;
        -h|--help)   usage 0 ;;
        *) log_error "Argumento desconhecido: $1"; usage 1 ;;
    esac
done

if [ -z "${BORG_PASSPHRASE:-}" ]; then
    die "BORG_PASSPHRASE nao definida (obrigatoria para abrir o repositorio criptografado)"
fi

if [ "$LIST_ONLY" = "1" ]; then
    log_info "Arquivos disponiveis em ${BORG_REPO}:"
    borg list "$BORG_REPO"
    exit 0
fi

if [ "$USE_LATEST" = "1" ]; then
    # `borg list` imprime: <nome-do-arquivo> <data> <...> — o nome e o primeiro campo.
    ARCHIVE="$(borg list "$BORG_REPO" 2>/dev/null | awk 'NF > 0 { print $1 }' | tail -n 1)"
    if [ -z "$ARCHIVE" ]; then
        die "Nenhum arquivo encontrado no repositorio ${BORG_REPO}"
    fi
    log_info "Arquivo selecionado (mais recente): ${ARCHIVE}"
fi

if [ -z "$ARCHIVE" ]; then
    usage 1
fi

TARGET_DB="${TARGET_DB:-${MYSQL_DATABASE:-m2shop}}"

log_info "Restaurando ${BORG_REPO}::${ARCHIVE} -> banco '${TARGET_DB}' (host=${MYSQL_HOST:-db})"

rm -rf "${RESTORE_DIR:?}/${ARCHIVE}"
mkdir -p "$RESTORE_DIR"

# `borg extract` extrai no diretorio de trabalho atual (o argumento opcional e um
# filtro de membros, nao um destino) — por isso o subshell com `cd`.
( cd "$RESTORE_DIR" && borg extract "${BORG_REPO}::${ARCHIVE}" ) || {
    rc=$?
    log_error "borg extract falhou (exit=${rc})"
    send_telegram "CRITICO" "RESTORE FALHOU no servidor ${SERVER_NAME:-$(hostname)}: borg extract exit=${rc}" || true
    exit "$rc"
}

DUMP_FILE="$(find "$RESTORE_DIR" -name 'database.sql.gz' -type f | head -n 1)"
if [ -z "$DUMP_FILE" ]; then
    log_error "Dump nao encontrado apos a extracao (procurado 'database.sql.gz' em ${RESTORE_DIR})"
    exit 4
fi
log_info "Dump extraido: ${DUMP_FILE} ($(du -h "$DUMP_FILE" | cut -f1))"

gunzip -c "$DUMP_FILE" | mysql_exec "$TARGET_DB" || {
    rc=$?
    log_error "Restauracao no MySQL falhou (exit=${rc})"
    send_telegram "CRITICO" "RESTORE FALHOU ao aplicar o dump no banco '${TARGET_DB}' (servidor ${SERVER_NAME:-$(hostname)}), exit=${rc}" || true
    exit "$rc"
}

TABLE_COUNT="$(mysql_exec "$TARGET_DB" -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${TARGET_DB}';")"
log_info "Restore concluido. Tabelas no banco '${TARGET_DB}': ${TABLE_COUNT}"
send_telegram "OK" "Restore concluido no servidor ${SERVER_NAME:-$(hostname)}
Arquivo: ${ARCHIVE}
Banco destino: ${TARGET_DB}
Tabelas restauradas: ${TABLE_COUNT}" || true
exit 0
