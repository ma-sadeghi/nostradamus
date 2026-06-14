"""Admin registrations, including CSV import/export for games."""

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Bet, Contest, Game, GameResource, Profile, Team, Tournament


@admin.register(Game)
class GameAdmin(ImportExportModelAdmin):
    resource_class = GameResource
    list_display = (
        "tournament",
        "home",
        "away",
        "home_score",
        "away_score",
        "scheduled_datetime",
        "isplayoff",
    )
    list_filter = ("tournament", "isplayoff")
    search_fields = (
        "home__name",
        "away__name",
        "home__abbreviation",
        "away__abbreviation",
    )
    date_hierarchy = "scheduled_datetime"
    autocomplete_fields = ("tournament", "home", "away")


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "abbreviation")
    search_fields = ("name", "abbreviation")


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ("name", "tournament")
    list_filter = ("tournament",)
    search_fields = ("name",)
    filter_horizontal = ("users",)


@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ("user", "contest", "game", "home_score", "away_score")
    list_filter = ("contest",)
    search_fields = ("user__username",)


admin.site.register(Profile)
