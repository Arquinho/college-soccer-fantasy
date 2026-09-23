# Date schedule fix v2

- Fixed calendar prefetch ordering: today and the next 3 dates are now warmed first.
- All 7 visible dates are refreshed in the background when missing.
- Exact-date NCAA refresh no longer aborts after 8.5 seconds.
- NCAA scoreboard fetch now tries both known GraphQL contestDate formats.
- The ncaa-api NCAA mirror is used as the fast first path; direct NCAA GraphQL is the authoritative fallback.
- Network fallbacks use shorter per-source timeouts so one unavailable source cannot block the calendar for 20+ seconds.
- Selecting a date shows a clear short loading state while only that date is being fetched.
