from flask import Flask, jsonify, request, send_from_directory
from datetime import date, timedelta
import threading
import os
from config import PORT, HOST
from database import init_db, rows, row, db
from services.sync import sync_tds_rankings, sync_tds_extended, sync_tds_standings_only, recalc_prices, sync_registry, sync_ncaa_stat_tables, sync_ncaa_game_history, sync_ncaa_season_schedule_fast, sync_registered_school_schedules, sync_ncaa_rankings, sync_ncaa_standings, sync_ncaa_upcoming_games, sync_all_school_stats, _team_key
from services.news import sync_news
from services.startup import auto_import_if_useful
from services.conferences import canonicalize_conference, fallback_conference_for_school

app = Flask(__name__, static_folder='static', static_url_path='')
# Ensure schema/migrations exist for both local runs and WSGI deployment.
init_db()
STARTUP_STATUS = {}
STATS_JOBS = {}
STATS_LOCK = threading.Lock()
SCHEDULE_JOBS = {}
SCHEDULE_LOCK = threading.Lock()

def _repair_conference_cache():
    """Normalize cached soccer conference labels without doing any network I/O."""
    try:
        with db() as conn:
            for table in ('teams','players','coaches'):
                for r in conn.execute(f"SELECT id,school,conference,division FROM {table}").fetchall():
                    conf=(fallback_conference_for_school(r['school'],r['division'])
                          or canonicalize_conference(r['conference']))
                    if conf and conf != r['conference']:
                        conn.execute(f"UPDATE {table} SET conference=? WHERE id=?",(conf,r['id']))
            for r in conn.execute("SELECT id,home_team,away_team,home_conference,away_conference,division FROM games").fetchall():
                hc=fallback_conference_for_school(r['home_team'],r['division']) or canonicalize_conference(r['home_conference'])
                ac=fallback_conference_for_school(r['away_team'],r['division']) or canonicalize_conference(r['away_conference'])
                conn.execute("UPDATE games SET home_conference=COALESCE(?,home_conference), away_conference=COALESCE(?,away_conference) WHERE id=?",(hc,ac,r['id']))
            for r in conn.execute("SELECT id,school,conference,division FROM stat_leaders").fetchall():
                conf=fallback_conference_for_school(r['school'],r['division']) or canonicalize_conference(r['conference'])
                if conf: conn.execute("UPDATE stat_leaders SET conference=? WHERE id=?",(conf,r['id']))
            for r in conn.execute("SELECT id,school,conference,division FROM standings").fetchall():
                conf=fallback_conference_for_school(r['school'],r['division']) or canonicalize_conference(r['conference'])
                if conf: conn.execute("UPDATE standings SET conference=? WHERE id=?",(conf,r['id']))
    except Exception:
        pass


WORLDS = {
    'D1': {'label':'NCAA D1','budget':120.0,'source':'https://www.ncaa.com/sports/soccer-men/d1'},
    'D2': {'label':'NCAA D2','budget':120.0,'source':'https://www.ncaa.com/sports/soccer-men/d2'},
    'D3': {'label':'NCAA D3','budget':120.0,'source':'https://www.ncaa.com/sports/soccer-men/d3'},
    'NAIA': {'label':'NAIA','budget':120.0,'source':'https://www.naia.org/sports/mens-soccer/'},
    'NJCAA1': {'label':'NJCAA D1','budget':120.0,'source':'https://www.njcaa.org/sports/msoc/index'},
}

def world_arg():
    w = request.args.get('division','D1')
    return w if w in WORLDS else 'D1'

def player_query(division, where='', params=()):
    sql = """SELECT p.*, s.games, s.starts, s.minutes, s.goals, s.assists, s.points,
             s.shots, s.shots_on_goal, s.yellow_cards, s.red_cards, s.game_winners,
             s.saves, s.goals_against, s.shutouts,
             s.source_url AS stats_source_url, s.source_name AS stats_source_name, s.source_updated_at AS stats_source_updated_at
             FROM players p LEFT JOIN player_season_stats s ON s.player_id=p.id AND s.season=2026
             WHERE p.division=?"""
    all_params = [division]
    if where:
        sql += ' AND ' + where
        all_params.extend(params)
    sql += ' ORDER BY p.price DESC,p.name'
    return rows(sql, tuple(all_params))

@app.route('/')
def index(): return send_from_directory('static','index.html')

@app.route('/api/health')
def api_health():
    try:
        db_ok = row("SELECT 1 ok")
        return jsonify({'ok': True, 'season': 2026, 'database': bool(db_ok), 'worlds': list(WORLDS.keys())})
    except Exception as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 500

@app.route('/api/meta')
def meta():
    return jsonify({'season':2026,'worlds':WORLDS,'login':True,'realMoney':False,'startup':STARTUP_STATUS})

@app.route('/api/players')
def api_players():
    div = world_arg(); clauses=[]; params=[]
    for field,qname in [('p.position','position'),('p.conference','conference'),('p.school','school')]:
        v=request.args.get(qname)
        if v and v!='all': clauses.append(f'{field}=?'); params.append(v)
    q=request.args.get('q','').strip().lower()
    if q: clauses.append('(lower(p.name) LIKE ? OR lower(p.school) LIKE ?)'); params += [f'%{q}%',f'%{q}%']
    return jsonify(player_query(div,' AND '.join(clauses),tuple(params)))

