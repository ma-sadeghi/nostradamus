from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.views import View
from itertools import groupby
from . import forms
from . import models
from . import utils


@login_required
def index(request):
    # return render(request, 'home.html')
    return HttpResponseRedirect(reverse('home'))


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
        # games = contest.tournament.games.all().order_by('scheduled_datetime')
        games = contest.tournament.games.filter(isplayoff=True).order_by('scheduled_datetime')
        games_by_date = [list(g) for t, g in groupby(games, key=utils.extract_date)]
        bets_by_date = []
        games_and_bets_by_date = []
        bets = []
        for games in games_by_date:
            bets = []
            for game in games:
                bet = request.user.bets.filter(game=game, contest=contest)
                bet = [bet[0].home_score, bet[0].away_score] if bet else ['','']
                bets.append(bet)
            bets_by_date.append(bets)
            games_and_bets_by_date.append((zip(games, bets), game.scheduled_datetime.date()))
        return render(request, 'predict.html', {'games_and_bets_by_date': games_and_bets_by_date,
                                                'contest': contest,
                                                'contests': request.user.contests.all()})

    def post(self, request, contest):
        req_dict = dict(request.POST.lists())
        home_scores = req_dict['home_score']
        away_scores = req_dict['away_score']

        contest = request.user.contests.filter(name=contest)[0]
        # games = contest.tournament.games.all().order_by('scheduled_datetime')
        games = contest.tournament.games.filter(isplayoff=True).order_by('scheduled_datetime')

        for home_score, away_score, game in zip(home_scores, away_scores, games):

            if utils.is_played(game): # no update if time passed
                continue

            bet_query = request.user.bets.filter(game=game, contest=contest)
            old_bet = [bet_query[0].home_score, bet_query[0].away_score] if bet_query else ['','']
            if home_score != old_bet[0] or away_score != old_bet[1]:
                if bet_query: # update existing
                    bet_query.update(home_score=home_score)
                    bet_query.update(away_score=away_score)
                else:
                    new_bet = models.Bet(
                        user=request.user, game=game, contest=contest,
                        home_score=home_score, away_score=away_score
                    )
                    new_bet.save()
        return HttpResponseRedirect('./')


@login_required
def standing_home_view(request):
    contests = request.user.contests.all()
    return render(request, 'standing_home.html', {'contests': contests})


@login_required
def show_standing(request, contest):
    contest = request.user.contests.filter(name=contest).all()[0]
    users = contest.users.all()
    rows = []

    for user in users:
        se = utils.get_correct_predictions(user, contest, 'exact')
        sg = utils.get_correct_predictions(user, contest, 'goal-difference')
        sw = utils.get_correct_predictions(user, contest, 'winner-only')

        row = []
        row.append(user)
        row.append(se)
        row.append(sg)
        row.append(sw)
        row.append(se*3 + sg*2 + sw*1)
        rows.append(row)

    rows = sorted(rows, key=lambda x:x[4], reverse=True)
    data = {'rows': rows,
            'contest': contest.name,
            'contests': request.user.contests.all()}

    return render(request, 'standing.html', data)


@login_required
def join_contest(request):
    user = request.user
    contest_id = request.POST['contest-id']
    contest = models.Contest.objects.filter(name=contest_id)
    if not contest:
        return HttpResponseRedirect(reverse('home'))
    contest = contest[0]
    if user not in contest.users.all():
        contest.users.add(user)
    return HttpResponseRedirect(reverse('predict', kwargs={'contest': contest.name}))
