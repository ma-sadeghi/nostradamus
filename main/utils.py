"""Helpers for grouping games and scoring user predictions."""

import datetime

from django.utils import timezone


def extract_date(game):
    """Returns the game's date in the currently active (viewer's) timezone."""
    return timezone.localtime(game.scheduled_datetime).date()


def get_correct_predictions(user, contest):
    """Returns the number of correct predictions for a user in a contest."""
    preds = {
        "groupstage": {"exact": 0, "goal-diff": 0, "winner": 0},
        "playoffs": {"exact": 0, "goal-diff": 0, "winner": 0},
    }
    bets = user.bets.filter(contest=contest).select_related("game")

    for bet in bets:
        game = bet.game
        # Only count games that have an actual recorded result.
        if not game.has_result:
            continue
        kind = "playoffs" if game.isplayoff else "groupstage"
        home_pred, away_pred = bet.home_score, bet.away_score
        home_actual, away_actual = game.home_score, game.away_score
        if (home_pred == home_actual) and (away_pred == away_actual):
            preds[kind]["exact"] += 1
        elif (home_pred - away_pred) == (home_actual - away_actual):
            preds[kind]["goal-diff"] += 1
        elif (home_pred - away_pred) * (home_actual - away_actual) > 0:
            preds[kind]["winner"] += 1

    return preds


def evaluate_bet(bet):
    """Returns the type of correct prediction for a bet, or None if unscored."""
    game = bet.game
    if not game.has_result:
        return None
    if (bet.home_score == game.home_score) and (bet.away_score == game.away_score):
        return "exact"
    if (bet.home_score - bet.away_score) == (game.home_score - game.away_score):
        return "goal-diff"
    if (bet.home_score - bet.away_score) * (game.home_score - game.away_score) > 0:
        return "winner"
    return "zilch"


def get_contests(user):
    """Returns a dictionary of active and past contests for a user."""
    contests = {"active": [], "past": []}
    for contest in user.contests.all():
        last_game = contest.tournament.games.order_by("-scheduled_datetime").first()
        if last_game is None:
            contests["active"].append(contest)
            continue
        last_date = last_game.scheduled_datetime.date()
        if datetime.date.today() - last_date > datetime.timedelta(days=7):
            contests["past"].append(contest)
        else:
            contests["active"].append(contest)
    contests["all"] = contests["active"] + contests["past"]
    return contests