@app.route('/api/players/<int:player_id>')
def api_player(player_id):
    p=row('SELECT * FROM players WHERE id=?',(player_id,))
    if not p:return jsonify({'error':'not found'}),404
    p['seasons']=rows('SELECT * FROM player_season_stats WHERE player_id=? ORDER BY season DESC',(player_id,))
    return jsonify(p)


@app.route('/api/prospects')
def api_prospects():
    div=world_arg(); limit=min(10,max(1,int(request.args.get('limit',5))))
    # Tiny cache-first query for the dashboard. Prefer verified player season stats.
    data=rows("""SELECT p.id,p.name,p.school,p.position,p.conference,p.price,p.rating,
                       COALESCE(s.minutes,0) minutes,COALESCE(s.goals,0) goals,COALESCE(s.assists,0) assists,
                       COALESCE(s.saves,0) saves,COALESCE(s.shutouts,0) shutouts
                FROM players p LEFT JOIN player_season_stats s ON s.player_id=p.id AND s.season=2026
                WHERE p.division=?
                ORDER BY (COALESCE(s.goals,0)*8 + COALESCE(s.assists,0)*5 + COALESCE(s.saves,0)*0.35 + COALESCE(s.shutouts,0)*4 + COALESCE(s.minutes,0)/90.0) DESC, p.rating DESC
                LIMIT ?""",(div,limit))
    if not data:
        leaders=rows("""SELECT name,school,conference,value goals,rank FROM stat_leaders
                         WHERE division=? AND category='goals' ORDER BY value DESC,rank ASC LIMIT ?""",(div,limit))
        data=[dict(x,position='FW',price=round(5.5+max(0,10-(x.get('rank') or 10))*.45,1),rating=max(75,min(99,99-(x.get('rank') or 1)*2))) for x in leaders]
    return jsonify(data)

@app.route('/api/coaches')
def api_coaches():
    div=world_arg(); school=request.args.get('school'); role=request.args.get('role')
    clauses=['division=?'];params=[div]
    if school:clauses.append('school=?');params.append(school)
    if role:
        if role=='Assistant Coach': clauses.append("role IN ('Assistant Coach','Associate Head Coach','Associate Head Coach/Assistant Coach')")
        else: clauses.append('role=?'); params.append(role)
    return jsonify(rows('SELECT * FROM coaches WHERE '+' AND '.join(clauses)+' ORDER BY price DESC,name',tuple(params)))

@app.route('/api/games')
def api_games():
    div=world_arg()
    since=request.args.get('since','2026-08-01')
    until=request.args.get('until','2026-12-31')
    status=(request.args.get('status') or '').strip().lower()
    clauses=['division=?','game_date>=?','game_date<=?']; params=[div,since,until]
    if status=='finished': clauses.append("lower(status) LIKE 'final%'")
    elif status=='live': clauses.append("lower(status) LIKE 'live%'")
    elif status=='scheduled': clauses.append("lower(status) LIKE 'scheduled%'")
    data=rows("SELECT * FROM games WHERE "+" AND ".join(clauses)+" ORDER BY game_date ASC, COALESCE(start_time,'') ASC, id ASC",tuple(params))
    return jsonify(data)

@app.route('/api/upcoming-games')
def api_upcoming_games():
    """Fast NEXT MATCH endpoint.

    Normal reads are database-only. Add ?refresh=1 only for an explicit/manual
    public-source refresh so opening the market never waits on NCAA.com.
    """
    div=world_arg(); days=min(60,max(3,int(request.args.get('days',30))))
    refresh=request.args.get('refresh') in ('1','true','yes')
    result={'ok':True,'items':[],'cached':True}
    if refresh and div in ('D1','D2','D3'):
        try:
            result=sync_ncaa_upcoming_games(div,days=days)
        except Exception as exc:
            result={'ok':False,'error':str(exc),'items':[],'cached':False}
    today=date.today()
    until=(today+timedelta(days=days)).isoformat()
    stored=rows("SELECT * FROM games WHERE division=? AND game_date>=? AND game_date<=? ORDER BY game_date,COALESCE(start_time,''),id LIMIT 800",(div,today.isoformat(),until))
    return jsonify({'ok':bool(result.get('ok')),'sync':result,'games':stored})

@app.route('/api/scoreboard-preview')
def api_scoreboard_preview():
    """Return today's scoreboard immediately from cache.

    ?refresh=1 performs the external NCAA refresh. This keeps dashboard navigation
    instant while still allowing live scores to update in the background.
    """
    div=world_arg(); refresh=request.args.get('refresh') in ('1','true','yes')
    if refresh and div in ('D1','D2','D3'):
        today=date.today().isoformat()
        try:
            sync_ncaa_game_history(div,start_date=today,end_date=today,recalc=False)
        except Exception:
            pass
    data=rows("SELECT * FROM games WHERE division=? AND game_date=? ORDER BY CASE WHEN lower(status) LIKE 'live%' THEN 0 WHEN lower(status) LIKE 'scheduled%' THEN 1 ELSE 2 END, COALESCE(start_time,'')",(div,date.today().isoformat()))
    return jsonify(data)

