# Schedule source fix

The 2026-09-23 D1 schedule is seeded from the official NCAA Men's Soccer scoreboard for that exact date.

Important implementation changes:
- NCAA's direct GraphQL scoreboard is tried before the community proxy.
- Returned contests are date-validated when `startDate` is present.
- Stale/cached upstream data can no longer be silently relabeled as the requested date.
- The packaged 2026-09-23 warm cache was replaced with the official eight-game slate.
- Game cards mirror NCAA ordering (away team first, home team second).
- AM/PM times are sorted numerically rather than lexicographically.
