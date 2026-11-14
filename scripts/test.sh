#!/usr/bin/env bash
#
# Roda a suíte completa do Django em container.
#
# Por que um script e não `docker compose run ... manage.py test` direto:
#   1. a imagem de produção NÃO embarca os testes (`.dockerignore` exclui
#      `**/tests.py`); sem montar o código o Django encontra 0 testes e
#      responde "OK" — falso verde (D-030);
#   2. o runner de testes não depende de `collectstatic` (D-030b): o settings
#      troca o storage de static durante os testes;
#   3. o script falha se nenhum teste executar, em vez de aceitar "Ran 0 tests".
#
# Uso:
#   scripts/test.sh                 # suíte completa
#   scripts/test.sh catalog orders  # apenas os apps indicados
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOG="${TMPDIR:-/tmp}/m2-test.log"
APPS="$*"

# frontend/ (templates e static) também entra montado: sem isso a suíte usaria
# os templates congelados na imagem e um lab com imagem antiga testaria código
# velho (falha vista em ProductWithoutImageTest).
# backend/ entra montado como somente-leitura, mas o compose monta volumes em
# backend/media e backend/staticfiles: o ponto de montagem precisa existir no
# host, senão um clone novo falha com "read-only file system" (ambos gitignored).
mkdir -p backend/media backend/staticfiles

echo "[test] montando backend/ + frontend/ e rodando a suíte (log: ${LOG})"
rc=0
docker compose run --rm --no-deps --entrypoint sh \
    -v "$ROOT/backend:/app/backend:ro" \
    -v "$ROOT/frontend:/app/frontend:ro" \
    web \
    -c "cd /app/backend && python manage.py test ${APPS} --verbosity=2" 2>&1 | tee "$LOG" || rc=$?

# Guarda contra o falso verde: sem esta checagem, "Ran 0 tests ... OK" passa.
if ! grep -Eq '^Ran [1-9][0-9]* test' "$LOG"; then
    echo "[test] ERRO: nenhum teste foi executado (falso verde). Veja ${LOG}" >&2
    exit 1
fi

if [ "$rc" -ne 0 ]; then
    echo "[test] FALHOU (exit=${rc}). Veja ${LOG}" >&2
    exit "$rc"
fi

echo "[test] OK"