@app.route('/api/rankings')
def api_rankings():
    div=world_arg(); source=request.args.get('source')
    if source and source != 'NCAA / United Soccer Coaches':
        latest=row('SELECT MAX(ranking_date) d FROM rankings WHERE source=? AND division=?',(source,div))
        if not latest or not latest['d']: return jsonify([])
        return jsonify(rows('SELECT * FROM rankings WHERE source=? AND division=? AND ranking_date=? ORDER BY rank,school',(source,div,latest['d'])))

    # Fast read path: never call public websites during a normal page load.
    # The Refresh button uses /api/sync-rankings when fresh public data is requested.
    official='NCAA / United Soccer Coaches'
    latest=row('SELECT MAX(ranking_date) d FROM rankings WHERE division=? AND source=?',(div,official))
    if not latest or not latest.get('d'): return jsonify([])
    return jsonify(rows('SELECT * FROM rankings WHERE division=? AND source=? AND ranking_date=? ORDER BY rank,school',(div,official,latest['d'])))

@app.route('/api/ranking-category')
def api_ranking_category():
    div=world_arg(); cat=request.args.get('category','national')
    conf=request.args.get('conference')
    conf = conf if conf and conf != 'all' else None

    if cat=='national':
        data=api_rankings().get_json()
        import re as _re
        def _nskool(v):
            v=_re.sub(r'[^a-z0-9 ]+',' ',str(v or '').lower())
            v=_re.sub(r'\b(university|college|the|of|at)\b',' ',v)
            return ' '.join(v.split())
        teams=rows("SELECT school,conference FROM teams WHERE division=?",(div,))
        standing_teams=rows("""SELECT school,conference FROM standings WHERE division=?
                              AND snapshot_date=(SELECT MAX(snapshot_date) FROM standings WHERE division=?)""",(div,div))
        team_conf={_nskool(x['school']):canonicalize_conference(x.get('conference')) for x in (teams+standing_teams) if x.get('conference')}
        enriched=[]
        for x in data:
            key=_nskool(x.get('school')); matched=team_conf.get(key)
            if not matched:
                for tk,tconf in team_conf.items():
                    if len(key)>=4 and len(tk)>=4 and (key in tk or tk in key): matched=tconf; break
            matched=fallback_conference_for_school(x.get('school'),div) or canonicalize_conference(matched)
            enriched.append(dict(x,conference=matched))
        data=enriched
        if conf: data=[x for x in data if x.get('conference')==conf]
        return jsonify(data)

    if cat in ('scorers','assists','clean_sheets'):
        col={'scorers':'goals','assists':'assists','clean_sheets':'shutouts'}[cat]
        pos_clause=" AND p.position IN ('GK','DF')" if cat=='clean_sheets' else ''
        params=[div]
        conf_clause=''
        if conf:
            conf_clause=' AND p.conference=?'; params.append(conf)
        data=rows(f"""SELECT p.name,p.school,p.conference,p.position,p.class_year,
                     s.games games,s.minutes minutes,s.goals goals,s.assists assists,s.shutouts shutouts,p.source_url
                     FROM players p JOIN player_season_stats s ON s.player_id=p.id AND s.season=2026
                     WHERE p.division=? {pos_clause} {conf_clause}
                       AND COALESCE(s.{col},0) > 0
                     ORDER BY s.{col} DESC, COALESCE(s.minutes,0) DESC, p.name""",tuple(params))

        category_key={'scorers':'goals','assists':'assists','clean_sheets':'shutouts'}[cat]
        latest=row("SELECT MAX(snapshot_date) d FROM stat_leaders WHERE division=? AND category=?",(div,category_key))
        # Normal browsing reads the complete cached NCAA leaderboard.  There is
        # intentionally no top-100 cap: every athlete with a positive goal or
        # assist value belongs in these lists.
        if latest and latest.get('d'):
            extra_params=[div,category_key,latest['d']]
            extra_where=''
            if conf:
                extra_where=' AND sl.conference=?'; extra_params.append(conf)
            extra=rows(f"""SELECT sl.rank,sl.name,sl.school,COALESCE(p.conference,sl.conference) conference,
                          p.position,COALESCE(p.class_year,sl.class_year) class_year,sl.games,
                          s.minutes minutes,
                          CASE WHEN sl.category='goals' THEN sl.value ELSE 0 END goals,
                          CASE WHEN sl.category='assists' THEN sl.value ELSE 0 END assists,
                          CASE WHEN sl.category='shutouts' THEN sl.value ELSE 0 END shutouts,
                          sl.source_url
                          FROM stat_leaders sl
                          LEFT JOIN players p ON p.division=sl.division AND lower(p.name)=lower(sl.name) AND lower(p.school)=lower(sl.school)
                          LEFT JOIN player_season_stats s ON s.player_id=p.id AND s.season=2026
                          WHERE sl.division=? AND sl.category=? AND sl.snapshot_date=? {extra_where}
                          ORDER BY sl.value DESC, COALESCE(sl.rank,9999), sl.name""",tuple(extra_params))
            # Fill spelling/alias mismatches from the imported official roster.
            if any(x.get('position') is None or x.get('minutes') is None for x in extra):
                import re as _re
                from difflib import SequenceMatcher as _SequenceMatcher
                pool=rows("""SELECT p.name,p.school,p.conference,p.position,p.class_year,s.minutes
                             FROM players p LEFT JOIN player_season_stats s ON s.player_id=p.id AND s.season=2026
                             WHERE p.division=?""",(div,))
                def _pkey(v): return _re.sub(r'[^a-z0-9]','',str(v or '').lower())
                by_team={}
                for pr in pool: by_team.setdefault(_team_key(pr.get('school')),[]).append(pr)
                for x in extra:
                    if x.get('position') is not None and x.get('minutes') is not None: continue
                    candidates=by_team.get(_team_key(x.get('school')),[])
                    target=None;score=0.0
                    nk=_pkey(x.get('name'))
                    for pr in candidates:
                        s=_SequenceMatcher(None,nk,_pkey(pr.get('name'))).ratio()
                        if s>score: score=s;target=pr
                    if target and score>=.90:
                        x['position']=x.get('position') or target.get('position')
                        x['class_year']=x.get('class_year') or target.get('class_year')
                        x['conference']=x.get('conference') or target.get('conference')
                        if x.get('minutes') is None: x['minutes']=target.get('minutes')
            data.extend(extra)

        # Collapse source/display aliases such as Liberty / Liberty University,
        # Longwood / Longwood University, etc.  One athlete appears exactly once.
        import re as _re
        def _name_key(v): return _re.sub(r'[^a-z0-9]','',str(v or '').lower())
        merged={}
        for x in data:
            key=(_name_key(x.get('name')),_team_key(x.get('school')))
            if not key[0] or not key[1]:
                continue
            cur=merged.get(key)
            if cur is None:
                merged[key]=dict(x); continue
            xv=float(x.get(col) or 0); cv=float(cur.get(col) or 0)
            # Keep the strongest verified statistic, while enriching the row
            # with whichever source has position/minutes/conference metadata.
            if xv>cv:
                base=dict(x); other=cur
            else:
                base=cur; other=x
            for field in ('position','class_year','conference','minutes','games','source_url','rank'):
                if base.get(field) in (None,'') and other.get(field) not in (None,''):
                    base[field]=other.get(field)
            base[col]=max(xv,cv)
            merged[key]=base
        data=sorted(merged.values(),key=lambda x:(-float(x.get(col) or 0),-float(x.get('minutes') or 0),x.get('name') or ''))
        return jsonify(data)

    if cat=='defenses':
        games=rows("SELECT home_team,away_team,home_score,away_score FROM games WHERE division=? AND home_score IS NOT NULL AND away_score IS NOT NULL",(div,))
        team_conf={x['school']:x.get('conference') for x in rows("SELECT school,conference FROM teams WHERE division=?",(div,))}
        agg={}
        for g in games:
            for team,ga in [(g['home_team'],g['away_score']),(g['away_team'],g['home_score'])]:
                if conf and team_conf.get(team)!=conf: continue
                item=agg.setdefault(team,{'school':team,'conference':team_conf.get(team),'games':0,'goals_against':0,'clean_sheets':0})
                item['games']+=1; item['goals_against']+=int(ga or 0); item['clean_sheets']+=1 if int(ga or 0)==0 else 0
        out=sorted(agg.values(),key=lambda x:(x['goals_against']/max(1,x['games']),-x['clean_sheets'],x['school']))
        for x in out: x['gaa']=round(x['goals_against']/max(1,x['games']),2)
        return jsonify(out[:100])
    return jsonify([])

