<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/Django-5.0-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django 5">
  <img src="https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL 8.0">
  <img src="https://img.shields.io/badge/Gunicorn-绿色-499848?style=for-the-badge&logo=gunicorn&logoColor=white" alt="Gunicorn">
  <br>
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5">
  <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3">
  <img src="https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white" alt="Nginx">
  <img src="https://img.shields.io/badge/Traefik-EE3D43?style=for-the-badge&logo=traefik&logoColor=white" alt="Traefik">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Docker%20Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Compose">
</p>

<br>

# 🛍️ M2 Moda Masculina

E-commerce de moda masculina com estilo streetwear. Construído com Django, MySQL e infraestrutura Docker, com deploy pronto para produção via Traefik + Let's Encrypt.

## Estrutura

```
m2-moda-masculina/
├── backend/              # Django
│   ├── m2shop/           # Projeto principal
│   ├── catalog/          # Catálogo de produtos
│   ├── cart/             # Carrinho de compras
│   ├── accounts/         # Logout (não há mais contas de cliente)
│   ├── orders/           # Pedidos
│   ├── scripts/          # Scripts de seed
│   └── manage.py
├── nginx/                # Config Nginx
├── traefik/              # Config Traefik (referência)
├── traefik-global/       # Stack Traefik global (borda, Let's Encrypt)
├── scripts/              # Scripts de inicialização
├── docker-compose.yml
├── .env                  # (não versionado — copie de .env.example)
└── .env.example          # Template documentado de variáveis
```

## Requisitos

- Docker
- Docker Compose v2+

## Como Rodar

```bash
# Entre no diretório
cd m2-moda-masculina

# Configure variáveis no .env (opcional)
cp .env.example .env

# Inicie a aplicação
chmod +x scripts/start.sh
./scripts/start.sh
```

Ou manualmente:

```bash
docker compose up -d --build
# Aguarde o MySQL ficar pronto
docker compose exec web python manage.py migrate
docker compose exec web python scripts/seed.py
```

## Acesso

- **Loja:** http://localhost:8080
- **Admin:** http://localhost:8080/admin/
  - Usuário: `admin`
   - Senha: definida via variável `ADMIN_PASSWORD` no `.env` (padrão: `admin123`)
- **Vendas (Balcão):** http://localhost:8080/vendas/
  - Login exclusivo em `/vendas/entrar/` (mesmo usuário/senha do admin)
  - É a **única** porta de autenticação da aplicação — o site público não tem login/registro de cliente
- **Estoque:** http://localhost:8080/vendas/estoque/

## Comandos Úteis

```bash
# Parar
docker compose down

# Ver logs de um serviço
docker compose logs -f web

# Reconstruir e reiniciar
docker compose up -d --build

# Executar seed manualmente
docker compose exec web python scripts/seed.py

# Criar superusuário
docker compose exec web python manage.py createsuperuser

# Acessar o shell do Django
docker compose exec web python manage.py shell

# Ver containers rodando
docker compose ps
```

## Testes

154 testes automatizados (unitários + integração) divididos entre os 5 apps (catalog, cart, orders, accounts, shipping).

```bash
# Rodar todos os testes
docker compose run --rm --no-deps web python manage.py test

# Rodar testes de um app específico
docker compose run --rm --no-deps web python manage.py test shipping

# Rodar com verbose
docker compose run --rm --no-deps web python manage.py test catalog cart orders accounts --verbosity=2
```

Os testes usam **SQLite em memória** (configurado automaticamente em `settings.py`), sem dependência do MySQL.

### Pre-push Hook

Um git hook local executa os testes automaticamente antes de cada `git push`. Se falharem, o push é cancelado.

O hook está em `.git/hooks/pre-push` e monta o diretório `backend/` em modo leitura para disponibilizar os arquivos de teste no container.

### Produção

Os arquivos de teste são excluídos da imagem Docker via `.dockerignore` — não rodam em produção.

## CI/CD (GitHub Actions)

Pipeline definido em `.github/workflows/ci.yml`. Roda em Pull Requests e em push para `main` (e manualmente via `workflow_dispatch`).

### Gates

