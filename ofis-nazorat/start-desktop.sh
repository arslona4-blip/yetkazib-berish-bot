#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -d node_modules ]]; then
  echo "Paketlar o'rnatilmoqda..."
  npm install
fi
echo "Ofis nazorat ochilmoqda..."
npm run desktop
