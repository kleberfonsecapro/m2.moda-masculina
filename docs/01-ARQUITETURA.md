# 01 — Arquitetura (R0: **como está**)

**Data:** 2026-11-02 · **Fase:** R0 (somente leitura) · **Escopo:** estrutura, componentes, fluxos, dados, deploy.

> Este documento descreve a arquitetura **existente**, sem proposta de mudança. Alvos de reestruturação
> ficam em `docs/ESTRUTURA-ALVO.md` (fase R3, após aprovação).

---

## 1. Visão de containers (produção)

```
Internet
   │ :80/:443
   ▼
┌──────────────────────────────────────────────┐
│ traefik-global (stack separada, host borda) │  Let's Encrypt / ACME HTTP challenge
│  traefik:v3.1  ·  api.dashboard:true ⚠       │  routers: m2moda.com.br, www, .duckdns.org
└───────────────┬──────────────────────────────┘
                │ rede externa "web"  →  http://m2-nginx:80
                ▼
┌──────────────────────────────────────────────┐
│ nginx (m2-nginx)  :8080→80  :8443→443        │  HTTP 80 interno p/ Traefik ✅
│  nginx:1.26-alpine · cert localhost.pem ⚠     │  sem gzip, sem cache, sem HSTS
└───────────────┬──────────────────────────────┘
                │ proxy_pass → m2-django:8000
                ▼
┌──────────────────────────────────────────────┐
│ web (m2-django)  ·  python:3.12-slim          │  gunicorn 3 workers
│  migrate --fake-initial → collectstatic →     │  ⚠ migrate roda a cada boot
│  gunicorn m2shop.wsgi:application             │  ⚠ sem multi-stage, sem USER
└───────────────┬──────────────────────────────┘
                │ MySQL 3306 (rede interna)
                ▼
┌──────────────────────────────────────────────┐
│ db (m2-mysql)  mysql:8.0                      │  sem porta publicada ✅
│  rede db-network (internal:true) ✅            │  volume mysql_data
│  healthcheck: mysqladmin ping ✅               │  sem user dedicado / read_only
└──────────────────────────────────────────────┘

Volumes nomeados: mysql_data · static_volume · media_volume
Envio de estáticos/mídia: nginx monta os volumes em :ro
```

**Topologia de redes** (`docker-compose.yml:83-87`): `web` (externa, compartilhada com o Traefik) e
`db-network` (**internal: true** — o banco não tem rota para a internet). Isolamento correto. ✅

## 2. Estrutura do código (monólito Django, 6 apps)

```
m2-moda-masculina/
├── backend/                    Django project
│   ├── m2shop/                 settings, urls raiz, wsgi, admin_views (logout)
│   ├── catalog/                ⚠ "faz-tudo": catálogo + carrinho de sessão + checkout
│   │                            + PDV + estoque + busca + newsletter (views.py = 581 linhas)
│   ├── cart/                   carrinho persistido (PDV) + helpers de sessão
│   ├── orders/                 Order / OrderItem + form de checkout
│   ├── shipping/               config de frete, ViaCEP, cálculo de peso cúbico
│   ├── management/             painel gerencial (autorização, pedidos, despacho, financeiro)
│   ├── mobile/                 views + middleware de versión mobile
│   ├── accounts/               ⚠ app morto (só logout; README: "não há contas de cliente")
│   └── scripts/seed.py         carga inicial (392 linhas) + superusuário
├── frontend/                   templates + estáticos (sem build step)
│   ├── templates/              23 templates: base, catalog/, mobile/, orders/
│   └── static/                 css/, js/ (app.js + vendor html5-qrcode 375 KB), images/
├── nginx/  traefik/  traefik-global/  scripts/   infra e operação
├── blendburguer-ref/           ⚠ 2 arquivos de outro projeto, versionados e órfãos
└── docs/                       documentação (criada no R0)
```

**Duas fontes de carrinho** (⚠ não sincronizam):
- **Sessão** `request.session['cart']` → site público (`cart/services.py:9`).
- **Banco** `Cart`/`CartItem` (OneToOne com `User`) → PDV (`cart/models.py:6-57`).

**Duas fontes de estoque** (⚠ divergem): `Product.stock` (PDV baixa aqui) e `Variant.stock` (site baixa aqui).

## 3. Middleware (ordem real) — `backend/m2shop/settings.py:31-42`

