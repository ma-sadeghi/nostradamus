# 2026 FIFA World Cup - Data Notes

Reference notes for the data files in this directory. Generated June 13, 2026.

## Output files

- `worldcup2026_teams.csv` - 48 qualified teams (name, FIFA tri-code).
- `worldcup2026.csv` - 72 group-stage matches, import-ready (blank scores).
- `worldcup2026_knockouts.md` - 32 knockout matches (R32 -> Final), reference only.
- `worldcup2026_notes.md` - this file.

## Sources

Primary source for groups, fixtures, kickoff times, and venues was Wikipedia,
fetched as raw wikitext (the `{{#invoke:football box|main ...}}` templates give
each match's date, local kickoff time WITH an explicit UTC offset, the two teams
as FIFA tri-codes, and the stadium/city). Using the offset embedded in the
source removes any timezone-conversion guesswork.

- 2026 FIFA World Cup (main article, group composition + qualification):
  https://en.wikipedia.org/wiki/2026_FIFA_World_Cup
- Per-group fixture articles (one per group, A-L), e.g.:
  https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_A
  (...through Group L; raw wikitext via `?action=raw`)
- 2026 FIFA World Cup knockout stage (R32 through 3rd-place):
  https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_knockout_stage
- 2026 FIFA World Cup final (the Final match box is transcluded from here):
  https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_final

Cross-checks:

- FIFA official tri-codes verified against Soccerphile's World Cup 2026 code list
  (https://www.soccerphile.com/world-cup-2026/fifa-country-codes) and FourFourTwo.
  All 48 codes matched the codes used in the Wikipedia match boxes.
- Group composition cross-checked against Al Jazeera's full schedule article
  (https://www.aljazeera.com/sports/2026/6/11/world-cup-2026-full-match-schedule-groups-teams-and-start-times)
  and FIFA.com's match schedule page. Groups A-L agreed.
- Tournament window (June 11 - July 19, 2026), host venues, and the opening match
  (Mexico vs South Africa, Estadio Azteca, June 11) confirmed across FIFA and
  multiple outlets.

## Time conversion to UTC

Every Wikipedia match box lists the local kickoff time together with the venue's
UTC offset, e.g. `1:00 p.m. UTC-6`. UTC = local + offset (all host venues are
west of UTC, so the offset is added). June/July 2026 is daylight saving time in
the US and Canada, which is already baked into the offsets the source provides:

- UTC-4 = Eastern (EDT): Toronto, NY/NJ, Philadelphia, Boston, Atlanta, Miami.
- UTC-5 = Central (CDT): Dallas, Houston, Kansas City.
- UTC-6 = Central (CST, no DST): Mexico City, Guadalajara, Monterrey (Mexico does
  not observe DST).
- UTC-7 = Pacific (PDT) / Mountain: Los Angeles, Santa Clara, Seattle, Vancouver.

Spot-checked conversions (all correct):

- Mexico vs South Africa: June 11, 1:00 PM UTC-6 -> 2026-06-11 19:00:00 UTC.
- USA vs Paraguay: June 12, 6:00 PM UTC-7 -> 2026-06-13 01:00:00 UTC (rolls to
  next UTC day).
- Canada vs Bosnia & Herz.: June 12, 3:00 PM UTC-4 -> 2026-06-12 19:00:00 UTC.
- England vs Croatia: June 17, 3:00 PM UTC-5 -> 2026-06-17 20:00:00 UTC.

Note: matchday-3 games in a group kick off simultaneously (anti-collusion rule).
This shows up as identical UTC timestamps for paired fixtures, e.g. Group J's
final pair both at 2026-06-28 02:00:00 UTC, Group K's both at 23:30 UTC. The two
late Group J fixtures (9 PM CDT on June 27) convert to 02:00 UTC on June 28 -
this is correct, not an error; the local matchday is still June 27.

## Team names (<= 20 chars for the DB)

Common English names, trimmed to fit the 20-char limit where needed:
- "Bosnia & Herz." (Bosnia and Herzegovina)
- "United States", "South Korea", "South Africa", "Saudi Arabia", "Czech Republic",
  "DR Congo", "Curacao" (no cedilla, to stay ASCII-safe), "Ivory Coast".

FIFA tri-codes that differ from the obvious abbreviation: RSA (South Africa),
SUI (Switzerland), KSA (Saudi Arabia), COD (DR Congo), CPV (Cape Verde),
CUW (Curacao), CIV (Ivory Coast), GER (Germany), NED (Netherlands), ALG (Algeria).

## Qualification status

All 48 teams are confirmed. The six playoff-decided slots all resolved by
March 31, 2026 and appear in the source as concrete teams (no placeholders
remain in any match box):

- UEFA second round Path A -> Bosnia & Herzegovina (BIH)
- UEFA second round Path B -> Sweden (SWE)
- UEFA second round Path C -> Turkey (TUR)
- UEFA second round Path D -> Czech Republic (CZE)
- Inter-confederation playoff Path 1 -> DR Congo (COD)
- Inter-confederation playoff Path 2 -> Iraq (IRQ)

## Assumptions / things to know

- "Home" team = the team listed first (team1) in the official Wikipedia fixture,
  per the instructions. World Cup matches have no true home team except for host
  nations; team1/team2 follows FIFA's published ordering.
- Scores are intentionally blank in worldcup2026.csv (players predict them).
- Group-stage CSV rows are ordered by official FIFA match number (1-72).
- Knockout matches cannot be imported yet (teams unknown until group results),
  so they are provided only as a human-readable reference in the .md file. Their
  kickoff times/venues ARE fixed and were converted to UTC the same way.
- A small number of group articles had a couple of completed early matches with
  real scores in the source (e.g. the opener); those results were NOT carried
  into the CSV - all score columns are left blank as required.

## Could NOT verify / caveats

- Nothing material was left unverified for the schedule itself: all 72 group
  fixtures, all 32 knockout slots, dates, UTC offsets, and venues came directly
  from the structured Wikipedia match templates and were cross-checked against
  FIFA/Al Jazeera for groups and venues.
- The single source of truth for kickoff times was Wikipedia's embedded UTC
  offsets. These match the known DST rules for each host city, but if FIFA makes
  any late kickoff-time change, re-fetch the per-group articles before the event.