| Job | Ferramenta | Bloqueia |
| --- | --- | --- |
| `lint` | Ruff + Black | Ruff em erros reais (`E9,F63,F7,F82`); demais regras e Black são advisory |
| `test` | Django test runner + coverage | Testes (SQLite em memória) e `manage.py check` |
| `sast` | Semgrep (`p/python`, `p/django`, `p/security-audit`) | Achados de severidade `ERROR` (em PR: apenas achados novos, via baseline) |
| `secrets` | Gitleaks | Segredos na árvore atual; histórico do Git é advisory |
| `sca` | Trivy filesystem | CVEs `HIGH`/`CRITICAL` corrigíveis nas dependências resolvidas e misconfigurações nos Dockerfiles |
| `container` | Buildx + Trivy image | CVEs `HIGH`/`CRITICAL` corrigíveis nas imagens backend e nginx |
| `deploy` | SSH + Docker Compose | Só após todos os gates, em `main` |

Relatórios SARIF são enviados ao GitHub Code Scanning (aba **Security**) e também ficam disponíveis como artefatos do workflow. O job `container` gera SBOM CycloneDX de ambas as imagens.

> O `requirements.txt` usa ranges (`>=x,<y`), que o Trivy não resolve. Por isso o job `sca` instala as dependências e escaneia o `pip freeze` resolvido.

### Configuração necessária no GitHub

1. **Secrets** (Settings → Secrets and variables → Actions, no escopo do repositório ou no environment `production`):
   - `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_HOST_FINGERPRINT`, `DEPLOY_PATH`
   - `DEPLOY_PORT` (opcional, padrão `22`)
   - `DEPLOY_SSH_KEY` é a chave **privada** completa (com `-----BEGIN ...-----`), não o caminho do arquivo.
   - `DEPLOY_HOST_FINGERPRINT` é o SHA256 da chave pública do host, não o conteúdo da chave:
     ```bash
     ssh-keyscan -t ed25519 <host> 2>/dev/null | ssh-keygen -lf -
     # saída: 256 SHA256:xxxxx... host (ED25519)  -> use o SHA256:...
     ```
   - O job tem um passo "Verificar secrets de deploy" que falha com a lista dos nomes ausentes antes de tentar o SSH.
2. **Variable** `DEPLOY_ENABLED` (opcional): é um *kill switch*. Ausente ou com qualquer valor diferente de `false`, o deploy roda normalmente em push na `main`; com `false`, ele é desligado. Se for criar, use uma *repository variable* (aba `Variables`) — variable de environment ou secret não é lida pelo `if` do job.
3. **Environment** `production` (Settings → Environments). Reviewers são **opcionais**: sem eles o deploy é automático; com eles o job para em *Waiting* até aprovação manual.
4. **Branch protection** em `main` exigindo os checks `Lint`, `Tests`, `SAST (Semgrep)`, `Secrets (Gitleaks)`, `SCA (Trivy)` e `Container (build + Trivy)`, e proibindo push direto.
5. **Code scanning**: mantenha o *default setup* desabilitado (Settings → Code security), pois o pipeline envia SARIF próprio.

O deploy faz `git fetch` + `git reset --hard origin/main` + `docker compose up -d --build --remove-orphans`, valida o `healthcheck` de `m2-django` e `m2-nginx` e **não executa `seed.py`** (seed é bootstrap, não deploy).

### Troubleshooting

**`Deploy (production)` aparece como *Skipped*.** O `if` do job deu falso; o GitHub não tentou conectar na VPS. Causas:

1. Algum dos seis gates falhou — `deploy` depende de `needs: [lint, test, sast, secrets, sca, container]`.
2. A variable `DEPLOY_ENABLED` existe com o valor exato `false` (kill switch ligado).
3. O evento não foi push na `main` nem `workflow_dispatch` (ex.: execução vinda de um PR).

O deploy é *opt-out*, então uma variable ausente **não** impede a execução.

Se o status for *Waiting* em vez de *Skipped*, o environment `production` tem reviewers exigindo aprovação manual.

Atenção: um job skipped **não reprova o workflow** — o run aparece verde mesmo sem deploy. Confira o job, não só o status do run.

**Deploy falha com `error: missing server host`.** `secrets.DEPLOY_HOST` chegou vazio — o secret não existe, está com outro nome ou foi criado como *variable*. O passo "Verificar secrets de deploy" lista os nomes ausentes antes de tentar o SSH.

**Warning `Unexpected input(s) 'script_stop'`.** Esse input foi removido da action na v1.2.5. O script já usa `set -eu`, que aborta no primeiro erro.

**`m2-nginx` em loop com `cannot load certificate key ... Permission denied`.** O nginx roda como UID/GID 101 e a chave do certificado está legível apenas por root (`0600`). Correção única no `DEPLOY_PATH`:

