from pathlib import Path
from database import row


def _candidate_databases():
    """Yield earlier College XI databases, newest-looking prototype folders first."""
    home=Path.home()
    roots=[home/'Downloads',home/'Desktop']
    names=['college_xi_d1.sqlite3','college_xi.db']
    explicit=[]
    for base in roots:
        for folder in ['college_xi_prototype_v7_4','college_xi_prototype_v7_3','college_xi_prototype_v7_updated','college_xi_prototype_v7','college_xi_fantasy_v4']:
            for name in names:
                explicit.append(base/folder/name)
    seen=set()
    for p in explicit:
        if p.exists() and p.resolve() not in seen:
            seen.add(p.resolve()); yield p
    for base in roots:
        if not base.exists(): continue
        for pattern in ('college_xi*/college_xi_d1.sqlite3','college_xi*/college_xi.db'):
            found=sorted(base.glob(pattern),key=lambda x:x.stat().st_mtime if x.exists() else 0,reverse=True)
            for p in found:
                try:r=p.resolve()
                except Exception:continue
                if p.exists() and r not in seen:
                    seen.add(r); yield p


def find_legacy_db():
    """Pick the earlier local database with the largest useful player/game footprint."""
    import sqlite3
    current_path=(Path(__file__).resolve().parents[1]/'college_xi_d1.sqlite3').resolve()
    best=None;best_score=-1
    for p in _candidate_databases():
        try:
            if p.resolve()==current_path: continue
            c=sqlite3.connect(f'file:{p.resolve()}?mode=ro',uri=True)
            tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            players=c.execute('SELECT COUNT(*) FROM players').fetchone()[0] if 'players' in tables else 0
            games=c.execute('SELECT COUNT(*) FROM games').fetchone()[0] if 'games' in tables else 0
            stats=c.execute('SELECT COUNT(*) FROM player_season_stats').fetchone()[0] if 'player_season_stats' in tables else 0
            c.close()
            score=players*10+stats*3+games
            if score>best_score: best,best_score=p,score
        except Exception:
            continue
    return best


def auto_import_if_useful():
    """Read-only import from the richest earlier College XI DB when this DB is sparse."""
    try:
        current=row("SELECT COUNT(*) n FROM players")['n']
        current_games=row("SELECT COUNT(*) n FROM games")['n']
        if current > 500 and current_games > 500:
            return {"attempted":False,"reason":"database already substantially populated"}
        legacy=find_legacy_db()
        if not legacy:return {"attempted":False,"reason":"earlier College XI database not found"}
        from tools.import_legacy import import_db
        return {"attempted":True,"path":str(legacy),"result":import_db(str(legacy), include_games=False)}
    except Exception as exc:
        return {"attempted":True,"error":str(exc)}
