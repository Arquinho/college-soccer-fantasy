#!/usr/bin/env python3
"""One-time cache warmup before sharing/deploying the evaluation build.

This does NOT change UI/feature behavior. It fills the local SQLite snapshot so
first-time visitors can see the dashboard, complete D1 schedule, completed-game
scores, news, rankings, goal scorers and assist leaders without waiting for live
source crawls after page load.
"""
from datetime import date
import time
import os
import sys

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

from database import init_db, rows
from services.news import sync_news
from services.sync import (
    sync_ncaa_season_schedule_fast,
    sync_ncaa_game_history,
    sync_ncaa_rankings,
    sync_ncaa_standings,
    sync_ncaa_stat_tables,
    recalc_prices,
)

DIVISION = "D1"
SEASON = 2026


def show(label, result):
    ok = bool(result and result.get("ok")) if isinstance(result, dict) else False
    count = None
    if isinstance(result, dict):
        count = result.get("stored", result.get("count"))
    suffix = f" · {count} rows" if count is not None else ""
    print(f"[{'OK' if ok else 'WARN'}] {label}{suffix}")
    if isinstance(result, dict) and not ok and result.get("error"):
        print(f"       {result['error']}")


def main():
    init_db()
    print("Preparing the NCAA D1 evaluation cache. This is a one-time pre-deploy step.\n", flush=True)
    print("Step 1/6: loading the complete NCAA D1 schedule…", flush=True)

    season = sync_ncaa_season_schedule_fast(DIVISION, year=SEASON, recalc=False)
    show("Complete 2026 division schedule", season)
    print("Step 2/6: refreshing completed-game results…", flush=True)

    # Refresh scores only on dates that actually exist in the cached schedule.
    # This is much faster than probing every day of the calendar.
    today = min(date.today(), date(SEASON, 12, 31)).isoformat()
    game_dates = [r["game_date"] for r in rows(
        """SELECT DISTINCT game_date FROM games
           WHERE division=? AND game_date>='2026-08-01' AND game_date<=?
           ORDER BY game_date""",
        (DIVISION, today),
    )]
    print(f"Refreshing results for {len(game_dates)} scheduled dates through {today} …", flush=True)
    score_ok = 0
    for idx, game_date in enumerate(game_dates, 1):
        try:
            result = sync_ncaa_game_history(DIVISION, start_date=game_date, end_date=game_date, recalc=False)
            if result.get("ok"):
                score_ok += 1
        except Exception as exc:
            print(f"[WARN] {game_date}: {exc}")
        if idx % 10 == 0 or idx == len(game_dates):
            print(f"       results {idx}/{len(game_dates)}", flush=True)
        time.sleep(0.22)
    print(f"[OK] Result dates refreshed: {score_ok}/{len(game_dates)}", flush=True)
    print("Step 3/6: refreshing news…", flush=True)

    try:
        show("Current NCAA news", sync_news(DIVISION))
    except Exception as exc:
        print(f"[WARN] Current NCAA news · {exc}")
    print("Step 4/6: refreshing national ranking and standings…", flush=True)
    try:
        show("National ranking", sync_ncaa_rankings(DIVISION))
    except Exception as exc:
        print(f"[WARN] National ranking · {exc}")
    try:
        show("Conference standings", sync_ncaa_standings(DIVISION))
    except Exception as exc:
        print(f"[WARN] Conference standings · {exc}")
    print("Step 5/6: refreshing all goal scorers and assist leaders…", flush=True)
    try:
        leaders = sync_ncaa_stat_tables(DIVISION, categories=["goals", "assists"])
        goals = leaders.get("goals", {}) if isinstance(leaders, dict) else {}
        assists = leaders.get("assists", {}) if isinstance(leaders, dict) else {}
        print(f"[{'OK' if goals.get('ok') else 'WARN'}] Goal scorers · {goals.get('count', 0)} rows")
        print(f"[{'OK' if assists.get('ok') else 'WARN'}] Assist leaders · {assists.get('count', 0)} rows")
    except Exception as exc:
        print(f"[WARN] Player leaderboards · {exc}")

    print("Step 6/6: recalculating fantasy values…", flush=True)
    recalc_prices()
    totals = rows("""SELECT
        (SELECT COUNT(*) FROM games WHERE division='D1') games,
        (SELECT COUNT(*) FROM stat_leaders WHERE division='D1' AND category='goals' AND value>0) scorers,
        (SELECT COUNT(*) FROM stat_leaders WHERE division='D1' AND category='assists' AND value>0) assists""")
    if totals:
        t = totals[0]
        print(f"\nCache ready: {t['games']} games · {t['scorers']} scorers · {t['assists']} assist leaders")
    print("You can now commit the updated SQLite database together with the code and push to Render.")


if __name__ == "__main__":
    main()
