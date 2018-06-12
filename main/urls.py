from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^home/$', views.home_view, name='home'),
    url(r'^accounts/login/$', views.LoginView.as_view(), name='login'),
    url(r'^accounts/logout/$', views.logout_view, name='logout'),
    url(r'^accounts/signup/$', views.SignupView.as_view(), name='signup'),
    url(r'^place_bet/$', views.place_bet, name='place_bet'),
    url(r'^standing/$', views.show_standing, name='standing'),
    url(r'^bets/$', views.show_bets, name='bets'),
	url(r'^contests/(?P<contest>\w{0,50})/predict/$',
		views.PredictView.as_view(), name='predict')
]
