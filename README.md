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
│   ├── accounts/         # Autenticação de usuários
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

137 testes automatizados (unitários + integração) divididos entre os 4 apps (catalog, cart, orders, accounts).

```bash
# Rodar todos os testes
docker compose run --rm --no-deps web python manage.py test

# Rodar testes de um app específico
docker compose run --rm --no-deps web python manage.py test catalog

# Rodar com verbose
docker compose run --rm --no-deps web python manage.py test catalog cart orders accounts --verbosity=2
```

Os testes usam **SQLite em memória** (configurado automaticamente em `settings.py`), sem dependência do MySQL.

### Pre-push Hook

Um git hook local executa os testes automaticamente antes de cada `git push`. Se falharem, o push é cancelado.

O hook está em `.git/hooks/pre-push` e monta o diretório `backend/` em modo leitura para disponibilizar os arquivos de teste no container.

### Produção

Os arquivos de teste são excluídos da imagem Docker via `.dockerignore` — não rodam em produção.

## Produção

### Preparação do ambiente

```bash
# 1. Crie o .env a partir do template (preencha SECRET_KEY, ADMIN_PASSWORD,
#    senhas do MySQL e, em produção, o bloco de SMTP)
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

### Email (verificação e password reset)

- Sem valores SMTP, o Django usa o **console backend** (imprime no log do container) — **não serve para produção**.
- Em produção configure `EMAIL_BACKEND=smtp`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER` e `EMAIL_HOST_PASSWORD` no `.env`.
- Links de email usam `SITE_URL` (ex: `https://m2moda.com.br`).

## Funcionalidades

- Catálogo com categorias e produtos
- Carrossel na página inicial
- Carrinho de compras
- Cadastro e login de usuários
- Finalização de pedidos
- Painel administrativo completo (Django Admin)
- Ticker de avisos ("bolsa de valores") no topo — gerido no admin (modelo `TickerMessage`)
- Design responsivo e moderno
- 15 produtos de exemplo em 8 categorias

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
