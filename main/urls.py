from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
	url(r'^standing/$', views.standing_home_view, name='standing_home'),    
    url(r'^home/$', views.home_view, name='home'),
    url(r'^accounts/login/$', views.LoginView.as_view(), name='login'),
    url(r'^accounts/logout/$', views.logout_view, name='logout'),
    url(r'^accounts/signup/$', views.SignupView.as_view(), name='signup'),
	url(r'^contests/(?P<contest>\w{0,50})/standing/$', views.show_standing,
		name='standing'),
	url(r'^contests/(?P<contest>\w{0,50})/predict/$',
		login_required(views.PredictView.as_view()), name='predict'),
	url(r'^contests/join/$', views.join_contest, name='join_contest')
]
