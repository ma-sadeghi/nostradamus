from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='home'),
    url(r'^login/$', views.login_view, name='login'),
    url(r'^logout/$', views.logout_view, name='logout'),
    url(r'^place_bet/$', views.place_bet, name='place_bet'),
    url(r'^standing/$', views.show_standing, name='standing'),
    url(r'^bets/$', views.show_bets, name='bets'),
]
