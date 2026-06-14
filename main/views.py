"""Request handlers for auth, predictions, standings and contest management."""

from collections.abc import Mapping
from itertools import groupby

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.decorators.http import require_POST

from . import avatars, forms, models, utils
from .models import Tournament


def _parse_score(raw):
    """Parses a submitted score into a non-negative int, or None if invalid."""
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


@login_required
def index(request):
    return redirect("home")


class SignupView(View):
    def get(self, request):
        return render(request, "signup.html", {"form": forms.SignupForm()})

    def post(self, request):
        form = forms.SignupForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
            return redirect("home")
        return render(request, "signup.html", {"form": form})


class LoginView(View):
    def get(self, request):
        return render(request, "login.html", {"form": forms.LoginForm()})

    def post(self, request):
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                login(request, user)
                return redirect("home")
            form.add_error(None, "Invalid username or password.")
        return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def force_password_change(request):
    """Let a user set a new password (any value); clears the must-change flag."""
    if request.method == "POST":
        form = forms.SimplePasswordForm(request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data["new_password1"])
            request.user.save()
            profile = request.user.profile
            profile.must_change_password = False
            profile.save(update_fields=["must_change_password"])
            update_session_auth_hash(request, request.user)
            messages.success(request, "Password updated — you're all set!")
            return redirect("home")
    else:
        form = forms.SimplePasswordForm()
    return render(request, "change_password.html", {"form": form})


@login_required
def home_view(request):
    data = {
        "contests": utils.get_contests(request.user),
        "tournaments": Tournament.objects.all(),
    }
    return render(request, "home.html", data)


@login_required
def profile_view(request):
    """Edit display name + avatar, and optionally set a new password."""
    user = request.user
    profile = user.profile
    profile_form = forms.ProfileForm(
        initial={
            "first_name": user.first_name,
            "last_name": user.last_name,
            "avatar": profile.avatar,
        }
    )
    password_form = forms.SimplePasswordForm()

    if request.method == "POST":
        if "save_password" in request.POST:
            password_form = forms.SimplePasswordForm(request.POST)
            if password_form.is_valid():
                user.set_password(password_form.cleaned_data["new_password1"])
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password updated.")
                return redirect("profile")
        else:
            profile_form = forms.ProfileForm(request.POST)
            if profile_form.is_valid():
                user.first_name = profile_form.cleaned_data["first_name"]
                user.last_name = profile_form.cleaned_data["last_name"]
                user.save(update_fields=["first_name", "last_name"])
                profile.avatar = profile_form.cleaned_data["avatar"]
                profile.save(update_fields=["avatar"])
                messages.success(request, "Profile updated.")
                return redirect("profile")

    data = {
        "form": profile_form,
        "password_form": password_form,
        "avatars": avatars.choices(),
        "contests": utils.get_contests(request.user),
    }
    return render(request, "profile.html", data)


class PredictView(View):
    def get(self, request, contest):
        contest = get_object_or_404(request.user.contests, name=contest)
        games = contest.tournament.games.select_related("home", "away").order_by(
            "scheduled_datetime"
        )
        bets = {b.game_id: b for b in request.user.bets.filter(contest=contest)}
        rounds = []
        for date, group in groupby(games, key=utils.extract_date):
            items = []
            for game in group:
                bet = bets.get(game.id)
                items.append(
                    {
                        "game": game,
                        "home_pred": bet.home_score if bet else "",
                        "away_pred": bet.away_score if bet else "",
                        "locked": game.is_locked,
                        "has_result": game.has_result,
                    }
                )
            rounds.append({"date": date, "games": items})
        data = {
            "contest": contest,
            "contests": utils.get_contests(request.user),
            "rounds": rounds,
        }
        return render(request, "predict.html", data)

    def post(self, request, contest):
        contest = get_object_or_404(request.user.contests, name=contest)
        games = contest.tournament.games.all()
        bets = {b.game_id: b for b in request.user.bets.filter(contest=contest)}
        saved = 0
        removed = 0
        for game in games:
            if game.is_locked:  # cannot change a prediction after kickoff
                continue
            raw_home = (request.POST.get(f"home_{game.id}") or "").strip()
            raw_away = (request.POST.get(f"away_{game.id}") or "").strip()
            bet = bets.get(game.id)
            if not raw_home and not raw_away:  # cleared row — drop any saved bet
                if bet is not None:
                    bet.delete()
                    removed += 1
                continue
            home = _parse_score(raw_home)
            away = _parse_score(raw_away)
            if home is None or away is None:  # ignore partial rows
                continue
            if bet is None:
                models.Bet.objects.create(
                    user=request.user,
                    game=game,
                    contest=contest,
                    home_score=home,
                    away_score=away,
                )
                saved += 1
            elif bet.home_score != home or bet.away_score != away:
                bet.home_score = home
                bet.away_score = away
                bet.save()
                saved += 1
        parts = []
        if saved:
            parts.append(f"saved {saved}")
        if removed:
            parts.append(f"removed {removed}")
        messages.success(
            request,
            f"Predictions {' and '.join(parts)}." if parts else "No changes to save.",
        )
        return redirect("predict", contest=contest.name)


