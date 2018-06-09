from django.contrib import admin
import inspect
from .models import Profile, Tournament, Contest, Team, Bet, Game

admin.site.register(Profile)
admin.site.register(Tournament)
admin.site.register(Contest)
admin.site.register(Team)
admin.site.register(Bet)
admin.site.register(Game)