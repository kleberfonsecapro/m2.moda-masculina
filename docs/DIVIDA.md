# DÍVIDA TÉCNICA — inventário inicial (R0)

**Data:** 2026-11-02 · **Fase:** R0 · **Fonte:** inventário do código + exploradores somente leitura.

**Legenda de severidade:** 🔴 crítica · 🟠 alta · 🟡 média · ⚪ baixa.
**Esforço:** P (≤ 1 h) · M (≤ 1 dia) · G (> 1 dia) · XL (> 1 semana).
**Risco da correção:** 🟢 baixo · 🟡 médio (exige cuidado) · 🔴 alto (quebra contrato/precisa de decisão).

> Regra da catraca (AGENTS.md §7): dívida **não** bloqueia o CI; ela é paga quando o código é tocado.
> **Um item por PR**, com teste de regressão.

## Atualizações da R1 (2026-11-14)

O repositório avançou em paralelo (`origin/main`: CI, multi-stage/non-root, Django 5.2, export CSV).
O que mudou no inventário original:

| Item | Situação em 2026-11-14 |
| :-- | :-- |
| **D-030** (falso verde: `Ran 0 tests ... OK`) | ✅ **corrigido** — `scripts/test.sh` monta `backend/` e **falha se 0 testes**; README atualizado |
| **D-030b** (manifesto de static derrubava 50 testes) | ✅ **corrigido** — `settings.py` usa storage simples quando `test` está em `sys.argv` |
| **D-031** (hook pre-push documentado mas inexistente) | ✅ **corrigido** — `scripts/hooks/pre-push` versionado + `core.hooksPath` (via `scripts/install-hooks.sh`) |
| **D-036** (sem linter/formatter/cobertura) | 🟡 **parcial** — `pyproject.toml` + `requirements-dev.txt` + `scripts/lint.sh`/`coverage.sh`; falta type-checker e pre-commit |
| **D-039** (sem lockfile/hashes) | 🟡 **parcial** — dev deps fixadas; runtime segue com ranges, lockfile com hashes pendente |
| **D-004** (export CSV 500) | ✅ **corrigido no upstream** (`d37f102`) com teste de regressão em `management/tests.py` |
| **D-059** (sem backup/DR) | ✅ **corrigido** — stack 3-2-1 com restore provado (`docs/BACKUP.md`) |
| **D-001, D-002, D-003** | 🧪 **caracterizados** (testes congelam o bug); correção é R2 |
| **D-080** (home 500 com produto sem imagem) | confirmado: até o PDV quebra ao montar o JSON do item (`catalog/views.py:118`) sem imagem |

Baseline medido e metas: `docs/BASELINE.md`.

---

## A. Correção / integridade de dados (prioridade máxima)

| ID | Local | Problema | Sev | Esf. | Risco |
| :-- | :-- | :-- | :-- | :-- | :-- |
| D-001 | `backend/catalog/views.py:149-182` | `sales_checkout` retorna erro **dentro** de `transaction.atomic()` sem `set_rollback(True)` → **pedido + itens + estoque são commitados apesar do HTTP 400**. O checkout do site (`:475`) faz certo. | 🔴 | P | 🟢 (espelhar `store_checkout`) |
| D-002 | `backend/shipping/views.py:49-56` | `/frete/calcular/` usa o `subtotal` **enviado pelo cliente** no limiar de frete grátis → manipulação de preço | 🔴 | M | 🟡 (muda contrato da API interna) |
| D-003 | `backend/management/views.py:52-63,73-75,253-294` | Agregações com fan-out de JOIN: frete somado uma vez por item; `Count('id')` conta itens, não pedidos → **financeiro/dashboard incorretos** | 🔴 | M | 🟡 (corrige números já exibidos) |
| D-004 | `backend/management/views.py:347` | `ExportOrdersView` chama `OrderListView().get_queryset(request)` → assinatura sem `request` e `self.request` inexistente → **500** na exportação CSV | 🟠 | P | 🟢 |
| D-005 | `backend/catalog/views.py:506-507` | Estoque baixado de `Variant` sem `select_for_update` (só `Product` é travado) → **oversell concorrente** | 🟠 | M | 🟡 |
| D-006 | `backend/management/views.py:168-188` | Cancelar pedido **não repõe estoque** (não existe nenhum `stock +=` no backend) | 🟠 | M | 🟡 (decisão de negócio) |
| D-007 | `backend/orders/models.py:66-68` | `OrderItem.product` com `on_delete=CASCADE` → apagar produto **apaga o histórico** de pedidos; sem snapshot de nome | 🟠 | G | 🔴 (migration = vermelho) |
| D-008 | `backend/catalog/views.py:156,173-180` | PDV ignora `Variant` e grava `email=request.user.email` no pedido do cliente | 🟡 | M | 🟡 |
| D-009 | `backend/catalog/views.py:93,231,256` | `Cart.objects.get_or_create(user=...)` com `OneToOne` → `IntegrityError` sob concorrência | 🟡 | P | 🟢 |
| D-010 | `backend/catalog/views.py:385-391` | `update_cart` não checa estoque ao aumentar quantidade (só no checkout) | 🟡 | P | 🟡 |
| D-011 | `backend/catalog/views.py:435-440,485-488` | Frete fica travado na sessão e é reutilizado no checkout **sem recálculo** | 🟡 | M | 🟡 |
| D-012 | `backend/cart/models.py:47` | `unique_together(cart,product,variant)` com `variant` nullable → MySQL trata NULL como distinto → item duplicado | 🟡 | G | 🔴 (migration) |
| D-013 | `backend/shipping/services.py:40-47` | Faixa de CEP comparada como string, sem normalizar o valor gravado no admin | 🟡 | P | 🟢 |
| D-014 | `backend/catalog/models.py:104-108` | `promotional_price` sem validação contra `price` → desconto negativo possível | 🟡 | P | 🟡 |

