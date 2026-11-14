# 02 — Contratos (R0: **as-is**)

Extraído **do código** (não da documentação) no R0, 2026-11-02. Estes contratos são a base dos testes
de caracterização da R1. **Alterar qualquer item aqui = vermelho** (quebra de comportamento externo).

---

## 1. Rotas HTTP

### 1.1 Raiz — `backend/m2shop/urls.py`

| Método | Path | View | Proteção |
| :-- | :-- | :-- | :-- |
| GET | `/admin/logout/` | `m2shop.admin_views.admin_logout` | nenhuma ⚠ logout por GET |
| * | `/admin/...` | Django admin | `is_staff` |
| — | `/accounts/` | include | — |
| — | `/orders/` | include | — |
| — | `/frete/` | include | — |
| — | `/gerencial/` | include | — |
| GET | `/view/mobile/` | `mobile.views.view_mobile` | público (grava cookie `view_mode`) |
| GET | `/view/desktop/` | `mobile.views.view_desktop` | público (grava cookie `view_mode`) |
| — | `/m/` | include | — |

### 1.2 Catálogo / loja — `backend/catalog/urls.py`

| Método | Path | View | Proteção |
| :-- | :-- | :-- | :-- |
| GET | `/` | `home` | público |
| GET | `/produtos/` | `product_list` | público |
| GET | `/produtos/<slug:category_slug>/` | `product_list` | público |
| GET | `/produto/<slug:slug>/` | `product_detail` | público |
| GET | `/buscar/?q=` | `product_search` | público (JSON, limite 8 resultados) |
| GET | `/carrinho/` | `cart_page` | público |
| POST | `/carrinho/adicionar/` | `add_to_cart` | público (JSON) |
| POST | `/carrinho/atualizar/` | `update_cart` | público (JSON) |
| POST | `/carrinho/frete/selecionar/` | `select_shipping` | público (JSON) |
| GET/POST | `/checkout/` | `store_checkout` | público |
| GET | `/checkout/sucesso/<int:order_id>/` | `order_success` | sessão (`recent_order_ids`) |
| POST | `/newsletter/` | `newsletter_signup` | público + `@ratelimit` 5/min/IP ⚠ LocMem |

### 1.3 PDV — `backend/catalog/urls.py:9-19`

| Método | Path | View | Proteção |
| :-- | :-- | :-- | :-- |
| GET | `/vendas/` | `sales_page` | `login_required` ⚠ sem papel |
| GET/POST | `/vendas/entrar/` | `LoginView` (`catalog/sales_login.html`) | público |
| GET | `/vendas/buscar/?code=` | `sales_product_lookup` | `login_required` ⚠ **órfã** |
| POST | `/vendas/adicionar/` | `sales_add_item` | `login_required` ⚠ sem papel |
| POST | `/vendas/finalizar/` | `sales_checkout` | `login_required` ⚠ sem papel |
| POST | `/vendas/item/<int:item_id>/atualizar/` | `sales_update_item` | `login_required` + escopo `cart` ✅ |
| POST | `/vendas/item/<int:item_id>/remover/` | `sales_remove_item` | `login_required` + escopo `cart` ✅ |
| GET | `/vendas/estoque/` | `stock_page` | `login_required` ⚠ **expõe custo** |

### 1.4 Pedidos — `backend/orders/urls.py`

| Método | Path | View | Proteção |
| :-- | :-- | :-- | :-- |
| GET | `/orders/<int:order_id>/` | `order_detail` | `login_required` + `user=request.user` ✅ |

### 1.5 Frete — `backend/shipping/urls.py`

| Método | Path | View | Proteção |
| :-- | :-- | :-- | :-- |
| POST | `/frete/cep/` | `cep_lookup` | público (JSON) |
| POST | `/frete/calcular/` | `shipping_quote` | público (JSON) |

### 1.6 Gerencial — `backend/management/urls.py`

