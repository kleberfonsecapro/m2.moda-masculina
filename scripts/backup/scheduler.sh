#!/usr/bin/env bash
#
# Agendador do backup: executa o backup.sh todos os dias no horario configurado
# (BACKUP_AT_HOUR, padrao 02:00, horario local do container).
#
# Sem dependencia de cron: o proprio container faz o loop.
#
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
LOG_COMPONENT="scheduler"

AT_HOUR="${BACKUP_AT_HOUR:-2}"

log_info "Agendador iniciado: backup diario as ${AT_HOUR}:00 (TZ=${TZ:-UTC})"

while true; do
    now_epoch="$(date '+%s')"
    today="$(date '+%Y-%m-%d')"
    tomorrow="$(date -d "@$(( now_epoch + 86400 ))" '+%Y-%m-%d')"

    target="$(date -d "${today} ${AT_HOUR}:00:00" '+%s')"
    if [ "$now_epoch" -ge "$target" ]; then
        target="$(date -d "${tomorrow} ${AT_HOUR}:00:00" '+%s')"
    fi

    sleep_seconds=$(( target - now_epoch ))
    log_info "Proximo backup em ${sleep_seconds}s ($(date -d "@${target}" '+%Y-%m-%d %H:%M:%S'))"
    sleep "$sleep_seconds"

    log_info "Disparando backup agendado"
    rc=0
    "${SCRIPT_DIR}/backup.sh" || rc=$?
    if [ "$rc" -ne 0 ]; then
        log_error "Backup agendado falhou (exit=${rc}) — o proximo ciclo continua apos 1h"
        sleep 3600
    fi
done
