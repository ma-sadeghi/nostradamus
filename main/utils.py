from .models import Bet, Game
from django.contrib.auth.models import User
from django.utils.timezone import now


def get_user_points(user):
    user_bets = list(Bet.objects.filter(user=user))
    games = Game.objects.all()
    pts = 0

    for bet in user_bets:
        game = games.filter(id=bet.game.id)[0]

        if not is_played(game):
            continue

        bt1s = bet.team1_score
        bt2s = bet.team2_score
        gt1s = game.team1_score
        gt2s = game.team2_score

        # exact result predicted
        if (bt1s == gt1s) and (bt2s == gt2s):
            pts += 3
        # only goal difference predicted
        elif (bt1s - bt2s) == (gt1s - gt2s):
            pts += 2
        # only winner predicted
        elif (bt1s - bt2s) * (gt1s - gt2s) > 0:
            pts += 1

    return pts


def get_correct_predictions(user, kind):
    user_bets = list(Bet.objects.filter(user=user))
    games = Game.objects.all()

    num_exact_predictions = 0
    num_goal_dif_predictions = 0
    num_winner_only_predictions = 0

    for bet in user_bets:
        game = games.filter(id=bet.game.id)[0]

        if not is_played(game):
            continue

        bt1s = bet.team1_score
        bt2s = bet.team2_score
        gt1s = game.team1_score
        gt2s = game.team2_score

        # exact result predicted
        if (bt1s == gt1s) and (bt2s == gt2s):
            num_exact_predictions += 1
        # only goal difference predicted
        elif (bt1s - bt2s) == (gt1s - gt2s):
            num_goal_dif_predictions += 1
        # only winner predicted
        elif (bt1s - bt2s) * (gt1s - gt2s) > 0:
            num_winner_only_predictions += 1

    if kind == 'exact':
        return num_exact_predictions
    elif kind == 'goal-difference':
        return num_goal_dif_predictions
    elif (kind == 'winner-only'):
        return num_winner_only_predictions
    else:
        raise TypeError("'kind' can only take 'exact', 'goal-difference', or 'winner-only'")


def is_played(game):
    return True if now() > game.scheduled_datetime else False