## B. Segurança

| ID | Local | Problema | Sev | Esf. | Risco |
| :-- | :-- | :-- | :-- | :-- | :-- |
| D-015 | histórico git (`57fd19a`, `24315c7`) | **`.env` com `SECRET_KEY` e senhas MySQL reais commitados**; removido só em `e2be947` → ainda recuperáveis | 🔴 | — | 🔴 **rotação é humana**; purge = vermelho |
| D-016 | `backend/catalog/views.py:63,75,125,197,215,228,253` + `backend/mobile/views.py:120` | PDV e estoque exigem **só `login_required`** → qualquer conta logada vende e vê `purchase_price` (custo) | 🟠 | M | 🟡 (pode bloquear vendedores) |
| D-017 | `backend/catalog/urls.py:10`, `backend/mobile/urls.py:16`, `backend/management/auth_views.py:8` | **Nenhum rate limit/lockout** nos 3 logins (`django-ratelimit` só no newsletter) | 🟠 | M | 🟡 |
| D-018 | `backend/m2shop/settings.py:133-137` + `docker-compose.yml:56` | Cache `LocMem` por processo com 3 workers → o único rate limit existente é contornável | 🟡 | M | 🟡 (dependência nova) |
| D-019 | `frontend/static/js/mobile/app.js:26`, `frontend/templates/mobile/sales/sales_page.html:603`, `frontend/templates/base.html:453,488` | `innerHTML` com dados do servidor → **XSS DOM** | 🟠 | M | 🟡 |
| D-020 | `backend/catalog/middleware.py:13` | CSP com `script-src 'unsafe-inline'` → neutraliza a defesa contra XSS inline | 🟡 | G | 🟡 (exige nonces/hashes) |
| D-021 | `backend/m2shop/admin_views.py:5-7`, `backend/management/auth_views.py:29-33` | Logout por **GET**, sem CSRF; `/gerencial/sair/` sem exigir gerente | 🟡 | P | 🟡 (links existentes) |
| D-022 | `backend/management/models.py:36` + `nginx/nginx.conf:18` | Upload de `label_pdf` sem validar tipo/tamanho/extensão; `client_max_body_size 100M` | 🟡 | P | 🟢 |
| D-023 | `backend/management/templates/management/dashboard.html:110`, `financial.html:122-125` | `|safe` serializando dicts Python (`repr`) → quebra o JS e abre espaço para injeção | 🟡 | P | 🟢 (`json_script`) |
| D-024 | `backend/management/auth_views.py:8-26` | `manager_login` não valida `next` (open redirect) | 🟡 | P | 🟢 |
| D-025 | `backend/m2shop/settings.py:9,147-154` | `DEBUG=True` é o default do `.env.example`; `DEBUG` sem trava → traceback/SQL expostos | 🟠 | P | 🟢 |
| D-026 | `backend/scripts/seed.py:32-35` + `README.md:75` | Superusuário criado com senha fallback `'admin123'`, sem passar pelos validadores | 🟠 | P | 🟡 |
| D-027 | `backend/shipping/services.py:19-30` | ViaCEP síncrono no request, sem cache/retry; falha silenciosa vira "CEP não encontrado" | 🟡 | M | 🟡 |
| D-028 | `backend/m2shop/settings.py:104` | Sessão de 24 h, sem expiração absoluta/revogação, sem MFA para gerentes | ⚪ | G | 🟡 |
| D-029 | `backend/catalog/views.py:288-292` | `/buscar/` público expõe estoque, preço e % de desconto | ⚪ | P | 🟡 |

