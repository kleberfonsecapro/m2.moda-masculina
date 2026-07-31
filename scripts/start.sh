#!/bin/bash
set -e

echo "============================================"
echo "  M2 Moda Masculina - Inicialização"
echo "============================================"
echo ""

if ! command -v docker &> /dev/null; then
    echo "ERRO: Docker não encontrado. Instale Docker e Docker Compose."
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "ERRO: Docker Compose não encontrado."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

if [ ! -f .env ]; then
    echo "Criando arquivo .env..."
    cp .env.example .env 2>/dev/null || true
fi

echo "[1/3] Construindo e iniciando containers..."
docker compose up -d --build

echo ""
echo "[2/3] Aguardando banco de dados ficar pronto..."
echo "     (isso pode levar até 30 segundos na primeira vez)"
sleep 15

echo ""
echo "[3/3] Populando banco de dados com produtos de exemplo..."
docker compose exec -T web python scripts/seed.py 2>/dev/null || {
  echo "     Primeira execução - copiando seed atualizado e tentando novamente..."
  docker compose cp backend/scripts/seed.py web:/app/scripts/seed.py 2>/dev/null
  docker compose exec -T web python scripts/seed.py
}

echo ""
echo "============================================"
echo "  Aplicação pronta!"
echo "============================================"
echo ""
echo "  Acesse: http://localhost:8080"
echo "  Admin:  http://localhost:8080/admin/"
echo "  Usuário: admin (senha definida via ADMIN_PASSWORD ou 'admin123')"
echo ""
echo "  Para parar: docker compose down"
echo "============================================"
