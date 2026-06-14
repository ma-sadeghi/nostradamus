"""Custom middleware: per-request timezone and forced password changes."""

from zoneinfo import ZoneInfo

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone


class TimezoneMiddleware:
    """Activate the admin's timezone under /admin, else the viewer's own.

    The viewer's timezone is read from a `tz` cookie set client-side; when it's
    missing or invalid we fall back to settings.DISPLAY_TIME_ZONE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin"):
            timezone.activate(ZoneInfo("America/New_York"))
        else:
            timezone.activate(self._viewer_tz(request))
        try:
            return self.get_response(request)
        finally:
            timezone.deactivate()

    @staticmethod
    def _viewer_tz(request):
        name = request.COOKIES.get("tz") or settings.DISPLAY_TIME_ZONE
        try:
            return ZoneInfo(name)
        except Exception:
            return ZoneInfo(settings.DISPLAY_TIME_ZONE)


class ForcePasswordChangeMiddleware:
    """Redirect users handed a temporary password to the change-password page."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            user is not None
            and user.is_authenticated
            and not request.path.startswith("/admin")
        ):
            allowed = {reverse("force_password_change"), reverse("logout")}
            profile = getattr(user, "profile", None)
            if (
                request.path not in allowed
                and profile is not None
                and profile.must_change_password
            ):
                return redirect("force_password_change")
        return self.get_response(request)
