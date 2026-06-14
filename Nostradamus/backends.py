"""Authentication backend that matches usernames case-insensitively."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class CaseInsensitiveModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None or password is None:
            return None
        try:
            user = UserModel.objects.get(username__iexact=username)
        except UserModel.DoesNotExist:
            # Run the hasher once anyway to reduce timing differences.
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            user = (
                UserModel.objects.filter(username__iexact=username).order_by("id").first()
            )
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
