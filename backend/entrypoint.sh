#!/bin/sh
# Entrypoint de produção.
#
# O processo roda como usuário sem privilégios (definido no Dockerfile).
# Não há chown em runtime: os volumes nomeados herdam a ownership do diretório
# da imagem na primeira criação. Se um volume legado estiver com outra
# ownership, falhamos cedo com instrução de correção em vez de erro obscuro.
set -e

for dir in /app/backend/staticfiles /app/backend/media; do
    if [ ! -w "$dir" ]; then
        echo "ERRO: $dir não é gravável pelo UID $(id -u):$(id -g)." >&2
        echo "Corrija a ownership do volume uma única vez, como root:" >&2
        echo "  docker compose run --rm --user root web chown -R $(id -u):$(id -g) $dir" >&2
        exit 1
    fi
done

exec "$@"
