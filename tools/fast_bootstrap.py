#!/usr/bin/env python3
"""Fast local bootstrap for College Fantasy v1.

A previous College XI database can be useful because it contains thousands of
real roster/player rows.  Its schedule cache is *not* reused: older prototypes
mixed several schedule transports and can contain aliases/duplicates.  We keep
the clean database shipped with this build and import roster/stat tables only.
"""
from __future__ import annotations
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CURRENT = ROOT / 'college_xi_d1.sqlite3'
SEED = ROOT / 'college_xi_d1.delivery-seed.sqlite3'


def counts(path: Path):
    try:
        c = sqlite3.connect(f'file:{path.resolve()}?mode=ro', uri=True)
        tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        def n(t): return c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] if t in tables else 0
        out = {'players': n('players'), 'games': n('games'), 'stats': n('player_season_stats'), 'news': n('news')}
        c.close(); return out
    except Exception:
        return {'players': 0, 'games': 0, 'stats': 0, 'news': 0}


def roster_score(x):
    # Schedules from legacy prototypes are deliberately ignored when choosing
    # the best local source. We only want the richest roster/stat database.
    return x['players'] * 10 + x['stats'] * 3 + x['news']


def candidates():
    home=Path.home()
    for base in (home/'Downloads', home/'Desktop'):
        if not base.exists(): continue
        for pattern in ('college_xi*/college_xi_d1.sqlite3','college_xi*/college_xi.db','College Fantasy*/college_xi_d1.sqlite3'):
            for p in base.glob(pattern):
                try:
                    if p.resolve()!=CURRENT.resolve(): yield p
                except Exception: pass


def maybe_import_richer_local_roster():
    cur=counts(CURRENT)
    # Once the clean build already contains a rich roster, do not re-import on
    # every run. This also preserves any local fantasy/user state in the DB.
    if cur['players']>=500:
        print(f"Fast bootstrap: current roster kept ({cur['players']} players, {cur['games']} schedule rows).")
        return

    best=None; best_counts=cur; best_score=roster_score(cur)
    for p in candidates():
        c=counts(p); s=roster_score(c)
        if s>best_score and c['players']>=500:
            best,best_counts,best_score=p,c,s
    if not best:
        print(f"Fast bootstrap: packaged seed kept ({cur['players']} players, {cur['games']} games).")
        return

    # Start from the known-clean delivery seed if available. Never copy the
    # legacy database wholesale because that is how stale/duplicate games came
    # back into earlier builds.
    if SEED.exists():
        shutil.copy2(SEED, CURRENT)

    from tools.import_legacy import import_db
    imported=import_db(str(best), include_games=False)
    print(
        f"Fast bootstrap: imported richer local roster only "
        f"({imported.get('players',0)} player rows; legacy games skipped) from {best}."
    )



def ensure_schedule_cache_generation():
    """Discard game caches created by pre-v5 prototypes exactly once."""
    from datetime import datetime, timezone
    from database import init_db, db
    init_db()
    source='College Fantasy v1'
    entity='schedule-cache:v5'
    with db() as conn:
        marker=conn.execute("SELECT id FROM source_status WHERE source=? AND entity=? LIMIT 1",
                            (source,entity)).fetchone()
        if marker:
            return
        old_count=conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]
        conn.execute("DELETE FROM games")
        conn.execute("INSERT INTO source_status(source,entity,status,detail,checked_at) VALUES(?,?,?,?,?)",
                     (source,entity,'ok',f'pre-v5 schedule cache cleared ({old_count} rows)',
                      datetime.now(timezone.utc).isoformat(timespec='seconds')))
        print(f"Schedule cache migration: removed {old_count} pre-v5 game rows.")

def overlay_verified_launch_schedule():
    """Seed the launch-window schedule without overwriting live/final results.

    The verified snapshot is a fixture snapshot, not a results feed.  Earlier
    builds replaced Sep 23-25 on every startup, which turned already-completed
    games back into ``scheduled`` rows with blank scores.  For today/past dates,
    only seed the snapshot when the date is completely absent.  Future snapshot
    dates may still be replaced as a unit to avoid aliases/duplicates.
    """
    from datetime import date
    from database import init_db, db
    from services.sync import _upsert_game
    from services.sources.verified_schedule import fetch_verified_schedule_snapshot
    init_db()
    today=date.today().isoformat()
    preserved=0
    installed=0
    with db() as conn:
        for d in ('2026-09-23','2026-09-24','2026-09-25'):
            existing=conn.execute(
                "SELECT COUNT(*) FROM games WHERE division='D1' AND game_date=?",
                (d,),
            ).fetchone()[0]
            if d <= today and existing:
                preserved += existing
                continue
            snap=fetch_verified_schedule_snapshot('D1',d)
            if not snap.get('items'):
                continue
            conn.execute("DELETE FROM games WHERE division='D1' AND game_date=?",(d,))
            for g in snap['items']:
                _upsert_game(conn,g)
                installed += 1
    c=counts(CURRENT)
    print(
        f"Schedule overlay: launch fixtures installed={installed}, "
        f"existing past/today rows preserved={preserved} "
        f"({c['games']} total game rows)."
    )



