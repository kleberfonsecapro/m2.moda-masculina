#!/usr/bin/env bash
#
# Cobertura de testes: roda a suíte num container efêmero com as dependências
# de desenvolvimento (o runtime de produção não tem pip nem coverage).
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

docker run --rm -v "$ROOT:/src" -w /src python:3.12-slim sh -c "
    apt-get update -qq &&
    apt-get install -y -qq --no-install-recommends build-essential default-libmysqlclient-dev pkg-config >/dev/null &&
    pip install --quiet --disable-pip-version-check -r backend/requirements.txt -r backend/requirements-dev.txt &&
    cd backend && mkdir -p staticfiles media &&
    SECRET_KEY=coverage-local DEBUG=True ALLOWED_HOSTS=localhost,127.0.0.1 \
        coverage run --source=. manage.py test &&
    coverage report --show-missing
"
