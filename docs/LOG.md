# LOG — Registro de passos

Formato: **O quê** / **Por quê** / **Evidência** / **Commit** / **Docs**. Curto e datado.

---

## 2026-11-02 — R0: Inventário (somente leitura)

**O quê**
- Instalado o playbook de retrofit como `AGENTS.md` da raiz (substitui o contrato global anterior),
  com a seção 2 preenchida com a stack detectada e o teto da seção 12 definido.
- Contrato anterior preservado em `docs/AGENTS-PADRAO-GLOBAL.md` (não é carregado automaticamente).
- Executado o inventário R0 com 5 subagentes **somente leitura** (domínio, camada web, infra/segredos,
  testes/qualidade/CI, superfície de segurança) + verificação manual dos achados críticos.
- Produzidos: `docs/00-VISAO.md`, `docs/01-ARQUITETURA.md`, `docs/MAPA-DO-CODIGO.md`,
  `docs/02-CONTRATOS.md`, `docs/DIVIDA.md` (**81 itens de dívida**, D-001..D-079 + D-030b + D-073b),
  `docs/PROGRESSO.md`.

**Por quê**
- Estabelecer a linha de base *como está* antes de qualquer escrita, conforme AGENTS.md §3/§4:
  "Antes de R1 concluída: só leitura (R0), documentação e backup."

**Evidência** (verificados manualmente no código e **por execução**)

### Validação executada (build + suíte real)

| Comando | Resultado |
| :-- | :-- |
| `docker compose build web` | ✅ imagem `m2moda-masculina-web:latest` construída |
| `docker compose run --rm --no-deps web python manage.py test` (comando do README) | ❌ **`Ran 0 tests in 0.000s` / `NO TESTS RAN`** → falso verde (D-030) |
| `docker compose run --rm --no-deps -v "$PWD/backend:/app/backend" web python manage.py test` | ⚠ `Ran 200 tests` → **FAILED (errors=50)**: `ValueError: Missing staticfiles manifest entry for 'images/logo-m2.jpg'` (D-030b) |
| `docker compose run --rm --no-deps -v "$PWD/backend:/app/backend" web sh -c "python manage.py collectstatic --noinput && python manage.py test"` | ✅ **`Ran 200 tests in 14.567s` → OK** — baseline verde (receita oficial da R1) |
| `docker compose run ...` sem `.env` | ❌ `env file .env not found` + `network web declared as external, but could not be found` (D-061, D-073b) |

### Achados verificados no código

| Achado | Evidência |
| :-- | :-- |
| Segredos reais no histórico git | `git show 57fd19a:.env` → `SECRET_KEY`, `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` (removido só em `e2be947`) |
| Pedido commitado em caso de erro | `backend/catalog/views.py:149-182` (`return` dentro de `atomic()` sem `set_rollback`) vs. `:475` (correto) |
| Frete grátis manipulável | `backend/shipping/views.py:49-56` → `backend/shipping/services.py:75` |
| Faturamento com fan-out de JOIN | `backend/management/views.py:52-63`, `:73-75`, `:253-294` |
| Export CSV 500 | `backend/management/views.py:347` vs. `:104-108` (`self.request` inexistente) |
| TLS público contornado | `nginx/nginx.conf:8,14-15` + `traefik-global/config/dynamic.yml:31` |
| PDV sem checagem de papel | `backend/catalog/views.py:63,75,125,197,215,228,253`; `frontend/templates/catalog/stock.html:178` |
| Suíte não roda na imagem (falso verde) | `.dockerignore:1` + `backend/Dockerfile:20` + `README.md:108-119` |
| Sem backup/DR | nenhum `*backup*`/`*borg*`/`*rclone*`/`cron` no repo; `crontab -l` vazio |
| Sem CI | `.github/` inexistente; `.git/hooks/pre-push` inexistente (README afirma que existe) |

**Commit**
- Ainda não commitado — aguarda aprovação do gate R0 e revisão das docs.

