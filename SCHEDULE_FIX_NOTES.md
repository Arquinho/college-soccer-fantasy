# College Fantasy v1 — schedule fix

## What changed
- NCAA D1 dashboard now has an official NCAA.com 2026-09-23 schedule snapshot in SQLite, so **Live & Today renders up to 5 games immediately** without waiting for a network refresh.
- `Games & Results` is cache-first. Clicking a date paints any prefetched rows immediately, then performs only an exact-date refresh if needed.
- The visible 7-day date strip is prefetched in the background so adjacent days are much more likely to be ready before they are clicked.
- NCAA 2026 scoreboard fetching now mirrors the maintained `henrygd/ncaa-api` GraphQL transport and adds an NCAA.com HTML fallback.
- Network timeouts and request delay were reduced for interactive use, and exact-date schedule refreshes no longer recalculate every fantasy price before returning.
- NCAA D1, NCAA D2, NAIA, and NJCAA D1 remain the four enabled worlds.

## Data policy
Cached games are only inserted from identified public sports sources. The packaged 2026-09-23 NCAA D1 snapshot comes from the NCAA men's soccer scoreboard; live refreshes can replace/enrich it.
