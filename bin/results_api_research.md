# World Cup 2026 Results API — Research

Goal: periodically fetch **final scores** for FIFA World Cup 2026 matches and fill
`Game.home_score` / `Game.away_score` in our Django app (~15 users). Schedule is
already loaded; we match a returned match to one of our `Game` rows by
**teams + kickoff date** and read the final score.

Our data model (`main/models.py`):
- `Team.name` (full English, e.g. "United States", "South Korea", "Bosnia & Herz.")
  and `Team.abbreviation` (3-letter FIFA code: USA, KOR, BIH, NED, POR, SUI, ...).
- `Game.home` / `Game.away` (FK to Team), `Game.home_score` / `Game.away_score`
  (nullable; null = not played), `Game.scheduled_datetime`.

All findings below were verified against official docs and, where possible, by
hitting the live endpoints (June 2026).

---

## Recommendation

**Primary: TheSportsDB** (free key, league id `4429`, `eventsseason.php?id=4429&s=2026`).
**Fallback: football-data.org** (free registered key, competition code `WC`,
`/v4/competitions/WC/matches`).

Why TheSportsDB first: it is the only option where I **confirmed live, on the free
tier, that WC 2026 fixtures + scores are actually returned**, with team names that
already match our DB and a real-time-enough `strStatus` (`FT`, `2H`, `NS`). No
signup needed for a working prototype (test key `123`); a $9/mo Patreon key is
optional for stability. football-data.org also includes WC free and maps cleaner
(it exposes a `tla` 3-letter code matching our abbreviations), but its free tier is
documented as **data-delayed** and it 403s without a registered key.

**Single most important caveat:** On **football-data.org**, the World Cup *is*
included on the free tier, BUT free-tier data is **delayed** (their own docs/3rd-party
analysis say it is unsuitable for live scores). For *final* scores polled every
15–30 min this is acceptable, just not instant. On **TheSportsDB**, the free
**v1** `eventsseason.php` endpoint returned current WC2026 results live in my test
(including an in-play `2H` match), but TheSportsDB officially markets "2-min
Livescores" as a paid v2 feature — so treat free-tier freshness as "good enough for
final scores, not guaranteed real-time," and the free test key `123` is shared/rate-limited
and could change.

---

## Comparison table

| API | WC2026 on FREE? | Auth | Free rate limit | WC list endpoint | Team identity | Map to our DB | Key gotcha |
|---|---|---|---|---|---|---|---|
| **TheSportsDB** | **Yes — verified live** (key `123`, league `4429`, season `2026`) | `X-API-KEY` header (v2); key in URL path (v1) | 30 req/min (free) | `v1/json/123/eventsseason.php?id=4429&s=2026` | Full names (no FIFA tricode in event) | By name + small alias table | Free key `123` is shared/can change; live scores officially a paid feature; names differ slightly ("Bosnia-Herzegovina", "Curaçao", "USA") |
| **football-data.org** | **Yes — free incl. WC** (docs verified; 403 without registered key) | `X-Auth-Token` header | 10 req/min (registered free) | `/v4/competitions/WC/matches` | `homeTeam.tla` 3-letter code + `.name` | By `tla` ≈ our abbreviation (cleanest) | Free tier data is **delayed**; not for live |
| **API-FOOTBALL** (api-sports.io) | Yes, all comps incl. WC (league id `1`, season `2026`) | `x-apisports-key` header (or RapidAPI) | **100 req/day** (free) | `/fixtures?league=1&season=2026` | `teams.home.name` + `teams.home.id` (no tricode in fixtures) | By name or numeric id | 100/day is tight for match-day polling; no credit card needed |
| **SportMonks** | **No** — free = Danish Superliga + Scottish Premiership only | Bearer token | (n/a for WC) | n/a on free | id/name | n/a | WC needs **Advanced €69/mo** (or €55/mo annual) |
| openfootball/worldcup.json | Yes (static JSON, no key) | none | n/a (GitHub raw) | repo JSON files | names/codes | by name | **Not a results feed** — schedule/historical only, not auto-updated final scores |
| ESPN hidden endpoints | Likely yes, free | none (undocumented) | unknown | `site.api.espn.com/.../soccer/fifa.world/scoreboard` | names + abbreviations | by name/abbr | **Unofficial/undocumented**, no ToS/SLA, sunset risk |

