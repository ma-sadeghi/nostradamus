"""Invalidate all stored passwords after the repo's password leak.

The old public repository exposed plaintext passwords and the database, so
every existing password must be considered compromised. This sets an unusable
password on all users; afterwards, set fresh credentials with:

    uv run python manage.py changepassword <username>

or, for an admin account, `uv run python manage.py createsuperuser`.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Set an unusable password on every user to kill leaked credentials."

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Run without the interactive confirmation prompt.",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.all()
        count = users.count()
        if not options["yes"]:
            answer = input(
                f"This will invalidate passwords for all {count} users. Continue? [y/N] "
            )
            if answer.strip().lower() not in {"y", "yes"}:
                self.stdout.write("Aborted.")
                return

        reset = 0
        for user in users:
            user.set_unusable_password()
            user.save(update_fields=["password"])
            reset += 1

        self.stdout.write(self.style.SUCCESS(f"Invalidated passwords for {reset} users."))
        self.stdout.write(
            "Set new ones with `manage.py changepassword <username>` "
            "or `manage.py createsuperuser`."
        )