| Método | Path | View | Proteção |
| :-- | :-- | :-- | :-- |
| GET/POST | `/gerencial/entrar/` | `manager_login` | público (checa grupo internamente) |
| GET | `/gerencial/sair/` | `manager_logout` | `login_required` ⚠ sem checagem de gerente, GET |
| GET | `/gerencial/` | `DashboardView` | `ManagerRequiredMixin` |
| GET | `/gerencial/pedidos/` | `OrderListView` | `ManagerRequiredMixin` |
| GET | `/gerencial/pedidos/exportar/` | `ExportOrdersView` | `ManagerRequiredMixin` ❌ **500** |
| GET | `/gerencial/pedidos/<int:pk>/` | `OrderDetailView` | `ManagerRequiredMixin` |
| POST | `/gerencial/pedidos/<int:pk>/status/` | `OrderStatusUpdateView` | `ManagerRequiredMixin` |
| GET/POST | `/gerencial/pedidos/<int:pk>/despachar/` | `DispatchView` | `ManagerRequiredMixin` (upload ⚠ sem validação) |
| GET | `/gerencial/financeiro/` | `FinancialView` | `ManagerRequiredMixin` |
| GET | `/gerencial/estoque/` | `StockAlertView` | `ManagerRequiredMixin` |

### 1.7 Mobile — `backend/mobile/urls.py`

| Método | Path | View | Proteção |
| :-- | :-- | :-- | :-- |
| GET | `/m/` | `home` | público |
| GET | `/m/categorias/` | `categories` | público |
| GET | `/m/produtos/` | `product_list` | público |
| GET | `/m/categorias/<slug:category_slug>/` | `product_list` | público |
| GET | `/m/produto/<slug:slug>/` | `product_detail` | público |
| GET | `/m/carrinho/` | `cart` | público |
| GET/POST | `/m/checkout/` | `checkout` → `catalog.store_checkout` | público |
| GET | `/m/checkout/sucesso/<int:order_id>/` | `order_success` → `catalog.order_success` | sessão |
| GET/POST | `/m/vendas/entrar/` | `SalesLoginView` | público |
| GET | `/m/vendas/` | `sales_page` | `login_required` ⚠ sem papel |
| GET | `/m/perfil/` | `profile` | público |

### 1.8 Accounts

| Método | Path | View | Proteção |
| :-- | :-- | :-- | :-- |
| POST | `/accounts/logout/` | `LogoutView` | sessão |

## 2. Contrato dos endpoints JSON

> ⚠ `subtotal` no `/frete/calcular/` é **confiável apenas por convenção** — o cliente o envia e o servidor
> o usa no limiar de frete grátis (`backend/shipping/views.py:49-56`).

### `POST /carrinho/adicionar/`
Request: `{ "product_id": int, "quantity": int, "variant_id": int|null }`
Response 200: `{ "success": true, "cart_count": int, "cart_total": str }`
Response 400: `{ "error": str }`

### `POST /carrinho/atualizar/`
Request: `{ "product_id": int, "quantity": int, "variant_id": int|null }` (`quantity: 0` remove)
Response 200: `{ "success": true, "cart_count": int, "cart_total": str }`

### `POST /carrinho/frete/selecionar/`
Request: `{ "cep": str, "method": str }`
Response 200: `{ "success": true, ... }` — persiste em `request.session['shipping']`

### `POST /frete/cep/`
Request: `{ "cep": str }` (8 dígitos, com ou sem hífen)
Response 200: `{ "success": true, "logradouro": str, "bairro": str, "localidade": str, "uf": str }`
Response 400: `{ "error": "CEP inválido. Digite 8 dígitos." }`
Response 404: `{ "error": "CEP não encontrado." }`

### `POST /frete/calcular/`
Request: `{ "cep": str, "subtotal": number|null }` ⚠
Response 200: `{ "success": true, "address": "Cidade - UF", "options": [ { "name": str, "value": str } ] }`
Response 200 (sem opção): `{ "success": true, "address": str, "options": [] }`
Response 400/404: `{ "error": str }`

