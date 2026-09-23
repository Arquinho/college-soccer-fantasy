# V5 performance changes

- Dashboard first paint no longer waits for the full player/coaches roster.
- Heavy roster data loads only when Lineup or Market is opened.
- Filters and season coverage are lazy-loaded only on pages that need them.
- Initial dashboard requests only cached news, today/live scores and a 10-day game window.
- One-time bootstrap clones the richest existing local College XI SQLite database at file level instead of row-by-row importing it during Flask startup.
- Conference repair and fantasy valuation recalculation run in a background thread after Flask is already serving pages.
- Flask debug/reloader stays off by default and threaded request handling is enabled.
- Live scoreboard refresh frequency is reduced while presenting the prototype.

- Expensive maintenance is off by default at boot; it can be enabled with `CXI_BACKGROUND_MAINTENANCE=1` or triggered by explicit sync workflows.