@app.route('/api/standings')
def api_standings():
    div=world_arg();conf=(request.args.get('conference') or 'all').strip()
    exists=row("SELECT COUNT(DISTINCT conference) n FROM standings WHERE division=?",(div,))
    min_expected=15 if div=='D1' else 5
    if (not exists or int(exists.get('n') or 0)<min_expected) and div in ('D1','D2','D3'):
        result={'ok':False}
        try: result=sync_ncaa_standings(div)
        except Exception: pass
        if div=='D1' and not result.get('ok'):
            try: sync_tds_standings_only()
            except Exception: pass
        _repair_conference_cache()
    if conf and conf!='all':
        conf=canonicalize_conference(conf) or conf
        latest=row('SELECT MAX(snapshot_date) d FROM standings WHERE conference=? AND division=?',(conf,div))
        if latest and latest['d']:
            return jsonify(rows('SELECT * FROM standings WHERE conference=? AND division=? AND snapshot_date=? ORDER BY id',(conf,div,latest['d'])))
        return jsonify([])
    # All conferences: latest verified snapshot for each conference.
    return jsonify(rows("""SELECT s.* FROM standings s
        JOIN (SELECT conference,MAX(snapshot_date) d FROM standings WHERE division=? GROUP BY conference) latest
          ON latest.conference=s.conference AND latest.d=s.snapshot_date
        WHERE s.division=? ORDER BY lower(s.conference),s.id""",(div,div)))

@app.route('/api/ranking-conferences')
def api_ranking_conferences():
    """Return every verified conference currently known for a ranking world."""
    div=world_arg()
    found=set()
    queries=[
        ("SELECT DISTINCT conference c FROM standings WHERE division=? AND conference IS NOT NULL AND conference<>''", (div,)),
        ("SELECT DISTINCT conference c FROM teams WHERE division=? AND conference IS NOT NULL AND conference<>''", (div,)),
        ("SELECT DISTINCT conference c FROM players WHERE division=? AND conference IS NOT NULL AND conference<>''", (div,)),
        ("SELECT DISTINCT conference c FROM stat_leaders WHERE division=? AND conference IS NOT NULL AND conference<>''", (div,)),
    ]
    for sql,params in queries:
        try:
            for x in rows(sql,params):
                if x.get('c'):
                    c=canonicalize_conference(x['c'])
                    if c: found.add(c)
        except Exception:
            pass
    return jsonify(sorted(found,key=lambda x:x.lower()))


