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
