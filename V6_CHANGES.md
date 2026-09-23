# V6 — Delivery Candidate

This is the near-final handoff prototype built from the approved College Soccer Fantasy flow.

## Entry flow
- The product opens on the Login screen on every fresh browser session.
- Sign in, demo-manager entry, create-account prototype, password reset prototype, EN/PT/ES selector, and password visibility control are wired.
- Login uses browser-session persistence so refreshes do not kick the manager out, while a new session starts at Login again.
- A loading handoff screen appears only while the first dashboard cache is being read.

## Product flow
- Dashboard → Lineup → position selection → Market follows the Cartola-style flow; there is no separate Market item in the top navigation.
- Profile editing, logout, notifications, lineup reminder, world participation, leagues, Pick'em, Budget Boost, Games & Results, and rankings controls are interactive.
- Manager/team profile fields persist locally in the delivery prototype.

## Performance
- Normal navigation is cache-first and does not trigger season-wide public scraping.
- API reads have a short browser timeout so a slow public-source dependency cannot freeze the UI.
- Players/coaches and extended filters remain lazy-loaded until Lineup/Market needs them.
- Market renders in batches rather than building thousands of cards at once.

## Dashboard fallback
- Each world has an image-backed official-source news fallback so the dashboard never opens as an empty news rectangle when a public feed is temporarily unavailable.
- Live/Today prefers live matches, then today's matches, then the next scheduled matchday.

## Previously approved behavior retained
- NCAA D1 / D2 / D3 / NAIA / NJCAA D1 worlds.
- 120M independent budget per world.
- 4-3-3, 4-4-2, 3-5-2, 3-4-3.
- 11 starters + Head Coach + Assistant Coach + optional bench.
- Player cards: Overall, price, last variation, school, conference, next match.
- Overall scale 75–99 with soccer-season production inputs where verified data exists.
- Conference normalization (including ACC normalization for Stanford, SMU, Louisville and aliases handled by the conference service).
- National rankings, top scorers, assist leaders, conference standings, Games & Results calendar, Pick'em, news images, and official-source refresh controls.

## Production note
Authentication, email delivery, payments and durable multi-user server persistence are deliberately represented as product-complete prototype flows. The handoff files document the production integrations required before public launch.
