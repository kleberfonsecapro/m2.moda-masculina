# M2 Moda Masculina

Loja virtual de moda masculina com Django, MySQL e Nginx.

## Tecnologias

- **Backend:** Django 5 + Gunicorn
- **Banco:** MySQL 8.0
- **Frontend:** HTML5 + CSS3 (design responsivo)
- **Servidor:** Nginx
- **Proxy/TLS:** Traefik + Let's Encrypt (produção)
- **Infra:** Docker + Docker Compose

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
├── traefik/              # Config Traefik
├── scripts/              # Scripts de inicialização
├── docker-compose.yml
└── .env
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
  - Senha: `admin123`

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

## Produção

Para produção:
- Configure o domínio em `.env` (`DOMAIN=seudominio.com.br`)
- Ajuste `nginx.conf` e `traefik/traefik.yml`
- O Traefik gerará certificados SSL automáticos via Let's Encrypt
- Consulte `docker-compose.prod.yml` para setup adicional

## Funcionalidades

- Catálogo com categorias e produtos
- Carrossel na página inicial
- Carrinho de compras
- Cadastro e login de usuários
- Finalização de pedidos
- Painel administrativo completo (Django Admin)
- Design responsivo e moderno
- 15 produtos de exemplo em 8 categorias
