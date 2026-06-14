"""Load a tournament's teams and games from CSV files.

Teams are matched by their (unique) name so existing countries are reused
across tournaments; each team's abbreviation is set to the value in the teams
CSV. Games are imported via the django-import-export resource, which is
idempotent on (tournament, home, away, kickoff), so re-running updates rather
than duplicates.
"""

import csv
from pathlib import Path

import tablib
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from main.models import GameResource, Team, Tournament


class Command(BaseCommand):
    help = "Load teams and games for a tournament from CSV files."

    def add_arguments(self, parser):
        parser.add_argument("--tournament", required=True, help="Tournament name.")
        parser.add_argument(
            "--teams", required=True, help="Teams CSV (columns: name,abbreviation)."
        )
        parser.add_argument(
            "--games", required=True, help="Games CSV in import/export format."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        teams_path = Path(options["teams"])
        games_path = Path(options["games"])
        for path in (teams_path, games_path):
            if not path.exists():
                raise CommandError(f"File not found: {path}")

        tournament, created = Tournament.objects.get_or_create(name=options["tournament"])
        verb = "Created" if created else "Found existing"
        self.stdout.write(f"{verb} tournament: {tournament.name}")

        created_teams = updated_teams = 0
        with teams_path.open(newline="") as fh:
            for row in csv.DictReader(fh):
                name = row["name"].strip()
                abbr = row["abbreviation"].strip()
                team, was_created = Team.objects.get_or_create(
                    name=name, defaults={"abbreviation": abbr}
                )
                if was_created:
                    created_teams += 1
                elif team.abbreviation != abbr:
                    team.abbreviation = abbr
                    team.save(update_fields=["abbreviation"])
                    updated_teams += 1
        self.stdout.write(
            f"Teams: {created_teams} created, {updated_teams} re-coded, rest reused."
        )

        dataset = tablib.Dataset().load(games_path.read_text(), format="csv")
        result = GameResource().import_data(dataset, dry_run=False, raise_errors=True)
        totals = result.totals
        self.stdout.write(
            self.style.SUCCESS(
                "Games imported: "
                f"new={totals.get('new', 0)} "
                f"updated={totals.get('update', 0)} "
                f"skipped={totals.get('skip', 0)}"
            )
        )
