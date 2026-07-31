#!/bin/sh
set -e

chown -R appuser:appgroup /app/backend/staticfiles /app/backend/media

exec gosu appuser "$@"