@app.route('/api/sync-rankings',methods=['POST'])
def api_sync_rankings():
    """Refresh only ranking/leaderboard data, without running the heavier game sync."""
    payload=request.get_json(silent=True) or {}
    div=payload.get('division') or request.args.get('division','D1')
    out={}; ok=False
    if div in ('D1','D2','D3'):
        try:
            out['national']=sync_ncaa_rankings(div)
            ok=ok or bool(out['national'].get('ok'))
        except Exception as exc:
            out['national']={'ok':False,'error':str(exc)}
        # Men's-soccer conference standings repair current affiliations and power
        # the all-conference standings view. NCAA is preferred; TopDrawerSoccer
        # is a D-I fallback when NCAA does not expose a standings table.
        try:
            out['conference_standings']=sync_ncaa_standings(div)
            ok=ok or bool(out['conference_standings'].get('ok'))
        except Exception as exc:
            out['conference_standings']={'ok':False,'error':str(exc)}
        if div=='D1' and not out['conference_standings'].get('ok'):
            try:
                out['conference_fallback']=sync_tds_standings_only()
                ok=ok or bool(out['conference_fallback'].get('ok'))
            except Exception as exc:
                out['conference_fallback']={'ok':False,'error':str(exc)}
        _repair_conference_cache()
        try:
            out['player_leaders']=sync_ncaa_stat_tables(div,categories=['goals','assists'])
            ok=ok or any(v.get('ok') for v in out['player_leaders'].values() if isinstance(v,dict))
        except Exception as exc:
            out['player_leaders']={'ok':False,'error':str(exc)}
    else:
        return jsonify({'ok':False,'division':div,'error':'Live national ranking sync currently supports NCAA D1/D2/D3.'}),400
    return jsonify({'ok':ok,'division':div,'results':out})


@app.route('/api/news')
def api_news():
    div=world_arg(); limit=min(60,max(1,int(request.args.get('limit',30))))
    if request.args.get('refresh') in ('1','true','yes'):
        try: sync_news(div)
        except Exception: pass
    if div in ('D1','D2','D3'):
        return jsonify(rows("""SELECT * FROM news WHERE division=? AND source LIKE 'NCAA%'
                            ORDER BY COALESCE(published_at,updated_at) DESC,id DESC LIMIT ?""",(div,limit)))
    return jsonify(rows("""SELECT * FROM news WHERE division=?
                        ORDER BY COALESCE(published_at,updated_at) DESC,id DESC LIMIT ?""",(div,limit)))

@app.route('/api/filters')
def api_filters():
    div=world_arg(); conf=(request.args.get('conference') or '').strip(); school=(request.args.get('school') or '').strip()
    team_rows=rows("SELECT school,conference,abbreviation,ncaa_slug FROM teams WHERE division=? ORDER BY school",(div,))
    if not team_rows:
        team_rows=rows("SELECT DISTINCT school,conference,NULL abbreviation,NULL ncaa_slug FROM players WHERE division=? ORDER BY school",(div,))
    conferences=sorted({x.get('conference') for x in team_rows if x.get('conference')})
    if conf and conf!='all':
        schools=[x['school'] for x in team_rows if x.get('conference')==conf]
    else:
        schools=[x['school'] for x in team_rows]
    selected_conference=None
    if school and school!='all':
        rec=next((x for x in team_rows if (x.get('school') or '').lower()==school.lower()),None)
        selected_conference=rec.get('conference') if rec else None
    return jsonify({'conferences':conferences,'schools':schools,'selected_conference':selected_conference,'teams':team_rows})

@app.route('/api/dashboard')
def api_dashboard():
    div=world_arg()
    return jsonify({
        'players':row("SELECT COUNT(*) n FROM players WHERE division=?",(div,))['n'],
        'schools':row("SELECT COUNT(*) n FROM teams WHERE division=?",(div,))['n'],
        'coaches':row("SELECT COUNT(*) n FROM coaches WHERE division=?",(div,))['n'],
        'games':row("SELECT COUNT(*) n FROM games WHERE division=? AND game_date>='2026-08-01'",(div,))['n']
    })

@app.route('/api/game-coverage')
def api_game_coverage():
    div=world_arg()
    totals=row("SELECT COUNT(*) n FROM games WHERE division=?",(div,))["n"]
    teams=rows("SELECT school, COUNT(*) games FROM (SELECT home_team school FROM games WHERE division=? UNION ALL SELECT away_team school FROM games WHERE division=?) GROUP BY school ORDER BY school",(div,div))
    span=row("SELECT MIN(game_date) min_date, MAX(game_date) max_date FROM games WHERE division=?",(div,))
    marker=row("SELECT status,detail,checked_at FROM source_status WHERE source='NCAA.com via ncaa-api' AND entity=? ORDER BY id DESC LIMIT 1",(f'games:{div}:2026',))
    return jsonify({
        "division":div,
        "games":totals,
        "schools_with_games":len(teams),
        "by_school":teams,
        "min_date":span.get("min_date") if span else None,
        "max_date":span.get("max_date") if span else None,
        "full_season_synced":bool(marker and marker.get("status")=="ok" and any(tag in str(marker.get("detail") or "") for tag in ("final-prototype-v3","final-prototype-v2"))),
        "sync_status":marker
    })