| # | Middleware | Papel | Observação |
| :-- | :-- | :-- | :-- |
| 1-7 | Django padrão (security, session, common, csrf, auth, messages, clickjacking) | — | `X_FRAME_OPTIONS='DENY'` ✅ |
| 8 | `catalog.middleware.SecurityHeadersMiddleware` | CSP + HSTS + headers | CSP com `script-src 'unsafe-inline'` ⚠ neutraliza a defesa contra XSS inline; `connect-src 'self'` bloqueia o WebSocket do html5-qrcode ⚠ |
| 9 | `mobile.middleware.DeviceRedirectMiddleware` | redireciona GET desktop↔mobile por User-Agent/cookie `view_mode` | ignora POST, XHR, `/admin/`, `/gerencial/`, `/accounts/`, `/media/`, `/static/`; mapa de rotas divergente entre plataformas ⚠ |
| 10 | `management.signals.CurrentUserMiddleware` | expõe o usuário atual ao signal de status | guarda estado em **atributo de função** → não thread-safe com 3 workers ⚠ |

## 4. Modelo de dados (resumo)

```
Category 1─┬──* Product 1─┬──* Variant (size, color, stock, sku)
           │               ├── stock, purchase_price, price, promotional_price
           │               ├── code (M2-XXXXX, unique, gerado no save)
           │               └── image / secondary_image / qrcode_image
           │
           ├──* FeaturedProduct ──> Product
           └──  SiteConfig (singleton) · TickerMessage · Newsletter

User 1─┬──1 Cart 1─┬──* CartItem (unique_together: cart, product, variant ⚠ nullable)
       │            └── product FK, variant FK, quantity
       └──* Order 1─┬──* OrderItem (product FK CASCADE ⚠, variant FK, price snapshot)
                    │     └── (sem snapshot de nome ⚠)
                    ├── status (pendente→confirmado→enviado→entregue/cancelado)
                    ├── payment_method (cash/card/pix/other)
                    └── shipping_cost, total (property)
User 1─┬──1 Shipment (Order OneToOne, label_pdf upload ⚠ sem validação)
       └──* OrderStatusHistory (signal pre_save)

ShippingConfig (singleton: CEP origem, embalagem, frete grátis)
ShippingRegion (faixa de CEP, fator) · ShippingRate (faixa de peso, valor base)
```

**Observações de modelagem:**
- Dinheiro em `Decimal` ✅ · `USE_TZ=True` ✅ · timezone `America/Sao_Paulo`.
- `Product.save()` gera código e **reescreve o arquivo QR a cada salvamento** (I/O em cada edição de preço) ⚠.
- `SiteConfig.save()` / `ShippingConfig.save()` **descartam silenciosamente** a criação se já existir ⚠.
- `Order.total` itera itens → N+1 no admin e no CSV ⚠.
- `CartItem.variant` nullable em `unique_together` → MySQL trata NULL como distinto → duplicidade ⚠.
- `Variant.sku` sem `unique` ⚠.

## 5. Fluxos críticos (as-is)

### 5.1 Checkout público (`POST /checkout/`) — `backend/catalog/views.py:448-541`
```
POST /checkout/
  → OrderCreateForm (CPF, telefone, endereço)                     forms.py:5-20
  → transaction.atomic()
      → SELECT ... FOR UPDATE nos Products (⚠ só Product, não Variant)
      → para cada item: checa estoque → set_rollback(True) em falta  ✅
      → cria Order + OrderItems, baixa estoque (Variant.stock se houver)
      → grava frete da sessão (⚠ travado na sessão, não recalculado)
  → limpa sessão, redireciona para /checkout/sucesso/<id>/
```
**Nunca há pagamento real** — `payment_method` default `cash`.

### 5.2 Checkout do PDV (`POST /vendas/finalizar/`) — `backend/catalog/views.py:127-194`
```
POST /vendas/finalizar/  (JSON: payment_method, customer_name, customer_phone, customer_cpf)
  → valida payment_method contra Order.PAYMENT_CHOICES
  → transaction.atomic()
      → FOR UPDATE nos Products
      → cria Order (user=request.user, email=request.user.email ⚠)
      → loop: se quantity > product.stock → return JsonResponse(400)  ❌ SEM set_rollback
              → cria OrderItem, baixa Product.stock
      → apaga itens do carrinho
  → JSON de sucesso
```
❌ **Divergência crítica:** no erro, `return` dentro do `with` **encerra o bloco com COMMIT** → o pedido
criado em `:153` e os itens já processados **são persistidos**, com estoque já debitado, enquanto o cliente
recebe HTTP 400. `store_checkout` (site) faz certo (`:475`).

