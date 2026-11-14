# Traefik global — como a borda publica o M2

**Atualizado:** 2026-11-14 · **Fonte da verdade:** `/home/kleber/traefik` (fora deste repositório).

> ⚠️ As pastas `traefik/` e `traefik-global/` **dentro deste repo** são cópias antigas e divergentes
> (D-075). Não edite produção por elas. Elas só servem de histórico.

## O que roda de verdade

| Item | Valor |
| :-- | :-- |
| Diretório do stack | `/home/kleber/traefik` (`docker-compose.yml`, `dynamic.yml`, `acme.json`) |
| Projeto / container | `traefik` / `traefik_global` |
| Imagem | `traefik:v3.7.1` |
| Providers | `file` (`/etc/traefik/dynamic.yml`, hot-reload) + `docker` (`exposedByDefault=false`) |
| Entrypoints | `web` (:80) e `websecure` (:443) |
| ACME | `letsencrypt`, HTTP-01 no entrypoint `web`, storage `acme.json` |
| Rede usada pelos serviços | `traefik_global` (externa) |
| Dashboard | `https://traefik.${DOMAIN}` com basicauth |

Cada aplicação é publicada de duas formas possíveis: **por labels** (provider Docker) ou **por arquivo**
(`dynamic.yml`). Neste host a convenção usada é o **arquivo**.

## Como o M2 está publicado

1. `docker-compose.yml` do M2: o serviço `nginx` (container `m2-nginx`) entra na rede externa
   `traefik_global`.
2. `/home/kleber/traefik/dynamic.yml`:

```yaml
    m2-http:   # :80 → 301 https
      rule: "Host(`m2moda.com.br`) || Host(`www.m2moda.com.br`)"
      entrypoints: web
      middlewares: [redirect-https]
      service: m2

    m2-https:  # TLS no Traefik; HTTP puro até o nginx
      rule: "Host(`m2moda.com.br`) || Host(`www.m2moda.com.br`)"
      entrypoints: websecure
      service: m2
      tls: { certresolver: letsencrypt }

    m2:
      loadBalancer:
        servers: [{ url: "http://m2-nginx:80" }]
```

3. `nginx/nginx.conf` distingue **borda** de **acesso direto**:
   - com `X-Forwarded-Proto` (veio do Traefik) → faz proxy para `m2-django:8000` sem redirecionar;
   - sem o cabeçalho (`http://host:8080`) → `301 https://host:8443` (comportamento local preservado).

## Quando o domínio for comprado

1. **DNS** (no registrador): `A m2moda.com.br → 209.50.245.51` e `A www.m2moda.com.br → 209.50.245.51`
   (ou `CNAME www → m2moda.com.br`).
2. Confirme a propagação: `getent hosts m2moda.com.br`.
3. O certificado é emitido sozinho (HTTP-01) quando o ACME tentar de novo. Para forçar:
   ```bash
   cd /home/kleber/traefik && docker compose restart traefik
   docker logs traefik_global --tail=50 | grep -i acme
   ```
4. Ajuste o `.env` do M2 para produção **antes** de divulgar a URL:
   `DEBUG=False`, `SITE_URL=https://m2moda.com.br`, SMTP real se for usar e-mail.
5. Valide: `curl -I https://m2moda.com.br/` deve devolver `200` e certificado válido.

## Verificação sem DNS (antes de comprar)

```bash
# roteamento pela borda, usando o Host do domínio e o IP local
curl -k -o /dev/null -w '%{http_code}\n' --resolve m2moda.com.br:443:127.0.0.1 https://m2moda.com.br/admin/login/
```

`-k` é necessário enquanto o certificado não existe (o Traefik serve o certificado default).

## Cuidados

- Editar `dynamic.yml` é **produção**: faça backup datado antes (`cp dynamic.yml dynamic.yml.bak-$(date +%F-%H%M%S)`)
  e valide o YAML — um erro derruba **todas** as rotas do arquivo (comeaqui, inventarius, ffsystem).
- `ACME_EMAIL` do stack global está com valor de exemplo (`admin@exemplo.com`): trocar por um e-mail real
  no `.env` daquele diretório.
- A aplicação M2 ainda não tem healthcheck de borda; ver D-071.