@app.route('/api/player-stats-coverage')
def api_player_stats_coverage():
    div=world_arg()
    total=row("SELECT COUNT(*) n FROM players WHERE division=?",(div,))["n"]
    with_stats=row("""SELECT COUNT(*) n FROM players p JOIN player_season_stats s ON s.player_id=p.id AND s.season=2026
                       WHERE p.division=? AND COALESCE(s.source_url,'')<>''""",(div,))["n"]
    schools_total=row("SELECT COUNT(DISTINCT school) n FROM players WHERE division=?",(div,))["n"]
    schools_stats=row("""SELECT COUNT(DISTINCT p.school) n FROM players p JOIN player_season_stats s ON s.player_id=p.id AND s.season=2026
                          WHERE p.division=? AND COALESCE(s.source_url,'')<>''""",(div,))["n"]
    marker=row("SELECT status,detail,checked_at FROM source_status WHERE source='official_school_bulk' AND entity=? ORDER BY id DESC LIMIT 1",(f'player_stats:{div}:2026',))
    with STATS_LOCK: running=bool(STATS_JOBS.get(div) and STATS_JOBS[div].is_alive())
    return jsonify({'division':div,'players':total,'players_with_verified_stats':with_stats,'schools':schools_total,
                    'schools_with_verified_stats':schools_stats,'running':running,'sync_status':marker})


def _run_stats_job(div):
    try: sync_all_school_stats(div)
    finally:
        with STATS_LOCK: STATS_JOBS.pop(div,None)


@app.route('/api/sync-player-stats',methods=['POST'])
def api_sync_player_stats():
    payload=request.get_json(silent=True) or {}; div=payload.get('division') or world_arg()
    if div not in WORLDS:return jsonify({'ok':False,'error':'Unsupported world'}),400
    with STATS_LOCK:
        existing=STATS_JOBS.get(div)
        if existing and existing.is_alive():
            return jsonify({'ok':True,'started':False,'running':True,'division':div})
        t=threading.Thread(target=_run_stats_job,args=(div,),daemon=True,name=f'cxi-stats-{div}')
        STATS_JOBS[div]=t;t.start()
    return jsonify({'ok':True,'started':True,'running':True,'division':div})


@app.route('/api/sources')
def api_sources():
    return jsonify([
        {'world':'D1','name':'NCAA Division I Men’s Soccer','url':'https://www.ncaa.com/sports/soccer-men/d1','type':'official'},
        {'world':'D2','name':'NCAA Division II Men’s Soccer','url':'https://www.ncaa.com/sports/soccer-men/d2','type':'official'},
        {'world':'D3','name':'NCAA Division III Men’s Soccer','url':'https://www.ncaa.com/sports/soccer-men/d3','type':'official'},
        {'world':'NAIA','name':'NAIA Men’s Soccer','url':'https://www.naia.org/sports/mens-soccer/','type':'official'},
        {'world':'NJCAA1','name':'NJCAA Men’s Soccer','url':'https://www.njcaa.org/sports/msoc/index','type':'official'},
        {'world':'D1','name':'TopDrawerSoccer College Men','url':'https://www.topdrawersoccer.com/college-soccer/men','type':'enrichment'},
    ])

@app.route('/api/games-date')
def api_games_date():
    """Return one day's schedule, cache-first.

    Normal calls are SQLite-only and return instantly.  refresh=1 starts an
    exact-date refresh in the background.  refresh=1&wait=1 performs only the
    exact-date upstream request and returns the refreshed rows; it never launches
    a full-season crawl, so a clicked calendar day can fill quickly.
    """
    div=world_arg(); selected=(request.args.get('date') or date.today().isoformat()).strip()
    def cached():
        return rows("SELECT * FROM games WHERE division=? AND game_date=? ORDER BY CASE WHEN lower(status) LIKE 'live%' THEN 0 WHEN lower(status) LIKE 'scheduled%' THEN 1 ELSE 2 END, COALESCE(start_time,''), id",(div,selected))
    items=cached()
    refresh=request.args.get('refresh') in ('1','true','yes')
    wait=request.args.get('wait') in ('1','true','yes')
    def do_refresh():
        try:
            if div in ('D1','D2','D3'):
                # Always ask the selected NCAA date first.  This keeps past/live
                # score clicks fast and prevents a full-season crawl from blocking
                # the response.  Future scoreboard endpoints are not allowed to
                # erase a cached fixture list just because the live transport has
                # not published that date yet.
                try:
                    selected_day=date.fromisoformat(selected)
                except Exception:
                    selected_day=date.today()
                exact=sync_ncaa_game_history(div,start_date=selected,end_date=selected,recalc=False)
                fresh_count=row("SELECT COUNT(*) n FROM games WHERE division=? AND game_date=?",(div,selected)).get('n',0)
                season=None
                # Only a completely empty future date triggers a season fallback. A one-game
                # date can be legitimate and must not launch a full-season crawl
                # during calendar navigation.
                if selected_day>date.today() and int(fresh_count or 0)==0:
                    season=sync_ncaa_season_schedule_fast(div,year=selected_day.year,recalc=False)
                    fresh_count=row("SELECT COUNT(*) n FROM games WHERE division=? AND game_date=?",(div,selected)).get('n',0)
                return {'ok':bool(exact.get('ok') or (season and season.get('ok'))),'exact_date':exact,'season_warm':season,'stored_for_date':int(fresh_count or 0)}
            elif div in ('NAIA','NJCAA1'):
                return sync_registered_school_schedules(div)
        except Exception as exc:
            return {'ok':False,'error':str(exc)}
        return {'ok':False,'error':'Unsupported world'}
    if refresh and wait:
        result=do_refresh()
        fresh=cached()
        return jsonify({'ok':True,'division':div,'date':selected,'items':fresh,'count':len(fresh),'cached':False,'refresh_started':False,'refresh_result':result})
    if refresh:
        threading.Thread(target=do_refresh,daemon=True,name=f'cfv1-date-{div}-{selected}').start()
    return jsonify({'ok':True,'division':div,'date':selected,'items':items,'count':len(items),'cached':True,'refresh_started':refresh})

