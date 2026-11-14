# DECISOES — Registro de decisões (ADR)

Formato: contexto → decisão → consequências. Uma entrada por decisão relevante.

---

## ADR-001 — 2026-11-14 — Borda TLS no Traefik; nginx da app sem redirect

**Status** — aprovado pelo humano (mudança classificada como vermelha: altera acesso público).

**Contexto** — o `nginx/nginx.conf` respondia `301 https://$host:8443` em qualquer requisição HTTP.
Como o Traefik termina o TLS e encaminha `http://m2-nginx:80`, o 301 desviava o cliente para a
porta `8443` com o certificado local `localhost.pem` — contornando o TLS do Let's Encrypt e
podendo gerar loop de redirecionamento. Registrado como D-060 em `docs/DIVIDA.md`.

**Decisão**
1. O redirect HTTP→HTTPS é responsabilidade exclusiva do Traefik (`entryPoints.web.http.redirections`).
2. O server `listen 80` do nginx passa a **servir** a aplicação (locations em
   `nginx/snippets/app-locations.conf`), sem redirecionar.
3. O `listen 443` (publicado como `8443`) permanece apenas para diagnóstico direto, com o
   certificado local.
4. `X-Forwarded-Proto` é preservado via `map`: quando o Traefik envia `https`, o Django mantém
   `SECURE_PROXY_SSL_HEADER`/`SECURE_SSL_REDIRECT`; sem proxy, usa `$scheme`.

**Consequências**
- O acesso público volta a usar o certificado válido da borda; `:8443` deixa de ser caminho de acesso.
- As locations ficam em um único arquivo incluído pelos dois `server` blocks (sem duplicação).
- O snippet vive em `/etc/nginx/snippets/` porque `conf.d/*.conf` é incluído no contexto `http`,
  onde `location` é inválido.
- Rollback: reverter o commit e reimplantar o SHA anterior com `deploy-m2.sh <sha> --rollback`.
