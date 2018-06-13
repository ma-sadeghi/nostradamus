from .models import Bet, Game
from django.contrib.auth.models import User
from django.utils.timezone import now


def get_correct_predictions(user, contest, kind):
    bets = user.bets.filter(contest=contest)
    games = Game.objects.all()

    num_exact_predictions = 0
    num_goal_dif_predictions = 0
    num_winner_only_predictions = 0

    for bet in bets:
        game = bet.game

        if not is_played(game):
            continue

        home_predicted = bet.home_score
        away_predicted = bet.away_score
        home_actual = game.home_score
        away_actual = game.away_score

        # exact result predicted
        if (home_predicted == home_actual) and (away_predicted == away_actual):
            num_exact_predictions += 1
        # only goal difference predicted
        elif (home_predicted - away_predicted) == (home_actual - away_actual):
            num_goal_dif_predictions += 1
        # only winner predicted
        elif (home_predicted - away_predicted) * (home_actual - away_actual) > 0:
            num_winner_only_predictions += 1

    if kind == 'exact':
        return num_exact_predictions
    elif kind == 'goal-difference':
        return num_goal_dif_predictions
    elif (kind == 'winner-only'):
        return num_winner_only_predictions

def is_played(game):
    return True if now() > game.scheduled_datetime else False

class Object(object):
    pass