@app.route('/api/ncaa-scoreboard-date')
def api_ncaa_scoreboard_date():
    div=world_arg(); selected=(request.args.get('date') or date.today().isoformat()).strip()
    if div not in ('D1','D2','D3'):
        return jsonify({'ok':False,'division':div,'date':selected,'items':[],'error':'Live NCAA scoreboard is available for NCAA D1/D2/D3 worlds.'}),400
    try:
        result=sync_ncaa_game_history(div,start_date=selected,end_date=selected,recalc=False)
        if not result.get('ok'):
            return jsonify({'ok':False,'division':div,'date':selected,'items':[],'error':result.get('error') or result.get('failures')}),502
        items=rows("SELECT * FROM games WHERE division=? AND game_date=? ORDER BY CASE WHEN lower(status) LIKE 'live%' THEN 0 WHEN lower(status) LIKE 'scheduled%' THEN 1 ELSE 2 END, COALESCE(start_time,''), id",(div,selected))
        return jsonify({'ok':True,'division':div,'date':selected,'items':items,'count':len(items),'source':'NCAA.com'})
    except Exception as exc:
        return jsonify({'ok':False,'division':div,'date':selected,'items':[],'error':str(exc)}),502

@app.route('/api/sync-games',methods=['POST'])
def api_sync_games():
    payload=request.get_json(silent=True) or {}
    div=payload.get('division') or request.args.get('division','D1')
    start_date=payload.get('start_date') or request.args.get('start_date','2026-08-01')
    end_date=payload.get('end_date') or request.args.get('end_date') or '2026-12-31'
    background=bool(payload.get('background')) or request.args.get('background') in ('1','true','yes')

    def do_sync():
        if div in ('D1','D2','D3'):
            # A full-range request now warms the NCAA division-wide season cache.
            # Exact-date requests still use the date scoreboard for current state.
            season_result=None
            if start_date != end_date:
                try: season_result=sync_ncaa_season_schedule_fast(div,year=int(start_date[:4] or 2026),recalc=False)
                except Exception as exc: season_result={'ok':False,'error':str(exc)}
            selected = start_date if start_date == end_date else date.today().isoformat()
            ncaa_result=sync_ncaa_game_history(div,start_date=selected,end_date=selected,recalc=False)
            # School schedules remain an enrichment/fallback, never the primary
            # source for deciding which games exist in the division calendar.
            school_result=sync_registered_school_schedules(div)
            return {
                'ok': bool(ncaa_result.get('ok') or (season_result or {}).get('ok') or school_result.get('ok')),
                'ncaa': ncaa_result,
                'season_schedule': season_result,
                'school_schedules': school_result,
            }
        if div in ('NAIA','NJCAA1'):
            return sync_registered_school_schedules(div)
        return {'ok':False,'division':div,'error':'Unsupported world'}

    def coverage_payload(result):
        coverage=row("SELECT COUNT(*) n FROM games WHERE division=?",(div,))['n']
        schools=row("SELECT COUNT(DISTINCT school) n FROM (SELECT home_team school FROM games WHERE division=? UNION SELECT away_team school FROM games WHERE division=?)",(div,div))['n']
        return {'ok':bool(result.get('ok')),'division':div,'result':result,'coverage':{'games':coverage,'schools':schools}}

    if background:
        with SCHEDULE_LOCK:
            existing=SCHEDULE_JOBS.get(div)
            if existing and existing.is_alive():
                return jsonify({'ok':True,'division':div,'started':False,'running':True})
            def worker():
                try:
                    do_sync()
                finally:
                    with SCHEDULE_LOCK:
                        SCHEDULE_JOBS.pop(div,None)
            t=threading.Thread(target=worker,daemon=True,name=f'cfv1-schedule-{div}')
            SCHEDULE_JOBS[div]=t
            t.start()
        return jsonify({'ok':True,'division':div,'started':True,'running':True})

    try:
        result=do_sync()
        if result.get('error')=='Unsupported world':
            return jsonify(result),400
        return jsonify(coverage_payload(result))
    except Exception as exc:
        return jsonify({'ok':False,'division':div,'error':str(exc)}),500

