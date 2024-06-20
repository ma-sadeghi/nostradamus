from collections.abc import Mapping
from itertools import groupby

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.cache import cache_page

from . import forms, models, utils
from .models import Tournament


@login_required
def index(request):
    # return render(request, 'home.html')
    return HttpResponseRedirect(reverse("home"))


class SignupView(View):
    def get(self, request):
        return render(request, "signup.html")

    def post(self, request):
        form = forms.SignupForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)
            if user is None:
                return HttpResponseRedirect("/home")
            login(request, user)
            return HttpResponseRedirect(reverse("home"))
        return render(request, "signup.html", {"form": form})


class LoginView(View):
    def get(self, request):
        form = forms.LoginForm()
        return render(request, "login.html", {"form": form})

    def post(self, request):
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)
            if user is None:
                return render(
                    request,
                    "login.html",
                    {
                        "form": form,
                        "error_message": "Invalid username or password.",
                    },
                )
            login(request, user)
            return HttpResponseRedirect(reverse("home"))


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))


@login_required
def home_view(request):
    contests = utils.get_contests(request.user)
    tournaments = Tournament.objects.all()
    data = {"contests": contests, "tournaments": tournaments}
    return render(request, "home.html", data)


# NOTE: name of the 2nd arg (contest) must match with 'contest' in home.html
class PredictView(View):
    def get(self, request, contest):
        contest = request.user.contests.filter(name=contest)[0]
        # Comment the next line and uncomment the line after, once group stage is completed!
        games = contest.tournament.games.all().order_by("scheduled_datetime")
        # games = contest.tournament.games.filter(isplayoff=True).order_by('scheduled_datetime')
        games_by_date = [list(g) for t, g in groupby(games, key=utils.extract_date)]
        bets_by_date = []
        games_and_bets_and_states_by_date = []
        bets = []
        for games in games_by_date:
            bets = []
            states = []
            for game in games:
                bet = request.user.bets.filter(game=game, contest=contest)
                bet = [bet[0].home_score, bet[0].away_score] if bet else ["", ""]
                bets.append(bet)
                states.append("played" if utils.is_played(game) else "not_played")
            bets_by_date.append(bets)
            games_and_bets_and_states_by_date.append(
                (zip(games, bets, states), game.scheduled_datetime.date())
            )
        data = {
            "games_and_bets_and_states_by_date": games_and_bets_and_states_by_date,
            "contest": contest,
            "contests": utils.get_contests(request.user),
        }
        return render(request, "predict.html", data)

    def post(self, request, contest):
        req_dict = dict(request.POST.lists())
        home_scores = req_dict["home_score"]
        away_scores = req_dict["away_score"]

        contest = request.user.contests.filter(name=contest)[0]
        # Comment the next line and uncomment the line after, once group stage is completed!
        games = contest.tournament.games.all().order_by("scheduled_datetime")
        # games = contest.tournament.games.filter(isplayoff=True).order_by('scheduled_datetime')

        for home_score, away_score, game in zip(home_scores, away_scores, games):
            if utils.is_played(game):  # no update if time passed
                continue

            bet_query = request.user.bets.filter(game=game, contest=contest)
            old_bet = (
                [bet_query[0].home_score, bet_query[0].away_score]
                if bet_query
                else ["", ""]
            )
            if home_score != old_bet[0] or away_score != old_bet[1]:
                if bet_query:  # update existing
                    bet_query.update(home_score=home_score)
                    bet_query.update(away_score=away_score)
                else:
                    new_bet = models.Bet(
                        user=request.user,
                        game=game,
                        contest=contest,
                        home_score=home_score,
                        away_score=away_score,
                    )
                    new_bet.save()
        return HttpResponseRedirect("./")


@login_required
def standing_home_view(request):
    contests = utils.get_contests(request.user)
    return render(request, "standing_home.html", {"contests": contests})


def count_points(preds: Mapping[str, int], w_exact: int, w_goal_diff: int, w_winner: int):
    """Returns the total points for a set of predictions."""
    return (
        preds["exact"] * w_exact
        + preds["goal-diff"] * w_goal_diff
        + preds["winner"] * w_winner
    )


# @cache_page(24 * 3600)  # Reset cache every 1 week
@login_required
def show_standing(request, contest):
    contest = request.user.contests.filter(name=contest).all()[0]
    users = contest.users.all()
    rows = []

    w_exact = 3
    w_goal_diff = 2
    w_winner = 1
    playoffs_multiplier = 2

    for user in users:
        preds = utils.get_correct_predictions(user, contest)
        preds_exact = preds["groupstage"]["exact"] + preds["playoffs"]["exact"]
        preds_goal_diff = preds["groupstage"]["goal-diff"] + preds["playoffs"]["goal-diff"]
        preds_winner = preds["groupstage"]["winner"] + preds["playoffs"]["winner"]
        points_groupstage = count_points(preds["groupstage"], w_exact, w_goal_diff, w_winner)
        points_playoffs = count_points(preds["playoffs"], w_exact, w_goal_diff, w_winner)
        row = {
            "user": user,
            "preds_exact": preds_exact,
            "preds_goal_diff": preds_goal_diff,
            "preds_winner": preds_winner,
            "points": points_groupstage + points_playoffs * playoffs_multiplier,
        }
        rows.append(row)

    rows = sorted(rows, key=lambda x: x["points"], reverse=True)
    data = {
        "rows": rows,
        "contest": contest,
        "contests": utils.get_contests(request.user),
    }

    return render(request, "standing.html", data)


@login_required
def join_contest(request):
    user = request.user
    contest_id = request.POST["contest-id"]
    contest = models.Contest.objects.filter(name=contest_id)
    if not contest:
        return redirect(reverse("home") + "?contest_not_found=True")
    contest = contest[0]
    if user not in contest.users.all():
        contest.users.add(user)
        return redirect(reverse("home") + "?joined_contest=True")
    return redirect(reverse("home") + "?already_member=True")


@login_required
def show_bets(request, contest_name, game_id):
    contests = utils.get_contests(request.user)
    contest = models.Contest.objects.get(name=contest_name)
    game = models.Game.objects.get(id=game_id)
    bets = models.Bet.objects.filter(contest=contest, game=game)
    results = [utils.evaluate_bet(bet) for bet in bets]
    bets_and_results = list(zip(bets, results))
    # We need to pass 'contests' for navbar to work (standings list)
    data = {
        "bets_and_results": bets_and_results,
        "game": game,
        "contest": contest,
        "contests": contests,
    }
    if utils.is_played(game):
        return render(request, "bets.html", data)
    else:
        return render(request, "bets_hidden.html", data)


def custom_404_view(request, exception):
    return render(request, "404.html", status=404)
