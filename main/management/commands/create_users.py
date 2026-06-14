"""Bulk-create accounts with temporary passwords for handing out to friends.

Each new account gets a random temporary password and is flagged to force a
password change on first login. The printed list is meant to be shared with the
players (e.g. in a group chat); they pick their own password when they sign in.

    uv run python manage.py create_users alice bob carol --contest Lobby2026
    uv run python manage.py create_users --file names.txt
"""

import secrets
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from main.models import Contest

# Readable alphabet (no 0/O/1/l/I) for passwords people may type once by hand.
ALPHABET = "abcdefghijkmnpqrstuvwxyzACDEFGHJKLMNPQRSTUVWXYZ23456789"


class Command(BaseCommand):
    help = "Create accounts with temporary passwords (forced change on first login)."

    def add_arguments(self, parser):
        parser.add_argument("usernames", nargs="*", help="Usernames to create.")
        parser.add_argument("--file", help="Text file with one username per line.")
        parser.add_argument("--contest", help="Add every new user to this contest.")
        parser.add_argument("--length", type=int, default=8, help="Password length.")

    def handle(self, *args, **options):
        User = get_user_model()
        names = list(options["usernames"])
        if options["file"]:
            path = Path(options["file"])
            if not path.exists():
                raise CommandError(f"File not found: {path}")
            names += [line for line in path.read_text().splitlines() if line.strip()]
        # Usernames are stored lowercase (canonical); de-duplicate, keep order.
        names = list(dict.fromkeys(n.strip().lower() for n in names))
        if not names:
            raise CommandError("Give at least one username (args or --file).")

        contest = None
        if options["contest"]:
            contest = Contest.objects.filter(name=options["contest"]).first()
            if contest is None:
                raise CommandError(f"Contest not found: {options['contest']}")

        created = []
        for name in names:
            if User.objects.filter(username__iexact=name).exists():
                self.stdout.write(self.style.WARNING(f"skip (exists): {name}"))
                continue
            password = "".join(secrets.choice(ALPHABET) for _ in range(options["length"]))
            user = User.objects.create_user(username=name, password=password)
            user.profile.must_change_password = True
            user.profile.save(update_fields=["must_change_password"])
            if contest is not None:
                contest.users.add(user)
            created.append((name, password))

        if not created:
            self.stdout.write("No new users created.")
            return

        self.stdout.write(self.style.SUCCESS(f"\nCreated {len(created)} accounts:\n"))
        width = max(len(name) for name, _ in created)
        for name, password in created:
            self.stdout.write(f"  {name.ljust(width)}  {password}")
        self.stdout.write(
            "\nShare these; each player is asked to set their own password on first login."
        )
