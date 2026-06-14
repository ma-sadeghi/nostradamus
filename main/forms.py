from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from . import avatars


class LoginForm(forms.Form):
    username = forms.CharField(label="username", max_length=20)
    password = forms.CharField(label="password", widget=forms.PasswordInput())


class SimplePasswordForm(forms.Form):
    """Set a new password with no strength rules — anything non-empty goes."""

    new_password1 = forms.CharField(label="New password", widget=forms.PasswordInput())
    new_password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput())

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")
        if p1 and p2 and p1 != p2:
            self.add_error("new_password2", "The two passwords don't match.")
        return cleaned


class ProfileForm(forms.Form):
    """Edit display name and chosen avatar."""

    first_name = forms.CharField(max_length=20, required=False)
    last_name = forms.CharField(max_length=20, required=False)
    avatar = forms.ChoiceField(choices=[(key, key) for key in avatars.KEYS])


class SignupForm(UserCreationForm):
    first_name = forms.CharField(label="first_name", max_length=20, required=False)
    last_name = forms.CharField(label="last_name", max_length=20, required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "password1", "password2")

    def clean_username(self):
        # Usernames are stored lowercase so they're canonical (login is already
        # case-insensitive). Avoids near-duplicate accounts differing only by case.
        return self.cleaned_data["username"].strip().lower()


# LABEL IS IRRELEVANT, VAR NAME MUST MATCH NAME TAG OF HTML