## C. Testes e qualidade

| ID | Local | Problema | Sev | Esf. | Risco |
| :-- | :-- | :-- | :-- | :-- | :-- |
| D-030 | `.dockerignore:1` + `backend/Dockerfile:20` | Testes fora da imagem → o comando do README **roda 0 testes e reporta "OK"** (falso verde) — *provado: `Ran 0 tests ... NO TESTS RAN`* | 🟠 | P | 🟢 |
| D-030b | `backend/m2shop/settings.py:117` | `ManifestStaticFilesStorage` **quebra 50 testes** quando a suíte roda sem `collectstatic` ("Missing staticfiles manifest entry") — em CI/fresh container a suíte fica vermelha por causa disso, não do código | 🟠 | P | 🟢 |
| D-031 | `README.md:123-127` | Hook `pre-push` **documentado mas inexistente**; hooks em `.git/hooks` não são versionados | 🟠 | P | 🟢 (`core.hooksPath`) |
| D-032 | `backend/management/` | App inteiro (autorização, despacho, financeiro) **sem um único teste** | 🟠 | G | 🟢 |
| D-033 | `backend/*/tests.py` | 129 URLs hardcoded, **zero `reverse()`** → renomear rota quebra testes silenciosamente | 🟡 | G | 🟢 |
| D-034 | `backend/cart/tests.py:73`, `backend/catalog/tests.py:61,128,149` | `assertRaises(Exception)` genérico (passa com qualquer exceção) | 🟡 | P | 🟢 |
| D-035 | `backend/catalog/tests.py:69-70,...`, `backend/shipping/tests.py:142,193` | 11 `assertTrue` sem mensagem → falha não indica o motivo | ⚪ | P | 🟢 |
| D-036 | — | **Sem linter, sem type-checker, sem coverage, sem pre-commit, sem `pyproject.toml`/lockfile** | 🟠 | M | 🟢 (ferramenta de dev = amarelo) |
| D-037 | `backend/catalog/views.py:554` | `@ratelimit` do newsletter **sem teste** | 🟡 | P | 🟢 |
| D-038 | `backend/catalog/middleware.py:7` | CSP e headers de segurança **sem teste** | 🟡 | P | 🟢 |
| D-039 | `backend/requirements.txt` | Sem lockfile/hashes → builds **não reprodutíveis**; sem `requirements-dev.txt` | 🟡 | M | 🟡 |
| D-040 | `backend/requirements.txt:6-7` | `django-colorfield` sem uso no código; `django-admin-interface` só declarado | ⚪ | P | 🟡 |
| D-041 | `README.md:108` | README diz "154 testes / 5 apps"; real = **200 testes / 6 apps** | ⚪ | P | 🟢 |

## D. Arquitetura e dívida estrutural