### `POST /newsletter/`
Request: `{ "email": str }` → Response `{ "success": bool, "message": str }` (ratelimit 5/min/IP)

### `POST /vendas/adicionar/`
Request: `{ "code": "M2-XXXXX", "quantity": int }`
Response 200: `{ "success": true, "product": {...}, "cart_total": str, "cart_items": int }`

### `POST /vendas/finalizar/`
Request: `{ "payment_method": "cash|card|pix|other", "customer_name": str, "customer_phone": str, "customer_cpf": str }`
Response 200: `{ "success": true, "order_id": int, "payment_method": str, "total": str, "items": [...], "redirect": "/orders/<id>/" }`
Response 400: `{ "error": str }` ⚠ **em caso de estoque insuficiente, o pedido é commitado**

### `POST /vendas/item/<id>/atualizar/` · `POST /vendas/item/<id>/remover/`
Request: `{ "quantity": int }` → Response `{ "success": true, "cart_total": str, "cart_items": int }`

### `GET /buscar/?q=`
Response 200: lista de produtos (até 8) com nome, slug, preço, imagem, categoria

## 3. Sessão, cookies e cabeçalhos

| Item | Valor (as-is) | Evidência |
| :-- | :-- | :-- |
| Engine de sessão | `django.contrib.sessions.backends.db` | `settings.py:131` |
| Expiração | `SESSION_EXPIRE_AT_BROWSER_CLOSE=True`, `SESSION_COOKIE_AGE=86400` (24 h) | `settings.py:103-104` |
| Cookies de sessão | `SameSite=Lax`; `Secure` só com `DEBUG=False` | `settings.py:105,153` |
| CSRF | `CSRF_COOKIE_HTTPONLY=False` (JS lê o cookie), `Secure` só com `DEBUG=False` | `settings.py:102,154` |
| Sessão no carrinho | `request.session['cart']` = `[{product_id, variant_id, quantity}]` | `cart/services.py:9` |
| Sessão do frete | `request.session['shipping']` = `{cep, method, value, ...}` | `catalog/views.py:418-445` |
| Sessão de pedido ok | `request.session['recent_order_ids']` = lista de ids | `catalog/views.py:513-516,545-550` |
| Cookie de modo de tela | `view_mode` (1 ano), gravado pelo servidor, **sem HttpOnly** | `mobile/views.py:132-152` |
| CSP | `script-src 'self' 'unsafe-inline' https://cdnjs... https://cdn.jsdelivr.net` | `catalog/middleware.py:7-17` |
| Cache | `LocMemCache` (por processo ⚠ com 3 workers) | `settings.py:133-137` |

## 4. Variáveis de ambiente (`.env.example`)

