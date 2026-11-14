# MAPA DO CÓDIGO

Referência rápida de **onde está o quê**. Gerado no R0 (2026-11-02). Use `grep`/`glob` a partir daqui
em vez de varrer o repositório inteiro.

**Convenção do projeto:** `frontend/` = templates + estáticos (server-rendered, sem build step) ·
`backend/` = Django (`m2shop/` = projeto, demais = apps) · `docs/` = documentação.

---

## 1. Entrypoints

| Arquivo | Papel |
| :-- | :-- |
| `backend/manage.py` | CLI do Django (`migrate`, `test`, `seed`, `shell`) |
| `backend/m2shop/wsgi.py` | ponto WSGI servido pelo gunicorn (`m2shop.wsgi:application`) |
| `backend/m2shop/urls.py` | URLs raiz: admin, accounts, orders, frete, gerencial, `/m/` |
| `backend/m2shop/settings.py` | configuração única (154 linhas); `DEBUG`, DB, sessão, cache, e-mail, `SECURE_*` |
| `backend/entrypoint.sh` | bootstrap do container: `chown` + `gosu appuser` → executa o CMD |
| `docker-compose.yml` | 3 serviços: `db`, `web`, `nginx` |
| `scripts/start.sh` | up + migrate + seed; ⚠ copia `.env.example` → `.env` se ausente |
| `nginx/nginx.conf` | reverse proxy + TLS; ⚠ redirect para `:8443` |
| `traefik-global/` | stack de borda (Traefik v3.1 + Let's Encrypt) |

## 2. Apps Django

| App | Modelos | Views | Rotas | Testes | Observação |
| :-- | :-- | :-- | :-- | :-- | :-- |
| `catalog` | `Category`, `Variant`, `Product`, `FeaturedProduct`, `SiteConfig`, `TickerMessage`, `Newsletter` | `views.py` **581 linhas** (catálogo + carrinho + checkout + PDV + estoque + busca + newsletter) | `urls.py` 21 rotas | **110** | ⚠ app "faz-tudo" |
| `cart` | `Cart`, `CartItem` | — (só `services.py` + `context_processors.py`) | — | 9 | `services.py` = helpers de sessão (38 linhas) |
| `orders` | `Order`, `OrderItem` | `views.py` (1 view) | `urls.py` 1 rota | 12 | `forms.py` = `OrderCreateForm` |
| `shipping` | `ShippingConfig`, `ShippingRegion`, `ShippingRate` | `views.py` (2 endpoints JSON) | `urls.py` 2 rotas | 21 | `services.py` = ViaCEP + cálculo (81 linhas) |
| `management` | `OrderStatusHistory`, `Shipment` | `views.py` **378 linhas** (7 classes) + `auth_views.py` | `urls.py` 8 rotas | **0** ⚠ | único guard de papel (`ManagerRequiredMixin`) |
| `mobile` | — | `views.py` 153 linhas | `urls.py` 11 rotas | 46 | `middleware.py` = `DeviceRedirectMiddleware` (105 linhas) |
| `accounts` | — | stub (só logout) | `urls.py` 1 rota | 2 | ⚠ app morto, ainda em `INSTALLED_APPS` |

## 3. Arquivos mais relevantes por tema

### Domínio e regras de negócio
| Arquivo | Linhas | Conteúdo |
| :-- | :-- | :-- |
| `backend/catalog/views.py` | 581 | **todo o catálogo, carrinho, checkout, PDV e estoque** |
| `backend/management/views.py` | 378 | dashboard, pedidos, status, despacho, financeiro, estoque, CSV |
| `backend/catalog/models.py` | 254 | `Product.save()` gera código + QR; `SiteConfig` singleton |
| `backend/scripts/seed.py` | 392 | carga inicial + superusuário + download de imagens |
| `backend/cart/services.py` | 38 | `get_cart_items` / `get_cart_total` (sessão) |
| `backend/shipping/services.py` | 81 | `lookup_cep()` (ViaCEP) + `quote()` (peso cúbico, região, frete grátis) |
| `backend/orders/models.py` | 88 | `Order`, `OrderItem`, `Order.total` |
| `backend/cart/models.py` | 57 | `Cart`, `CartItem` (carrinho do PDV) |

### Segurança e acesso
| Arquivo | Linhas | Conteúdo |
| :-- | :-- | :-- |
| `backend/management/views.py:20-34` | — | `ManagerRequiredMixin` / `is_manager` — **o único controle de papel do sistema** |
| `backend/management/auth_views.py` | 34 | `manager_login` (login manual), `manager_logout` (GET ⚠) |
| `backend/catalog/middleware.py` | 18 | CSP + HSTS + headers de segurança |
| `backend/mobile/middleware.py` | 105 | redirecionamento por dispositivo |
| `backend/management/signals.py` | 45 | `pre_save(Order)` grava histórico ⚠ estado global |
| `backend/m2shop/settings.py:88-106,131-137` | — | validadores de senha, sessão, cookies, cache LocMem |

### Front
| Arquivo | Linhas | Conteúdo |
| :-- | :-- | :-- |
| `frontend/templates/base.html` | 704 | layout desktop + **todo o JS do carrinho/busca/frete inline** |
| `frontend/templates/catalog/sales.html` | 981 | PDV desktop (scanner QR + modal de checkout) |
| `frontend/templates/mobile/sales/sales_page.html` | 636 | PDV mobile (duplica o desktop) |
| `frontend/templates/mobile/catalog/cart.html` | 270 | carrinho mobile + frete |
| `frontend/static/css/style.css` | 701 | CSS global (carregado também no mobile) |
| `frontend/static/css/mobile/app.css` | 825 | CSS mobile |
| `frontend/static/js/html5-qrcode.min.js` | 375 KB | vendor ⚠ sem SRI/pin |
| `frontend/static/js/mobile/app.js` | 45 | JS mobile (⚠ `innerHTML` sem escape) |
| `frontend/static/landpage.html` | 270 | ⚠ página HTML dentro de `STATICFILES_DIRS` (publicada sem rota) |

### Infra
| Arquivo | Papel |
| :-- | :-- |
| `backend/Dockerfile` | ⚠ single-stage; `gcc`/`libmariadb-dev` na imagem final; sem `USER` (usa `gosu`) |
| `nginx/Dockerfile` | `nginx:1.26-alpine`, ⚠ `EXPOSE 8080` incorreto |
| `nginx/nginx.conf` | TLS, proxy, aliases de static/media; ⚠ sem gzip/HSTS, 301 para `:8443` |
| `traefik-global/docker-compose.yml` | Traefik v3.1 + Let's Encrypt, rede `web` |
| `traefik-global/config/dynamic.yml` | routers; ⚠ aponta para `nginx_blend` (container inexistente) |
| `traefik/` | ⚠ cópia de referência de `traefik-global/config/` **com drift** |
| `blendburguer-ref/` | ⚠ 2 arquivos de outro projeto, versionados, órfãos, com senhas fracas literais |
| `.env.example` | 16 variáveis (5 segredos, 1 delas `DEBUG=True` por default) |
| `.dockerignore` | ⚠ exclui `**/tests.py` → suíte ausente na imagem |

## 4. Templates (31)

| Grupo | Templates |
| :-- | :-- |
| Base | `base.html` (desktop, 704) · `mobile/base.html` (93) · `management/base.html` |
| Catálogo | `catalog/home.html` · `catalog/product_list.html` · `catalog/product_detail.html` |
| Carrinho/checkout | `catalog/cart.html` · `catalog/checkout.html` · `catalog/order_success.html` · `orders/order_detail.html` |
| PDV | `catalog/sales.html` (981) · `catalog/sales_login.html` · `catalog/stock.html` |
| Mobile | `mobile/catalog/{home,categories,product_list,product_detail,cart,checkout,order_success}.html` · `mobile/sales/{login,sales_page}.html` · `mobile/account/profile.html` |
| Gerencial | `management/{login,dashboard,order_list,order_detail,dispatch,financial,stock_alert}.html` |

**Tags/filters customizados:** `catalog/templatetags/static_versioned.py` (cache-busting por mtime) ·
`management/templatetags/management_tags.py` (filter `div` para gráficos).

## 5. Onde mexer para cada tema

| Tema | Arquivos |
| :-- | :-- |
| Estoque | `catalog/models.py` (`Product.stock`, `Variant.stock`) · `catalog/views.py:179,506` · `catalog/views.py:215` |
| Frete | `shipping/models.py` · `shipping/services.py` · `shipping/views.py` · `catalog/views.py:418-445` |
| Preços/margem | `catalog/models.py` (`price`, `promotional_price`, `purchase_price`) · `catalog/views.py:215-225` (estoque) |
| Autorização | `management/views.py:20-34` · `catalog/views.py:63,75,125,197,215,228,253` · `mobile/views.py:120` |
| Checkout | `catalog/views.py:448-541` (site) · `catalog/views.py:127-194` (PDV) · `orders/forms.py` |
| Relatórios | `management/views.py:38-95` (dashboard) · `:232-304` (financeiro) |
| TLS/borda | `nginx/nginx.conf` · `traefik-global/config/dynamic.yml` · `traefik-global/config/traefik.yml` |
| Segredos | `.env.example` · `backend/m2shop/settings.py:8-11` · `scripts/start.sh:24-27` |

## 6. Mapeamento rota → view (comando de regeneração)

```bash
grep -rn "path(" backend/*/urls.py backend/m2shop/urls.py
```

Detalhe completo em `docs/02-CONTRATOS.md`.
