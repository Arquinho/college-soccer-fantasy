# College Fantasy v1

Delivery-focused prototype for men's college soccer fantasy.

Launch worlds:
- NCAA Division I
- NCAA Division II
- NAIA
- NJCAA Division I

## Data strategy
Primary/official sources are preferred:
- NCAA men's soccer scoreboards, rankings and news for NCAA D1/D2
- Official university athletics roster, stats and schedule pages
- NAIA men's soccer and official NAIA-member athletics pages
- NJCAA men's soccer and official NJCAA-member athletics pages

TopDrawerSoccer is retained only as an enrichment/fallback source when an official
field is missing; official sources remain authoritative when they disagree.

## Performance changes
- Schedule views are cache-first.
- Clicking View Full Schedule reads SQLite immediately.
- Clicking another date reads that date from SQLite immediately.
- A date-specific official refresh starts in the background and never blocks the UI.
- A rolling 21-day cache is warmed in the background for the four launch worlds.
- Dashboard navigation never waits on a full-season crawl.

## UX changes
- New compact budget card with clear C$ balance and boost.
- Four worlds visible in the selector: D1, D2, NAIA, NJCAA D1.

## September 23 compatibility hotfix
- Fixed startup failure `sqlite3.OperationalError: no such column: abbreviation` when the fast bootstrap reuses an older richer local College XI database.
- Legacy `teams`, `players`, `coaches`, and player-stat tables are now migrated automatically before the verified schedule overlay runs.
- Team-name resolution is tolerant of legacy databases while aliases are being migrated.
- Verified Sep 23-25 D1 schedule overlay remains installed after a legacy roster database is reused.

## September 23 schedule-integrity fix
- Exact-date refreshes now replace that calendar date atomically instead of adding rows onto an older cache.
- The full-season parser is no longer mixed into a clicked date refresh.
- Team aliases are matched conservatively and favor the roster-backed school identity; UC San Diego remains distinct from the University of San Diego.
- Reversed home/away rows and long/short school-name aliases collapse to one game.
- The browser replaces one date's local state after refresh, so stale duplicate cards disappear immediately without requiring a page reload.
- NCAA 24-hour start times are normalized to a consistent 12-hour Eastern display.
- When a richer older College XI database is found, only teams/players/coaches/verified player stats are imported. Legacy game tables are intentionally skipped.
- The bundled D1 cache for Sep. 23 contains exactly 8 verified fixtures; Sep. 24 contains 1; Sep. 25 contains 21.
