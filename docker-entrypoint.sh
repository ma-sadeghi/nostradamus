#!/bin/sh
# Apply migrations, collect static, ensure tournament data, then serve.
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Idempotent: loads World Cup 2026 only if not already present.
python manage.py load_tournament \
  --tournament "World Cup 2026" \
  --teams bin/worldcup2026_teams.csv \
  --games bin/worldcup2026.csv || true

exec gunicorn Nostradamus.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --access-logfile - \
  --error-logfile -
