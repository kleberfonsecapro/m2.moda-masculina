# Imagem da stack de backup 3-2-1 do M2 Moda Masculina.
# AGENTS.md §10: base fixada por digest (nunca :latest) e container sem privilégios (USER).
#
# Debian (glibc) e não Alpine porque o MySQL 8 usa caching_sha2_password: o cliente
# MariaDB do Alpine não embarca esse plugin ("Plugin caching_sha2_password could not be
# loaded"), enquanto o do Debian tem (/usr/lib/x86_64-linux-gnu/libmariadb3/plugin/).
FROM debian:bookworm-slim@sha256:99c0b25c46d0214d5a2091092e7908907dcaecd6a962cde0ac700acee222b6f3

# uid/gid fixos (10001): o volume nomeado backup_data mantem a propriedade
# mesmo quando a imagem e reconstruida com outra base/versao de pacote.
# Versoes fixadas: rebuild so quebra se o repositorio Debian remover a versao
# (nesse caso, atualizar o pin aqui — nunca remover o pin).
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      borgbackup=1.2.4-1 \
      rclone=1.60.1+dfsg-2+b5 \
      mariadb-client=1:10.11.19-0+deb12u1 \
      jq=1.6-2.1+deb12u3 \
      gzip=1.12-1 \
      findutils=4.9.0-4 \
      coreutils=9.1-1 \
      tzdata=2026f-0+deb12u1 \
      ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --system --gid 10001 m2backup \
 && useradd --system --uid 10001 --gid 10001 --home-dir /home/m2backup --shell /usr/sbin/nologin m2backup \
 && mkdir -p /backup/repo /backup/stage /backup/payload /backup/restore /backup/heartbeat /backup/home \
 && chown -R m2backup:m2backup /backup \
 && mkdir -p /opt/backup/lib

ENV TZ=America/Sao_Paulo \
    HOME=/backup/home \
    BORG_REPO=/backup/repo \
    STAGE_DIR=/backup/stage \
    PAYLOAD_DIR=/backup/payload \
    RESTORE_DIR=/backup/restore \
    HEARTBEAT_DIR=/backup/heartbeat \
    MEDIA_DIR=/media \
    BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK=no \
    BORG_RELOCATED_REPO_ACCESS_IS_OK=yes \
    BORG_EXIT_CODES=modern \
    LC_ALL=C

USER m2backup
WORKDIR /opt/backup

# --chmod fixa o bit de execucao na propria COPY (sem RUN como root).
COPY --chown=m2backup:m2backup --chmod=0644 lib/ /opt/backup/lib/
COPY --chown=m2backup:m2backup --chmod=0755 *.sh /opt/backup/

ENTRYPOINT ["/bin/bash", "/opt/backup/entrypoint.sh"]
