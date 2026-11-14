#!/usr/bin/env bash
#
# Ativa os hooks versionados deste repositório (D-031).
#
# `core.hooksPath` aponta para scripts/hooks/, que está no git — ao contrário
# de .git/hooks/, que não é versionado e se perde a cada clone.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

chmod +x scripts/hooks/*
git config core.hooksPath scripts/hooks
echo "hooks ativos: $(git config core.hooksPath)"