@app.route('/api/sync',methods=['POST'])
def api_sync():
    div=(request.get_json(silent=True) or {}).get('division') or request.args.get('division','D1')
    out={};ok=False
    try:
        out['news']=sync_news(div); ok=ok or out['news'].get('ok',False)
    except Exception as exc: out['news']={'ok':False,'error':str(exc)}
    if div in ('D1','D2','D3'):
        try:
            out['ncaa_rankings']=sync_ncaa_rankings(div)
            ok=ok or out['ncaa_rankings'].get('ok',False)
        except Exception as exc:
            out['ncaa_rankings']={'ok':False,'error':str(exc)}
        try:
            out['conference_standings']=sync_ncaa_standings(div)
            ok=ok or out['conference_standings'].get('ok',False)
        except Exception as exc:
            out['conference_standings']={'ok':False,'error':str(exc)}
        try:
            out['ncaa_stats']=sync_ncaa_stat_tables(div)
            ok=ok or any(v.get('ok') for v in out['ncaa_stats'].values())
        except Exception as exc:
            out['ncaa_stats']={'ok':False,'error':str(exc)}
        try:
            out['game_history']=sync_ncaa_game_history(div)
            ok=ok or out['game_history'].get('ok',False)
        except Exception as exc:
            out['game_history']={'ok':False,'error':str(exc)}
    if div=='D1':
        try:
            out['registry']=sync_registry(); ok=ok or out['registry'].get('ok',False)
        except Exception as exc: out['registry']={'ok':False,'error':str(exc)}
        try:
            out['rankings']=sync_tds_rankings(); ok=ok or out['rankings'].get('ok',False)
        except Exception as exc: out['rankings']={'ok':False,'error':str(exc)}
        try:
            out['extended']=sync_tds_extended(); ok=True
        except Exception as exc: out['extended']={'ok':False,'error':str(exc)}
        recalc_prices()
    elif div in ('NAIA','NJCAA1'):
        try:
            out['game_history']=sync_registered_school_schedules(div)
            ok=ok or out['game_history'].get('ok',False)
        except Exception as exc:
            out['game_history']={'ok':False,'error':str(exc)}
        out['world_data']={'ok':out['game_history'].get('ok',False),'detail':'Only official registered school schedule pages are imported. Missing schools remain visibly unsynced; no games or stats are fabricated.'}
    return jsonify({'ok':ok,'division':div,'results':out})


def _warm_delivery_cache():
    """Warm the four launch worlds after the HTTP server is available.

    The UI never waits on this work. NCAA D1/D2 use NCAA plus official school
    schedules; NAIA/NJCAA D1 use registered official athletics schedules and
    their organization news feeds. Data remains cached in SQLite for instant reads.
    """
    today=date.today()
    start=(today-timedelta(days=2)).isoformat()
    end=(today+timedelta(days=21)).isoformat()
    for div in ('D1','D2','NAIA','NJCAA1'):
        try: sync_news(div)
        except Exception: pass
        if div in ('D1','D2'):
            # First warm the complete 2026 NCAA schedule so future calendar
            # dates contain every school in the division, not only schools with
            # a manually discovered athletics schedule URL.
            try: sync_ncaa_season_schedule_fast(div,year=2026,recalc=False)
            except Exception: pass
            # Then refresh the immediate window for live/final status.
            for offset in range(0,8):
                d=(today+timedelta(days=offset)).isoformat()
                try: sync_ncaa_game_history(div,start_date=d,end_date=d,recalc=False)
                except Exception: pass
            try: sync_ncaa_rankings(div)
            except Exception: pass
            try: sync_ncaa_standings(div)
            except Exception: pass
            try: sync_ncaa_stat_tables(div)
            except Exception: pass
        try: sync_registered_school_schedules(div)
        except Exception: pass

        # D1 player ratings use exactly the same model for every school. Start
        # one bulk official-stat crawl after the fast NCAA tables are available;
        # the UI remains responsive while verified school stats fill in.
        if div=='D1':
            try:
                with STATS_LOCK:
                    running=bool(STATS_JOBS.get(div) and STATS_JOBS[div].is_alive())
                    if not running:
                        t=threading.Thread(target=_run_stats_job,args=(div,),daemon=True,name='cxi-stats-D1-auto')
                        STATS_JOBS[div]=t;t.start()
            except Exception:
                pass

def start_background_warm_cache():
    if os.environ.get('CXI_DISABLE_WARM_CACHE','0')=='1': return
    t=threading.Thread(target=_warm_delivery_cache,daemon=True,name='cxi-warm-cache')
    t.start()

if __name__=='__main__':
    # Fast boot: serve the UI immediately. Local database cleanup/valuation runs
    # in the background instead of blocking http://127.0.0.1:5012.
    init_db()
    with db() as conn:
        for table in ('games','rankings','standings','player_rankings'):
            try:
                conn.execute(f"UPDATE {table} SET division='D1' WHERE division IS NULL OR division='' ")
            except Exception:
                pass

    STARTUP_STATUS={'attempted':False,'reason':'fast startup; maintenance deferred'}

    def _background_maintenance():
        global STARTUP_STATUS
        try:
            _repair_conference_cache()
            recalc_prices()
            STARTUP_STATUS={'attempted':True,'ok':True,'reason':'background local maintenance complete'}
        except Exception as exc:
            STARTUP_STATUS={'attempted':True,'ok':False,'error':str(exc)}

    if os.getenv('CXI_BACKGROUND_MAINTENANCE','0') == '1':
        threading.Thread(target=_background_maintenance,daemon=True,name='cxi-local-maintenance').start()

    start_background_warm_cache()
    app.run(host=HOST,port=PORT,debug=os.getenv('FLASK_DEBUG','0') == '1',threaded=True)
