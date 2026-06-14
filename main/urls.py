"""URL routes for the main app: auth, predictions, standings and contests."""

from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("home/", views.home_view, name="home"),
    path("standing/", views.standing_home_view, name="standing_home"),
    path("accounts/login/", views.LoginView.as_view(), name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("accounts/signup/", views.SignupView.as_view(), name="signup"),
    path(
        "accounts/password/change/",
        views.force_password_change,
        name="force_password_change",
    ),
    path("contests/join/", views.join_contest, name="join_contest"),
    path("contests/create/", views.create_contest, name="create_contest"),
    path("contests/<str:contest>/standing/", views.show_standing, name="standing"),
    path(
        "contests/<str:contest>/predict/",
        login_required(views.PredictView.as_view()),
        name="predict",
    ),
    path(
        "contests/<str:contest>/predict/save/<int:game_id>/",
        views.save_bet,
        name="save_bet",
    ),
    path(
        "contests/<str:contest_name>/bets/game/<int:game_id>/",
        views.show_bets,
        name="show_bets",
    ),
]
