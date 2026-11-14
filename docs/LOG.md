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

## 2026-11-14 — R1: rede de segurança (backup, testes confiáveis, baseline)

**O quê**
- **Reconciliação com o upstream:** `origin/main` avançou 9 commits durante o intervalo (CI completo,
  Docker multi-stage/non-root, Django 5.2 LTS, Pillow 13, correção de injeção de fórmula no CSV).
  A branch da R1 foi atualizada com **merge** de `origin/main` (sem reescrever histórico).
  Consequência: o CI (item 5) e o export CSV (D-004) já estavam resolvidos no upstream.
- **Backup 3-2-1** (`docs/BACKUP.md`): dump lógico → Borg `repokey` → `borg prune` → `rclone sync`
  → Telegram + heartbeat; perfil `backup` isolado no Compose. Restore **provado** (27 tabelas,
  199 linhas, 0 divergências) e teste negativo comprovando que o detector acusa divergência (exit 1).
- **Falso verde eliminado (D-030/D-030b):** `scripts/test.sh` monta `backend/` e falha se
  `Ran 0 tests`; `settings.py` usa storage de static simples durante os testes (sem `collectstatic`).
  Comando antigo do README confirmado: `Ran 0 tests ... NO TESTS RAN`.
- **Qualidade dev (D-036/D-039 parcial):** `backend/requirements-dev.txt` (versões idênticas ao CI),
  `pyproject.toml` (ruff/black), `backend/.coveragerc`, `scripts/lint.sh`, `scripts/coverage.sh`.
- **Hook versionado (D-031):** `scripts/hooks/pre-push` + `scripts/install-hooks.sh`
  (`core.hooksPath=scripts/hooks`); executado de ponta a ponta com a suíte verde.
- **Testes de caracterização:** D-001 (pedido fantasma no 400 do PDV), D-002 (subtotal do cliente
  zera o frete), D-003 (frete somado por item no faturamento). Passam **porque os bugs existem**.

**Por quê**
- AGENTS.md §4/R1: backup verificado + restore testado antes de qualquer escrita; suíte confiável,
  baseline medido e plano de rollback. Sem isso, a R2 corrigiria bugs sobre um "verde" falso.

**Evidência**
| Comando | Resultado |
| :-- | :-- |
| `scripts/test.sh` | **Ran 206 tests ... OK** (15 s), sem `collectstatic` |
| `scripts/coverage.sh` | **84%** (1492 stmts, 236 missed) |
| `scripts/lint.sh --select E9,F63,F7,F82` | **0 erros** (gate bloqueante) |
| `scripts/lint.sh --statistics` | 166 achados advisory (56 auto-fixáveis) |
| `black --check backend` | 49 de 62 arquivos a reformatar (advisory) |
| `gitleaks dir .` | 0 (o cert local `nginx/certs/` é gitignored) |
| `gitleaks git . --all` | 2 achados no `.env` de `57fd19a` (D-015 — rotação humana) |
| backup + verify | 27 tabelas / 199 linhas / 0 divergências; teste negativo → exit 1 |

**Commit**
- `feat(backup): stack 3-2-1 com dump logico, Borg criptografado e rclone offsite` (`a26f1c8`)
- `docs(backup): runbook de restore, evidencias da R1 e pendencias` (`b076539`)
- `test/tooling` e `test(characterization)` desta sessão (ver `git log`).

**Docs**
- `docs/BASELINE.md` · `docs/R1-PLANO-ROLLBACK.md` · `docs/BACKUP.md` · `docs/DIVIDA.md`
  (seção "Atualizações da R1") · `docs/PROGRESSO.md` · `README.md` · este `LOG.md`.

**Pendente (aguarda o humano)**
- Rotação dos segredos expostos no histórico (D-015) e configuração real do offsite/Telegram do backup.
- Gate humano da R1 após revisão.

## 2026-11-14 — R1: suíte não depende mais do `.env` do host

**O que** — `settings.py`: HSTS, `SECURE_SSL_REDIRECT` e cookies `Secure` não são ligados durante
`manage.py test` (flag `TESTING`).

**Por quê** — com `DEBUG=False` no `.env` de produção (o correto), o runner — que força `DEBUG=False`
— devolvia 301 em toda requisição e a suíte acusava 123 falhas falsas, mascarando o resultado real.

**Evidência** — `scripts/test.sh` com `DEBUG=False` no `.env` → `Ran 206 tests ... OK`.
