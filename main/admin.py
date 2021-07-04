import inspect

from django.contrib import admin

from .models import Bet, Contest, Game, Profile, Team, Tournament

admin.site.register(Profile)
admin.site.register(Tournament)
admin.site.register(Contest)
admin.site.register(Team)
admin.site.register(Bet)
admin.site.register(Game)
