from django.utils import timezone


class AdminTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin"):
            timezone.activate("America/New_York")  # Or your preferred timezone
        else:
            timezone.deactivate()  # Revert to the default settings.TIME_ZONE
        response = self.get_response(request)
        return response