### 5.3 Frete — `backend/shipping/services.py:10-81`
```
POST /frete/cep/       → lookup_cep()  → ViaCEP (urlopen síncrono, timeout 4s, sem cache)
POST /frete/calcular/  → lookup_cep()  → quote(cep, subtotal=<valor do cliente>) ⚠
     peso = max(peso_real, L×A×P/6000) → faixa de peso → ShippingRate
     fator de região por CEP (comparação de string) → frete grátis se subtotal ≥ limiar ⚠
```

### 5.4 PDV — `backend/catalog/views.py:63-259`
```
/vendas/            (login_required, sem checagem de papel ⚠)
/vendas/buscar/     busca por código M2-XXXXX ⚠ órfã (sem consumidor no front)
/vendas/adicionar/  POST JSON → Cart/CartItem no banco
/vendas/finalizar/  POST JSON → sales_checkout ⚠ (ver 5.2)
/vendas/item/<id>/atualizar|remover/ → filtrado por cart=cart_obj ✅ sem IDOR
/vendas/estoque/    lista produtos + purchase_price + valor de estoque ⚠ expõe custo
```

### 5.5 Gerencial — `backend/management/views.py:37-379`
```
/gerencial/          DashboardView  — agregações com fan-out de JOIN ❌
/gerencial/pedidos/  OrderListView  — filtros + paginação (25)
/gerencial/pedidos/<pk>/        detalhe + status + histórico (signal)
/gerencial/pedidos/<pk>/despachar/  upload label_pdf ⚠ + rastreio
/gerencial/pedidos/exportar/    ExportOrdersView ❌ 500 (get_queryset sem self.request)
/gerencial/financeiro/ FinancialView — mesmas agregações ❌
/gerencial/estoque/  StockAlertView — produtos com estoque baixo/zerado
```

## 6. Contrato de autorização (as-is)

| Área | Regra implementada | Evidência |
| :-- | :-- | :-- |
| Loja pública | sem autenticação (anônima) | `backend/catalog/urls.py:8-30` |
| `/admin/*` | `is_staff` (Django) | `backend/m2shop/urls.py:14` |
| `/vendas/*` (PDV) | **só `login_required`** ⚠ | `backend/catalog/views.py:63-257` |
| `/m/vendas/*` | **só `login_required`** ⚠ | `backend/mobile/views.py:120-125` |
| `/gerencial/*` | `ManagerRequiredMixin` = superuser **ou** grupo "Gerentes" | `backend/management/views.py:20-34` |
| `/orders/<id>/` | `login_required` + `user=request.user` ✅ sem IDOR | `backend/orders/views.py:6-8` |
| `/checkout/sucesso/<id>/` | sessão (`recent_order_ids`) ✅ | `backend/catalog/views.py:544-550` |

`manager_login` (`backend/management/auth_views.py:8-26`) autentica manualmente e **não valida `next`**;
os 3 logins (`/admin/`, `/vendas/entrar/`, `/gerencial/entrar/`) **não têm rate limit nem lockout** ⚠.

## 7. Integrações externas

| Integração | Onde | Risco / Observação |
| :-- | :-- | :-- |
| **ViaCEP** | `backend/shipping/services.py:11,19-30` | `urlopen` síncrono no request, timeout 4 s, sem cache, sem retry; falha silenciosa → 404 "CEP não encontrado" |
| **Let's Encrypt / Traefik** | `traefik-global/config/` | ACME HTTP challenge; `api.dashboard:true` e `api.debug:true` sem autenticação ⚠ |
| **CDN** | `frontend/templates/base.html:11-14`, `mobile/base.html:13-16` | FontAwesome, Google Fonts, Chart.js, html5-qrcode — **sem SRI**, sem pin de versão |
| **SMTP** | `backend/m2shop/settings.py:139-145` | configurado e **nunca usado** (nenhum `send_mail`) |
| **Unsplash** | `backend/scripts/seed.py:20-27` | download de imagens no seed (rede externa) |

## 8. Decisões arquiteturais implícitas (não documentadas)

1. **Site 100% anônimo** — pedido sem `user` (`order.user = None`), o que habilita checkout sem cadastro.
2. **PDV = carrinho em banco por usuário**, site = carrinho em sessão — decisão implícita, não documentada, e as duas não conversam.
3. **Estoque em duas tabelas** — decisão implícita que causa divergência entre canais.
4. **Mobile como "views" paralelas**, não como camada de apresentação — gera duplicação de template e de JS.
5. **nginxTLS na aplicação, não na borda** — o Traefik termina TLS mas o nginx força outro TLS; duas camadas de certificado.
6. **Sem serviço de e-mail, sem pagamento, sem cache compartilhado** — features de UI prometidas sem implementação.
