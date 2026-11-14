#!/usr/bin/env bash
#
# Prova de RESTAURACAO (R1 gate): restaura o ultimo backup em um banco "scratch"
# e compara, tabela a tabela, a contagem de linhas com o banco de origem.
#
# Uso:
#   verify-restore.sh [--archive <nome>] [--source-db <banco>] [--scratch-db <banco>]
#
# Saida: relatorio por tabela + "RESULTADO: OK" e exit 0 quando tudo bate.
#        Em caso de divergencia: exit 1 (o backup nao e confiavel).
#
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"
LOG_COMPONENT="verify-restore"

ARCHIVE=""
SOURCE_DB="${SOURCE_DB:-${MYSQL_DATABASE:-m2shop}}"
SCRATCH_DB="${SCRATCH_DB:-${MYSQL_DATABASE:-m2shop}_restore_verify}"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --archive)   ARCHIVE="$2"; shift 2 ;;
        --source-db) SOURCE_DB="$2"; shift 2 ;;
        --scratch-db) SCRATCH_DB="$2"; shift 2 ;;
        -h|--help)   log_info "Uso: verify-restore.sh [--archive <nome>] [--source-db <db>] [--scratch-db <db>]"; exit 0 ;;
        *) log_error "Argumento desconhecido: $1"; exit 1 ;;
    esac
done

for var in BORG_PASSPHRASE MYSQL_DATABASE; do
    if [ -z "${!var:-}" ]; then
        die "Variavel obrigatoria ausente: ${var}"
    fi
done
if [ -z "${MYSQL_BACKUP_PASSWORD:-}" ] && [ -z "${MYSQL_ROOT_PASSWORD:-}" ]; then
    die "MYSQL_ROOT_PASSWORD (ou MYSQL_BACKUP_PASSWORD) obrigatoria: a prova de restore cria o banco scratch"
fi

log_info "=== VERIFICACAO DE RESTORE ==="
log_info "Origem: ${SOURCE_DB} | Scratch: ${SCRATCH_DB} | Repo: ${BORG_REPO:-/backup/repo}"

RESTORE_ARGS=(--target-db "$SCRATCH_DB")
if [ -n "$ARCHIVE" ]; then
    RESTORE_ARGS+=(--archive "$ARCHIVE")
else
    RESTORE_ARGS+=(--latest)
fi

# 1) Recria o banco scratch do zero (garante que nao ha residuo mascarando divergencia).
mysql_exec -e "DROP DATABASE IF EXISTS \`${SCRATCH_DB}\`; CREATE DATABASE \`${SCRATCH_DB}\` CHARACTER SET utf8mb4;" \
    || die "Falha ao criar o banco scratch '${SCRATCH_DB}'"

# 2) Restaura a partir do repositorio Borg.
"${SCRIPT_DIR}/restore.sh" "${RESTORE_ARGS[@]}" || die "Restore falhou — backup NAO confiavel"

# 3) Compara contagens tabela a tabela.
TABLES="$(mysql_exec -e "SELECT table_name FROM information_schema.tables WHERE table_schema='${SOURCE_DB}' AND table_type='BASE TABLE' ORDER BY table_name;")"
if [ -z "$TABLES" ]; then
    die "O banco de origem '${SOURCE_DB}' nao tem tabelas — nada a comparar"
fi

MISMATCH=0
TOTAL_TABLES=0
TOTAL_ROWS=0
REPORT=""

while IFS= read -r table; do
    [ -z "$table" ] && continue
    TOTAL_TABLES=$((TOTAL_TABLES + 1))
    src_rows="$(mysql_exec "$SOURCE_DB" -e "SELECT COUNT(*) FROM \`${table}\`;")"
    dst_rows="$(mysql_exec "$SCRATCH_DB" -e "SELECT COUNT(*) FROM \`${table}\`;")"
    TOTAL_ROWS=$((TOTAL_ROWS + src_rows))
    if [ "$src_rows" != "$dst_rows" ]; then
        MISMATCH=$((MISMATCH + 1))
        REPORT="${REPORT}\n  DIVERGENCIA  ${table}: origem=${src_rows} scratch=${dst_rows}"
        log_error "Divergencia em ${table}: origem=${src_rows} scratch=${dst_rows}"
    else
        REPORT="${REPORT}\n  ok           ${table}: ${src_rows} linhas"
    fi
done <<< "$TABLES"

log_info "Relatorio de comparacao:"
printf '%b\n' "$REPORT"

if [ "$MISMATCH" -gt 0 ]; then
    send_telegram "CRITICO" "FALHA na verificacao de restore (servidor ${SERVER_NAME:-$(hostname)}): ${MISMATCH} tabela(s) divergente(s) entre '${SOURCE_DB}' e '${SCRATCH_DB}'." || true
    write_heartbeat "restore-failed" "mismatch=${MISMATCH}" || true
    log_error "RESULTADO: FALHOU (${MISMATCH}/${TOTAL_TABLES} tabelas divergentes)"
    exit 1
fi

log_info "RESULTADO: OK — ${TOTAL_TABLES} tabelas conferidas, ${TOTAL_ROWS} linhas, 0 divergencias"
send_telegram "OK" "Verificacao de restore OK no servidor ${SERVER_NAME:-$(hostname)}: ${TOTAL_TABLES} tabelas / ${TOTAL_ROWS} linhas conferidas entre '${SOURCE_DB}' e '${SCRATCH_DB}'." || true
exit 0
