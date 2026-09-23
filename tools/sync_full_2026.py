"""One-command verified-data sync for the final College XI prototype.

Run from the project root:
    python3 tools/sync_full_2026.py

NCAA D1/D2/D3 schedules are sourced from NCAA schedule/scoreboard data.
NAIA/NJCAA D1 schedules and all-world player cumulative stats are sourced from
registered official school athletics pages. Missing source coverage stays
explicitly missing rather than being fabricated.
"""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from database import init_db
from services.sync import (
    sync_ncaa_game_history, sync_registered_school_schedules,
    sync_ncaa_rankings, sync_ncaa_stat_tables, sync_all_school_stats,
    recalc_prices,
)

WORLDS=("D1","D2","D3","NAIA","NJCAA1")


def main():
    init_db()
    for world in WORLDS:
        print(f"\n=== {world} ===")
        try:
            if world in {"D1","D2","D3"}:
                result=sync_ncaa_game_history(world,"2026-08-01","2026-12-31")
                print("games:", result.get("stored",0), "complete:", result.get("complete"))
                try:
                    print("rankings:", sync_ncaa_rankings(world).get("count",0))
                except Exception as exc:
                    print("rankings warning:", exc)
                try:
                    print("national stat tables:", sync_ncaa_stat_tables(world))
                except Exception as exc:
                    print("national stats warning:", exc)
            else:
                print("games:", sync_registered_school_schedules(world))
            try:
                print("school player stats:", sync_all_school_stats(world))
            except Exception as exc:
                print("school player stats warning:", exc)
        except Exception as exc:
            print("world sync warning:", exc)
    recalc_prices()
    print("\nDone. Missing values were left unverified rather than invented.")

if __name__ == "__main__":
    main()
