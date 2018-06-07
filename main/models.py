from django.db import models
from django.contrib.auth.models import User


class Team(models.Model):
    name = models.CharField(max_length=20)
    abbreviation = models.CharField(max_length=3)
    flag = models.ImageField(upload_to='flags')

    def __str__(self):
        return self.name


class Game(models.Model):
    # contest = models.ForeignKey(Contest)
    # home = models.CharField(max_length=100)
    # away = models.CharField(max_length=100)
    # home_abbreviation = models.CharField(max_length=3)
    # away_abbreviation = models.CharField(max_length=3)
    contest = models.ForeignKey(Contest)
    home = models.ForeignKey(Team)
    away = models.ForeignKey(Team)
    home_score = models.IntegerField()
    away_score = models.IntegerField()
    scheduled_datetime = models.DateTimeField()

    def __str__(self):
        return self.home_abbreviation + ' vs. ' + self.away_abbreviation


class Bet(models.Model):
    user = models.ForeignKey(User)
    game = models.ForeignKey(Game)
    home_score = models.IntegerField()
    away_score = models.IntegerField()

    def __str__(self):
        return self.user.username + ': ' + self.game.home + ' - ' + self.game.away


class Contest(models.Model):
    name = models.CharField(max_length=20)

