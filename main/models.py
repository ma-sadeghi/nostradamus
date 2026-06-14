"""Data models for tournaments, games, contests and user predictions."""

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget


class Tournament(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Contest(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    name = models.CharField(max_length=20, unique=True)
    users = models.ManyToManyField(User, related_name="contests")

    def save(self, *args, **kwargs):
        self.name = "_".join(self.name.strip().split())
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Set when an account is handed out with a temporary password; forces a
    # password change on the next login.
    must_change_password = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    Profile.objects.get_or_create(user=instance)


class Team(models.Model):
    name = models.CharField(max_length=20, unique=True)
    abbreviation = models.CharField(max_length=3)

    def __str__(self):
        return self.name


class Game(models.Model):
    tournament = models.ForeignKey(
        Tournament, on_delete=models.CASCADE, related_name="games"
    )
    home = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="%(class)s_home")
    away = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="%(class)s_away")
    # Scores are null until a result is entered; null means "not played yet".
    home_score = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(0)]
    )
    away_score = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(0)]
    )
    isplayoff = models.BooleanField(default=False)
    scheduled_datetime = models.DateTimeField()

    @property
    def is_locked(self):
        """Predictions freeze and become visible once kickoff has passed."""
        return now() >= self.scheduled_datetime

    @property
    def has_result(self):
        """True once a final score has been recorded for the game."""
        return self.home_score is not None and self.away_score is not None

    def __str__(self):
        return f"{self.tournament.name} : {self.home.abbreviation} vs. {self.away.abbreviation}"


class GameResource(resources.ModelResource):
    tournament = fields.Field(
        column_name="tournament",
        attribute="tournament",
        widget=ForeignKeyWidget(Tournament, "name"),
    )
    home = fields.Field(
        column_name="home_team_abbreviation",
        attribute="home",
        widget=ForeignKeyWidget(Team, "abbreviation"),
    )
    away = fields.Field(
        column_name="away_team_abbreviation",
        attribute="away",
        widget=ForeignKeyWidget(Team, "abbreviation"),
    )

    class Meta:
        model = Game
        # Identify rows by the natural key so re-imports update instead of
        # duplicating, while still allowing a repeated pairing on a new date.
        import_id_fields = ("tournament", "home", "away", "scheduled_datetime")
        skip_unchanged = True
        report_skipped = True
        fields = (
            "id",
            "tournament",
            "home",
            "away",
            "home_score",
            "away_score",
            "scheduled_datetime",
            "isplayoff",
        )
        export_order = fields


# So that every time a game is updated, the Standing view's cache is reset
@receiver(post_save, sender=Game)
def clear_cache(sender, **kwargs):
    cache.clear()


class Bet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bets")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="bets")
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="bets")
    home_score = models.IntegerField(validators=[MinValueValidator(0)])
    away_score = models.IntegerField(validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ("user", "game", "contest")

    def __str__(self):
        return f"{self.user.username} : {self.contest} : {self.game}"
