from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Tournament(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Contest(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)
    users = models.ManyToManyField(User, related_name="contests")

    def save(self, *args, **kwargs):
        self.name = "_".join(self.name.strip().split())
        return super(Contest, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contests = models.ManyToManyField(Contest, related_name="contests")

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Team(models.Model):
    name = models.CharField(max_length=20, unique=True)
    abbreviation = models.CharField(max_length=3)
    # flag = models.ImageField(upload_to='flags')

    def __str__(self):
        return self.name


class Game(models.Model):
    tournament = models.ForeignKey(
        Tournament, on_delete=models.CASCADE, related_name="games"
    )
    home = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="%(class)s_home"
    )
    away = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="%(class)s_away"
    )
    home_score = models.IntegerField()
    away_score = models.IntegerField()
    isplayoff = models.BooleanField(default=False)
    scheduled_datetime = models.DateTimeField()

    def __str__(self):
        return (
            self.tournament.name
            + " : "
            + self.home.abbreviation
            + " vs. "
            + self.away.abbreviation
        )


# So that every time a game is updated, the Standing view's cache is reset
@receiver(post_save, sender=Game)
def clear_cache(sender, **kwargs):
    cache.clear()


class Bet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bets")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="bets")
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="bets")
    home_score = models.IntegerField()
    away_score = models.IntegerField()

    class Meta:
        unique_together = ("user", "game", "contest")

    def __str__(self):
        return self.user.username + " : " + str(self.contest) + " : " + str(self.game)
