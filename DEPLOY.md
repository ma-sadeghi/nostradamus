# Deploying Nostradamus

The live instance runs at **https://nostradamus.mine.bz** on a Hetzner box,
as a Docker container behind a shared host reverse proxy.

## Stack

- **Docker Compose**: one `web` service — gunicorn serving Django, static files
  via WhiteNoise, SQLite on a host bind mount.
- **Shared ingress** (`/srv/ingress`, `caddy-docker-proxy`): a single Caddy that
  owns `:80/:443` for the whole host and terminates TLS (Let's Encrypt). It
  discovers this app from the `caddy` labels in `compose.yml` — the app declares
  its own route (`nostradamus.mine.bz` → port 8000) and nothing else on the box
  needs to know about it. Other apps front the same way on the `edge` network.

## Updating (day to day)

From your machine, push to `master`. Then on the server:

```sh
cd /srv/nostradamus
./deploy.sh          # git pull + docker compose up -d --build
```

## First-time server setup

```sh
# 1. Shared ingress network (once per host)
docker network create edge

# 2. Bring up the shared reverse proxy (once per host) — see /srv/ingress

# 3. Clone the app and create its data dir
git clone https://github.com/ma-sadeghi/nostradamus.git /srv/nostradamus
mkdir -p /srv/nostradamus-data        # holds db.sqlite3 (bind-mounted to /data)
cd /srv/nostradamus

# 4. Create .env (see .env.example). Generate a secret key with:
#    docker run --rm python:3.12-slim python -c \
#      "import secrets; print('DJANGO_SECRET_KEY=' + secrets.token_urlsafe(64))"
#    Set DJANGO_DEBUG=false, DJANGO_ALLOWED_HOSTS=nostradamus.mine.bz,
#    DJANGO_CSRF_TRUSTED_ORIGINS=https://nostradamus.mine.bz, DJANGO_SECURE_SSL=true,
#    DJANGO_DB_PATH=/data/db.sqlite3

# 5. Build and start
docker compose up -d --build
```

The entrypoint runs migrations, collects static, and loads the World Cup 2026
fixtures (idempotently) on every start. Create your admin login with:

```sh
docker compose exec web python manage.py createsuperuser
```

## Notes

- The database is **not** in git; it lives in `/srv/nostradamus-data` and should
  be backed up separately (and is covered by Hetzner snapshots).
- If the GitHub repo is made private, add a read-only deploy key on the server
  for `git pull` (see the forkolio DEPLOY.md for the same pattern).
- Results auto-update via cron: `*/30 * * * * docker exec nostradamus python manage.py sync_results`.