---

## Per-API detail

### 1. TheSportsDB — PRIMARY  ✅ verified live

- **WC2026 free coverage:** Confirmed by live call. Free key `123`, FIFA World Cup
  league id `4429`, season `2026`:
  `https://www.thesportsdb.com/api/v1/json/123/eventsseason.php?id=4429&s=2026`
  returned real fixtures incl. `Mexico vs South Africa` at `2026-06-11T19:00:00`,
  score `2-0`, `strStatus: "FT"`. Statuses seen across the set: `FT` (finished),
  `2H` (in-play 2nd half), `NS` (not started).
- **Auth / signup:** v1 free key is `123`, embedded in the URL path — no signup to
  prototype. v2 uses an `X-API-KEY` header. A dedicated production key + v2 (2-min
  livescores, higher limits) is the **$9/mo Patreon** supporter tier.
- **Rate limit (free):** 30 req/min (429 if exceeded). Our 15–30 min poll is trivially
  within this.
- **Endpoints (v1):**
  - All season events/results: `eventsseason.php?id=4429&s=2026`
  - Past/finished only: `eventspastleague.php?id=4429`
  - Next/upcoming: `eventsnextleague.php?id=4429`
- **Response shape (real fields from live call):**
  `idEvent`, `strHomeTeam`, `strAwayTeam`, `idHomeTeam`, `idAwayTeam`,
  `intHomeScore`, `intAwayScore`, `strStatus`, `dateEvent` (`2026-06-11`),
  `strTime`, `strTimestamp` (`2026-06-11T19:00:00`, appears to be match-local/venue
  time — verify against our stored UTC-ish datetimes), `intRound`, `strVenue`.
- **Detect finished:** `strStatus == "FT"`. Final score in `intHomeScore` /
  `intAwayScore` (strings — cast to int).
- **Team identity / mapping:** Full English names, **no FIFA tricode** in the event
  object. Names mostly match our DB but a few differ — needs a small alias map:
  - `"Bosnia-Herzegovina"` → our `"Bosnia & Herz."` / BIH
  - `"Curaçao"` → our `"Curacao"` / CUW
  - `"USA"` → our `"United States"` / USA
  - `"Ivory Coast"` matches; `"South Korea"`, `"South Africa"`, `"Czech Republic"`
    match exactly.
  Build a `{thesportsdb_name: abbreviation}` dict once (≈48 teams) and map to our
  Team via abbreviation — robust and explicit.
- **Gotchas:** Free key `123` is shared and rate-limited globally; for a real
  deployment, the $9/mo key is worth it. Live scores are officially a paid v2
  feature, though v1 season results updated fine in testing. Confirm `strTimestamp`
  timezone before date-matching.

### 2. football-data.org — FALLBACK  ✅ verified from docs

- **WC2026 free coverage:** World Cup is one of the 12 free-tier competitions
  (code `WC`, numeric id `2000`). Confirmed in coverage + lookup-table docs. Note:
  the API **403s without a registered key** even for the competitions list
  (verified live: `{"errorCode":403,"message":"...restricted..."}`), so you must
  register a free key.
- **Auth / signup:** Header `X-Auth-Token: <key>`. Free key by **email signup only**
  (no credit card).
- **Rate limit (free):** Registered free = **10 req/min**. (Unauthenticated = 100
  req/24h, restricted endpoints.) 10/min easily covers our polling.
- **Endpoint:** `GET https://api.football-data.org/v4/competitions/WC/matches`
  Optional filters: `?status=FINISHED`, `?dateFrom=YYYY-MM-DD&dateTo=YYYY-MM-DD`,
  `?stage=`, `?matchday=`.
- **Response shape:** match object has `id`, `utcDate` (ISO 8601 UTC, e.g.
  `2026-06-11T19:00:00Z`), `status`, `homeTeam.{id,name,tla}`,
  `awayTeam.{id,name,tla}`, `score.fullTime.{home,away}` (ints or null),
  also `score.halfTime`, `score.winner`.
- **Detect finished:** `status == "FINISHED"`. Status enum:
  `SCHEDULED, TIMED, IN_PLAY, PAUSED, FINISHED, SUSPENDED, POSTPONED, CANCELLED, AWARDED`.
  Final score in `score.fullTime.home` / `score.fullTime.away`.
