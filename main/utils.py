import datetime
from django.utils.timezone import now


def is_played(game):
    """Returns True if a game has been played."""
    return True if now() > game.scheduled_datetime else False


def extract_date(game):
    """Returns the date of a game."""
    return game.scheduled_datetime.date()


def get_correct_predictions(user, contest):
    """Returns the number of correct predictions for a user in a contest."""
    preds = {
        "groupstage": {"exact": 0, "goal-diff": 0, "winner": 0},
        "playoffs": {"exact": 0, "goal-diff": 0, "winner": 0},
    }
    bets = user.bets.filter(contest=contest)

    for bet in bets:
        game = bet.game
        kind = "playoffs" if game.isplayoff else "groupstage"
        # If game hasn't been played yet, don't count towards standing
        if not is_played(game):
            continue
        # Get the predictions and actual scores
        home_pred = bet.home_score
        away_pred = bet.away_score
        home_actual = game.home_score
        away_actual = game.away_score
        # Exact prediction
        if (home_pred == home_actual) and (away_pred == away_actual):
            preds[kind]["exact"] += 1
        # Goal difference
        elif (home_pred - away_pred) == (home_actual - away_actual):
            preds[kind]["goal-diff"] += 1
        # Winner only
        elif (home_pred - away_pred) * (home_actual - away_actual) > 0:
            preds[kind]["winner"] += 1

    return preds


def evaluate_bet(bet):
    """Returns the type of correct prediction for a bet."""
    game = bet.game
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
    for contest_ in user.contests.all():
        latest_game_date = contest_.tournament.games.latest(
            "scheduled_datetime"
        ).scheduled_datetime.date()
        if datetime.date.today() - latest_game_date > datetime.timedelta(days=7):
            contests["past"].append(contest_)
        else:
            contests["active"].append(contest_)
    contests["all"] = contests["active"] + contests["past"]
    return contests
