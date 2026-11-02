#!/usr/bin/env bash
#
# Healthcheck do servico de backup.
#
# Retorna 0 (saudavel) quando:
#   - existe um heartbeat de backup bem-sucedido; e
#   - esse heartbeat nao e mais antigo que BACKUP_MAX_AGE_HOURS (padrao 30h).
#
# Retorna 1 quando o backup esta atrasado ou nunca rodou — o container fica "unhealthy"
# e o alerta/monitoramento externo pode agir.
#
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
LOG_COMPONENT="healthcheck"

HEARTBEAT_FILE="${HEARTBEAT_DIR:-/backup/heartbeat}/last"
MAX_AGE_HOURS="${BACKUP_MAX_AGE_HOURS:-30}"

if [ ! -f "$HEARTBEAT_FILE" ]; then
    log_error "Nenhum heartbeat encontrado em ${HEARTBEAT_FILE}: o backup nunca rodou com sucesso."
    exit 1
fi

content="$(cat "$HEARTBEAT_FILE")"
status="$(printf '%s' "$content" | sed -n 's/.*status=\([a-zA-Z]*\).*/\1/p')"
timestamp="$(printf '%s' "$content" | cut -d' ' -f1)"

if [ "$status" != "ok" ]; then
    log_error "Ultimo backup nao foi bem-sucedido (status=${status}): ${content}"
    exit 1
fi

age_seconds=$(( $(date -u '+%s') - $(date -u -d "$timestamp" '+%s' 2>/dev/null || echo 0) ))
max_seconds=$(( MAX_AGE_HOURS * 3600 ))

if [ "$age_seconds" -gt "$max_seconds" ]; then
    log_error "Ultimo backup bem-sucedido ha ${age_seconds}s (limite ${max_seconds}s): backup atrasado."
    exit 1
fi

log_info "Backup saudavel: ${content}"
exit 0
