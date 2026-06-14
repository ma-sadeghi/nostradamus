"""Fetch finished match results from TheSportsDB and fill them into our games.

TheSportsDB's free v1 API (test key ``123``) returns FIFA World Cup events with
final scores. This command matches each finished event to one of our Game rows
by team pairing and writes the score, only touching games that don't yet have a
result (unless --force). Set ``THESPORTSDB_API_KEY`` for a dedicated key.

Run it periodically during the tournament, e.g. via cron (it only calls the API
once a match has been kicked off long enough to have a result, and retries):
    */30 * * * * cd /path/to/app && uv run python manage.py sync_results
"""

import json
import os
import urllib.error
import urllib.request
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from main.models import Team, Tournament

API_URL = (
    "https://www.thesportsdb.com/api/v1/json/{key}/eventsseason.php?id={league}&s={season}"
)

# TheSportsDB names that don't match our Team.name; map them to our FIFA codes.
NAME_ALIASES = {
    "bosnia-herzegovina": "BIH",
    "bosnia and herzegovina": "BIH",
    "curacao": "CUW",
    "curaçao": "CUW",
    "usa": "USA",
    "united states": "USA",
    "ivory coast": "CIV",
    "cote d'ivoire": "CIV",
    "côte d'ivoire": "CIV",
    "dr congo": "COD",
    "democratic republic of the congo": "COD",
    "congo dr": "COD",
    "cape verde": "CPV",
    "cabo verde": "CPV",
    "south korea": "KOR",
    "korea republic": "KOR",
    "turkiye": "TUR",
    "türkiye": "TUR",
}


class Command(BaseCommand):
    help = "Sync finished World Cup results from TheSportsDB into Game scores."

    def add_arguments(self, parser):
        parser.add_argument("--tournament", default="World Cup 2026")
        parser.add_argument("--season", default="2026")
        parser.add_argument("--league-id", default="4429", help="TheSportsDB league id.")
        parser.add_argument(
            "--min-age-minutes",
            type=int,
            default=120,
            help="Only fetch once a match kicked off this long ago (default 120).",
        )
        parser.add_argument(
            "--force", action="store_true", help="Overwrite scores that already exist."
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Report changes without saving."
        )

    def handle(self, *args, **options):
        tournament = Tournament.objects.filter(name=options["tournament"]).first()
        if tournament is None:
            raise CommandError(f"Tournament not found: {options['tournament']}")

        # Only call the API once a kicked-off match is old enough to have a
        # result; a periodic cron then retries until the score lands (handy for
        # playoff games that run long with extra time / penalties).
        min_age = options["min_age_minutes"]
        cutoff = timezone.now() - timedelta(minutes=min_age)
        due = tournament.games.filter(
            home_score__isnull=True, scheduled_datetime__lte=cutoff
        )
        if not options["force"] and not due.exists():
            self.stdout.write(
                f"No matches due yet (none kicked off over {min_age} min ago "
                "without a result)."
            )
            return

        key = os.environ.get("THESPORTSDB_API_KEY", "123")
        url = API_URL.format(key=key, league=options["league_id"], season=options["season"])
        events = self._fetch(url)

        updated = skipped = unmatched = pending = 0
        for event in events:
            if event.get("strStatus") != "FT":
                pending += 1
                continue
            home_score = self._to_int(event.get("intHomeScore"))
            away_score = self._to_int(event.get("intAwayScore"))
            if home_score is None or away_score is None:
                pending += 1
                continue

            home = self._resolve_team(event.get("strHomeTeam"))
            away = self._resolve_team(event.get("strAwayTeam"))
            game = self._find_game(tournament, home, away)
            if game is None:
                unmatched += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  unmatched: {event.get('strHomeTeam')} vs "
                        f"{event.get('strAwayTeam')} ({event.get('dateEvent')})"
                    )
                )
                continue

            # Map the API's home/away score onto our home/away orientation.
            if game.home_id == home.id:
                new_home, new_away = home_score, away_score
            else:
                new_home, new_away = away_score, home_score

            if game.has_result and not options["force"]:
                skipped += 1
                continue
            if game.home_score == new_home and game.away_score == new_away:
                skipped += 1
                continue

            self.stdout.write(
                f"  {game.home} {new_home}-{new_away} {game.away}"
                + ("  (dry-run)" if options["dry_run"] else "")
            )
            if not options["dry_run"]:
                game.home_score = new_home
                game.away_score = new_away
                game.save(update_fields=["home_score", "away_score"])
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. updated={updated} skipped={skipped} "
                f"unmatched={unmatched} not-finished={pending}"
            )
        )

    def _fetch(self, url):
        request = urllib.request.Request(url, headers={"User-Agent": "nostradamus"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode())
        except (urllib.error.URLError, ValueError) as exc:
            raise CommandError(f"Could not fetch results: {exc}") from exc
        return payload.get("events") or []

    @staticmethod
    def _to_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _resolve_team(name):
        if not name:
            return None
        key = name.strip().lower()
        if key in NAME_ALIASES:
            return Team.objects.filter(abbreviation=NAME_ALIASES[key]).first()
        return Team.objects.filter(name__iexact=name.strip()).first()

    @staticmethod
    def _find_game(tournament, home, away):
        if home is None or away is None:
            return None
        return (
            tournament.games.filter(home__in=[home, away], away__in=[home, away])
            .exclude(home=away)
            .first()
        )
