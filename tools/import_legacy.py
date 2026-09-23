"""Read-only importer from an earlier College XI SQLite database.

The source database is opened with SQLite mode=ro. Nothing is ever changed in
that file. This importer can carry over every supported fantasy world, roster
URLs, player/coaching records and season statistics when those tables/columns
exist in the old project.
"""
import argparse
import sqlite3
from pathlib import Path
from database import init_db, db
from services.fantasy import normalize_position
from services.sync import recalc_prices

WORLD_MAP = {
    'D1':'D1','NCAA D1':'D1','NCAA1':'D1',
    'D2':'D2','NCAA D2':'D2','NCAA2':'D2',
    'D3':'D3','NCAA D3':'D3','NCAA3':'D3',
    'NAIA':'NAIA',
    'NJCAA1':'NJCAA1','NJCAA D1':'NJCAA1','NJCAA D1 MEN':'NJCAA1',
}

def table_exists(conn, name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None

def cols(conn, name):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({name})")}

def div_of(r):
    raw=(r.get('division') or r.get('world') or 'D1').strip()
    return WORLD_MAP.get(raw, raw if raw in {'D1','D2','D3','NAIA','NJCAA1'} else 'D1')

def pick(r,*names):
    for n in names:
        if n in r and r.get(n) not in (None,''): return r.get(n)
    return None

def import_db(path, include_games=True):
    source = Path(path).expanduser().resolve()
    if not source.exists():
        raise SystemExit(f"File not found: {source}")
    init_db()
    old = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    old.row_factory = sqlite3.Row
    counts = {"teams":0,"players":0,"coaches":0,"stats":0,"games":0}
    old_to_new={}
    with db() as new:
        if table_exists(old, "teams"):
            for rr in old.execute("SELECT * FROM teams"):
                r=dict(rr); school=pick(r,'school','name'); div=div_of(r)
                if not school: continue
                official=pick(r,'official_url','source_url','athletics_url')
                roster=pick(r,'roster_url'); stats=pick(r,'stats_url'); schedule=pick(r,'schedule_url')
                new.execute("""INSERT INTO teams(school,conference,division,official_url,roster_url,stats_url,schedule_url)
                               VALUES(?,?,?,?,?,?,?) ON CONFLICT(school) DO UPDATE SET
                               conference=COALESCE(excluded.conference,teams.conference),
                               division=COALESCE(excluded.division,teams.division),
                               official_url=COALESCE(excluded.official_url,teams.official_url),
                               roster_url=COALESCE(excluded.roster_url,teams.roster_url),
                               stats_url=COALESCE(excluded.stats_url,teams.stats_url),
                               schedule_url=COALESCE(excluded.schedule_url,teams.schedule_url)""",
                            (school,pick(r,'conference'),div,official,roster,stats,schedule))
                counts['teams']+=1

        if table_exists(old, "players"):
            for rr in old.execute("SELECT * FROM players"):
                r=dict(rr); div=div_of(r); name=pick(r,'name'); school=pick(r,'school','team')
                pos=normalize_position(pick(r,'position','pos'))
                if not name or not school or pos not in {'GK','DF','MF','FW'}: continue
                src=pick(r,'source_url','roster_url')
                new.execute("""INSERT INTO players(name,school,position,class_year,jersey,conference,division,source_url,source_name)
                               VALUES(?,?,?,?,?,?,?,?, 'legacy_copy')
                               ON CONFLICT(name,school,division) DO UPDATE SET
                               position=excluded.position,class_year=COALESCE(excluded.class_year,players.class_year),
                               jersey=COALESCE(excluded.jersey,players.jersey),conference=COALESCE(excluded.conference,players.conference),
                               source_url=COALESCE(excluded.source_url,players.source_url)""",
                            (name,school,pos,pick(r,'class_year','class'),pick(r,'jersey_number','jersey'),pick(r,'conference'),div,src))
                new_id=new.execute("SELECT id FROM players WHERE name=? AND school=? AND division=?",(name,school,div)).fetchone()[0]
                if 'id' in r: old_to_new[r['id']]=new_id
                if src:
                    new.execute("""INSERT INTO teams(school,conference,division,official_url)
                                   VALUES(?,?,?,?) ON CONFLICT(school) DO UPDATE SET
                                   conference=COALESCE(excluded.conference,teams.conference),
                                   official_url=COALESCE(teams.official_url,excluded.official_url)""",
                                (school,pick(r,'conference'),div,src))
                counts['players']+=1

        if table_exists(old, "coaches"):
            for rr in old.execute("SELECT * FROM coaches"):
                r=dict(rr); div=div_of(r); role=pick(r,'role') or ''
                if role in ('Associate Head Coach','Associate Head Coach/Assistant Coach'): role='Assistant Coach'
                if role not in ('Head Coach','Assistant Coach'): continue
                new.execute("""INSERT INTO coaches(name,school,role,conference,division,source_url)
                               VALUES(?,?,?,?,?,?) ON CONFLICT(name,school,division,role) DO UPDATE SET
                               conference=COALESCE(excluded.conference,coaches.conference),source_url=COALESCE(excluded.source_url,coaches.source_url)""",
                            (pick(r,'name'),pick(r,'school'),role,pick(r,'conference'),div,pick(r,'source_url')))
                counts['coaches']+=1

        if table_exists(old,'player_season_stats'):
            stat_cols=cols(old,'player_season_stats')
            allowed=['games','starts','minutes','goals','assists','points','shots','shots_on_goal','yellow_cards','red_cards','game_winners','saves','goals_against','shutouts']
            for rr in old.execute("SELECT * FROM player_season_stats"):
                r=dict(rr); old_pid=r.get('player_id'); new_pid=old_to_new.get(old_pid)
                if not new_pid: continue
                season=int(r.get('season') or 2026)
                stat_source=pick(r,'source_url')
                # Old prototypes often had all-zero default stat rows. Do not
                # promote those placeholders to verified data in the final build.
                if not stat_source:
                    continue
                vals=[r.get(c,0) if c in stat_cols else 0 for c in allowed]
                new.execute("""INSERT INTO player_season_stats(player_id,season,games,starts,minutes,goals,assists,points,shots,shots_on_goal,yellow_cards,red_cards,game_winners,saves,goals_against,shutouts,source_url,source_name,source_updated_at)
                               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(player_id,season) DO UPDATE SET
                               games=excluded.games,starts=excluded.starts,minutes=excluded.minutes,goals=excluded.goals,assists=excluded.assists,
                               points=excluded.points,shots=excluded.shots,shots_on_goal=excluded.shots_on_goal,yellow_cards=excluded.yellow_cards,
                               red_cards=excluded.red_cards,game_winners=excluded.game_winners,saves=excluded.saves,goals_against=excluded.goals_against,
                               shutouts=excluded.shutouts,source_url=COALESCE(excluded.source_url,player_season_stats.source_url),source_name='legacy_copy'""",
                            (new_pid,season,*vals,stat_source,'legacy_copy',pick(r,'source_updated_at')))
                counts['stats']+=1

        if include_games and table_exists(old,'games'):
            for rr in old.execute("SELECT * FROM games"):
                r=dict(rr); div=div_of(r)
                gd=pick(r,'game_date','date'); home=pick(r,'home_team','home'); away=pick(r,'away_team','away')
                if not gd or not home or not away: continue
                new.execute("""INSERT INTO games(game_date,home_team,away_team,home_score,away_score,status,conference_game,venue,division,source_url,source_name,source_updated_at)
                               VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(game_date,home_team,away_team,division) DO UPDATE SET
                               home_score=COALESCE(excluded.home_score,games.home_score),away_score=COALESCE(excluded.away_score,games.away_score),
                               status=COALESCE(excluded.status,games.status),source_url=COALESCE(excluded.source_url,games.source_url)""",
                            (gd,home,away,pick(r,'home_score'),pick(r,'away_score'),pick(r,'status') or 'scheduled',int(pick(r,'conference_game') or 0),pick(r,'venue'),div,pick(r,'source_url'),'legacy_copy',pick(r,'source_updated_at')))
                counts['games']+=1
    old.close()
    recalc_prices()
    return counts

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument('old_db'); p.add_argument('--skip-games', action='store_true'); args=p.parse_args()
    print('Imported read-only copy:', import_db(args.old_db, include_games=not args.skip_games))
