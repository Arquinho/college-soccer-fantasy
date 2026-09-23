# College Fantasy v1 — legacy database compatibility fix

This build fixes startup when `fast_bootstrap.py` reuses an older College XI database.

- Adds missing `games.conference_game` and all other current game fields automatically.
- Keeps the earlier `teams.abbreviation` / `teams.ncaa_slug` migration.
- Defers indexes until after legacy columns have been migrated.
- Preserves the richer legacy roster while overlaying the verified launch schedule.