| Variável | Segredo? | Default | Uso |
| :-- | :-- | :-- | :-- |
| `SECRET_KEY` | 🔴 sim | **sem default** (falha no boot) | `settings.py:8` |
| `DEBUG` | não | `True` ⚠ | `settings.py:9` — controla `SECURE_*` |
| `ALLOWED_HOSTS` | não | `localhost,127.0.0.1` | `settings.py:10` |
| `CSRF_TRUSTED_ORIGINS` | não | vazio | `settings.py:11` |
| `SITE_URL` | não | `http://localhost:8080` | `settings.py:129` |
| `ADMIN_PASSWORD` | 🔴 sim | fallback `'admin123'` ⚠ no seed | `scripts/seed.py:32-35` |
| `MYSQL_DATABASE` | não | `m2shop` | `settings.py:70` |
| `MYSQL_USER` | não | `m2shop` | `settings.py:71` |
| `MYSQL_PASSWORD` | 🔴 sim | **sem default** | `settings.py:72` |
| `MYSQL_ROOT_PASSWORD` | 🔴 sim | — (compose) | `docker-compose.yml:19` |
| `MYSQL_HOST` | não | `127.0.0.1` | `settings.py:73` |
| `MYSQL_PORT` | não | `3306` | `settings.py:74` |
| `EMAIL_BACKEND` | não | console backend | `settings.py:139` |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_USE_TLS` | não | `''` / `587` / `True` | `settings.py:140-142` |
| `EMAIL_HOST_USER` | 🟡 identificador | `''` | `settings.py:143` |
| `EMAIL_HOST_PASSWORD` | 🔴 sim | `''` | `settings.py:144` |
| `DEFAULT_FROM_EMAIL` | não | `noreply@m2moda.com.br` | `settings.py:145` — **ausente do `.env.example`** ⚠ |
| `DOMAIN` | não | — | **não é lido pelo settings** ⚠ |

## 5. Schema resumido (as-is)

| Model | App | Campos-chave | Relations / constraints |
| :-- | :-- | :-- | :-- |
| `Category` | catalog | `name`, `slug` (unique), `featured` | ordering `name` |
| `Product` | catalog | `name`, `slug` (index), `code` (unique, `M2-XXXXX`), `price`, `promotional_price`, `purchase_price`, `stock`, `available`, `image`, `secondary_image`, `qrcode_image` | FK `category`; index `-created_at`; `save()` gera código + QR |
| `Variant` | catalog | `size`, `color`, `stock`, `sku` (⚠ sem unique), `order` | FK `product`; `unique_together(product,size,color)` |
| `SiteConfig` | catalog | config do site (social, dados) | singleton por `save()` |
| `TickerMessage` | catalog | mensagem do ticker | — |
| `Newsletter` | catalog | `email` | — |
| `FeaturedProduct` | catalog | ordem/destaque | FK `product` |
| `Cart` | cart | — | `OneToOne(user)` |
| `CartItem` | cart | `quantity` | FK `cart`, `product`, `variant` (nullable ⚠); `unique_together(cart,product,variant)` |
| `Order` | orders | `full_name`, `email`, `phone`, `cpf`, `address`, `city`, `state`, `zip_code`, `status`, `payment_method`, `shipping_cost`, `shipping_method`, `total`(property) | FK `user` nullable ⚠ (site ⇒ `None`); `created_at` index |
| `OrderItem` | orders | `price` (snapshot), `quantity` | FK `order`, `product` (**CASCADE** ⚠), `variant`; **sem snapshot de nome** ⚠ |
| `ShippingConfig` | shipping | `origin_cep`, packaging, `frete_gratis_acima_de` | singleton por `save()` |
| `ShippingRegion` | shipping | `cep_start`, `cep_end`, `fator` | — |
| `ShippingRate` | shipping | `peso_min`, `peso_max`, `valor_base`, `servico` | — |
| `OrderStatusHistory` | management | `status`, `changed_by`, `changed_at` | FK `order` |
| `Shipment` | management | `tracking_code`, `label_pdf` | `OneToOne(order)`; upload ⚠ sem validação |

**Enums:**
- `Order.STATUS_CHOICES`: `pending, confirmed, shipped, delivered, cancelled` (`orders/models.py:7-14`)
- `Order.PAYMENT_CHOICES`: `cash, card, pix, other` (`orders/models.py:16-21`)

## 6. Comandos operacionais (as-is)

| Comando | Efeito |
| :-- | :-- |
| `docker compose up -d --build` | sobe db → web (migrate + collectstatic) → nginx |
| `docker compose exec web python manage.py migrate` | aplica migrations |
| `docker compose exec web python scripts/seed.py` | ⚠ cria superusuário com senha fallback, popula 15 produtos e baixa imagens |
| `docker compose exec web python manage.py seed` | mesmo seed via command do Django |
| `docker compose run --rm --no-deps web python manage.py test` | ⚠ **roda 0 testes** (imagem exclui `tests.py`) |
| `docker compose run --rm --no-deps web python manage.py test <app>` | idem, por app |
| `docker compose logs -f web` | logs (texto, sem `LOGGING` estruturado) |

**Migrations:** `catalog` 15 · `orders` 6 · `cart` 2 · `shipping` 1 · `management` 1 · `accounts` 2.
O boot roda `migrate --fake-initial` ⚠ (pode mascarar drift de schema).
