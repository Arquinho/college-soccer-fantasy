# Delivery Candidate v4 — performance pass

This version keeps the v3 soccer-data improvements and makes normal navigation database-first.

## Speed improvements
- Normal page loads no longer call NCAA/other public websites synchronously.
- Rankings, news, scoreboard and next-match views read cached verified data immediately.
- Public-source updates happen only from explicit Refresh/Sync actions or the lightweight live timers.
- Opening Games & Results no longer starts a full-season synchronization automatically.
- Opening the Market no longer starts a full all-school player-stat crawl automatically.
- Initial game payload is limited to a useful window around today; exact dates are loaded from the local database on demand.
- Market renders 60 players/coaches at a time with a Load More control instead of creating 1,000+ DOM cards at once.
- renderAll only renders the page that is actually visible.
- Live scores refresh every 90 seconds in the background; news refreshes every 10 minutes.
- run.sh skips pip install when dependencies already exist and disables Flask's double-process debug reloader by default.

## Data behavior retained
- NCAA men's soccer national rankings and scoring leader caches.
- Conference normalization/repair (including ACC aliases and school fallback mappings).
- News images where the source exposes an image.
- Next-match schedule cache.
- 75–99 soccer-only overall model based on verified 2026 player stats.
