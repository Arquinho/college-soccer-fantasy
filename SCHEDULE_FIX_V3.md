# Schedule fix v3 — Sept. 23, 2026

This build fixes the multi-date NCAA scoreboard bug.

Root cause: NCAA scoreboard results are scoped by the requested U.S. calendar date, while each contest's `startDate` can roll into the following UTC date for evening games. Earlier builds compared `startDate` directly to the selected date and discarded valid evening fixtures.

Changes:
- Trust the requested NCAA scoreboard date for all returned contests.
- Prefer NCAA's direct GraphQL scoreboard transport, with ncaa-api as fallback.
- Exact-date calendar clicks skip slow season schedule discovery.
- `SYNC 2026 SCHEDULE` refreshes the selected day first, then warms the full season in a background thread.
- Neighboring visible dates continue to prefetch in the background.
