#!/usr/bin/env bash
# Pull the latest code and redeploy. Run on the server in the repo root.
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

echo "==> Pulling latest master"
git pull --ff-only origin master

echo "==> Rebuilding and restarting the container"
docker compose up -d --build

echo "==> Recent logs"
docker compose logs --tail=20 web

echo "==> Done. https://nostradamus.mine.bz"
