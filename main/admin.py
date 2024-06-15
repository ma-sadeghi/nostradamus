from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Bet, Contest, Game, GameResource, Profile, Team, Tournament


class GameAdmin(ImportExportModelAdmin):
    resource_class = GameResource
    # Optional: Specify list_display to improve the admin interface usability
    list_display = (
        "tournament",
        "home",
        "away",
        "home_score",
        "away_score",
        "scheduled_datetime",
        "isplayoff",
    )


admin.site.register(Profile)
admin.site.register(Tournament)
admin.site.register(Contest)
admin.site.register(Team)
admin.site.register(Bet)
admin.site.register(Game, GameAdmin)
