"""WSGI entry point exposing the ``application`` callable for the project.

Static files are served by WhiteNoise via middleware (see settings.MIDDLEWARE).
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Nostradamus.settings")

application = get_wsgi_application()
