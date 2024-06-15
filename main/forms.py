from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class LoginForm(forms.Form):
    username = forms.CharField(label="username", max_length=20)
    password = forms.CharField(label="password", widget=forms.PasswordInput())


class SignupForm(UserCreationForm):
    first_name = forms.CharField(label="first_name", max_length=20)
    last_name = forms.CharField(label="last_name", max_length=20)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "password1", "password2")


# LABEL IS IRRELEVANT, VAR NAME MUST MATCH NAME TAG OF HTML
