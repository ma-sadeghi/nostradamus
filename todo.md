# To do

## Resolved

- [x] Repeated games (A vs. B twice, e.g. in the knockouts): a game's identity
  now includes its kickoff time, so the same pairing on a different date is a
  distinct match — both in the model and in the idempotent CSV import.

## Possible future work

- [ ] Self-serve password reset by email (currently the admin sets passwords
  via `manage.py changepassword`).
- [ ] Auto-populate knockout fixtures from group results instead of entering
  them by hand in the admin.