- **Team identity / mapping:** Exposes `tla` (3-letter abbreviation) per team — this
  is the **cleanest mapping** to our `Team.abbreviation`, *if* their `tla` values use
  FIFA codes. football-data's `tla` is their own code and may not be exactly FIFA
  (e.g. clubs use `BMG`, `BET`); for national teams verify against our codes and fall
  back to `.name` matching where they differ. Worth a one-time spot check once the
  bracket is real.
- **Gotchas:** Free-tier data is **delayed** (documented; not for live scores) — fine
  for final-score backfill polled every 15–30 min, not for live. Aggressive caching
  recommended (we already store in DB, so good). No credit card. Well-documented,
  stable, low sunset risk.

### 3. API-FOOTBALL (api-sports.io / RapidAPI)

- **WC2026 free coverage:** All competitions/endpoints are available on free; World
  Cup is `league=1`, `season=2026`. The constraint is **volume, not coverage**.
- **Auth / signup:** Direct: header `x-apisports-key`. Via RapidAPI: RapidAPI headers.
  Free dashboard signup, **no credit card**.
- **Rate limit (free):** **100 requests/day** (resets 00:00 UTC). This is the problem:
  on a heavy match day with 6+ simultaneous matches and 15-min polling over ~12h,
  you can blow 100/day. Workable only if you poll sparsely (e.g. once after each
  match window) and request all WC fixtures per call.
- **Endpoint:** `GET https://v3.football.api-sports.io/fixtures?league=1&season=2026`
  (one call returns all WC fixtures; also `&date=YYYY-MM-DD` or `&id=` for one).
- **Response shape:** `response[].fixture.{id,date,timestamp,status.{long,short,elapsed}}`,
  `response[].teams.home.{id,name,logo}`, `...away...`,
  `response[].goals.{home,away}`, `response[].score.fulltime.{home,away}`.
  `date` is ISO 8601; timezone configurable via `&timezone=`.
- **Detect finished:** `fixture.status.short == "FT"` (also AET/PEN for extra
  time/penalties). Final score in `goals.home`/`goals.away` (or `score.fulltime`).
- **Team identity / mapping:** `teams.home.name` + persistent numeric `teams.home.id`.
  **No FIFA tricode in the fixtures payload** — map by name or by storing the numeric
  team ids once.
- **Gotchas:** 100/day cap is the deciding negative for match-day polling. Otherwise
  excellent, well-documented data. Docs site blocks scripted fetches (403 to
  WebFetch) but works in a browser / with a key.

### 4. SportMonks — not free for WC

- **WC2026 free coverage:** **No.** The forever-free plan covers only **Danish
  Superliga + Scottish Premiership**. World Cup requires the **Advanced** plan at
  **€69/mo (€55/mo billed annually)**; All-In is €129/mo. Generic paid ladder is
  €29 (5 leagues) / €99 (30) / €249 (120). Not worth it for a 15-user hobby app.
- Auth = Bearer token; well-documented; just not economical here.

### 5. Other options considered

- **openfootball/worldcup.json** (GitHub, public domain, no key): great for the
  *schedule* and historical data, but it is **community-maintained static JSON**, not
  an auto-updating live results feed. Not suitable for "fetch final scores during the
  tournament."
- **ESPN hidden endpoints**
  (`site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard`): free, rich,
  includes status + scores + team abbreviations, but **undocumented/unofficial** — no
  ToS, no SLA, can change or be blocked without notice. Acceptable as a last-resort
  fallback, not a primary.
- **Sportradar / LiveScore**: enterprise, paid, sales-gated trials — overkill.

---

## Integration sketch (recommended: TheSportsDB primary)

A periodic Django management command (cron/systemd-timer, every 15–30 min on match
days):

1. **Fetch** all WC2026 events:
   `GET https://www.thesportsdb.com/api/v1/json/<KEY>/eventsseason.php?id=4429&s=2026`
   (`KEY` from env `THESPORTSDB_API_KEY`, default `123` for prototype).