def overlay_fgcu_official_schedule():
    """Install FGCU's published 2026 regular-season fixtures without touching other games."""
    from datetime import datetime, timezone
    from database import init_db, db
    from services.sync import _upsert_game, _team_key
    init_db()
    source_url='https://fgcuathletics.com/sports/mens-soccer/schedule/2026'
    updated=datetime.now(timezone.utc).isoformat(timespec='seconds')
    fgcu='Florida Gulf Coast University'
    fixtures=[
        ('2026-09-26','Queens',fgcu,'6:00 PM ET'),
        ('2026-09-29',fgcu,'FIU','7:00 PM ET'),
        ('2026-10-03',fgcu,'Bellarmine','7:00 PM ET'),
        ('2026-10-06',fgcu,'FAU','7:00 PM ET'),
        ('2026-10-10',fgcu,'Lipscomb','7:00 PM ET'),
        ('2026-10-17','Central Arkansas',fgcu,'7:00 PM ET'),
        ('2026-10-24',fgcu,'Stetson','7:00 PM ET'),
        ('2026-10-31','Jacksonville',fgcu,'7:00 PM ET'),
    ]
    fgcu_keys={'fgcu','floridagulfcoast'}
    with db() as conn:
        conn.execute("""UPDATE teams SET schedule_url=?,stats_url=COALESCE(stats_url,?),official_url=COALESCE(official_url,?)
                     WHERE division='D1' AND lower(school) IN ('florida gulf coast university','florida gulf coast','fgcu')""",
                     (source_url,'https://fgcuathletics.com/sports/mens-soccer/stats','https://fgcuathletics.com/sports/mens-soccer/'))
        for d,home,away,start in fixtures:
            # Remove only an existing FGCU alias of this same fixture/date.
            for r in conn.execute("SELECT id,home_team,away_team FROM games WHERE division='D1' AND game_date=?",(d,)).fetchall():
                if _team_key(r['home_team']) in fgcu_keys or _team_key(r['away_team']) in fgcu_keys:
                    conn.execute('DELETE FROM games WHERE id=?',(r['id'],))
            _upsert_game(conn,{
                'game_date':d,'home_team':home,'away_team':away,'status':f'scheduled · {start}',
                'division':'D1','source_url':source_url,'source_name':'FGCU Athletics (official schedule)',
                'source_updated_at':updated,'start_time':start,
            })
    print('Schedule overlay: FGCU official future schedule installed.')




def remove_single_school_future_overlay():
    """Remove the old FGCU-only future cache from previous v1 builds.

    A date with one preloaded school looked complete to the client and prevented
    an exact NCAA refresh.  Future schedules now come from the division-wide
    NCAA season/date sync instead.
    """
    from database import init_db, db
    init_db()
    with db() as conn:
        cur=conn.execute("""DELETE FROM games
                            WHERE division='D1'
                              AND game_date>='2026-09-26'
                              AND lower(COALESCE(source_name,'')) LIKE 'fgcu athletics%'""")
        if cur.rowcount:
            print(f'Schedule migration: removed {cur.rowcount} FGCU-only future cache rows.')

