# Security notes

The previous version of this project was a **public** repository that committed:

- `flags/passwords.txt` — friends' passwords in plaintext
- `db.sqlite3` — the full database (accounts, password hashes, sessions, logs)
- a hardcoded Django `SECRET_KEY` in `settings.py`

Anything ever pushed to a public repo must be treated as permanently exposed.
Removing the files from the latest commit is **not enough** — they remain in
git history (and in any clones, forks, or caches). The steps below contain the
damage.

## What this revamp already did

- Removed `passwords.txt`, the stray `.env`, and stopped tracking `db.sqlite3`
  (now git-ignored).
- Moved `SECRET_KEY` and all config to environment variables. **Generate a new
  secret key** for your deployment — the old one is public, so any session or
  signed value made with it is forgeable.
- Added the `reset_leaked_passwords` management command (below).

## 1. Rotate all passwords

Every stored password should be considered known. Invalidate them all:

```bash
uv run python manage.py reset_leaked_passwords
```

This sets an *unusable* password on every account, so no leaked password works
anymore. Then set fresh credentials as needed:

```bash
uv run python manage.py changepassword <username>   # for a returning friend
uv run python manage.py createsuperuser             # for your admin login
```

(New players who sign up afterwards are unaffected.)

## 2. Use a fresh secret key

Generate one and put it in your deployment environment (never in git):

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

## 3. Scrub secrets from git history

Removing the files in a new commit leaves them in history. Rewrite history to
purge them. Using
[`git filter-repo`](https://github.com/newren/git-filter-repo) (recommended):

```bash
# from a fresh clone you can afford to rewrite
git filter-repo --invert-paths \
  --path flags/passwords.txt \
  --path db.sqlite3 \
  --path Nostradamus/static/.env

# then force-update the remote (this rewrites public history)
git push origin --force --all
git push origin --force --tags
```

> ⚠️ This rewrites every commit hash. Anyone else with a clone must re-clone.
> Because the data was already public, treat rotation (steps 1–2) as the real
> fix and history rewriting as cleanup.

## 4. Make the repository private

A prediction game for ~15 friends has no reason to be a public repo. Making it
private removes the ongoing exposure of any future commits and the database.
(Already-public history may still live in forks/caches, so steps 1–2 still
matter.)