| ID | Local | Problema | Sev | Esf. | Risco |
| :-- | :-- | :-- | :-- | :-- | :-- |
| D-042 | `backend/catalog/views.py` (581 linhas) | App "faz-tudo": catálogo + carrinho + checkout + PDV + estoque + busca + newsletter em um arquivo | 🟠 | G | 🟡 |
| D-043 | `frontend/templates/catalog/sales.html` (981) · `base.html` (704) · `mobile/sales/sales_page.html` (636) | Templates gigantes com JS inline (violam o limite de ~300 linhas do AGENTS.md §7) | 🟡 | G | 🟡 |
| D-044 | `backend/mobile/views.py` + `frontend/templates/mobile/**` | Duplicação desktop↔mobile (8 pares de templates, lógica de carrinho/PDV/frete copiada) | 🟠 | XL | 🟡 |
| D-045 | `backend/cart/services.py` vs `backend/cart/models.py` | Dois carrinhos (sessão × banco) que **não sincronizam** | 🟠 | G | 🟡 |
| D-046 | `backend/catalog/models.py` (`Product.stock`) vs `Variant.stock` | Duas fontes de estoque divergentes entre canais | 🟠 | G | 🔴 (migration) |
| D-047 | `backend/management/signals.py:11-28` | `CurrentUserMiddleware` guarda estado em **atributo de função** → não thread-safe com 3 workers | 🟡 | P | 🟡 |
| D-048 | `backend/catalog/models.py:120-157` | QR Code regerado (com preço embutido) a cada `save()` → I/O em toda edição | ⚪ | M | 🟡 |
| D-049 | `backend/catalog/models.py:220-223`, `backend/shipping/models.py:35-38` | Singletons **descartam silenciosamente** a criação quando já existe | ⚪ | P | 🟢 |
| D-050 | `backend/orders/models.py:55-58` | `Order.total` itera itens → N+1 no admin e no CSV | 🟡 | M | 🟢 |
| D-051 | `backend/catalog/views.py:25-27,38,53-55`, `backend/cart/services.py:8-33` | N+1 em listagens e no carrinho de sessão (`get_cart_total` refaz `get_cart_items`) | 🟡 | M | 🟢 |
| D-052 | `backend/catalog/context_processors.py:25-26,41-42` | `except Exception` engole falhas e devolve vazio | ⚪ | P | 🟢 |
| D-053 | `backend/accounts/` | App morto (só comentários) ainda em `INSTALLED_APPS` | ⚪ | P | 🟢 |
| D-054 | `frontend/templates/**` (7 arquivos) | `getCookie` duplicado em 7 templates; 2 versionamentos de estáticos (`ManifestStaticFilesStorage` + tag `static_versioned`) | ⚪ | M | 🟢 |
| D-055 | `frontend/static/landpage.html` | Página HTML dentro de `STATICFILES_DIRS` → publicada como `/static/landpage.html`, sem rota | ⚪ | P | 🟡 |
| D-056 | `backend/catalog/urls.py:14` | `/vendas/buscar/` órfã (sem consumidor no front) | ⚪ | P | 🟢 |
| D-057 | `backend/mobile/middleware.py:25-64` | Mapa de redirecionamento divergente entre plataformas (`/produtos/<slug>/` é lista desktop, mas vira `/m/categorias/<slug>/`) | 🟡 | M | 🟡 |
| D-058 | `backend/scripts/seed.py:20-27` | Seed baixa imagens da internet (Unsplash) → build não determinístico | ⚪ | M | 🟡 |

## E. Infraestrutura e operação

| ID | Local | Problema | Sev | Esf. | Risco |
| :-- | :-- | :-- | :-- | :-- | :-- |
| D-059 | — | **Nenhum backup/DR**: sem dump, Borg, rclone, cron, alerta ou restore testado | 🔴 | G | 🟢 (roteiro do AGENTS.md §10) |
| D-060 | `nginx/nginx.conf:8,14-15` | Nginx força `https://$host:8443` com cert `localhost.pem` → **TLS do Let's Encrypt contornado** | 🟠 | M | 🔴 (muda acesso público) |
| D-061 | `scripts/start.sh:24-27` | Copia `.env.example` → `.env` automaticamente, propagando `DEBUG=True` e senhas placeholder para produção | 🟠 | P | 🟡 |
| D-062 | `backend/Dockerfile:7-13` | Single-stage: `gcc`, `libmariadb-dev`, `pkg-config` na imagem final | 🟡 | M | 🟢 |
| D-063 | `backend/Dockerfile` (sem `USER`) | Container **inicia como root** e faz `chown -R` a cada boot (o processo final roda como `appuser` via `gosu`) | 🟡 | M | 🟡 |
| D-064 | `docker-compose.yml:8`, `traefik-global/docker-compose.yml:3`, `nginx/Dockerfile:1` | Imagens sem pin por digest/patch | 🟡 | P | 🟡 |
| D-065 | `traefik-global/config/traefik.yml:1-3` | `api.dashboard:true` + `api.debug:true` sem autenticação na borda | 🟠 | P | 🟡 |
| D-066 | `traefik-global/config/dynamic.yml:36` | Router aponta para `http://nginx_blend:80` — container inexistente (o compose do ref usa `blend-nginx`) | 🟡 | P | 🟡 |
| D-067 | `nginx/nginx.conf:23-32` | Sem gzip, sem cache de proxy; `/media/` com `Cache-Control immutable` (bug) | 🟡 | P | 🟢 |
| D-068 | `nginx/nginx.conf` | Sem HSTS e sem CSP no nginx (só no Django, com `unsafe-inline`) | 🟡 | P | 🟡 |
| D-069 | `docker-compose.yml:54` | `migrate --fake-initial` a cada boot → pode mascarar drift de schema | 🟡 | M | 🟡 |
| D-070 | `docker-compose.yml:7-26` | Serviço `db` sem `read_only`/`cap_drop`/`no-new-privileges`; sem usuário dedicado no MySQL | ⚪ | M | 🟡 |
| D-071 | — | Sem `/healthz` (healthchecks são TCP/socket), sem `LOGGING` estruturado, sem Sentry/alertas/heartbeat | 🟠 | M | 🟢 |
| D-072 | `nginx/Dockerfile:4` | `EXPOSE 8080` incorreto (escuta 80/443) | ⚪ | P | 🟢 |
| D-073 | `.gitignore:31` + `docker-compose.yml:72` | `nginx/certs/` não existe no repo → container não sobe em clone novo sem passo manual (mkcert) | ⚪ | P | 🟡 |
| D-073b | `docker-compose.yml:42-43` + `docker-compose.yml:85` | `docker compose` **falha** em ambiente novo: exige `.env` (não existe no clone) e a rede externa `web` (`docker network create web`) — passos manuais não automatizados | 🟡 | P | 🟡 |
| D-074 | `blendburguer-ref/` | 2 arquivos de **outro projeto** versionados, órfãos, com senhas fracas literais (`sua_senha_aqui`) | 🟡 | P | 🟡 |
| D-075 | `traefik/` vs `traefik-global/config/` | Cópia duplicada **com drift** (`blend-nginx` vs `nginx_blend`) | 🟡 | P | 🟡 |

