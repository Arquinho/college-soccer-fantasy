import sqlite3
from contextlib import contextmanager
from config import DB_PATH

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school TEXT NOT NULL,
    abbreviation TEXT,
    conference TEXT,
    division TEXT NOT NULL DEFAULT 'D1',
    official_url TEXT,
    roster_url TEXT,
    schedule_url TEXT,
    stats_url TEXT,
    tds_slug TEXT,
    ncaa_slug TEXT,
    source_updated_at TEXT,
    UNIQUE(school)
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    school TEXT NOT NULL,
    position TEXT NOT NULL,
    class_year TEXT,
    jersey TEXT,
    previous_school TEXT,
    conference TEXT,
    division TEXT NOT NULL DEFAULT 'D1',
    price REAL NOT NULL DEFAULT 5.0,
    rating REAL NOT NULL DEFAULT 50.0,
    source_url TEXT,
    source_name TEXT,
    source_updated_at TEXT,
    UNIQUE(name, school, division)
);

CREATE TABLE IF NOT EXISTS coaches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    school TEXT NOT NULL,
    role TEXT NOT NULL,
    conference TEXT,
    division TEXT NOT NULL DEFAULT 'D1',
    price REAL NOT NULL DEFAULT 5.0,
    source_url TEXT,
    UNIQUE(name, school, division, role)
);

CREATE TABLE IF NOT EXISTS player_season_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    games INTEGER NOT NULL DEFAULT 0,
    starts INTEGER NOT NULL DEFAULT 0,
    minutes REAL NOT NULL DEFAULT 0,
    goals INTEGER NOT NULL DEFAULT 0,
    assists INTEGER NOT NULL DEFAULT 0,
    points INTEGER NOT NULL DEFAULT 0,
    shots INTEGER NOT NULL DEFAULT 0,
    shots_on_goal INTEGER NOT NULL DEFAULT 0,
    yellow_cards INTEGER NOT NULL DEFAULT 0,
    red_cards INTEGER NOT NULL DEFAULT 0,
    game_winners INTEGER NOT NULL DEFAULT 0,
    saves INTEGER NOT NULL DEFAULT 0,
    goals_against INTEGER NOT NULL DEFAULT 0,
    shutouts REAL NOT NULL DEFAULT 0,
    source_url TEXT,
    source_name TEXT,
    source_updated_at TEXT,
    UNIQUE(player_id, season),
    FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_date TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    status TEXT NOT NULL DEFAULT 'scheduled',
    conference_game INTEGER NOT NULL DEFAULT 0,
    venue TEXT,
    division TEXT NOT NULL DEFAULT 'D1',
    source_url TEXT,
    source_name TEXT,
    source_updated_at TEXT,
    start_time TEXT,
    current_period TEXT,
    contest_clock TEXT,
    external_id TEXT,
    home_conference TEXT,
    away_conference TEXT,
    UNIQUE(game_date, home_team, away_team, division)
);

CREATE TABLE IF NOT EXISTS rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ranking_date TEXT NOT NULL,
    source TEXT NOT NULL,
    rank INTEGER NOT NULL,
    school TEXT NOT NULL,
    overall_record TEXT,
    conference_record TEXT,
    score REAL,
    rank_label TEXT,
    previous TEXT,
    first_votes INTEGER,
    total_points REAL,
    source_updated_text TEXT,
    division TEXT NOT NULL DEFAULT 'D1',
    source_url TEXT,
    UNIQUE(ranking_date, source, rank, division)
);

CREATE TABLE IF NOT EXISTS standings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    conference TEXT NOT NULL,
    school TEXT NOT NULL,
    conference_record TEXT,
    overall_record TEXT,
    source TEXT NOT NULL,
    division TEXT NOT NULL DEFAULT 'D1',
    source_url TEXT,
    UNIQUE(snapshot_date, conference, school, source, division)
);

CREATE TABLE IF NOT EXISTS player_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ranking_date TEXT NOT NULL,
    source TEXT NOT NULL,
    category TEXT NOT NULL,
    rank INTEGER NOT NULL,
    name TEXT NOT NULL,
    school TEXT,
    conference TEXT,
    position TEXT,
    division TEXT NOT NULL DEFAULT 'D1',
    source_url TEXT,
    UNIQUE(ranking_date, source, category, rank, division)
);

CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'all',
    source TEXT NOT NULL,
    url TEXT,
    image_url TEXT,
    division TEXT NOT NULL DEFAULT 'ALL',
    published_at TEXT,
    updated_at TEXT,
    icon TEXT,
    UNIQUE(title, source)
);


CREATE TABLE IF NOT EXISTS stat_leaders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    division TEXT NOT NULL,
    category TEXT NOT NULL,
    rank INTEGER,
    name TEXT NOT NULL,
    school TEXT,
    class_year TEXT,
    games REAL,
    value REAL NOT NULL,
    conference TEXT,
    source_url TEXT,
    source_name TEXT NOT NULL DEFAULT 'NCAA',
    UNIQUE(snapshot_date, division, category, name, school)
);

CREATE TABLE IF NOT EXISTS source_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    entity TEXT NOT NULL,
    status TEXT NOT NULL,
    detail TEXT,
    checked_at TEXT NOT NULL
);

