# syntax=docker/dockerfile:1
#
# Build em dois estágios:
#   builder  -> instala toolchain e compila as dependências num venv isolado
#   runtime  -> copia apenas o venv pronto; sem compiladores na imagem final
#
# A imagem final roda como usuário sem privilégios (appuser, UID/GID fixos).

# ---------------------------------------------------------------------------
# Estágio 1: builder
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Toolchain necessária apenas para compilar o mysqlclient.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        libmariadb-dev \
        libmariadb-dev-compat \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv "$VIRTUAL_ENV"

WORKDIR /tmp/build

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Estágio 2: runtime
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Apenas a biblioteca runtime do mysqlclient. Sem gcc/pkg-config/-dev.
# `upgrade` aplica os patches de segurança do Debian na imagem base (a tag
# está fixada, mas os pacotes da distro continuam recebendo correções).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmariadb3 \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# UID/GID fixos: mantêm a ownership dos volumes nomeados estável entre builds.
# São os mesmos UIDs históricos do projeto (100:101).
RUN groupadd --system --gid 101 appgroup \
    && useradd --system --uid 100 --gid appgroup --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY --from=builder --chown=100:101 /opt/venv /opt/venv
COPY --chown=100:101 backend/ /app/backend/
COPY --chown=100:101 frontend/ /app/frontend/

# Diretórios graváveis: quando o volume nomeado é novo, o Docker herda esta
# ownership, então o processo não precisa de root para dar chown em runtime.
RUN mkdir -p /app/backend/staticfiles /app/backend/media \
    && chown -R 100:101 /app/backend/staticfiles /app/backend/media

# O runtime não instala nada: pip/ensurepip só aumentam a superfície de ataque
# (e o pip vendora cópias antigas de setuptools em _vendor/vendor.txt, que
# aparecem como CVE na varredura de imagem sem serem código executável aqui).
RUN rm -rf \
        /usr/local/lib/python3.*/ensurepip \
        /usr/local/lib/python3.*/site-packages/pip \
        /usr/local/lib/python3.*/site-packages/pip-*.dist-info \
        /opt/venv/lib/python3.*/site-packages/pip \
        /opt/venv/lib/python3.*/site-packages/pip-*.dist-info \
        /opt/venv/bin/pip \
        /opt/venv/bin/pip3 \
        /opt/venv/bin/pip3.* \
        /usr/local/bin/pip \
        /usr/local/bin/pip3 \
        /usr/local/bin/pip3.*

COPY --chown=100:101 --chmod=755 backend/entrypoint.sh /entrypoint.sh

WORKDIR /app/backend

USER 100:101

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "m2shop.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
