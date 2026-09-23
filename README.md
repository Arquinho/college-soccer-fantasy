# College Fantasy v1 — Delivery Candidate v6

**Near-final handoff prototype. The product opens on Login and then follows the complete fantasy flow.**

> Performance note (v5): the dashboard uses lazy loading. The full roster is loaded only when Lineup/Market is opened.

# College Soccer Fantasy — Delivery Candidate 2026

A polished, self-contained handoff prototype for a multi-world U.S. college soccer fantasy game.

The product direction is intentionally close to the approved concept: **Cartola-style fantasy flow + College Soccer Fantasy blue/white identity**, without a separate Market tab in the main navigation.

## Start locally

```bash
bash run.sh
```

Then open:

```text
http://127.0.0.1:5012
```

The prototype login accepts any non-empty email/password. The prefilled demo credentials work immediately.

## Product experience included

### Dashboard
- College Soccer Fantasy identity and top navigation.
- Active world selector: NCAA D1, NCAA D2, NCAA D3, NAIA, NJCAA D1.
- World-specific official news source links.
- Live & Today panel with up to five prioritized games.
- Full schedule shortcut, lineup CTA, profile and world participation.

### Lineup + integrated Market
- Main nav contains **Lineup**, not a separate Market tab.
- Click an open field position to open the market for that position.
- Formations: 4-3-3, 4-4-2, 3-5-2, 3-4-3.
- 11 starters + Head Coach + Assistant Coach.
- Optional bench: GK, DF, MF, FW.
- 120M base budget per world.
- Market cards show Overall, price, last value movement, school, conference and next verified match.
- Player detail modal includes 2026 season stats and source link when available.

### Games & Results
- Full calendar/date input and seven-day strip.
- Conference and school filters.
- Schedule / Live / Upcoming / Results tabs.
- Future schedule is preserved when a scoreboard refresh returns zero games.
- NCAA scoreboard information is merged with official school schedule data.
- Pick'em uses future stored fixtures.

### Rankings & Competitions
- NCAA ranking view.
- Player scoring/assist/clean-sheet leaders when data are available.
- Conference standings.
- Fantasy-manager presentation layer.
- Create/join league prototype flow.

### Localization
- English, Portuguese and Spanish interface controls.

## Sports data policy

The app never fabricates missing scores/statistics. If a source has not been synchronized, the UI shows a pending/unavailable state.

Data adapters are included for:
- NCAA scoreboards, rankings and national stat tables.
- Official school roster/stat/schedule pages.
- NAIA/NJCAA registered official school schedules.
- TopDrawerSoccer enrichment for selected D1 metadata.

Run a broader verified-data sync with:

```bash
python3 tools/sync_full_2026.py
```

This can take time because it checks real public sources.

## Integrity checks

```bash
python3 -m py_compile app.py database.py services/*.py services/sources/*.py
node --check static/app.js
python3 tools/check_final.py
```

A Flask endpoint smoke test is also included as `tools/smoke_test.py` and can be run after dependencies are installed.

## Temporary public preview from VS Code

1. Run `bash run.sh`.
2. Open VS Code **Ports**.
3. Forward `5012`.
4. Set Visibility to **Public**.
5. Share the generated `devtunnels.ms` address.

## Permanent review deployment

Deployment files are included for Render/Gunicorn:
- `render.yaml`
- `Procfile`
- `start.sh`
- `/api/health`

See `DEPLOYMENT.md`.

## What “delivery candidate” means

This build is suitable for demos, supervisor/developer handoff, UX review and continued VS Code refinement. It is **not yet a production public launch** with real accounts or payments.

Before a public launch, migrate browser-only manager state to authenticated server-side accounts, move SQLite to PostgreSQL, add scheduled background data jobs, monitoring/backups, final round/scoring audit rules, and legal/privacy/payment flows.

See `HANDOFF_CHECKLIST.md` for the exact production gap list.