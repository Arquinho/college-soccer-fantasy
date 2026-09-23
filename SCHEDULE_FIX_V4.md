# Schedule fix v4

This build fixes two independent causes of empty calendar dates.

1. **Legacy database overwrite:** `run.sh` reused a richer older local College XI database when one was found in Downloads/Desktop. That was useful for the large player roster, but it could silently replace the corrected schedule bundled in a new ZIP. The bootstrap now reuses the richer roster when available **and then always overlays the verified Sep. 23–25 D1 schedule cache**.

2. **Future-date transport:** future fixtures no longer depend only on the live scoreboard. The date refresh order is now:
   - NCAA exact-date scoreboard / GraphQL for live and final state;
   - NCAA official monthly Casablanca schedule for future fixtures;
   - NCAA 2026+ full-season schedule GraphQL;
   - public support/official-school fallbacks;
   - verified launch-week snapshot only as the final transport safety net.

The full-season Sync action no longer performs a long sequential scoreboard crawl. It warms the season schedule and enriches only one relevant date with live/final scoreboard data.

Expected launch-week behavior for NCAA D1:
- Sep. 23: 8 cached games
- Sep. 24: verified UC Irvine vs California Baptist fixture cached
- Sep. 25: 21 verified fixtures cached

After a richer legacy database is imported, the terminal prints a line beginning with:

`Schedule overlay: verified Sep 23-25 cache installed`

That line confirms the schedule patch was applied after the roster import.