@login_required
@require_POST
def save_bet(request, contest, game_id):
    """Autosave a single prediction, or delete it when both fields are cleared."""
    contest = get_object_or_404(request.user.contests, name=contest)
    game = get_object_or_404(models.Game, id=game_id, tournament=contest.tournament)
    if game.is_locked:
        return JsonResponse({"ok": False, "error": "locked"}, status=409)
    raw_home = (request.POST.get("home_score") or "").strip()
    raw_away = (request.POST.get("away_score") or "").strip()
    if not raw_home and not raw_away:
        # Both fields cleared — remove the prediction entirely.
        models.Bet.objects.filter(
            user=request.user, game=game, contest=contest
        ).delete()
        return JsonResponse({"ok": True, "deleted": True})
    home = _parse_score(raw_home)
    away = _parse_score(raw_away)
    if home is None or away is None:
        return JsonResponse({"ok": False, "error": "invalid"}, status=400)
    models.Bet.objects.update_or_create(
        user=request.user,
        game=game,
        contest=contest,
        defaults={"home_score": home, "away_score": away},
    )
    return JsonResponse({"ok": True, "home": home, "away": away})


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


@login_required
def show_standing(request, contest):
    contest = get_object_or_404(request.user.contests, name=contest)

    w_exact = 3
    w_goal_diff = 2
    w_winner = 1
    playoffs_multiplier = 2

    rows = []
    for user in contest.users.all():
        preds = utils.get_correct_predictions(user, contest)
        points_groupstage = count_points(
            preds["groupstage"], w_exact, w_goal_diff, w_winner
        )
        points_playoffs = count_points(preds["playoffs"], w_exact, w_goal_diff, w_winner)
        rows.append(
            {
                "user": user,
                "preds_exact": preds["groupstage"]["exact"] + preds["playoffs"]["exact"],
                "preds_goal_diff": preds["groupstage"]["goal-diff"]
                + preds["playoffs"]["goal-diff"],
                "preds_winner": preds["groupstage"]["winner"] + preds["playoffs"]["winner"],
                "points": points_groupstage + points_playoffs * playoffs_multiplier,
            }
        )

    rows.sort(
        key=lambda r: (r["points"], r["preds_exact"], r["preds_goal_diff"]),
        reverse=True,
    )
    # Standard competition ranking (ties share a rank, e.g. 1, 2, 2, 4).
    previous_points = None
    for position, row in enumerate(rows, start=1):
        if row["points"] != previous_points:
            row["rank"] = position
            previous_points = row["points"]
        else:
            row["rank"] = rows[position - 2]["rank"]

    data = {
        "rows": rows,
        "contest": contest,
        "contests": utils.get_contests(request.user),
    }
    return render(request, "standing.html", data)


@login_required
@require_POST
def join_contest(request):
    name = "_".join(request.POST.get("contest-id", "").split())
    contest = models.Contest.objects.filter(name=name).first()
    if not contest:
        messages.error(request, "Competition not found. Check the ID and try again.")
        return redirect("home")
    if request.user in contest.users.all():
        messages.info(request, f"You're already in “{contest.name}”.")
    else:
        contest.users.add(request.user)
        messages.success(request, f"Joined “{contest.name}”!")
    return redirect("home")


@login_required
@require_POST
def create_contest(request):
    name = "_".join(request.POST.get("contest-id", "").split())
    tournament = models.Tournament.objects.filter(
        id=request.POST.get("tournament", "")
    ).first()
    if not name:
        messages.error(request, "Please enter a competition name.")
        return redirect("home")
    if tournament is None:
        messages.error(request, "Please choose a tournament.")
        return redirect("home")
    if models.Contest.objects.filter(name=name).exists():
        messages.error(request, f"A competition called “{name}” already exists.")
        return redirect("home")
    contest = models.Contest.objects.create(tournament=tournament, name=name)
    contest.users.add(request.user)
    messages.success(request, f"Created “{contest.name}” — share this ID with friends!")
    return redirect("predict", contest=contest.name)


@login_required
def show_bets(request, contest_name, game_id):
    contest = get_object_or_404(request.user.contests, name=contest_name)
    game = get_object_or_404(models.Game, id=game_id, tournament=contest.tournament)
    data = {
        "game": game,
        "contest": contest,
        "contests": utils.get_contests(request.user),
    }
    if not game.is_locked:
        return render(request, "bets_hidden.html", data)
    bets = models.Bet.objects.filter(contest=contest, game=game).select_related("user")
    data["bets_and_results"] = [(bet, utils.evaluate_bet(bet)) for bet in bets]
    return render(request, "bets.html", data)


def custom_404_view(request, exception):
    return render(request, "404.html", status=404)
