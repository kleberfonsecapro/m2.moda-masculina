# 00 — Visão Geral (R0: como está)

**Projeto:** M2 Moda Masculina — e-commerce de moda masculina (streetwear) + PDV de balcão + painel gerencial.
**Fase:** R0 — Inventário (somente leitura). **Data:** 2026-11-02. **Branch:** `main` @ `ad58319`.
**Tamanho:** 152 arquivos versionados · ~5.715 linhas Python · ~4.837 linhas de template · 6 apps Django.

> Legenda de confiança: ✅ **verificado manualmente** no código durante o R0 · ⚠️ **achado de explorador**, a reconfirmar na fase R2.

---

## 1. O que o sistema é

Loja pública **anônima** (sem cadastro de cliente): catálogo → carrinho em sessão → cálculo de frete (ViaCEP +
tabela própria) → checkout anônimo → pedido. Ao lado, **PDV de balcão** (`/vendas/`, `/m/vendas/`) para venda
presencial com leitor de QR Code e **painel gerencial** (`/gerencial/`) para pedidos, despacho, financeiro e estoque.
A autenticação existe **apenas** para的工作人员 (admin, PDV, gerentes).

## 2. Stack (preservada — não muda)

| Camada | Tecnologia | Evidência |
| :-- | :-- | :-- |
| Runtime | Python 3.12 (`python:3.12-slim`) | `backend/Dockerfile:1` |
| Framework | Django 5.0.x (MVT, server-rendered) | `backend/requirements.txt:1` |
| Banco | MySQL 8.0 (prod) / SQLite `:memory:` (testes) | `docker-compose.yml:8`, `backend/m2shop/settings.py:82-86` |
| ORM | Django ORM (`sql_mode=STRICT_TRANS_TABLES`) | `backend/m2shop/settings.py:76` |
| App server | Gunicorn 3 workers, timeout 120 | `docker-compose.yml:56` |
| Front | Templates Django + CSS/JS próprios; sem build step, sem framework JS | `frontend/` |
| Edge | Nginx 1.26-alpine (TLS) atrás de Traefik v3.1 (Let's Encrypt) | `nginx/`, `traefik-global/` |
| Orquestração | Docker Compose v2 (3 serviços) | `docker-compose.yml` |
| Testes | `unittest`/`django.test` — **200 testes**, 6 apps; `management/` com **0 testes** | `backend/*/tests.py` |

## 3. Estado de maturidade (diagnóstico)

| Dimensão | Estado | Observação |
| :-- | :-- | :-- |
| Funcionalidade | 🟢 **Sólida** | Loja, PDV e gerencial funcionam de ponta a ponta; 200 testes; UI responsiva desktop + mobile. |
| Arquitetura | 🟡 **Acoplada** | Regras de negócio dentro de views (`catalog/views.py` 581 linhas, `management/views.py` 378); duplicação desktop/mobile; 2 carrinhos e 2 estoques divergentes. |
| Segurança | 🔴 **Crítica** | Segredos no histórico git; pedido commitado em erro; frete grátis manipulável; PDV sem checagem de papel vazando custo. |
| Testes | 🟡 **Parcial** | 200 testes sem `reverse()`, 0 testes no app `management`, suíte **não roda na imagem** (`.dockerignore`). |
| Infra | 🟡 **Parcial** | Compose já tem healthchecks, `restart: unless-stopped`, rede interna e volumes; falta multi-stage, `USER`, pin de digest, backup. |
| DR / Backup | 🔴 **Inexistente** | Nenhum dump, Borg, rclone, cron ou restore testado. |
| CI/CD | 🔴 **Inexistente** | Sem `.github/`, sem lint, sem SAST, sem secret scan; deploy manual. |
| Observabilidade | 🔴 **Inexistente** | Sem `LOGGING`, sem `/healthz`, sem alertas, sem Sentry. |
| Documentação | 🟡 **Parcial** | README bom e desatualizado; hook `pre-push` documentado **mas inexistente**; `backlog.md` com ~30 itens. |

## 4. Top 10 riscos (ordenados por severidade × probabilidade)

| # | Sev | Achado | Evidência | Verif. |
| :-- | :-- | :-- | :-- | :-- |
| 1 | 🔴 crítico | `SECRET_KEY` e senhas MySQL **reais commitados** no histórico (`.env` em `57fd19a`, `24315c7`; removido só em `e2be947`) → ainda recuperáveis | `git show 57fd19a:.env` | ✅ |
| 2 | 🔴 crítico | **Pedido falso commitado**: `sales_checkout` retorna erro *dentro* de `transaction.atomic()` sem `set_rollback(True)` → pedido + itens + estoque baixado são gravados apesar da resposta 400 | `backend/catalog/views.py:149-182` (vs. `store_checkout` correto em `:465-480`) | ✅ |
| 3 | 🔴 crítico | **Frete grátis manipulável**: `/frete/calcular/` aceita `subtotal` do cliente e o aplica no limiar de isenção | `backend/shipping/views.py:49-56` + `backend/shipping/services.py:75` | ✅ |
| 4 | 🔴 alto | **Faturamento do gerencial está errado** (fan-out de JOIN): `Sum('shipping_cost')` soma o frete **uma vez por item** e `Count('id')` conta **itens**, não pedidos | `backend/management/views.py:52-63`, `:73-75`, `:253-294` | ✅ |
| 5 | 🟠 alto | **Nginx força `https://$host:8443` com certificado `localhost.pem`** → o TLS público do Traefik (Let's Encrypt) é contornado; usuário cai em cert self-signed | `nginx/nginx.conf:8,14-15` + `traefik-global/config/dynamic.yml:31` | ✅ |
| 6 | 🟠 alto | **PDV sem checagem de papel**: `/vendas/*` e `/vendas/estoque/` exigem só `login_required`; qualquer conta logada vende e vê `purchase_price` (custo) | `backend/catalog/views.py:63,75,125,197,215,228,253` + `frontend/templates/catalog/stock.html:178` | ✅ |
| 7 | 🟠 alto | **Suíte não roda na imagem**: `.dockerignore` exclui `**/tests.py` → o comando do README executa **0 testes** e reporta "OK" (falso verde). *Provado por execução: `Ran 0 tests ... NO TESTS RAN`.* | `.dockerignore:1` + `backend/Dockerfile:20` + `README.md:108-119` | ✅ |
| 8 | 🟠 alto | **Sem backup/DR**: não existe dump, Borg, rclone, cron nem restore testado; um incidente de dados é perda total | ausência verificada no repo e no `crontab` | ✅ |
| 9 | 🟠 alto | **Export CSV quebrado (500)**: `OrderListView().get_queryset(request)` — assinatura sem `request` e `self.request` nunca definido | `backend/management/views.py:347` + `:104-108` | ✅ |
| 10 | 🟠 médio | **Sem CI e sem gate**: `main` recebe push direto; nenhum lint/SAST/secret scan; hook `pre-push` documentado mas inexistente | `.github/` ausente, `README.md:123-127` | ✅ |

## 5. Riscos de negócio (não técnicos, mas que definem a prioridade)

- **Estoque duplo e divergente**: `Product.stock` (usado pelo PDV) vs `Variant.stock` (usado pelo site). Cancelar pedido **não repõe** estoque; oversell é possível (variante não travada com `select_for_update`). ⚠️
- **Checkout do site sempre cria pedido `payment_method='cash'`** — não há pagamento online (PIX/cartão) real. ⚠️
- **SMTP configurado e nunca usado** — a UI promete e-mail de confirmação que não existe. ⚠️
- **Cancelar pedido não repõe estoque** e **apagar produto apaga histórico de pedido** (`OrderItem.product` em `CASCADE`). ⚠️

## 6. Decisões que dependem do humano (bloqueiam fases seguintes)

1. **Rotação de segredos** — o agente detecta, **o humano rotaciona** `SECRET_KEY`, `MYSQL_PASSWORD` e `MYSQL_ROOT_PASSWORD`. O histórico git não pode ser reescrito sem aprovação (vermelho).
2. **Purge do histórico** — reescrever git é vermelho; alternativa segura = rotacionar + documentar.
3. **Modelo de estoque** — unificar `Product.stock` e `Variant.stock` toca schema (migration) = **vermelho**.
4. **Frete grátis** — corrigir exige o servidor calcular o subtotal a partir do carrinho (mudança de contrato da API interna `POST /frete/calcular/`).
5. **TLS na borda** — remover o redirect `:8443` do nginx muda o comportamento de acesso (vermelho para deploy, mas essencial).
6. **Conta de acesso do PDV** — exigir `staff` ou grupo "Vendedores" altera a autorização (pode bloquear vendedores legítimos → precisa de regra de negócio do humano).

## 7. Próximo passo (gate R0 → R1)

Aguardando aprovação do humano para entrar em **R1 (Rede de segurança)**:

1. **Backup verificado + restore testado** (dump MySQL → Borg → rclone → Telegram) — **antes de qualquer escrita em produção**.
2. **Fix do falso verde** dos testes (`.dockerignore` + `requirements-dev.txt` + comando real de teste) — falha funcional, baixo risco.
3. **Caracterização** dos caminhos críticos (checkout site, checkout PDV, gerencial, frete).
4. **Baseline** (`docs/BASELINE.md`): lint, tipos, cobertura, vulnerabilidades — em modo relatório.
5. **CI de baseline** (GitHub Actions, sem deploy) + `core.hooksPath` versionado.
6. **Plano de rollback** documentado.

Ver `docs/DIVIDA.md` para o inventário completo de dívida e `docs/LOG.md` para o histórico de passos.