```bash
sudo chown root:101 nginx/certs/localhost.pem nginx/certs/localhost-key.pem
sudo chmod 640 nginx/certs/localhost-key.pem
sudo chmod 644 nginx/certs/localhost.pem
docker compose restart nginx
```

Evite `chmod 644` na chave em produção (expõe o segredo a qualquer usuário do host). O script de deploy tenta aplicar `chgrp 101` + `chmod 640/644` automaticamente e avisa quando não tem permissão; o healthcheck aborta assim que o container entra em `restarting`, em vez de esperar 3 minutos.

**Deploy falha com `não é gravável pelo UID 100:101`.** Volumes criados por uma versão anterior rodando como root. Correção única, no `DEPLOY_PATH` da VPS:

```bash
docker compose run --rm --user root web chown -R 100:101 /app/backend/staticfiles /app/backend/media
```

**Deploy falha com `network web not found`.** A rede é `external: true` e não é criada pelo compose: `docker network create web`.

### Segurança do histórico

O `.env` já foi versionado no passado e removido depois. Considere `SECRET_KEY`, senhas do MySQL e `ADMIN_PASSWORD` **comprometidos**: rotacione-os e limpe o histórico (BFG/filter-repo). Até lá, o scan de histórico do Gitleaks permanece advisory.

### Dívida técnica

Itens já resolvidos e cobertos por regressão no pipeline:

- **Injeção de fórmula em CSV** (`management/views.py`): `csv_safe()` prefixa células iniciadas por `=`, `+`, `-`, `@`, tab ou CR com apóstrofo. A supressão do Semgrep é pontual e justificada em comentário; `management/tests.py` fixa o comportamento.
- **Dependências desatualizadas**: Django 5.2 LTS (`>=5.2,<5.3`) e Pillow 13 (`>=13.0,<14.0`). O baseline de 42 CVEs corrigíveis (37 HIGH, 5 CRITICAL) caiu para zero no `pip freeze` e nas imagens.
- **Imagens**: `backend/Dockerfile` é multi-stage (toolchain só no builder) e roda como UID 100; `nginx/Dockerfile` roda como UID 101. Inclui remoção do `pip` do runtime (superfície de ataque e metadados vendorizados que geravam falso positivo no Trivy) e `apt-get upgrade`/`apk upgrade` para patch dos pacotes da distro.

Pendências conhecidas:

- **Rotação de segredos**: `.env` no histórico do Git (ver "Segurança do histórico").
- **Imagens base fixadas por tag, não por digest**: o `upgrade` de pacotes mitiga, mas o ideal é digest pinning + Renovate/Dependabot.

## Produção

### Preparação do ambiente

```bash
# 1. Crie o .env a partir do template (preencha SECRET_KEY, ADMIN_PASSWORD e
#    senhas do MySQL; o bloco de SMTP é opcional — não há mais email de cliente)
cp .env.example .env

# 2. Em produção SEMPRE: DEBUG=False e ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS/SITE_URL
#    apontando para o domínio real (ex: m2moda.com.br)
```

### Rede e TLS

- O Traefik (stack `traefik-global/`) é o reverse proxy de borda e gera certificados **Let's Encrypt** automáticos (m2moda.com.br, m2moda.duckdns.org).
- A aplicação publica apenas a porta `8080` (nginx) — em produção o acesso público é exclusivamente via Traefik (`:80` → `:443`).
- **Topologia de redes** (isolamento):
  - `web` (externa): Traefik ↔ nginx (app web e estáticos)
  - `db-network` (**internal**): apenas a aplicação acessa o MySQL — o banco não tem saída para a internet

### Deploy

```bash
# Suba o Traefik global (rede 'web' externa + Let's Encrypt) — rodar na máquina de borda
docker network create web  # apenas na primeira vez
docker compose -f traefik-global/docker-compose.yml up -d

# Suba a aplicação
./scripts/start.sh          # equivalem a: docker compose up -d --build + migrate + seed
```

- `restart: unless-stopped` em todos os serviços (recupera de falhas/reboot).
- `depends_on` atrelado a `healthcheck` real (`service_healthy`) em todas as dependências.
- Persistência em volumes nomeados (`mysql_data`, `static_volume`, `media_volume`).
- Com `DEBUG=False`, o Django ativa automaticamente: redirect HTTPS, HSTS, cookies `secure` e `SECURE_PROXY_SSL_HEADER`.

