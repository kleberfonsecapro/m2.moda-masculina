# syntax=docker/dockerfile:1
#
# nginx sem privilégios.
#
# A imagem oficial roda o master como root. Aqui o processo já inicia como
# `nginx` (UID/GID 101) e todas as rotas de escrita são preparadas no build:
#   - diretórios temporários de proxy em /var/cache/nginx
#   - pid em /tmp (o padrão /var/run/nginx.pid exige root)
#   - diretiva `user` removida (sem efeito e gera warning quando não-root)
#
# As portas 80/443 são privilegiadas fora de containers, mas dentro do Docker
# o sysctl `net.ipv4.ip_unprivileged_port_start` já é 0 por padrão. O compose
# deste projeto reforça isso explicitamente.

FROM nginx:1.26-alpine

RUN rm /etc/nginx/conf.d/default.conf \
    && apk upgrade --no-cache \
    && sed -i \
        -e 's#^user  nginx;#\# user removido: o processo já roda como nginx#' \
        -e 's#^pid        /var/run/nginx.pid;#pid /tmp/nginx.pid;#' \
        /etc/nginx/nginx.conf \
    && mkdir -p \
        /var/cache/nginx/client_temp \
        /var/cache/nginx/proxy_temp \
        /var/cache/nginx/fastcgi_temp \
        /var/cache/nginx/uwsgi_temp \
        /var/cache/nginx/scgi_temp \
    && chown -R nginx:nginx /var/cache/nginx \
    && chmod -R 0750 /var/cache/nginx

COPY --chown=nginx:nginx nginx.conf /etc/nginx/conf.d/

USER nginx

# 8081: entrada interna do Traefik global (nao publicada no host).
EXPOSE 80 443 8081

CMD ["nginx", "-g", "daemon off;"]
