"""Tests for auth, scoring, prediction locking, access control and imports."""

from datetime import timedelta
from io import StringIO

import tablib
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main import avatars, quotes, utils
from main.models import Bet, Contest, Game, GameResource, Profile, Team, Tournament


def make_game(tournament, home, away, kickoff, isplayoff=False, score=None):
    home_score, away_score = (None, None) if score is None else score
    return Game.objects.create(
        tournament=tournament,
        home=home,
        away=away,
        scheduled_datetime=kickoff,
        isplayoff=isplayoff,
        home_score=home_score,
        away_score=away_score,
    )


class BaseData(TestCase):
    def setUp(self):
        self.past = timezone.now() - timedelta(hours=2)
        self.future = timezone.now() + timedelta(days=2)
        self.tournament = Tournament.objects.create(name="Cup")
        self.other_tournament = Tournament.objects.create(name="Other Cup")
        self.a = Team.objects.create(name="Alpha", abbreviation="ALP")
        self.b = Team.objects.create(name="Bravo", abbreviation="BRV")
        self.user = User.objects.create_user("amin", password="Predict2026!")
        self.contest = Contest.objects.create(name="Lobby", tournament=self.tournament)
        self.contest.users.add(self.user)


class AuthTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("signup"),
            {
                "first_name": "Ann",
                "last_name": "Lee",
                "username": "annlee",
                "password1": "Predict2026!",
                "password2": "Predict2026!",
            },
        )
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(User.objects.filter(username="annlee").exists())

    def test_signup_lowercases_username(self):
        self.client.post(
            reverse("signup"),
            {
                "username": "MixedCase",
                "password1": "Predict2026!",
                "password2": "Predict2026!",
            },
        )
        self.assertTrue(User.objects.filter(username="mixedcase").exists())
        self.assertFalse(User.objects.filter(username="MixedCase").exists())

    def test_signup_name_is_optional(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "noname",
                "password1": "Predict2026!",
                "password2": "Predict2026!",
            },
        )
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(User.objects.filter(username="noname").exists())

    def test_login_success_redirects_home(self):
        User.objects.create_user("bob", password="Predict2026!")
        response = self.client.post(
            reverse("login"), {"username": "bob", "password": "Predict2026!"}
        )
        self.assertRedirects(response, reverse("home"))

    def test_login_is_case_insensitive(self):
        User.objects.create_user("Carol", password="Predict2026!")
        response = self.client.post(
            reverse("login"), {"username": "carol", "password": "Predict2026!"}
        )
        self.assertRedirects(response, reverse("home"))

    def test_invalid_login_does_not_500(self):
        User.objects.create_user("dave", password="Predict2026!")
        response = self.client.post(
            reverse("login"), {"username": "dave", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 200)

    def test_empty_login_does_not_500(self):
        response = self.client.post(reverse("login"), {})
        self.assertEqual(response.status_code, 200)

    def test_invalid_login_shows_inline_form_error(self):
        User.objects.create_user("erin", password="Predict2026!")
        response = self.client.post(
            reverse("login"), {"username": "erin", "password": "nope"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form-alert")
        self.assertTrue(response.context["form"].non_field_errors())


class ScoringTests(BaseData):
    def _bet(self, game, home, away):
        return Bet.objects.create(
            user=self.user,
            game=game,
            contest=self.contest,
            home_score=home,
            away_score=away,
        )

    def test_evaluate_bet_categories(self):
        game = make_game(self.tournament, self.a, self.b, self.past, score=(2, 1))
        self.assertEqual(utils.evaluate_bet(self._bet(game, 2, 1)), "exact")
        Bet.objects.all().delete()
        self.assertEqual(utils.evaluate_bet(self._bet(game, 3, 2)), "goal-diff")
        Bet.objects.all().delete()
        self.assertEqual(utils.evaluate_bet(self._bet(game, 5, 0)), "winner")
        Bet.objects.all().delete()
        self.assertEqual(utils.evaluate_bet(self._bet(game, 0, 3)), "zilch")

    def test_bet_without_result_is_unscored(self):
        game = make_game(self.tournament, self.a, self.b, self.past, score=None)
        self.assertIsNone(utils.evaluate_bet(self._bet(game, 1, 0)))
        preds = utils.get_correct_predictions(self.user, self.contest)
        self.assertEqual(preds["groupstage"]["exact"], 0)

    def test_correct_predictions_split_group_and_playoff(self):
        group = make_game(self.tournament, self.a, self.b, self.past, score=(2, 1))
        playoff = make_game(
            self.tournament, self.b, self.a, self.past, isplayoff=True, score=(0, 0)
        )
        self._bet(group, 2, 1)  # exact
        self._bet(playoff, 1, 1)  # goal-diff (draw)
        preds = utils.get_correct_predictions(self.user, self.contest)
        self.assertEqual(preds["groupstage"]["exact"], 1)
        self.assertEqual(preds["playoffs"]["goal-diff"], 1)


class GameStateTests(BaseData):
    def test_is_locked_and_has_result(self):
        upcoming = make_game(self.tournament, self.a, self.b, self.future)
        started = make_game(self.tournament, self.b, self.a, self.past, score=(1, 0))
        self.assertFalse(upcoming.is_locked)
        self.assertFalse(upcoming.has_result)
        self.assertTrue(started.is_locked)
        self.assertTrue(started.has_result)


class PredictViewTests(BaseData):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        self.upcoming = make_game(self.tournament, self.a, self.b, self.future)
        self.locked = make_game(self.tournament, self.b, self.a, self.past)

    def test_member_can_open_predict(self):
        response = self.client.get(reverse("predict", args=[self.contest.name]))
        self.assertEqual(response.status_code, 200)

    def test_non_member_gets_404(self):
        Contest.objects.create(name="Secret", tournament=self.tournament)
        response = self.client.get(reverse("predict", args=["Secret"]))
        self.assertEqual(response.status_code, 404)

    def test_post_saves_prediction_for_upcoming_game(self):
        self.client.post(
            reverse("predict", args=[self.contest.name]),
            {f"home_{self.upcoming.id}": "3", f"away_{self.upcoming.id}": "1"},
        )
        bet = Bet.objects.get(user=self.user, game=self.upcoming)
        self.assertEqual((bet.home_score, bet.away_score), (3, 1))

    def test_post_ignores_locked_game(self):
        self.client.post(
            reverse("predict", args=[self.contest.name]),
            {f"home_{self.locked.id}": "2", f"away_{self.locked.id}": "2"},
        )
        self.assertFalse(Bet.objects.filter(game=self.locked).exists())

    def test_post_ignores_partial_row(self):
        self.client.post(
            reverse("predict", args=[self.contest.name]),
            {f"home_{self.upcoming.id}": "2", f"away_{self.upcoming.id}": ""},
        )
        self.assertFalse(Bet.objects.filter(game=self.upcoming).exists())

    def test_post_deletes_cleared_prediction(self):
        Bet.objects.create(
            user=self.user,
            game=self.upcoming,
            contest=self.contest,
            home_score=2,
            away_score=2,
        )
        self.client.post(
            reverse("predict", args=[self.contest.name]),
            {f"home_{self.upcoming.id}": "", f"away_{self.upcoming.id}": ""},
        )
        self.assertFalse(Bet.objects.filter(game=self.upcoming).exists())


class StandingTests(BaseData):
    def test_non_member_gets_404(self):
        self.client.force_login(self.user)
        Contest.objects.create(name="Secret", tournament=self.tournament)
        response = self.client.get(reverse("standing", args=["Secret"]))
        self.assertEqual(response.status_code, 404)

    def test_ranking_orders_by_points(self):
        leader = User.objects.create_user("leader", password="Predict2026!")
        self.contest.users.add(leader)
        game = make_game(self.tournament, self.a, self.b, self.past, score=(2, 1))
        Bet.objects.create(
            user=leader, game=game, contest=self.contest, home_score=2, away_score=1
        )  # exact -> 3 pts
        Bet.objects.create(
            user=self.user, game=game, contest=self.contest, home_score=5, away_score=0
        )  # winner -> 1 pt
        self.client.force_login(self.user)
        response = self.client.get(reverse("standing", args=[self.contest.name]))
        rows = response.context["rows"]
        self.assertEqual(rows[0]["user"], leader)
        self.assertEqual(rows[0]["rank"], 1)
        self.assertGreater(rows[0]["points"], rows[1]["points"])


class ShowBetsTests(BaseData):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_hidden_before_kickoff(self):
        game = make_game(self.tournament, self.a, self.b, self.future)
        response = self.client.get(
            reverse(
                "show_bets", kwargs={"contest_name": self.contest.name, "game_id": game.id}
            )
        )
        self.assertTemplateUsed(response, "bets_hidden.html")

    def test_visible_after_kickoff(self):
        game = make_game(self.tournament, self.a, self.b, self.past, score=(1, 0))
        response = self.client.get(
            reverse(
                "show_bets", kwargs={"contest_name": self.contest.name, "game_id": game.id}
            )
        )
        self.assertTemplateUsed(response, "bets.html")

    def test_game_from_other_tournament_404(self):
        stray = make_game(self.other_tournament, self.a, self.b, self.past, score=(1, 0))
        response = self.client.get(
            reverse(
                "show_bets", kwargs={"contest_name": self.contest.name, "game_id": stray.id}
            )
        )
        self.assertEqual(response.status_code, 404)


class ContestManagementTests(BaseData):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_create_contest(self):
        response = self.client.post(
            reverse("create_contest"),
            {"tournament": self.tournament.id, "contest-id": "My League"},
        )
        contest = Contest.objects.get(name="My_League")
        self.assertIn(self.user, contest.users.all())
        self.assertRedirects(response, reverse("predict", args=["My_League"]))

    def test_create_duplicate_contest_blocked(self):
        self.client.post(
            reverse("create_contest"),
            {"tournament": self.tournament.id, "contest-id": "Lobby"},
        )
        self.assertEqual(Contest.objects.filter(name="Lobby").count(), 1)

    def test_join_contest(self):
        other = User.objects.create_user("zoe", password="Predict2026!")
        self.client.force_login(other)
        self.client.post(reverse("join_contest"), {"contest-id": "Lobby"})
        self.assertIn(other, self.contest.users.all())

    def test_join_missing_contest(self):
        response = self.client.post(reverse("join_contest"), {"contest-id": "Nope"})
        self.assertRedirects(response, reverse("home"))


class ImportTests(BaseData):
    def _dataset(self, kickoff="2030-06-01 18:00:00"):
        data = tablib.Dataset(
            headers=[
                "tournament",
                "home_team_abbreviation",
                "away_team_abbreviation",
                "home_score",
                "away_score",
                "scheduled_datetime",
                "isplayoff",
            ]
        )
        data.append(["Cup", "ALP", "BRV", "", "", kickoff, "False"])
        return data

    def test_import_is_idempotent(self):
        GameResource().import_data(self._dataset(), dry_run=False, raise_errors=True)
        result = GameResource().import_data(
            self._dataset(), dry_run=False, raise_errors=True
        )
        self.assertEqual(Game.objects.filter(tournament=self.tournament).count(), 1)
        self.assertEqual(result.totals.get("skip", 0), 1)


class SaveBetTests(BaseData):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        self.upcoming = make_game(self.tournament, self.a, self.b, self.future)
        self.locked = make_game(self.tournament, self.b, self.a, self.past)

    def _url(self, game):
        return reverse("save_bet", args=[self.contest.name, game.id])

    def test_autosave_persists_bet(self):
        response = self.client.post(
            self._url(self.upcoming), {"home_score": "2", "away_score": "0"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        bet = Bet.objects.get(user=self.user, game=self.upcoming)
        self.assertEqual((bet.home_score, bet.away_score), (2, 0))

    def test_autosave_updates_existing(self):
        self.client.post(self._url(self.upcoming), {"home_score": "1", "away_score": "1"})
        self.client.post(self._url(self.upcoming), {"home_score": "3", "away_score": "2"})
        self.assertEqual(Bet.objects.filter(game=self.upcoming).count(), 1)
        bet = Bet.objects.get(game=self.upcoming)
        self.assertEqual((bet.home_score, bet.away_score), (3, 2))

    def test_autosave_rejected_for_locked_game(self):
        response = self.client.post(
            self._url(self.locked), {"home_score": "1", "away_score": "0"}
        )
        self.assertEqual(response.status_code, 409)
        self.assertFalse(Bet.objects.filter(game=self.locked).exists())

    def test_autosave_rejects_partial(self):
        response = self.client.post(
            self._url(self.upcoming), {"home_score": "1", "away_score": ""}
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Bet.objects.filter(game=self.upcoming).exists())

    def test_autosave_deletes_when_both_cleared(self):
        Bet.objects.create(
            user=self.user,
            game=self.upcoming,
            contest=self.contest,
            home_score=1,
            away_score=1,
        )
        response = self.client.post(
            self._url(self.upcoming), {"home_score": "", "away_score": ""}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("deleted"))
        self.assertFalse(Bet.objects.filter(game=self.upcoming).exists())

    def test_autosave_non_member_404(self):
        other = User.objects.create_user("intruder", password="Predict2026!")
        self.client.force_login(other)
        response = self.client.post(
            self._url(self.upcoming), {"home_score": "1", "away_score": "0"}
        )
        self.assertEqual(response.status_code, 404)


class ForcePasswordChangeTests(BaseData):
    def setUp(self):
        super().setUp()
        self.user.profile.must_change_password = True
        self.user.profile.save()
        self.client.force_login(self.user)

    def _flag(self):
        return Profile.objects.get(user=self.user).must_change_password

    def test_flagged_user_is_redirected(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, reverse("force_password_change"))

    def test_change_page_is_reachable_while_flagged(self):
        response = self.client.get(reverse("force_password_change"))
        self.assertEqual(response.status_code, 200)

    def test_any_password_is_accepted_and_clears_flag(self):
        response = self.client.post(
            reverse("force_password_change"),
            {"new_password1": "abc", "new_password2": "abc"},  # deliberately weak
        )
        self.assertRedirects(response, reverse("home"))
        self.assertFalse(self._flag())
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("abc"))
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    def test_mismatch_keeps_flag(self):
        response = self.client.post(
            reverse("force_password_change"),
            {"new_password1": "abc", "new_password2": "xyz"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._flag())

    def test_unflagged_user_is_not_redirected(self):
        self.user.profile.must_change_password = False
        self.user.profile.save()
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)


class CreateUsersCommandTests(TestCase):
    def test_creates_flagged_users_with_usable_password(self):
        call_command("create_users", "newpal", stdout=StringIO())
        user = User.objects.get(username="newpal")
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.profile.must_change_password)

    def test_usernames_are_lowercased(self):
        call_command("create_users", "MixedPal", stdout=StringIO())
        self.assertTrue(User.objects.filter(username="mixedpal").exists())

    def test_adds_users_to_contest(self):
        tournament = Tournament.objects.create(name="T")
        contest = Contest.objects.create(name="League", tournament=tournament)
        call_command("create_users", "pal2", "--contest", "League", stdout=StringIO())
        self.assertTrue(contest.users.filter(username="pal2").exists())


class TimezoneDisplayTests(BaseData):
    def test_round_date_uses_display_timezone(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo

        # 02:00 UTC on Jun 28 is the evening of Jun 27 in US Eastern (the default
        # DISPLAY_TIME_ZONE), so the match must group under Jun 27, not Jun 28.
        kickoff = datetime(2026, 6, 28, 2, 0, tzinfo=ZoneInfo("UTC"))
        make_game(self.tournament, self.a, self.b, kickoff)
        self.client.force_login(self.user)
        response = self.client.get(reverse("predict", args=[self.contest.name]))
        dates = [r["date"].isoformat() for r in response.context["rounds"]]
        self.assertIn("2026-06-27", dates)
        self.assertNotIn("2026-06-28", dates)


class SyncResultsGateTests(BaseData):
    def test_skips_when_no_match_is_due(self):
        make_game(self.tournament, self.a, self.b, self.future)  # not kicked off yet
        out = StringIO()
        call_command("sync_results", "--tournament", "Cup", stdout=out)
        self.assertIn("No matches due yet", out.getvalue())
        self.assertFalse(Game.objects.filter(home_score__isnull=False).exists())


class ProfileTests(BaseData):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_profile_page_loads(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)

    def test_save_profile_updates_name_and_avatar(self):
        self.client.post(
            reverse("profile"),
            {
                "save_profile": "1",
                "first_name": "Amin",
                "last_name": "Sadeghi",
                "avatar": "moon",
            },
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Amin")
        self.assertEqual(self.user.last_name, "Sadeghi")
        self.assertEqual(self.user.profile.avatar, "moon")

    def test_save_profile_rejects_unknown_avatar(self):
        self.client.post(
            reverse("profile"),
            {"save_profile": "1", "first_name": "X", "avatar": "not-an-avatar"},
        )
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.first_name, "X")

    def test_change_password_from_profile(self):
        self.client.post(
            reverse("profile"),
            {"save_password": "1", "new_password1": "newpass", "new_password2": "newpass"},
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass"))


class AvatarTests(BaseData):
    def test_new_profile_gets_a_valid_random_avatar(self):
        user = User.objects.create_user("freshpal", password="Predict2026!")
        self.assertIn(user.profile.avatar, avatars.KEYS)

    def test_avatar_data_has_icon_and_colours(self):
        data = avatars.get("moon")
        self.assertIn("icon", data)
        self.assertIn("c1", data)

    def test_unknown_avatar_key_falls_back(self):
        self.assertEqual(avatars.get("bogus"), avatars.AVATARS[avatars.DEFAULT])


class FlagTests(TestCase):
    def test_known_abbreviation_maps_to_code(self):
        team = Team.objects.create(name="Brazil", abbreviation="BRA")
        self.assertEqual(team.flag, "br")

    def test_home_nation_uses_subdivision_code(self):
        team = Team.objects.create(name="England", abbreviation="ENG")
        self.assertEqual(team.flag, "gb-eng")

    def test_unknown_abbreviation_has_no_flag(self):
        team = Team.objects.create(name="Placeholder", abbreviation="W1")
        self.assertIsNone(team.flag)


class QuoteTests(BaseData):
    def test_random_quote_has_text_and_author(self):
        q = quotes.random()
        self.assertIn("text", q)
        self.assertIn("author", q)

    def test_quote_is_in_page_context(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("home"))
        self.assertIn("quote", response.context)


class GreetingTests(BaseData):
    def test_greeting_uses_first_name(self):
        self.user.first_name = "Ahmad"
        self.user.save(update_fields=["first_name"])
        self.client.force_login(self.user)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Ahmad")

    def test_greeting_falls_back_to_username(self):
        nameless = User.objects.create_user("solonick", password="Predict2026!")
        self.client.force_login(nameless)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "solonick")