**Docs**
- `AGENTS.md` (raiz) · `docs/00-VISAO.md` · `docs/01-ARQUITETURA.md` · `docs/MAPA-DO-CODIGO.md` ·
  `docs/02-CONTRATOS.md` · `docs/DIVIDA.md` · `docs/PROGRESSO.md` · `docs/AGENTS-PADRAO-GLOBAL.md` · este `LOG.md`.

**Limpeza do ambiente de validação**
- `.env` temporário (chaves falsas, só para a validação) **removido** ao final.
- `backend/staticfiles/` gerado pelo `collectstatic` — já ignorado pelo `.gitignore` (`.gitignore:13`).
- Rede Docker externa `web` criada (`docker network create web`) — passo já documentado no `README.md:158`.

**Pendente (aguarda o humano)**
- Rotação de `SECRET_KEY`, `MYSQL_PASSWORD` e `MYSQL_ROOT_PASSWORD` (o agente detecta; o humano rotaciona).
- Aprovação para iniciar **R1** (backup + restore testado, fix do falso verde dos testes, caracterização, baseline, CI de baseline).

---

## 2026-11-14 — Publicação do M2 no Traefik global

**O quê**
- Descoberto que o Traefik em produção **não é** o stack `traefik-global/` deste repo: roda em
  `/home/kleber/traefik` (projeto `traefik`, container `traefik_global`, Traefik v3.7.1, file provider
  `dynamic.yml` + dashboard com basicauth). As cópias do repo estavam obsoletas (drift de D-075).
- Adicionado `m2-nginx` à rede externa `traefik_global` (`docker-compose.yml`) para o Traefik
  resolvê-lo por nome.
- Adicionados routers `m2-http` (redirect) e `m2-https` (TLS/ACME) + service `m2` →
  `http://m2-nginx:80` em `/home/kleber/traefik/dynamic.yml` (com backup datado no mesmo diretório).
- `nginx/nginx.conf`: a porta 80 agora **serve o proxy** quando a requisição vem do Traefik
  (`X-Forwarded-Proto` preenchido, TLS terminado na borda) e mantém o `301 → :8443` apenas no acesso
  direto ao container. Resolve D-060 no caminho público, sem quebrar o acesso local.
- `.env`: `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` passaram a incluir `m2moda.com.br`/`www`.
- `nginx/certs/` gerado localmente (self-signed, gitignored) para o listener 443 — D-073.
- Healthcheck do `m2-nginx` passou a sondar `/admin/login/` (o `/` retorna 500 por dados de teste
  sem imagem — D-080; sonda de liveness não deve depender do catálogo).

**Por quê**
- Pedido do humano: deixar a aplicação registrada na borda para já receber a URL quando o domínio
  for comprado, sem mudar a stack nem o comportamento interno.

**Evidência**
- `docker network inspect traefik_global` → `m2-nginx 172.18.0.6`.
- `curl -k --resolve m2moda.com.br:443:127.0.0.1 https://m2moda.com.br/admin/login/` → **200**
  (idem `/vendas/entrar/`, `/gerencial/entrar/`, `/carrinho/`); `http://…/` → **301** para https.
- `docker logs traefik_global` → roteia `m2-https@file` → `http://m2-nginx:80`; ACME falha com
  `NXDOMAIN` para `m2moda.com.br` (domínio ainda não comprado/apontado) — esperado.
- `curl` local `:8443` e `inventarius`/`ffsystem` continuam respondendo (sem regressão).
- `docker inspect m2-nginx` → `healthy`; suíte `manage.py test` → **Ran 200 tests ... OK**.
- ⚠️ `GET /` continua **500** por dados de teste (`Product.image` vazio em 2 registros) — D-080,
  fora desta mudança.

**Commit**
- Pendente (aguarda revisão humana).

**Docs**
- `docs/LOG.md` · `docs/DIVIDA.md` (D-060 atualizado, D-080 novo) · `docs/01-ARQUITETURA.md`.
- Runbook: `docs/TRAEFIK.md`.