## F. Documentação

| ID | Local | Problema | Sev | Esf. | Risco |
| :-- | :-- | :-- | :-- | :-- | :-- |
| D-076 | — | Sem ADRs, sem contrato de API documentado, sem diagrama de fluxo oficial | ⚪ | M | 🟢 |
| D-077 | `README.md:170-174` | README promete e-mail de confirmação que **não existe** (SMTP configurado e nunca usado) | 🟡 | P | 🟢 |
| D-078 | `backlog.md` (raiz) | Backlog em `backlog.md` na raiz; o playbook espera `docs/BACKLOG.md` | ⚪ | P | 🟢 |
| D-079 | `README.md:19,108,123` | README sem README de execução em 5 min testável; contagem de testes e hook desatualizados | ⚪ | P | 🟢 |

---

## Cruzamento com o `backlog.md` existente (não duplicar)

Itens já registrados pelo humano e **não** repetidos aqui: remoção do `.env` do git e rotação de
segredos (`backlog.md:9-12`) · lockout de brute force e reCAPTCHA (`:16-20`) · HTTPS no nginx (`:18`) ·
validação de URLs sociais (`:19`) · CSP `base-uri` (`:20`) · sync do carrinho dual (`:25`) ·
`Order.user` nullable (`:26`) · registro/email verify/password reset (`:30-34`) ·
rate limiting e CSRF em POST (`:32-34`) · healthcheck e rede interna (`:38-41`) ·
logs estruturados (`:51`) · CI/CD com GitHub Actions + bandit + truffleHog (`:53`) ·
backup Borg/Rclone (`:54`).

**Reclassificação:** o item "remover `.env` do git" do backlog está **parcialmente feito** (removido em
`e2be947`) mas **incompleto** — o histórico ainda contém os segredos (D-015). O item "HTTPS no nginx"
é **mais grave** do que o backlog supõe: não é só ausência de HTTPS, é um **redirect que invalida o TLS
do Traefik** (D-060).

## Ordem de ataque sugerida (sujeita ao gate humano)

1. **R1 (rede de segurança):** D-059 (backup + restore testado) → D-030 (falso verde) → D-031 (hook) → D-036/D-039 (lint+lockfile dev) → CI de baseline → testes de caracterização de D-001..D-004.
2. **R2 (segurança), um PR por item:** D-015 (rotação humana) → D-016 → D-017 → D-019 → D-021 → D-022 → D-023 → D-025 → D-026 → D-059 já tratado.
3. **R2 (integridade):** D-001 → D-004 → D-002 → D-003 → D-005 → D-006.
4. **R3 (estrutura):** D-042, D-043, D-044, D-045, D-046, D-053, D-054, D-055, D-074, D-075.
5. **R4 (infra):** D-060 → D-061 → D-062 → D-063 → D-064 → D-065 → D-071 → D-067 → D-068 → D-069 → D-070.