def overlay_verified_player_stats():
    """Seed a small current set of verified leader stats; bulk school sync adds the rest."""
    import re
    from datetime import datetime, timezone
    from database import init_db, db
    from services.sync import _team_key
    init_db()
    updated=datetime.now(timezone.utc).isoformat(timespec='seconds')
    rows=[
        {'names':['Zach Ramsey'],'school':'Washington','games':8,'starts':6,'minutes':583,'goals':12,'assists':2,'points':26,'shots':38,'shots_on_goal':25,'game_winners':1,'url':'https://gohuskies.com/sports/mens-soccer/stats/2026'},
        {'names':['Isaiah Chisolm'],'school':'Ohio State','games':4,'starts':4,'minutes':223,'goals':7,'assists':0,'points':14,'shots':14,'shots_on_goal':9,'game_winners':3,'url':'https://ohiostatebuckeyes.com/sports/mens-soccer/stats/2026'},
        {'names':['Samson Kpardeh','Samson Kparde'],'school':'Liberty','games':5,'starts':5,'minutes':433,'goals':6,'assists':0,'points':12,'shots':29,'shots_on_goal':12,'yellow_cards':2,'game_winners':1,'url':'https://libertyflames.com/sports/mens-soccer/stats/2026'},
        {'names':['Joshwa Campbell'],'school':'Longwood','games':8,'starts':7,'minutes':639,'goals':5,'assists':1,'points':11,'shots':12,'shots_on_goal':10,'yellow_cards':1,'game_winners':2,'url':'https://longwoodlancers.com/sports/mens-soccer/stats/'},
        {'names':['Luca Bartoni'],'school':'Lindenwood','games':8,'starts':8,'minutes':619,'goals':5,'assists':0,'points':10,'shots':14,'shots_on_goal':9,'yellow_cards':3,'url':'https://lindenwoodlions.com/sports/mens-soccer/stats/2026'},
        {'names':['Mukisa Emmanuel'],'school':'SMU','games':8,'starts':1,'minutes':384,'goals':5,'assists':1,'points':11,'shots':20,'shots_on_goal':9,'yellow_cards':1,'game_winners':1,'url':'https://smumustangs.com/sports/mens-soccer/stats/2026'},
        {'names':['Tomiwa Adewumi'],'school':'Marquette','games':8,'starts':8,'minutes':507,'goals':8,'assists':1,'points':17,'shots':15,'shots_on_goal':9,'game_winners':2,'url':'https://gomarquette.com/sports/mens-soccer/stats/2026'},
    ]
    def pkey(v): return re.sub(r'[^a-z0-9]','',str(v or '').lower())
    with db() as conn:
        players=[dict(r) for r in conn.execute("SELECT id,name,school FROM players WHERE division='D1'").fetchall()]
        seeded=0
        for s in rows:
            aliases={pkey(x) for x in s['names']}
            target=None
            for pl in players:
                if _team_key(pl['school'])!=_team_key(s['school']):
                    continue
                pk=pkey(pl['name'])
                if pk in aliases or any(pk.startswith(a) or a.startswith(pk) for a in aliases if len(a)>=8):
                    target=pl;break
            if not target:
                continue
            vals={k:s.get(k,0) for k in ('games','starts','minutes','goals','assists','points','shots','shots_on_goal','yellow_cards','red_cards','game_winners','saves','goals_against','shutouts')}
            conn.execute("""INSERT INTO player_season_stats(player_id,season,games,starts,minutes,goals,assists,points,shots,shots_on_goal,yellow_cards,red_cards,game_winners,saves,goals_against,shutouts,source_url,source_name,source_updated_at)
                          VALUES(?,2026,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                          ON CONFLICT(player_id,season) DO UPDATE SET
                          games=MAX(player_season_stats.games,excluded.games),starts=MAX(player_season_stats.starts,excluded.starts),minutes=MAX(player_season_stats.minutes,excluded.minutes),
                          goals=MAX(player_season_stats.goals,excluded.goals),assists=MAX(player_season_stats.assists,excluded.assists),points=MAX(player_season_stats.points,excluded.points),
                          shots=MAX(player_season_stats.shots,excluded.shots),shots_on_goal=MAX(player_season_stats.shots_on_goal,excluded.shots_on_goal),
                          yellow_cards=MAX(player_season_stats.yellow_cards,excluded.yellow_cards),red_cards=MAX(player_season_stats.red_cards,excluded.red_cards),
                          game_winners=MAX(player_season_stats.game_winners,excluded.game_winners),saves=MAX(player_season_stats.saves,excluded.saves),
                          goals_against=MAX(player_season_stats.goals_against,excluded.goals_against),shutouts=MAX(player_season_stats.shutouts,excluded.shutouts),
                          source_url=excluded.source_url,source_name=excluded.source_name,source_updated_at=excluded.source_updated_at""",
                         (target['id'],*[vals[k] for k in ('games','starts','minutes','goals','assists','points','shots','shots_on_goal','yellow_cards','red_cards','game_winners','saves','goals_against','shutouts')],s['url'],'official_school',updated))
            seeded+=1
    print(f'Player data overlay: {seeded} verified leader stat rows installed.')

def main():
    maybe_import_richer_local_roster()
    overlay_verified_player_stats()
    ensure_schedule_cache_generation()
    remove_single_school_future_overlay()
    overlay_verified_launch_schedule()
    # Do not install a single-school future schedule. Future NCAA dates are
    # populated division-wide by the background NCAA season sync in app.py.
    # Apply one valuation/overall model to every imported player before the UI
    # opens.  This prevents legacy ratings from surviving for non-FGCU schools.
    from services.sync import recalc_prices
    recalc_prices()
    print('Player overalls: universal 2026 model applied to all imported schools.')


if __name__=='__main__': main()
