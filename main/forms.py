from django import forms
from .models import Bet
from django.contrib.admin import widgets

class LoginForm(forms.Form):
    username = forms.CharField(label='Username', max_length=64)
    password = forms.CharField(label='Password', widget=forms.PasswordInput())
