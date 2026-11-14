#!/usr/bin/env bash
#
# Deploy de produção do m2.moda-masculina.
#
# Instalado na VPS em /home/kleber/deploy-m2.sh e acionado pelo GitHub Actions
# via SSH com uma chave restrita (forced command) no ~/.ssh/authorized_keys:
#
#   command="/home/kleber/deploy-m2.sh",restrict ssh-ed25519 AAAA... m2-deploy
#
# A chave NÃO dá shell: o único argumento aceito é o SHA (40 hex) a implantar,
# que chega em $SSH_ORIGINAL_COMMAND. Uso manual na VPS:
#
#   /home/kleber/deploy-m2.sh <sha>               # deploy normal
#   /home/kleber/deploy-m2.sh <sha> --rollback    # volta para um commit anterior
#
# Fonte versionada: scripts/vps/deploy-m2.sh (reinstale com
#   install -m 755 scripts/vps/deploy-m2.sh /home/kleber/deploy-m2.sh)
set -Eeuo pipefail
set -f  # sem expansão de glob nos argumentos recebidos via SSH

APP_DIR=/home/kleber/m2.moda-masculina
LOG_DIR="$APP_DIR/logs"
CERT_KEY="$APP_DIR/nginx/certs/localhost-key.pem"
NGINX_GID=101

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_DIR/deploy.log") 2>&1

fail() { echo "ERRO: $*"; exit 1; }

# shellcheck disable=SC2206
args=(${SSH_ORIGINAL_COMMAND:-$*})
SHA="${args[0]:-}"
MODE="${args[1]:-}"

echo "=== deploy $(date -u +%FT%TZ) sha=${SHA:-<vazio>} ${MODE} ==="

[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || fail "argumento inválido: esperado SHA de 40 caracteres hex."
[[ -z "$MODE" || "$MODE" == "--rollback" ]] || fail "opção desconhecida: $MODE"
[[ ${#args[@]} -le 2 ]] || fail "argumentos demais."

# Um deploy por vez.
exec 9>"$LOG_DIR/deploy.lock"
flock -w 900 9 || fail "outro deploy em andamento há mais de 15 min."

cd "$APP_DIR"

# Pré-checagens do ambiente (problemas já vistos em produção).
[[ -f .env ]] || fail ".env ausente em $APP_DIR."
[[ -f "$CERT_KEY" ]] || fail "certificado ausente: $CERT_KEY."
if [[ "$(stat -c %g "$CERT_KEY")" != "$NGINX_GID" ]] || (( ( 8#$(stat -c %a "$CERT_KEY") & 040 ) == 0 )); then
    fail "a chave do certificado precisa ser legível pelo grupo $NGINX_GID (nginx). Rode: sudo chown root:$NGINX_GID nginx/certs/*.pem && sudo chmod 640 $CERT_KEY"
fi

git fetch --quiet origin main
git merge-base --is-ancestor "$SHA" origin/main \
    || fail "$SHA não pertence ao histórico de origin/main."

CURRENT="$(git rev-parse HEAD)"
if [[ "$CURRENT" != "$SHA" ]] && git merge-base --is-ancestor "$SHA" "$CURRENT" && [[ "$MODE" != "--rollback" ]]; then
    fail "$SHA é mais antigo que o commit em produção ($CURRENT). Use --rollback para voltar de propósito."
fi

echo "produção: ${CURRENT:0:7} -> ${SHA:0:7}"
git reset --hard --quiet "$SHA"

docker compose up -d --build --remove-orphans

echo "aguardando healthchecks..."
for _ in $(seq 1 60); do
    ok=1
    for c in m2-django m2-nginx; do
        state="$(docker inspect -f '{{.State.Status}}' "$c" 2>/dev/null || echo missing)"
        health="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$c" 2>/dev/null || true)"
        case "$state" in
            restarting|exited|dead|missing)
                docker compose ps
                docker compose logs --tail=100 web nginx
                fail "$c em estado '$state'." ;;
        esac
        [[ "$health" == "healthy" ]] || ok=0
    done
    if (( ok )); then
        curl -skf -o /dev/null https://127.0.0.1:8443/healthz || fail "/healthz não respondeu 200."
        docker compose ps
        docker image prune -f >/dev/null || true
        echo "deploy OK: $(git log -1 --format='%h %s')"
        exit 0
    fi
    sleep 5
done

docker compose ps
docker compose logs --tail=100 web nginx
fail "serviços não ficaram healthy em 5 minutos."
