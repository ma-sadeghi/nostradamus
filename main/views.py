from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import LoginForm
from .models import Game, Bet

from .utils import get_user_points, get_correct_predictions, is_played


@login_required(login_url='/login/')
def index(request):
    games = Game.objects.all().order_by('scheduled_datetime')
    bets = Bet.objects.filter(user=request.user)

    team1_score = []
    team2_score = []

    for game in games:
        game.is_played = is_played(game)
        if bets.filter(game=game):
            team1_score.append(bets.filter(game=game)[0].team1_score)
            team2_score.append(bets.filter(game=game)[0].team2_score)
        else:
            team1_score.append('')
            team2_score.append('')

    data = {'gts': zip(games, team1_score, team2_score)}

    return render(request, 'index.html', data)


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            uname = form.cleaned_data['username']
            pword = form.cleaned_data['password']
            user = authenticate(username=uname, password=pword)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect('/')
            else:
                return HttpResponseRedirect('/login')
    else:
        form = LoginForm()
        return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')


def place_bet(request):
    if request.method == 'POST':
        req_dict = dict(request.POST.lists())
        team1_score = req_dict['team1_score']
        team2_score = req_dict['team2_score']
        games = Game.objects.all().order_by('scheduled_datetime')
        user_bets = Bet.objects.filter(user=request.user)
        for t1, t2, g in zip(team1_score, team2_score, games):
            bet = Bet(user=request.user, game=g, team1_score=t1,
                      team2_score=t2)

            if t1 == '' or t2 == '':
                continue

            if not user_bets.filter(game=g):
                bet.save()
            else:
                bet = user_bets.filter(game=g)
                bet.update(team1_score=t1)
                bet.update(team2_score=t2)

    return HttpResponseRedirect('/standing/')

@login_required
def show_standing(request):
    users = User.objects.all()
    usernames = [user.first_name or user.get_username() for user in users]

    points = []
    exact_predictions = []
    goal_difference_predictions = []
    winner_only_predictions = []

    for user in users:
        points.append(get_user_points(user))
        exact_predictions.append(
            get_correct_predictions(user, 'exact'))
        goal_difference_predictions.append(
            get_correct_predictions(user, 'goal-difference'))
        winner_only_predictions.append(
            get_correct_predictions(user, 'winner-only'))

    zipped = list(zip(points, usernames, exact_predictions,
                      goal_difference_predictions, winner_only_predictions))
    zipped.sort()
    p, u, e, g, w = zip(*zipped)
    p, u, e, g, w = list(p), list(u),list(e), list(g), list(w)

    [arr.reverse() for arr in [p, u, e, g, w]]

    data = {'puegw_zip': zip(p, u, e, g, w)}

    return render(request, 'standing.html', data)


@login_required
def show_bets(request):
    games = Game.objects.all().order_by('scheduled_datetime')
    games_copy = games
    games = []

    for game in games_copy:
        if is_played(game):
            games.append(game)

    bets = Bet.objects.all()
    users = User.objects.all()
    usernames = [user.first_name or user.get_username() for user in users]

    user_bets = [[] for i in range(len(games))]

    for i, game in enumerate(games):
        game_bets = bets.filter(game=game)
        for usr in users:
            user_bet = game_bets.filter(user=usr)
            if not user_bet:
                user_bets[i].append('-')
            else:
                user_bet = user_bet[0]
                bet = str(user_bet.team1_score) + '-' + str(user_bet.team2_score)
                user_bets[i].append(bet)

    data = {'games': games, 'users': usernames, 'gub': zip(games, user_bets)}

    return render(request, 'bets.html', data)
