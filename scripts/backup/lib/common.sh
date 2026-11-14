#!/usr/bin/env bash
# Funcoes compartilhadas pela stack de backup.
# AGENTS.md §4: logs estruturados, exit codes capturados, alerta Telegram em falha e sucesso.

# --- Logging ---------------------------------------------------------------
log() {
    local level="$1"; shift
    printf '%s [backup] [%s] [%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$level" "${LOG_COMPONENT:-core}" "$*" >&2
}
log_info()  { log INFO "$@"; }
log_warn()  { log WARN "$@"; }
log_error() { log ERROR "$@"; }

die() {
    log_error "$*"
    exit 1
}

# --- Telegram --------------------------------------------------------------
# Regras (AGENTS.md §4):
#  - falha de QUALQUER comando => alerta CRITICO com nome do servidor, erro e exit codes
#  - sucesso => resumo silencioso/informativo com tempo de execucao e tamanho deduplicado
# TELEGRAM_DRY_RUN=1 apenas registra o payload (usado na validacao local, sem bot token).
send_telegram() {
    local severity="$1"; shift
    local message="$*"
    local payload

    if [ "${TELEGRAM_DRY_RUN:-0}" = "1" ]; then
        log_info "TELEGRAM[DRY-RUN] severity=${severity} message=${message}"
        return 0
    fi

    if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
        log_warn "TELEGRAM nao configurado (BOT_TOKEN/CHAT_ID vazios): alerta nao enviado. severity=${severity} message=${message}"
        return 10
    fi

    payload=$(jq -n \
        --arg chat_id "${TELEGRAM_CHAT_ID}" \
        --arg text "[${severity}] ${SERVER_NAME:-$(hostname)}
${message}" \
        '{chat_id: $chat_id, text: $text, disable_web_page_preview: true}')

    if ! curl -sS --fail --max-time 20 \
        -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -H 'Content-Type: application/json' \
        -d "$payload" >/dev/null; then
        log_error "Falha ao enviar alerta ao Telegram (severity=${severity})"
        return 10
    fi

    log_info "Alerta Telegram enviado (severity=${severity})"
    return 0
}

# --- Heartbeat -------------------------------------------------------------
# Sinal de "o backup rodou". Monitoring externo pode ler o timestamp mais recente.
write_heartbeat() {
    local status="$1" detail="${2:-}"
    local ts_file="${HEARTBEAT_DIR:-/backup/heartbeat}/last"
    printf '%s status=%s %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$status" "$detail" > "$ts_file"
    log_info "Heartbeat gravado: status=${status} ${detail}"
}

# --- MySQL -----------------------------------------------------------------
# O dump/restore usa a conexao administrativa (root) por dois motivos:
#   1. rotinas/triggers/eventos exigem privilegios elevados;
#   2. a prova de restore precisa criar um banco "scratch" para restaurar.
# Recomenda-se (pendencia aberta) um usuario dedicado de backup com
# SELECT no banco da aplicacao + ALL apenas no banco scratch.
mysql_admin_user()     { printf '%s' "${MYSQL_BACKUP_USER:-${MYSQL_ROOT_USER:-root}}"; }
mysql_admin_password() { printf '%s' "${MYSQL_BACKUP_PASSWORD:-${MYSQL_ROOT_PASSWORD:-}}"; }

mysql_exec() {
    mariadb --protocol=TCP \
        --host="${MYSQL_HOST:-db}" \
        --port="${MYSQL_PORT:-3306}" \
        --user="$(mysql_admin_user)" \
        --password="$(mysql_admin_password)" \
        --default-character-set=utf8mb4 \
        --batch --skip-column-names "$@"
}

mysql_dump_file() {
    # Dump logico completo. --single-transaction garante consistencia do InnoDB
    # sem travar a tabela (AGENTS.md §4: nunca fazer backup dos arquivos fisicos do banco).
    mariadb-dump --protocol=TCP \
        --host="${MYSQL_HOST:-db}" \
        --port="${MYSQL_PORT:-3306}" \
        --user="$(mysql_admin_user)" \
        --password="$(mysql_admin_password)" \
        --single-transaction \
        --quick \
        --routines --triggers --events \
        --hex-blob \
        --default-character-set=utf8mb4 \
        --no-tablespaces \
        "${MYSQL_DATABASE}" \
        | gzip -9 > "$1"
}
