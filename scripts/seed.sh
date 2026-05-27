#!/bin/bash
set -e

echo "Populando banco de dados com produtos de exemplo..."
docker compose exec -T web python scripts/seed.py
echo "Pronto!"
