# Backlog — M2 Moda Masculina

## 🚨 Críticos (antes do deploy)

- [ ] **Remover `.env` do git** — `git rm --cached .env` (já criei `.gitignore`)
- [ ] **Rotacionar credenciais** — `SECRET_KEY` e senhas MySQL (as atuais estão no histórico do git)
- [ ] **Criar `.env` de produção** com `DEBUG=False`, `SECRET_KEY` forte, senhas fortes, `ALLOWED_HOSTS` real, `CSRF_TRUSTED_ORIGINS` real
- [ ] **Configurar email SMTP de verdade** — `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` no `.env` de produção (senão password reset e verificação de email não funcionam)

## 🔒 Segurança

- [ ] **Adicionar `django-axes` ou `django-defender`** — proteção contra brute force com lockout de conta (o rate limit atual é por IP, não por conta)
- [ ] **Adicionar reCAPTCHA/hCaptcha** no registro e login (bots ainda conseguem criar conta, só ficam inativas)
- [ ] **Forçar HTTPS no nginx** — redirect 301 de HTTP para HTTPS com certificado Let's Encrypt (Traefik já existe configurado)
- [ ] **Validar URLs de redes sociais** server-side (instagram, facebook etc. vêm do banco sem validação de domínio)
- [ ] **Adicionar `base-uri 'self'`** na CSP (previne injeção de base tag)

## 🏗️ Arquitetura

- [ ] **Resolver dual cart system** — session cart (público) e DB cart (logado) não sincronizam. O signal de `user_logged_in` já foi criado, mas precisa ser testado
- [ ] **Remover nullable de `Order.user`** — `blank=True, null=True` no modelo permite pedidos órfãos
- [ ] **Criar `.env.example` definitivo** com todas as variáveis necessárias documentadas (incluindo `SITE_URL`, `EMAIL_*`, `ADMIN_PASSWORD`)

## 🧪 Testes

- [ ] **Testar fluxo completo de registro + email verification** — cadastro → email → clicar link → login
- [ ] **Testar password reset** — formulário → email → link → nova senha
- [ ] **Testar rate limiting** — 6 requisições de registro em 1 min deve bloquear
- [ ] **Testar cart sync** — adicionar itens na session cart (sem login) → logar → verificar se migrou para DB cart
- [ ] **Testar CSRF nas mutations POST** — todas as chamadas AJAX com `X-CSRFToken`

## 🐳 Docker/Infra

- [ ] **Reconstruir imagem Docker** com `docker compose build` (as alterações no Dockerfile e requirements.txt só valerão após rebuild)
- [ ] **Verificar healthcheck do banco** no docker-compose (já existe para db, web depende de `service_healthy`)
- [ ] **Verificar redes isoladas** — atualmente só tem rede `web` (externa). Avaliar se precisa de rede interna só para banco
- [ ] **Adicionar `SESSION_COOKIE_DOMAIN`** se houver subdomínios

## 📝 Documentação

- [ ] **README desatualizado** — refletir novo fluxo de registro (com verificação), password reset, e credenciais
- [ ] **Documentar variáveis de ambiente** — todas as env vars necessárias no `.env.example`
- [ ] **ADR para decisões arquiteturais** — dual cart, email verification, CSP policy

## 💡 Melhorias (pós-deploy)

- [ ] **Logs estruturados** — substituir `print()` por logging com JSON
- [ ] **Monitoramento** — healthcheck endpoint, métricas básicas
- [ ] **CI/CD** — GitHub Actions com lint, testes, SAST (bandit), scan de secrets (truffleHog), deploy automático
- [ ] **Backup automático** — script Borg + Rclone + Telegram conforme AGENTS.md
