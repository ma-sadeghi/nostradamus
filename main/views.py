from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.views import View
from . import forms
from . import models
from . import utils


@login_required
def index(request):
    print(reverse('home'))
    return render(request, 'home.html')


class SignupView(View):

    def get(self, request):
        return render(request, 'signup.html')

    def post(self, request):
        form = forms.SignupForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user == None:
                return HttpResponseRedirect('/home')
            login(request, user)
        return render(request, 'signup.html', {'form': form})


class LoginView(View):
    
    def get(self, request):
        form = forms.LoginForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request):
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user == None:
                return HttpResponseRedirect(reverse('login'))
            login(request, user)
            return HttpResponseRedirect(reverse('home'))

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))


@login_required
def home_view(request):
    contests = request.user.contests.all()
    return render(request, 'home.html', {'contests': contests})

# NOTE: name of the 2nd arg (contest) must match with 'contest' in home.html
class PredictView(View):

    def get(self, request, contest):
        contest = request.user.contests.filter(name=contest)[0]
        games = contest.tournament.games.all()
        bets = []
        for game in games:
            bet = request.user.bets.filter(game=game)
            bet = [bet[0].home_score, bet[0].away_score] if bet else ['','']
            bets.append(bet)
        return render(request, 'predict.html', {'games_and_bets': zip(games, bets),
                                                'contest': contest})

    def post(self, request):
        pass


@login_required
def my_bets(request):
    games = Game.objects.all().order_by('scheduled_datetime')
    bets = Bet.objects.filter(user=request.user)

    home_score = []
    away_score = []

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



def place_bet(request):
    if request.method == 'POST':
        req_dict = dict(request.POST.lists())
        home_score = req_dict['home_score']
        away_score = req_dict['away_score']
        games = Game.objects.all().order_by('scheduled_datetime')
        user_bets = Bet.objects.filter(user=request.user)

        for t1, t2, g in zip(home_score, away_score, games):
            bet = Bet(user=request.user, game=g, home_score=t1, away_score=t2)
            if t1 == '' or t2 == '':
                continue
            # new bet
            if not user_bets.filter(game=g):
                bet.save()
            # update existing
            else:
                bet = user_bets.filter(game=g)
                bet.update(home_score=t1)
                bet.update(away_score=t2)

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
            utils.get_correct_predictions(user, 'exact'))
        goal_difference_predictions.append(
            utils.get_correct_predictions(user, 'goal-difference'))
        winner_only_predictions.append(
            utils.get_correct_predictions(user, 'winner-only'))

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
