#!/usr/bin/env bash
#
# Lint com versões fixadas (backend/requirements-dev.txt).
# A ferramenta roda em container efêmero: nada é instalado no host nem na
# imagem de produção (AGENTS.md §2).
#
# Uso:
#   scripts/lint.sh                    # regras padrão do ruff
#   scripts/lint.sh --statistics       # resumo por regra (baseline)
#   scripts/lint.sh --select E9,F63,F7,F82   # somente erros reais
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

docker run --rm -v "$ROOT:/src" -w /src python:3.12-slim sh -c "
    pip install --quiet --disable-pip-version-check -r backend/requirements-dev.txt &&
    ruff check backend $*
"
