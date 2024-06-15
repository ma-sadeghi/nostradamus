from django.contrib.auth.decorators import login_required
from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.index, name="index"),
    re_path(r"^standing/$", views.standing_home_view, name="standing_home"),
    re_path(r"^home/$", views.home_view, name="home"),
    re_path(r"^accounts/login/$", views.LoginView.as_view(), name="login"),
    re_path(r"^accounts/logout/$", views.logout_view, name="logout"),
    re_path(r"^accounts/signup/$", views.SignupView.as_view(), name="signup"),
    re_path(
        r"^contests/(?P<contest>\w{0,50})/standing/$",
        views.show_standing,
        name="standing",
    ),
    re_path(
        r"^contests/(?P<contest>\w{0,50})/predict/$",
        login_required(views.PredictView.as_view()),
        name="predict",
    ),
    re_path(
        r"^contests/(?P<contest_name>\w{0,50})/bets/game/(?P<game_id>\w{0,50})",
        login_required(views.show_bets),
        name="show_bets",
    ),
    re_path(r"^contests/join/$", views.join_contest, name="join_contest"),
]