"""


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db():
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _columns(conn, table):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def _migrate(conn):
    # Keep older local College XI databases compatible with the current app.
    # fast_bootstrap.py can intentionally reuse a richer legacy roster DB, so
    # every column the current code reads must be added before schedule overlay.
    migrations = {
        'teams': [
            ('abbreviation','TEXT'), ('conference','TEXT'),
            ('division', "TEXT NOT NULL DEFAULT 'D1'"),
            ('official_url','TEXT'), ('roster_url','TEXT'), ('schedule_url','TEXT'),
            ('stats_url','TEXT'), ('tds_slug','TEXT'), ('ncaa_slug','TEXT'),
            ('source_updated_at','TEXT'),
        ],
        'players': [
            ('class_year','TEXT'), ('jersey','TEXT'), ('previous_school','TEXT'),
            ('conference','TEXT'), ('division', "TEXT NOT NULL DEFAULT 'D1'"),
            ('price','REAL NOT NULL DEFAULT 5.0'), ('rating','REAL NOT NULL DEFAULT 50.0'),
            ('source_url','TEXT'), ('source_name','TEXT'), ('source_updated_at','TEXT'),
        ],
        'coaches': [
            ('conference','TEXT'), ('division', "TEXT NOT NULL DEFAULT 'D1'"),
            ('price','REAL NOT NULL DEFAULT 5.0'), ('source_url','TEXT'),
        ],
        'player_season_stats': [
            ('games','INTEGER NOT NULL DEFAULT 0'), ('starts','INTEGER NOT NULL DEFAULT 0'),
            ('minutes','REAL NOT NULL DEFAULT 0'), ('goals','INTEGER NOT NULL DEFAULT 0'),
            ('assists','INTEGER NOT NULL DEFAULT 0'), ('points','INTEGER NOT NULL DEFAULT 0'),
            ('shots','INTEGER NOT NULL DEFAULT 0'), ('shots_on_goal','INTEGER NOT NULL DEFAULT 0'),
            ('yellow_cards','INTEGER NOT NULL DEFAULT 0'), ('red_cards','INTEGER NOT NULL DEFAULT 0'),
            ('game_winners','INTEGER NOT NULL DEFAULT 0'), ('saves','INTEGER NOT NULL DEFAULT 0'),
            ('goals_against','INTEGER NOT NULL DEFAULT 0'), ('shutouts','REAL NOT NULL DEFAULT 0'),
            ('source_url','TEXT'), ('source_name','TEXT'), ('source_updated_at','TEXT'),
        ],
        # Legacy v4/v7 databases can have a much smaller games table.  Keep
        # every non-key field here because fast_bootstrap may reuse that database
        # before the verified schedule is overlaid.
        'games': [
            ('home_score','INTEGER'), ('away_score','INTEGER'),
            ('status', "TEXT NOT NULL DEFAULT 'scheduled'"),
            ('conference_game','INTEGER NOT NULL DEFAULT 0'), ('venue','TEXT'),
            ('division', "TEXT NOT NULL DEFAULT 'D1'"),
            ('source_url','TEXT'), ('source_name','TEXT'), ('source_updated_at','TEXT'),
            ('start_time','TEXT'), ('current_period','TEXT'), ('contest_clock','TEXT'),
            ('external_id','TEXT'), ('home_conference','TEXT'), ('away_conference','TEXT'),
        ],
        'rankings': [
            ('overall_record','TEXT'), ('conference_record','TEXT'), ('score','REAL'),
            ('rank_label','TEXT'), ('previous','TEXT'), ('first_votes','INTEGER'),
            ('total_points','REAL'), ('source_updated_text','TEXT'),
            ('division', "TEXT NOT NULL DEFAULT 'D1'"), ('source_url','TEXT'),
        ],
        'standings': [
            ('conference_record','TEXT'), ('overall_record','TEXT'), ('source','TEXT'),
            ('division', "TEXT NOT NULL DEFAULT 'D1'"), ('source_url','TEXT'),
        ],
        'player_rankings': [
            ('school','TEXT'), ('conference','TEXT'), ('position','TEXT'),
            ('division', "TEXT NOT NULL DEFAULT 'D1'"), ('source_url','TEXT'),
        ],
        'news': [
            ('category', "TEXT NOT NULL DEFAULT 'all'"), ('url','TEXT'),
            ('image_url','TEXT'), ('division', "TEXT NOT NULL DEFAULT 'ALL'"),
            ('published_at','TEXT'), ('updated_at','TEXT'), ('icon','TEXT'),
        ],
    }
    for table, cols in migrations.items():
        existing = _columns(conn, table)
        for name, ddl in cols:
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def init_db():
    with db() as conn:
        # Create missing tables first.  Indexes are intentionally created only
        # after _migrate(): an older local database may already have a table but
        # not yet have the columns referenced by the current indexes.
        conn.executescript(SCHEMA)
        _migrate(conn)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stat_leaders ON stat_leaders(division, category, value DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_players_market ON players(division, conference, school, position, price)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stats_player_season ON player_season_stats(player_id, season)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_games_date_v3 ON games(division, game_date, status)")


def rows(sql, params=()):
    with db() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def row(sql, params=()):
    with db() as conn:
        r = conn.execute(sql, params).fetchone()
        return dict(r) if r else None