### Containers sem privilégios

As duas imagens rodam como usuário sem privilégios (backend UID 100, nginx UID 101) e o `backend/Dockerfile` é multi-stage — a imagem final não contém compilador (`gcc`, `pkg-config`, headers do MariaDB) nem `pip`.

- **Volumes nomeados novos** herdam a ownership dos diretórios da imagem, então nada precisa de `chown` em runtime. Se um volume legado estiver com outra ownership, o entrypoint falha com a instrução de correção (`docker compose run --rm --user root web chown -R 100:101 /app/backend/...`).
- **Certificados locais**: o nginx não-root precisa conseguir ler `nginx/certs/localhost-key.pem`. Como os certificados são de desenvolvimento (mkcert, fora do Git), garanta `chmod 644 nginx/certs/localhost-key.pem` na máquina. Em produção o TLS é terminado pelo Traefik.
- **Portas baixas**: o nginx escuta 80/443 dentro do container como usuário comum. O compose fixa `net.ipv4.ip_unprivileged_port_start: 0` para não depender do default do runtime.

### Email (verificação e password reset)

O site público é **100% anônimo** — não há contas de cliente, registro, verificação de e-mail nem password reset. Os usuários existem apenas para acesso ao admin e ao balcão de vendas (criados via `createsuperuser` ou pelo seed). Por isso, configurar SMTP no `.env` é **opcional**: sem valores, o Django usa o backend de console (imprime no log do container).

O `ADMIN_PASSWORD` do seed continua sendo o único dado sensível de usuário a definir em produção.

## Funcionalidades

- Catálogo com categorias e produtos
- Carrinho de compras em sessão (sem login)
- Checkout anônimo com confirmação de pedido
- Calculadora de frete por CEP no carrinho (tabela própria com lógica de peso cúbico dos Correios)
- Painel administrativo completo (Django Admin)
- Ticker de avisos ("bolsa de valores") no topo — gerido no admin (modelo `TickerMessage`)
- Design responsivo e moderno
- 15 produtos de exemplo em 8 categorias

### Calculadora de Frete

**URL:** widget no carrinho (`catalog/cart.html`)

O cliente digita o CEP no carrinho e vê as opções de envio (ex: Sedex, PAC) com o valor; escolhe uma delas e o frete é aplicado ao total e persistido na sessão. No checkout, o CEP informado **preenche o endereço automaticamente** (logradouro, cidade e UF via ViaCEP), e o método/valor do frete vão para o pedido. O prazo **não** é exibido (evita promessa de dias que depende dos Correios).

- **Validação de CEP** via ViaCEP (gratuito, sem chave) — CEP inexistente é rejeitado com mensagem amigável
- **Cálculo próprio** que replica a lógica dos Correios: usa o maior entre peso real e peso cúbico (`comprimento × largura × altura ÷ 6000`), arredondado para cima
- **Regiões de entrega** (`ShippingRegion`) — faixas de CEP de destino com fator de acréscimo (ex: Capital = ×1,00; Norte = ×1,25)
- **Tarifas** (`ShippingRate`) — valor base por serviço e faixa de peso, cadastradas no admin (valores de referência dos Correios que você mantém atualizados)
- **Frete grátis** configurável acima de um subtotal (`ShippingConfig.frete_gratis_acima_de`)
- **Configuração** (`ShippingConfig`, singleton no admin) — CEP de origem, embalagem padrão (peso/dimensões) e regras
- **API:** `POST /frete/calcular/` (JSON `{cep, subtotal?}`) → `{success, address, options: [{name, value}]}`; `POST /frete/cep/` (JSON `{cep}`) → dados do endereço; `POST /carrinho/frete/selecionar/` (JSON `{cep, method}`) → persiste o frete na sessão

> **Observação:** a tarifa oficial dos Correios é uma tabela proprietária. Esta calculadora a aproxima via tarifas configuráveis no admin — mantenha-as atualizadas para valores fiéis.

### Código Único e QR Code

Cada produto possui um **código único** no formato `M2-XXXXX` (ex: `M2-00001`) gerado automaticamente no primeiro salvamento. Ao salvar, um **QR Code** é gerado contendo nome, código e preço do produto.

- Código visível no admin, na página do produto e no QR Code
- QR Code armazenado em `media/qrcodes/`
- Regenerado automaticamente se nome ou preço mudarem

