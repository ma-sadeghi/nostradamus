# Nostradamus

A small, self-hosted **sports tournament prediction game**. Friends join a
shared competition, predict the score of every match, and compete on a
leaderboard as results come in. Built with Django; runs happily on SQLite for a
group of friends.

It ships preloaded with the **FIFA World Cup 2026** group stage.

## How it works

- An **admin** loads a tournament's teams and fixtures (a CSV import), then
  enters real scores as matches finish.
- Players sign up, **join a competition** by its ID (or create their own), and
  enter a predicted score for each upcoming match.
- A match **locks at kickoff**: predictions can no longer be changed and
  everyone's predictions for that match become visible.
- Points are awarded once the admin records the final score.

### Scoring

| Outcome of your prediction              | Points |
| --------------------------------------- | ------ |
| Exact score                             | **3**  |
| Correct goal difference (not exact)     | **2**  |
| Correct winner / draw only              | **1**  |
| Wrong                                   | 0      |

Knockout-stage matches are worth **double**.

## Local development

Requires [uv](https://docs.astral.sh/uv/) (and nothing else — uv manages the
Python version and dependencies).

```bash
# 1. Install dependencies into a local virtualenv
uv sync

# 2. Create your local environment file
cp .env.example .env
# then set DJANGO_DEBUG=true and generate a secret key:
uv run python -c "from django.core.management.utils import get_random_secret_key as k; print('DJANGO_SECRET_KEY=' + k())" >> .env

# 3. Apply migrations
uv run python manage.py migrate

# 4. Create an admin account
uv run python manage.py createsuperuser

# 5. Run it
uv run python manage.py runserver
```

Open http://127.0.0.1:8000/. The admin lives at `/admin/`.

### Loading tournament data

Teams and fixtures are loaded from CSV. World Cup 2026 files are in `bin/`:

```bash
uv run python manage.py load_tournament \
  --tournament "World Cup 2026" \
  --teams bin/worldcup2026_teams.csv \
  --games bin/worldcup2026.csv
```

The import is **idempotent** — re-running updates existing matches instead of
creating duplicates. Teams are matched by name and reused across tournaments.

- **Entering results:** edit a game in `/admin/` and fill in its scores. Leave
  scores blank until a match has actually been played — blank means "no result
  yet" and the match won't be scored.
- **Knockout games:** their teams aren't known until the group stage ends, so
  they aren't in the import CSV. Add them in the admin once the bracket fills in
  (set *isplayoff* = yes). The schedule for reference is in
  `bin/worldcup2026_knockouts.md`.
- You can also import games directly through the admin's *Game → Import* button
  using the same CSV format.

### Auto-updating results

Instead of typing every score by hand, you can pull finished results from
[TheSportsDB](https://www.thesportsdb.com/):

```bash
uv run python manage.py sync_results            # fill any finished matches
uv run python manage.py sync_results --dry-run  # preview without saving
```

It matches each finished match to one of your games by team pairing and writes
the score, skipping games that already have a result (use `--force` to
overwrite). To avoid pointless calls it only contacts the API once a match
kicked off more than `--min-age-minutes` ago (default **120**) without a
result — so run it on a short cron and it will retry until the score lands,
including playoff games that run long with extra time / penalties:

```cron
*/30 * * * * cd /path/to/nostradamus && uv run python manage.py sync_results >> /tmp/sync.log 2>&1
```

That means: ~2 hours after kickoff the command starts looking for a result and
retries every 30 minutes until it appears, then leaves the game alone.

Notes: the free API works out of the box with a shared test key; for a stable
production key, sign up at TheSportsDB and set `THESPORTSDB_API_KEY`. The free
endpoint returns a rolling window of recent matches, so the short cron matters.
Knockout games must already exist in the DB (added via admin) to be filled. See
`bin/results_api_research.md` for the full API comparison and the
football-data.org fallback.

### Running tests

```bash
uv run python manage.py test
```

## Configuration

All configuration is read from environment variables (loaded from `.env` in
development). See `.env.example` for the full list. The important ones:

| Variable                       | Purpose                                             |
| ------------------------------ | --------------------------------------------------- |
| `DJANGO_SECRET_KEY`            | Required when `DEBUG` is off.                       |
| `DJANGO_DEBUG`                 | `true` only for local development.                  |
| `DJANGO_ALLOWED_HOSTS`         | Comma-separated hostnames the site is served from.  |
| `DJANGO_CSRF_TRUSTED_ORIGINS`  | Comma-separated origins (with scheme).              |
| `DJANGO_SECURE_SSL`            | HTTPS-only cookies, SSL redirect, HSTS. On unless `DEBUG`. |
| `DJANGO_HSTS_SECONDS`          | HSTS max-age (0 disables). Enable once HTTPS is stable. |
| `DJANGO_DB_PATH`               | Optional override for the SQLite file location.     |

## Deployment

The app is portable — anything that runs a WSGI app works. Static files are
served by [WhiteNoise](https://whitenoise.readthedocs.io/), so no separate
static server is needed.

```bash
# Install with production extras (adds gunicorn)
uv sync --extra prod

# Collect static assets
uv run python manage.py collectstatic --noinput

# Run migrations
uv run python manage.py migrate

# Serve
uv run gunicorn Nostradamus.wsgi --bind 0.0.0.0:8000
```

Set these in the environment of your host (not in a committed file):

```
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=...                 # a fresh, secret value
DJANGO_ALLOWED_HOSTS=yourdomain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com
DJANGO_SECURE_SSL=true                # if you terminate TLS at this app
```

**PythonAnywhere note:** point the web app's WSGI file at
`Nostradamus.wsgi.application`, set the environment variables above in the WSGI
config, and run `migrate` + `collectstatic` from a console. If TLS is
terminated by PythonAnywhere's proxy, keep `DJANGO_SECURE_SSL=true`.

## Security

The database holds real user accounts and **must not be committed**; it is
git-ignored. If you forked or cloned the old public repository, read
[`SECURITY.md`](SECURITY.md) — it covers rotating the leaked credentials and
scrubbing secrets from git history.

## Project layout

```
Nostradamus/        project settings, URLs, WSGI, auth backend, middleware
main/               the app: models, views, forms, admin, templates, static
  management/commands/  load_tournament, reset_leaked_passwords
bin/                tournament CSVs and reference schedules
```
