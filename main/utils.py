from django.utils.timezone import now


def get_correct_predictions(user, contest, kind, round):
    bets = user.bets.filter(contest=contest)
    # games = Game.objects.all()

    num_exact_predictions = 0
    num_goal_dif_predictions = 0
    num_winner_only_predictions = 0

    for bet in bets:
        game = bet.game

        # If game hasn't been played yet, don't count towards standing
        if not is_played(game):
            continue

        if round == "groupstage":
            if game.isplayoff:
                continue
        elif round == "playoffs":
            if not game.isplayoff:
                continue
        else:
            raise Exception('Round can only be "groupstage" or "playoffs"')

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

    if kind == "exact":
        return num_exact_predictions
    elif kind == "goal-difference":
        return num_goal_dif_predictions
    elif kind == "winner-only":
        return num_winner_only_predictions


def is_played(game):
    return True if now() > game.scheduled_datetime else False


class Object(object):
    pass


def extract_date(game):
    return game.scheduled_datetime.date()


def evaluate_bet(bet):
    game = bet.game
    if (bet.home_score == game.home_score) and (bet.away_score == game.away_score):
        return "exact"
    if (bet.home_score - bet.away_score) == (game.home_score - game.away_score):
        return "goal-difference"
    if (bet.home_score - bet.away_score) * (game.home_score - game.away_score) > 0:
        return "winner-only"
    return "zilch"