### Página de Vendas (Balcão)

**URL:** `/vendas/` (requer login)

Sistema de ponto de venda (PDV) para vendas presenciais:

- **Leitor de QR Code** — ativação manual com botão "Iniciar Scanner", usa a câmera do dispositivo
- **Input manual** — digitar o código do produto (`M2-XXXXX`)
- **Carrinho lateral** — sticky, com foto, quantidade (+/−) e valor por item
- **Finalizar Venda** — modal com:
  - Nome e telefone do cliente (opcional)
  - Forma de pagamento: Dinheiro / Cartão / PIX / Outro
- **Confirmação** — modal de sucesso com resumo da venda
- **Subtração automática de estoque** ao confirmar a venda
- **Login exclusivo** em `/vendas/entrar/` — página limpa, sem header/footer do site

### Inventário de Estoque

**URL:** `/vendas/estoque/` (requer login)

Tabela completa do inventário:

- Código, produto, categoria, quantidade
- Preço de compra, preço de venda e preço promocional
- Valor total por produto (preço de compra × quantidade)
- Total geral do estoque (custo)
- Destaque visual para estoque baixo (≤5) e zerado
- Cards de resumo: total de itens e valor total (custo)

### Painel Gerencial

**URL:** `/gerencial/` (requer login de gerente/superuser)

Sistema de gestão administrativa para gerentes:

- **Login exclusivo** em `/gerencial/entrar/` — página limpa, sem header/footer do site
- **Dashboard** — visão geral com métricas (pedidos pendentes, faturamento, estoque baixo)
- **Pedidos** — lista paginada com filtros (status, data, busca por cliente/código)
  - Detalhe do pedido com itens, histórico de status e ações
  - Atualização de status (Pendente → Confirmado → Enviado → Entregue / Cancelado)
  - Despacho de pedidos (registro de código de rastreio)
  - Exportação CSV
- **Financeiro** — resumo financeiro com faturamento por período, ticket médio, métodos de pagamento
- **Estoque (Alertas)** — lista de produtos com estoque baixo/zerado para reposição
- **Permissões** — acesso restrito a usuários no grupo "Gerentes" ou superusers

### Versão Mobile (`/m/`)

Interface mobile-first, separada do desktop, com bottom navigation (Início, Categorias, Carrinho, Vendas, Perfil) e touch-friendly. Acessível via link "Versão Mobile" no rodapé do site ou diretamente em `/m/`:

- **Loja** — home com categorias/destaques/novidades, busca, listagem por categoria, detalhe do produto com galeria e "Adicionar ao Carrinho" fixo, carrinho com calculadora de frete e checkout
  - `/m/`, `/m/categorias/`, `/m/produtos/`, `/m/categorias/<slug>/`, `/m/produto/<slug>/`, `/m/carrinho/`, `/m/checkout/`
- **PDV Mobile** — `Venda no Balcão` em `/m/vendas/` (requer login), layout de tela cheia com leitor de QR Code (câmera traseira em celulares, com fallback para frontal), input manual de código e bottom bar de finalização
- **Login do vendedor** em `/m/vendas/entrar/`
- **Perfil** em `/m/perfil/` — área do vendedor, acesso ao gerencial (staff) e logout

A loja mobile reutiliza o mesmo carrinho de sessão do desktop (lógica compartilhada em `cart/services.py`), e o PDV mobile reutiliza os mesmos endpoints de venda do PDV desktop — sem duplicação de regras de negócio.

#### Detecção automática de dispositivo

O `DeviceRedirectMiddleware` (`mobile/middleware.py`) detecta o dispositivo pelo `User-Agent` e redireciona automaticamente:

- **Mobile** em URLs desktop → equivalente mobile (`/` → `/m/`, `/produtos/<categoria>/` → `/m/categorias/<categoria>/`, `/vendas/` → `/m/vendas/`, etc.)
- **Desktop** em URLs `/m/` → equivalente desktop (`/m/` → `/`, `/m/produto/<slug>/` → `/produto/<slug>/`, etc.)
- **Nunca redireciona**: `POST`, requisições `XHR`, bots/crawlers, `/admin/`, `/gerencial/`, `/accounts/`, `/media/` e `/static/`
- **Override manual**: links "Versão Mobile"/"Versão Desktop" definem um cookie `view_mode` (1 ano), preservando a escolha do usuário
- **Query string** é preservada nos redirects