2. **For each event** where `strStatus == "FT"` (finished):
   - Map `strHomeTeam` / `strAwayTeam` → our `Team` via a name→abbreviation alias
     dict (handles "Bosnia-Herzegovina", "Curaçao", "USA", etc.), then
     `Team.objects.get(abbreviation=...)`.
   - Parse `strTimestamp` → date; **find our `Game`** by
     `Game.objects.get(home=h, away=a, scheduled_datetime__date=<date>)`
     (team pair + kickoff date; date is enough since the same pair won't repeat on a
     day — matches our `import_id_fields` natural key minus exact time).
   - If found and `game.home_score is None`: set
     `home_score = int(intHomeScore)`, `away_score = int(intAwayScore)`, `save()`.
     (Idempotent — skip games that already have a result.)
3. **Log** unmatched events so we catch any name/date drift early.

football-data.org fallback is the same shape: call `/v4/competitions/WC/matches?status=FINISHED`
with header `X-Auth-Token`, match by `homeTeam.tla`/`awayTeam.tla` → our
`abbreviation` and `utcDate` date, read `score.fullTime.home`/`.away`, and only fill
where `status == "FINISHED"`.

**What you (Amin) must do:**
- Optionally create a free TheSportsDB account / $9 Patreon key for a stable
  production key; set env `THESPORTSDB_API_KEY` (prototype works with `123`).
- For the fallback, register a free key at football-data.org (email only) and set
  `FOOTBALLDATA_API_TOKEN`.
- One-time: verify team-name aliases and the `strTimestamp` timezone against our
  stored `scheduled_datetime` once the real bracket is loaded (our current
  `worldcup2026.csv` is a placeholder bracket, so re-check codes/names then).

---

## Caveats / honesty

- TheSportsDB free **live-score** freshness is officially a paid v2 feature; the v1
  season-results endpoint updated correctly in my test (it showed a `2H` in-play
  match), but I cannot guarantee free-tier latency during the real tournament.
- football-data.org free tier is **documented as delayed** — fine for final scores,
  not live.
- API-FOOTBALL free = **100 req/day**; coverage is fine, volume is the limiter.
- The team identifiers/dates above were checked against TheSportsDB's current 2026
  data and our placeholder CSV; football-data.org `tla` codes for national teams were
  not individually verified against every FIFA code — do a one-time spot check.
- I could not load API-FOOTBALL's docs/pricing pages directly (HTTP 403 to scripted
  fetch); those numbers (100/day, league id 1, `x-apisports-key`, `status.short=FT`)
  come from official-site search snippets and the api-sports docs, cross-checked, not
  from a rendered page I fetched.

## Sources verified
- football-data.org coverage: https://www.football-data.org/coverage
- football-data.org API reference (auth `X-Auth-Token`, 10 req/min, WC code, status enum, score.fullTime): https://www.football-data.org/documentation/api
- football-data.org match docs: https://docs.football-data.org/general/v4/match.html
- football-data.org competition docs: https://docs.football-data.org/general/v4/competition.html
- football-data.org lookup tables (WC code `WC`, id `2000`): https://docs.football-data.org/general/v4/lookup_tables.html
- football-data.org free-tier analysis (10/min, delayed data): https://www.thestatsapi.com/blog/football-data-org-free-tier-limits-2026
- football-data.org live test: `GET /v4/competitions/WC/matches` → 403 without token (confirmed registered key required)
- TheSportsDB free API: https://www.thesportsdb.com/free_sports_api
- TheSportsDB docs (free key `123`, 30 req/min, eventsseason.php): https://www.thesportsdb.com/documentation
- TheSportsDB WC league id 4429: https://www.thesportsdb.com/league/4429-FIFA-World-Cup
- TheSportsDB live test: `eventsseason.php?id=4429&s=2026` → real WC2026 fixtures + scores + statuses (FT/2H/NS), team names
- API-FOOTBALL pricing/free plan (100/day, no card): https://www.api-football.com/pricing
- API-FOOTBALL WC2026 guide (league id 1, season 2026): https://www.api-football.com/news/post/fifa-world-cup-2026-guide-to-using-data-with-api-sports
- API-FOOTBALL fixtures fields/status short FT: https://www.api-football.com/news/post/how-to-get-all-fixtures-data-from-one-league
- SportMonks free plan (Danish + Scottish only): https://www.sportmonks.com/football-api/free-plan/
- SportMonks World Cup pricing (Advanced €69/mo): https://www.sportmonks.com/football-api/world-cup-api/
