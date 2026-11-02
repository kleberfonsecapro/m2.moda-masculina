#!/usr/bin/env bash
#
# Entrypoint da imagem de backup.
#
#   backup     executa um backup agora (padrao)
#   schedule   fica em loop executando o backup diariamente (BACKUP_AT_HOUR)
#   restore    restaura um arquivo (ver restore.sh)
#   verify     prova de restore (ver verify-restore.sh)
#   list       lista os arquivos do repositorio Borg
#   healthcheck  verifica se o ultimo backup foi bem-sucedido
#
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

COMMAND="${1:-backup}"

case "$COMMAND" in
    backup)      exec "${SCRIPT_DIR}/backup.sh" ;;
    schedule)    exec "${SCRIPT_DIR}/scheduler.sh" ;;
    restore)     shift; exec "${SCRIPT_DIR}/restore.sh" "$@" ;;
    verify)      shift; exec "${SCRIPT_DIR}/verify-restore.sh" "$@" ;;
    list)        exec "${SCRIPT_DIR}/restore.sh" --list ;;
    healthcheck) exec "${SCRIPT_DIR}/healthcheck.sh" ;;
    *)           log_error "Comando desconhecido: ${COMMAND}"; exit 64 ;;
esac
