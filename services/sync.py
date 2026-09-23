from datetime import date, datetime, timezone
from database import db
from services.valuation import compute_player_value, compute_player_overall, compute_coach_value
from services.sources.school_sites import parse_sidearm_roster, parse_sidearm_stats, discover_related_urls, parse_official_schedule
from services.sources.topdrawer import fetch_tds_top25, fetch_tds_player_rankings, fetch_tds_freshman_rankings, fetch_tds_composite, fetch_tds_standings
from services.sources.ncaa import fetch_ncaa_goal_leaders, fetch_ncaa_stat_leaders, fetch_ncaa_scoreboard_history, fetch_ncaa_schedule_alt_games, fetch_ncaa_month_schedule_games, fetch_ncaa_rankings, fetch_ncaa_standings, fetch_ncaa_upcoming_window
from services.sources.d1_registry import fetch_registry
from services.conferences import canonicalize_conference, fallback_conference_for_school


def upsert_player(conn, p, division=None):
    conn.execute("""
        INSERT INTO players(name, school, position, class_year, jersey, previous_school,
                            conference, division, price, source_url, source_name, source_updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(name, school, division) DO UPDATE SET
            position=excluded.position,
            class_year=COALESCE(excluded.class_year, players.class_year),
            jersey=COALESCE(excluded.jersey, players.jersey),
            conference=COALESCE(excluded.conference, players.conference),
            source_url=excluded.source_url,
            source_name=excluded.source_name,
            source_updated_at=excluded.source_updated_at
    """, (
        p["name"], p["school"], p["position"], p.get("class_year"), p.get("jersey"), p.get("previous_school"),
        canonicalize_conference(p.get("conference")) or fallback_conference_for_school(p.get("school"), division or p.get("division") or "D1"), division or p.get("division") or "D1", 5.0, p.get("source_url"), p.get("source_name"), p.get("source_updated_at")
    ))



def sync_registry():
    result=fetch_registry()
    if not result.get("ok"):
        return result
    with db() as conn:
        for item in result.get("items",[]):
            conn.execute("""INSERT INTO teams(school,conference,division,source_updated_at)
                          VALUES(?,?,'D1',?)
                          ON CONFLICT(school) DO UPDATE SET conference=excluded.conference,source_updated_at=excluded.source_updated_at""",
                         (item["school"],item.get("conference"),item.get("updated_at")))
    return result

def sync_team_school_site(school, division=None, recalc=True):
    """Sync one school's official roster + cumulative 2026 stats.

    The same code path is used for every fantasy world. Only values actually
    published by the school are stored; unknown fields remain absent instead of
    being synthesized.
    """
    with db() as conn:
        if division:
            team = conn.execute("SELECT * FROM teams WHERE school=? AND division=?", (school, division)).fetchone()
        else:
            team = conn.execute("SELECT * FROM teams WHERE school=?", (school,)).fetchone()
        if not team:
            raise ValueError(f"Unknown team: {school}")
        team = dict(team)
    div = division or team.get("division") or "D1"
    start_url = team.get("stats_url") or team.get("roster_url") or team.get("official_url")
    if not start_url:
        raise ValueError(f"No official URL registered for {school}")
    urls = discover_related_urls(start_url)
    roster_url = team.get("roster_url") or urls.get("roster") or start_url
    stats_url = team.get("stats_url") or urls.get("stats")
    schedule_url = team.get("schedule_url") or urls.get("schedule")

    payload = parse_sidearm_roster(roster_url, school, team.get("conference"))
    stats = []
    if stats_url:
        candidates=[]
        def add_candidate(u):
            if u and u not in candidates: candidates.append(u)
        add_candidate(stats_url)
        if str(stats_url).rstrip('/').endswith('/2026'):
            add_candidate(str(stats_url).rstrip('/')[:-5])
        else:
            add_candidate(str(stats_url).rstrip('/')+'/2026')
        for candidate in candidates:
            try:
                parsed=parse_sidearm_stats(candidate)
                if parsed:
                    stats=parsed; stats_url=candidate; break
            except Exception:
                continue

    with db() as conn:
        conn.execute("""UPDATE teams SET roster_url=COALESCE(?,roster_url), stats_url=COALESCE(?,stats_url),
                     schedule_url=COALESCE(?,schedule_url), official_url=COALESCE(official_url,?), division=? WHERE school=?""",
                     (roster_url, stats_url, schedule_url, start_url, div, school))
        for pp in payload["players"]:
            pp["division"] = div
            upsert_player(conn, pp, div)
        for c in payload["coaches"]:
            role = c["role"]
            if role in ("Associate Head Coach", "Associate Head Coach/Assistant Coach"):
                role = "Assistant Coach"
            conn.execute("""
                INSERT INTO coaches(name, school, role, conference, division, source_url)
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(name, school, division, role) DO UPDATE SET
                    conference=excluded.conference, source_url=excluded.source_url
            """, (c["name"], school, role, c.get("conference"), div, c.get("source_url")))
        # Build one normalized name index for the school. Official stat pages
        # often use accents, punctuation, suffixes or "Last, First" formatting;
        # matching only exact strings was dropping valid rows for many schools.
        def person_key(value):
            import unicodedata, re as _re
            s=unicodedata.normalize('NFKD',str(value or '')).encode('ascii','ignore').decode('ascii').lower()
            s=_re.sub(r'\b(jr|sr|ii|iii|iv)\b',' ',s)
            return _re.sub(r'[^a-z0-9]','',s)
        school_players=conn.execute("SELECT id,name FROM players WHERE school=? AND division=?",(school,div)).fetchall()
        by_name={person_key(x['name']):x for x in school_players if person_key(x['name'])}
        for stat in stats:
            player = by_name.get(person_key(stat["name"]))
            if not player:
                continue
            conn.execute("""
                INSERT INTO player_season_stats(player_id, season, games, starts, minutes, goals, assists, points,
                    shots, shots_on_goal, yellow_cards, red_cards, game_winners, saves, goals_against, shutouts,
                    source_url, source_name, source_updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(player_id, season) DO UPDATE SET
                    games=excluded.games, starts=excluded.starts, minutes=excluded.minutes,
                    goals=excluded.goals, assists=excluded.assists, points=excluded.points,
                    shots=excluded.shots, shots_on_goal=excluded.shots_on_goal,
                    yellow_cards=excluded.yellow_cards, red_cards=excluded.red_cards,
                    game_winners=excluded.game_winners, saves=excluded.saves,
                    goals_against=excluded.goals_against, shutouts=excluded.shutouts,
                    source_url=excluded.source_url, source_name=excluded.source_name,
                    source_updated_at=excluded.source_updated_at
            """, (player["id"], 2026, stat["games"], stat["starts"], stat["minutes"], stat["goals"], stat["assists"], stat["points"],
                  stat["shots"], stat["shots_on_goal"], stat["yellow_cards"], stat["red_cards"], stat["game_winners"],
                  stat["saves"], stat["goals_against"], stat["shutouts"], stat["source_url"], stat["source_name"], stat["source_updated_at"]))
        conn.execute("DELETE FROM source_status WHERE source='official_school' AND entity=?", (f"stats:{div}:{school}",))
        conn.execute("INSERT INTO source_status(source,entity,status,detail,checked_at) VALUES(?,?,?,?,?)",
                     ('official_school', f"stats:{div}:{school}", 'ok' if stats else 'partial',
                      f"{len(stats)} cumulative-stat rows; {len(payload['players'])} roster players",
                      datetime.now(timezone.utc).isoformat(timespec='seconds')))
    if recalc:
        recalc_prices()
    return {"school": school, "division": div, "players": len(payload["players"]), "coaches": len(payload["coaches"]), "stats": len(stats), "stats_url": stats_url, "schedule_url": schedule_url}


def _backfill_team_sources_from_players(division):
    """Ensure every roster-derived school can participate in official-site sync.

    Legacy College XI imports often have a source URL on each player even when
    the corresponding teams row is incomplete. Promote one verified roster URL
    per school into teams so the bulk cumulative-stat sync is not limited to the
    handful of schools that already had a teams URL.
    """
    with db() as conn:
        rows_ = conn.execute("""SELECT school, MAX(conference) conference,
                              MAX(CASE WHEN source_url IS NOT NULL AND source_url<>'' THEN source_url END) source_url
                              FROM players WHERE division=? GROUP BY school""", (division,)).fetchall()
        for r in rows_:
            if not r['school']:
                continue
            conn.execute("""INSERT INTO teams(school,conference,division,official_url,roster_url)
                          VALUES(?,?,?,?,?)
                          ON CONFLICT(school) DO UPDATE SET
                          conference=COALESCE(teams.conference,excluded.conference),
                          division=COALESCE(teams.division,excluded.division),
                          official_url=COALESCE(teams.official_url,excluded.official_url),
                          roster_url=COALESCE(teams.roster_url,excluded.roster_url)""",
                         (r['school'],r['conference'],division,r['source_url'],r['source_url']))


def sync_all_school_stats(division, max_teams=None):
    """Walk every registered school in one world and ingest official cumulative stats.

    This is deliberately best-effort because athletics sites use several vendors.
    Progress is persisted in source_status so the UI can show verified coverage.
    """
    from database import rows
    _backfill_team_sources_from_players(division)
    teams = rows("""SELECT school,official_url,roster_url,stats_url FROM teams
                  WHERE division=? AND COALESCE(stats_url,roster_url,official_url,'')<>'' ORDER BY school""", (division,))
    # Prioritize schools currently represented in NCAA stat leaderboards so the
    # visible player tables gain positions/minutes quickly while the full crawl
    # continues in the background.
    try:
        leader_schools={_team_key(x.get('school')) for x in rows("SELECT DISTINCT school FROM stat_leaders WHERE division=?",(division,)) if x.get('school')}
        # One rule for every school: teams represented in verified NCAA leader
        # tables are processed first, then all remaining schools alphabetically.
        teams=sorted(teams,key=lambda t:(0 if _team_key(t.get('school')) in leader_schools else 1,str(t.get('school') or '').lower()))
    except Exception:
        pass
    if max_teams:
        teams = teams[:int(max_teams)]
    out={"ok":False,"division":division,"teams_total":len(teams),"teams_checked":0,"teams_with_stats":0,"stat_rows":0,"failures":[]}
    entity=f"player_stats:{division}:2026"
    with db() as conn:
        conn.execute("DELETE FROM source_status WHERE source='official_school_bulk' AND entity=?",(entity,))
        conn.execute("INSERT INTO source_status(source,entity,status,detail,checked_at) VALUES(?,?,?,?,?)",
                     ('official_school_bulk',entity,'running',f"0/{len(teams)} schools checked",datetime.now(timezone.utc).isoformat(timespec='seconds')))
    for idx, team in enumerate(teams, start=1):
        try:
            r=sync_team_school_site(team['school'],division,recalc=False)
            out['teams_checked']+=1; out['stat_rows']+=int(r.get('stats') or 0)
            if r.get('stats'): out['teams_with_stats']+=1
        except Exception as exc:
            out['teams_checked']+=1
            out['failures'].append({'school':team['school'],'error':str(exc)[:240]})
        if idx==1 or idx%5==0 or idx==len(teams):
            with db() as conn:
                conn.execute("UPDATE source_status SET detail=?,checked_at=? WHERE source='official_school_bulk' AND entity=?",
                             (f"{idx}/{len(teams)} schools checked · {out['teams_with_stats']} with stats",datetime.now(timezone.utc).isoformat(timespec='seconds'),entity))
    recalc_prices()
    out['ok']=out['teams_with_stats']>0
    with db() as conn:
        conn.execute("UPDATE source_status SET status=?,detail=?,checked_at=? WHERE source='official_school_bulk' AND entity=?",
                     ('ok' if not out['failures'] else 'partial',f"{out['teams_checked']}/{len(teams)} checked · {out['teams_with_stats']} schools with stats · {out['stat_rows']} player rows",datetime.now(timezone.utc).isoformat(timespec='seconds'),entity))
    return out


def sync_tds_rankings():
    result = fetch_tds_top25()
    if not result["ok"]:
        return result
    snapshot = date.today().isoformat()
    with db() as conn:
        conn.execute("DELETE FROM rankings WHERE ranking_date=? AND source='TopDrawerSoccer'", (snapshot,))
        for item in result["items"]:
            conn.execute("""
                INSERT OR REPLACE INTO rankings(ranking_date, source, rank, school, overall_record, conference_record, source_url)
                VALUES(?,?,?,?,?,?,?)
            """, (snapshot, "TopDrawerSoccer", item["rank"], item["school"], item.get("overall_record"), item.get("conference_record"), item.get("source_url")))
    recalc_prices()
    return result


def sync_ncaa_leaders():
    return fetch_ncaa_goal_leaders()


def recalc_prices():
    """Recalculate every player/coach with one cross-world valuation model.

    Inputs are the player's verified production, verified team results, national
    ranking when one exists, conference context derived from teams in the same
    world, experience and recent/career usage. Missing sports data contributes
    zero rather than a fabricated estimate.
    """
    with db() as conn:
        players = conn.execute("SELECT * FROM players").fetchall()
        teams = conn.execute("SELECT school,conference,division FROM teams").fetchall()
        team_conf={(r['division'],r['school']):r['conference'] for r in teams}

        # Latest official NCAA/United Soccer Coaches ranking by world. D1 may also
        # use TopDrawer player rankings as a small enrichment signal, never as the
        # national-team ranking source.
        ranks={}
        for div in ('D1','D2','D3','NAIA','NJCAA1'):
            rr=conn.execute("""SELECT r1.school,r1.rank FROM rankings r1 JOIN
                 (SELECT school,MAX(ranking_date) d FROM rankings WHERE division=? AND source='NCAA / United Soccer Coaches' GROUP BY school) x
                 ON x.school=r1.school AND x.d=r1.ranking_date
                 WHERE r1.division=? AND r1.source='NCAA / United Soccer Coaches'""",(div,div)).fetchall()
            for r in rr: ranks[(div,r['school'])]=r['rank']

        # Verified final-game results -> team performance in [0,1]. A draw is 0.5.
        perf={}
        game_rows=conn.execute("""SELECT division,home_team,away_team,home_score,away_score,status FROM games
                                  WHERE home_score IS NOT NULL AND away_score IS NOT NULL AND lower(status) LIKE 'final%'""").fetchall()
        agg={}
        for g in game_rows:
            hs=float(g['home_score']);as_=float(g['away_score']);div=g['division']
            for team,is_home in ((g['home_team'],True),(g['away_team'],False)):
                a=agg.setdefault((div,team),[0.0,0])
                a[1]+=1
                if hs==as_: a[0]+=0.5
                elif (is_home and hs>as_) or ((not is_home) and as_>hs): a[0]+=1.0
        for key,(pts,gp) in agg.items(): perf[key]=pts/gp if gp else 0.0

        # Conference strength is derived in the SAME way in every world: mean
        # verified team performance, lightly reinforced by official ranked teams.
        conf_members={}
        for t in teams:
            if t['conference']:
                conf_members.setdefault((t['division'],t['conference']),[]).append(t['school'])
        conf_strength={}
        for key,members in conf_members.items():
            div,conf=key
            vals=[perf[(div,m)] for m in members if (div,m) in perf]
            base=sum(vals)/len(vals) if vals else 0.0
            ranked=sum(max(0.0,(26-float(ranks[(div,m)]))/25.0) for m in members if (div,m) in ranks)
            ranked_bonus=min(0.25, ranked/max(1,len(members))*0.35)
            conf_strength[key]=min(1.0,base+ranked_bonus)

        pranks={r['name'].lower():r['rank'] for r in conn.execute("""SELECT name,MIN(rank) rank FROM player_rankings
                  WHERE ranking_date=(SELECT MAX(ranking_date) FROM player_rankings) GROUP BY lower(name)""").fetchall()}
        for p in players:
            div=p['division'] or 'D1'; current=conn.execute("SELECT * FROM player_season_stats WHERE player_id=? AND season=2026",(p['id'],)).fetchone()
            history=conn.execute("SELECT * FROM player_season_stats WHERE player_id=? AND season<2026",(p['id'],)).fetchall()
            conf=p['conference'] or team_conf.get((div,p['school']))
            value=compute_player_value(dict(p),dict(current) if current else {},[dict(x) for x in history],
                       ranks.get((div,p['school'])),pranks.get(p['name'].lower()) if div=='D1' else None,
                       conf_strength.get((div,conf),0),perf.get((div,p['school']),0))
            leader=conn.execute("""SELECT MIN(COALESCE(rank,9999)) r FROM stat_leaders
                                   WHERE division=? AND lower(name)=lower(?) AND lower(school)=lower(?)
                                     AND snapshot_date=(SELECT MAX(snapshot_date) FROM stat_leaders WHERE division=?)""",
                                (div,p['name'],p['school'],div)).fetchone()
            leader_rank=(leader['r'] if leader and leader['r'] and leader['r']<9999 else None)
            player_rank=pranks.get(p['name'].lower()) if div=='D1' else None
            overall_rank=min([r for r in (leader_rank,player_rank) if r is not None],default=None)
            overall=compute_player_overall(dict(p),dict(current) if current else {},
                       ranks.get((div,p['school'])),overall_rank,
                       conf_strength.get((div,conf),0),perf.get((div,p['school']),0))
            conn.execute("UPDATE players SET price=?, rating=?, conference=COALESCE(?,conference) WHERE id=?",
                         (value,overall,canonicalize_conference(conf) or fallback_conference_for_school(p['school'],div),p['id']))

        coaches=conn.execute("SELECT * FROM coaches").fetchall()
        for c in coaches:
            div=c['division'] or 'D1';team=c['school']; games=0; wins=0
            for g in conn.execute("""SELECT * FROM games WHERE division=? AND lower(status) LIKE 'final%'
                                     AND (home_team=? OR away_team=?)""",(div,team,team)).fetchall():
                if g['home_score'] is None or g['away_score'] is None: continue
                games+=1
                if (g['home_team']==team and g['home_score']>g['away_score']) or (g['away_team']==team and g['away_score']>g['home_score']):wins+=1
            conf=c['conference'] or team_conf.get((div,team))
            value=compute_coach_value(ranks.get((div,team)),wins,games,conf_strength.get((div,conf),0),c['role'])
            conn.execute("UPDATE coaches SET price=? WHERE id=?",(value,c['id']))

def sync_tds_extended():
    snapshot = date.today().isoformat()
    results = {}
    upper = fetch_tds_player_rankings()
    fresh = fetch_tds_freshman_rankings()
    comp = fetch_tds_composite()
    standings = fetch_tds_standings()
    with db() as conn:
        for result, category in [(upper, "upperclassman_top100"), (fresh, "freshman_top100")]:
            if result.get("ok"):
                conn.execute("DELETE FROM player_rankings WHERE ranking_date=? AND source='TopDrawerSoccer' AND category=?", (snapshot, category))
                for x in result.get("items", []):
                    conn.execute("""INSERT OR REPLACE INTO player_rankings(ranking_date,source,category,rank,name,school,conference,position,source_url)
                                  VALUES(?,?,?,?,?,?,?,?,?)""", (snapshot,"TopDrawerSoccer",category,x["rank"],x["name"],x.get("school"),x.get("conference"),x.get("position"),x.get("source_url")))
        if comp.get("ok"):
            conn.execute("DELETE FROM rankings WHERE ranking_date=? AND source='TopDrawerSoccer Composite'", (snapshot,))
            for x in comp.get("items", []):
                conn.execute("""INSERT OR REPLACE INTO rankings(ranking_date,source,rank,school,source_url) VALUES(?,?,?,?,?)""",
                             (snapshot,"TopDrawerSoccer Composite",x["rank"],x["school"],x.get("source_url")))
        if standings.get("ok"):
            for x in standings.get("items", []):
                conf=fallback_conference_for_school(x.get("school"),'D1') or canonicalize_conference(x.get("conference"))
                if not conf or not x.get("school"): continue
                conn.execute("""INSERT OR REPLACE INTO standings(snapshot_date,conference,school,conference_record,overall_record,source,division,source_url)
                              VALUES(?,?,?,?,?,?,?,?)""", (snapshot,conf,x["school"],x.get("conference_record"),x.get("overall_record"),x["source"],'D1',x.get("source_url")))
                existing=conn.execute("SELECT id FROM teams WHERE division='D1' AND lower(school)=lower(?) LIMIT 1",(x['school'],)).fetchone()
                if existing:
                    conn.execute("UPDATE teams SET conference=? WHERE id=?",(conf,existing['id']))
                else:
                    conn.execute("INSERT OR IGNORE INTO teams(school,conference,division) VALUES(?,?,'D1')",(x['school'],conf))
                conn.execute("UPDATE players SET conference=? WHERE division='D1' AND lower(school)=lower(?)",(conf,x['school']))
                conn.execute("UPDATE coaches SET conference=? WHERE division='D1' AND lower(school)=lower(?)",(conf,x['school']))
    results["upperclassman"] = upper
    results["freshman"] = fresh
    results["composite"] = comp
    results["standings"] = standings
    return results


def sync_tds_standings_only():
    """Fast D-I men's-soccer standings refresh from the public TDS table."""
    snapshot=date.today().isoformat()
    result=fetch_tds_standings()
    if not result.get('ok'):
        return result
    with db() as conn:
        # Replace today's TDS standings snapshot only after a successful fetch.
        conn.execute("DELETE FROM standings WHERE snapshot_date=? AND division='D1' AND source='TopDrawerSoccer'",(snapshot,))
        for x in result.get('items',[]):
            school=x.get('school')
            conf=fallback_conference_for_school(school,'D1') or canonicalize_conference(x.get('conference'))
            if not school or not conf: continue
            conn.execute("""INSERT OR REPLACE INTO standings(snapshot_date,conference,school,conference_record,overall_record,source,division,source_url)
                          VALUES(?,?,?,?,?,'TopDrawerSoccer','D1',?)""",
                         (snapshot,conf,school,x.get('conference_record'),x.get('overall_record'),x.get('source_url')))
            team=conn.execute("SELECT id FROM teams WHERE division='D1' AND lower(school)=lower(?) LIMIT 1",(school,)).fetchone()
            if team:
                conn.execute("UPDATE teams SET conference=? WHERE id=?",(conf,team['id']))
            else:
                conn.execute("INSERT OR IGNORE INTO teams(school,conference,division) VALUES(?,?,'D1')",(school,conf))
            conn.execute("UPDATE players SET conference=? WHERE division='D1' AND lower(school)=lower(?)",(conf,school))
            conn.execute("UPDATE coaches SET conference=? WHERE division='D1' AND lower(school)=lower(?)",(conf,school))
    recalc_prices()
    return {'ok':True,'count':len(result.get('items',[])),'conferences':len({x.get('conference') for x in result.get('items',[]) if x.get('conference')}),
            'profiles_checked':result.get('profiles_checked',0),'errors':result.get('errors',[])}


def sync_ncaa_standings(division):
    """Import every NCAA men's-soccer conference table and propagate league names."""
    result=fetch_ncaa_standings(division)
    if not result.get('ok'):
        return result
    snapshot=date.today().isoformat()
    with db() as conn:
        conn.execute("DELETE FROM standings WHERE snapshot_date=? AND division=? AND source='NCAA'",(snapshot,division))
        for x in result.get('items',[]):
            conf=canonicalize_conference(x.get('conference'))
            school=x.get('school')
            if not conf or not school: continue
            conn.execute("""INSERT OR REPLACE INTO standings(snapshot_date,conference,school,conference_record,overall_record,source,division,source_url)
                          VALUES(?,?,?,?,?,'NCAA',?,?)""",
                         (snapshot,conf,school,x.get('conference_record'),x.get('overall_record'),division,x.get('source_url')))
            # Conference standings are the strongest live source for current league
            # membership, so they repair stale/sluggish team and player labels.
            existing=conn.execute("SELECT id FROM teams WHERE division=? AND lower(school)=lower(?) LIMIT 1",(division,school)).fetchone()
            if existing:
                conn.execute("UPDATE teams SET conference=? WHERE id=?",(conf,existing['id']))
            else:
                conn.execute("INSERT OR IGNORE INTO teams(school,conference,division,source_updated_at) VALUES(?,?,?,?)",
                             (school,conf,division,datetime.now(timezone.utc).isoformat(timespec='seconds')))
            conn.execute("UPDATE players SET conference=? WHERE division=? AND lower(school)=lower(?)",(conf,division,school))
            conn.execute("UPDATE coaches SET conference=? WHERE division=? AND lower(school)=lower(?)",(conf,division,school))
        # Normalize aliases left by older imports and fill a small current D-I fallback.
        for table in ('teams','players','coaches'):
            for r in conn.execute(f"SELECT id,school,conference FROM {table} WHERE division=?",(division,)).fetchall():
                conf=canonicalize_conference(r['conference']) or fallback_conference_for_school(r['school'],division)
                if conf: conn.execute(f"UPDATE {table} SET conference=? WHERE id=?",(conf,r['id']))
        for r in conn.execute("SELECT id,home_team,away_team,home_conference,away_conference FROM games WHERE division=?",(division,)).fetchall():
            hc=canonicalize_conference(r['home_conference']) or fallback_conference_for_school(r['home_team'],division)
            ac=canonicalize_conference(r['away_conference']) or fallback_conference_for_school(r['away_team'],division)
            conn.execute("UPDATE games SET home_conference=COALESCE(?,home_conference),away_conference=COALESCE(?,away_conference) WHERE id=?",(hc,ac,r['id']))
    recalc_prices()
    return {'ok':True,'count':len(result.get('items',[])),'source_url':result.get('source_url'),'updated':result.get('updated'),'transport':result.get('transport')}


def sync_ncaa_upcoming_games(division, days=10):
    """Fast market-card schedule refresh; full-season sync remains separate."""
    result=fetch_ncaa_upcoming_window(division,days=days)
    if not result.get('ok'):
        return result
    with db() as conn:
        for g in result.get('items',[]):
            _upsert_game(conn,g)
    return result

def sync_ncaa_rankings(division):
    result=fetch_ncaa_rankings(division)
    if not result.get("ok"):
        return result
    snapshot=date.today().isoformat()
    source="NCAA / United Soccer Coaches"
    with db() as conn:
        # The National Ranking tab represents NCAA/United Soccer Coaches only.
        # Remove older copies so a stale or enrichment ranking can never look current.
        conn.execute("DELETE FROM rankings WHERE source=? AND division=?",(source,division))
        for sort_index, x in enumerate(result.get("items",[]), start=1):
            # Legacy schema keyed numeric ranks uniquely, while NCAA rankings can tie.
            # Store display order in rank and preserve the exact NCAA rank in rank_label.
            conn.execute("""INSERT INTO rankings(
                            ranking_date,source,rank,school,overall_record,score,rank_label,previous,
                            first_votes,total_points,source_updated_text,division,source_url)
                          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                         (snapshot,source,sort_index,x["school"],x.get("overall_record"),x.get("score"),
                          x.get("rank_label") or str(x.get("rank")),x.get("previous"),x.get("first_votes"),x.get("total_points"),
                          x.get("source_updated_text") or result.get("updated"),division,x.get("source_url")))
        conn.execute("DELETE FROM source_status WHERE source=? AND entity=?",(source,f'rankings:{division}'))
        conn.execute("INSERT INTO source_status(source,entity,status,detail,checked_at) VALUES(?,?,?,?,?)",
                     (source,f'rankings:{division}','ok',
                      f"{len(result.get('items',[]))} NCAA rows · {result.get('updated') or 'current table'} · transport: {result.get('transport') or 'NCAA'}",
                      __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(timespec='seconds')))
    return {"ok":True,"count":len(result.get("items",[])),"source_url":result.get("source_url"),
            "updated":result.get("updated"),"transport":result.get("transport"),"warning":result.get("warning")}


def sync_ncaa_stat_tables(division, categories=None):
    """Sync public NCAA leaderboards for D1/D2/D3 and enrich known players.

    Field-player minutes are not published in NCAA national leaderboards, so
    those remain sourced from official school cumulative-stat pages.
    """
    labels={
        "goals":"Total Goals",
        "assists":"Total Assists",
        "shutouts":"Shutouts",
        "goalie_minutes":"Goalie Minutes Played",
        "total_saves":"Total Saves",
        "game_winners":"Game-Winning Goals",
    }
    if categories:
        wanted=set(categories)
        labels={k:v for k,v in labels.items() if k in wanted}
    snapshot=date.today().isoformat()
    out={}
    with db() as conn:
        for category,label in labels.items():
            result=fetch_ncaa_stat_leaders(division,label)
            out[category]={"ok":result.get("ok",False),"count":len(result.get("items",[])),"error":result.get("error")}
            if not result.get("ok"): continue
            conn.execute("DELETE FROM stat_leaders WHERE snapshot_date=? AND division=? AND category=?",(snapshot,division,category))
            for x in result.get("items",[]):
                confrow=conn.execute("SELECT conference FROM teams WHERE division=? AND lower(school)=lower(?) LIMIT 1",(division,x.get("team"))).fetchone()
                if not confrow:
                    confrow=conn.execute("SELECT conference FROM standings WHERE division=? AND lower(school)=lower(?) ORDER BY snapshot_date DESC LIMIT 1",(division,x.get("team"))).fetchone()
                conf=canonicalize_conference(confrow["conference"] if confrow else None) or fallback_conference_for_school(x.get("team"),division)
                conn.execute("""INSERT OR REPLACE INTO stat_leaders(snapshot_date,division,category,rank,name,school,class_year,games,value,conference,source_url,source_name)
                              VALUES(?,?,?,?,?,?,?,?,?,?,?,'NCAA')""",
                             (snapshot,division,category,x.get("rank"),x.get("name"),x.get("team"),x.get("class_year"),x.get("games"),x.get("value"),conf,x.get("source_url")))
                p=conn.execute("SELECT id FROM players WHERE division=? AND lower(name)=lower(?) AND lower(school)=lower(?) LIMIT 1",
                               (division,x.get("name"),x.get("team"))).fetchone()
                if not p: continue
                existing=conn.execute("SELECT * FROM player_season_stats WHERE player_id=? AND season=2026",(p["id"],)).fetchone()
                if not existing:
                    conn.execute("INSERT INTO player_season_stats(player_id,season,source_name,source_url) VALUES(?,2026,'NCAA',?)",
                                 (p["id"],x.get("source_url")))
                col={"goals":"goals","assists":"assists","shutouts":"shutouts","goalie_minutes":"minutes","total_saves":"saves","game_winners":"game_winners"}[category]
                conn.execute(f"UPDATE player_season_stats SET {col}=?, games=CASE WHEN ? IS NOT NULL THEN MAX(games,?) ELSE games END, source_name='NCAA', source_url=COALESCE(?,source_url), source_updated_at=? WHERE player_id=? AND season=2026",
                             (x.get("value"),x.get("games"),x.get("games"),x.get("source_url"),x.get("updated_at"),p["id"]))
    recalc_prices()
    return out


def _team_key(value):
    """Conservative school-name key used only for cross-source identity matching.

    NCAA, school sites and legacy roster databases often use different display
    labels (``Seattle U`` vs ``Seattle University``).  The key intentionally
    keeps schools such as *San Diego* and *UC San Diego* distinct.
    """
    import re
    text=str(value or '').strip().lower().replace('&',' and ')
    if not text:
        return ''
    # Preserve meaningful institutional prefixes before dropping generic words.
    text=re.sub(r"[^a-z0-9]+", " ", text).strip()
    phrase_replacements=(
        (r'^umass\b', 'massachusetts'),
        (r'^fdu$', 'fairleigh dickinson'),
        (r'^fairleigh dickinson university$', 'fairleigh dickinson'),
        (r'^unc\b', 'north carolina'),
        (r'^nc state\b', 'north carolina state'),
        (r'^uc\b', 'california'),
        (r'^cal st\b', 'california state'),
        (r'^cal state\b', 'california state'),
        (r'^sacramento st$', 'sacramento state'),
        (r'^oregon st$', 'oregon state'),
        (r'^georgia st$', 'georgia state'),
        (r'^michigan st$', 'michigan state'),
        (r'^ohio st$', 'ohio state'),
        (r'^penn st$', 'penn state'),
        (r'^san diego st$', 'san diego state'),
        (r'^florida international$', 'fiu'),
        (r'^south florida$', 'usf'),
        (r'^central florida$', 'ucf'),
        (r'^florida atlantic$', 'fau'),
        (r'^florida gulf coast university$', 'fgcu'),
        (r'^florida gulf coast$', 'fgcu'),
    )
    for pat,repl in phrase_replacements:
        text=re.sub(pat,repl,text)
    # ``St. John's`` means Saint; a trailing ``St.`` in ``Oregon St.`` means State.
    text=re.sub(r'^st\b', 'saint', text)
    text=re.sub(r'\bst$', 'state', text)
    # Athletics sites commonly shorten University to a trailing U.
    text=re.sub(r'\bu$', 'university', text)
    text=re.sub(r'\b(the|university|college|of|at)\b',' ',text)
    return re.sub(r'[^a-z0-9]+','',text)


def _resolve_team_name(conn, raw_name, division):
    """Map source labels onto the richest registered school identity.

    Exact display-name matches are not automatically trusted: an earlier sync
    may have created an empty alias row.  When two rows normalize to the same
    school, prefer the one actually used by the roster/player database.
    """
    from difflib import SequenceMatcher
    raw=str(raw_name or '').strip()
    if not raw:return raw
    key=_team_key(raw)
    team_cols={r[1] for r in conn.execute("PRAGMA table_info(teams)").fetchall()}
    alias_cols=[c for c in ('abbreviation','ncaa_slug') if c in team_cols]
    select_alias=', '.join(f't.{c}' for c in alias_cols)
    if select_alias: select_alias=', '+select_alias
    team_rows=conn.execute(f"""SELECT t.school{select_alias},
        (SELECT COUNT(*) FROM players p
         WHERE p.division=t.division AND lower(p.school)=lower(t.school)) AS player_count
        FROM teams t WHERE t.division=?""",(division,)).fetchall()

    # First prefer any row whose canonical/alias key is identical, selecting the
    # identity with actual roster coverage over an empty alias created by sync.
    same=[]
    for t in team_rows:
        vals=[t['school']]+[t[c] for c in alias_cols]
        if any(_team_key(v)==key for v in vals if v):
            same.append(t)
    if same:
        same.sort(key=lambda t:(int(t['player_count'] or 0),
                                1 if str(t['school']).lower()==raw.lower() else 0,
                                -len(str(t['school']))),reverse=True)
        return same[0]['school']

    # Conservative fuzzy fallback for punctuation/minor spelling deltas only.
    best=None;best_score=0.0;best_players=-1
    for t in team_rows:
        for cand in [t['school']]+[t[c] for c in alias_cols]:
            ck=_team_key(cand)
            if not ck or not key:continue
            score=SequenceMatcher(None,ck,key).ratio()
            # Large length deltas are usually genuinely different institutions.
            if abs(len(ck)-len(key))>=5: score*=.80
            players=int(t['player_count'] or 0)
            if score>best_score or (score==best_score and players>best_players):
                best_score=score;best=t['school'];best_players=players
    return best if best_score>=.91 else raw


def _upsert_game(conn, g):
    """Insert/refresh a game while collapsing aliases and reversed source order."""
    division = g.get("division") or "D1"
    g=dict(g)
    g["home_team"]=_resolve_team_name(conn,g.get("home_team"),division)
    g["away_team"]=_resolve_team_name(conn,g.get("away_team"),division)
    if not g.get('game_date') or not g.get('home_team') or not g.get('away_team'):
        return None
    if _team_key(g['home_team']) == _team_key(g['away_team']):
        return None

    g["home_conference"]=(fallback_conference_for_school(g.get("home_team"),division)
                          or canonicalize_conference(g.get("home_conference")))
    g["away_conference"]=(fallback_conference_for_school(g.get("away_team"),division)
                          or canonicalize_conference(g.get("away_conference")))
    for school, conf in ((g.get("home_team"),g.get("home_conference")),
                         (g.get("away_team"),g.get("away_conference"))):
        existing_team=conn.execute(
            "SELECT id FROM teams WHERE division=? AND lower(school)=lower(?) LIMIT 1",
            (division,school)).fetchone()
        if existing_team:
            conn.execute("""UPDATE teams SET conference=COALESCE(?,conference),
                         source_updated_at=COALESCE(?,source_updated_at) WHERE id=?""",
                         (conf,g.get('source_updated_at'),existing_team['id']))
        else:
            conn.execute("""INSERT INTO teams(school,conference,division,source_updated_at)
                         VALUES(?,?,?,?)""",(school,conf,division,g.get('source_updated_at')))

    existing=None; reversed_order=False
    ext=str(g.get('external_id') or '').strip()
    if ext:
        existing=conn.execute("""SELECT * FROM games WHERE division=? AND external_id=? LIMIT 1""",
                              (division,ext)).fetchone()
    if not existing:
        hk,ak=_team_key(g['home_team']),_team_key(g['away_team'])
        for r in conn.execute("SELECT * FROM games WHERE division=? AND game_date=?",
                              (division,g['game_date'])).fetchall():
            rh,ra=_team_key(r['home_team']),_team_key(r['away_team'])
            if rh==hk and ra==ak:
                existing=r;break
            if rh==ak and ra==hk:
                existing=r;reversed_order=True;break

    if existing:
        hs,as_=g.get('home_score'),g.get('away_score')
        home_name,away_name=g['home_team'],g['away_team']
        home_conf,away_conf=g.get('home_conference'),g.get('away_conference')
        if reversed_order:
            # Keep the already stored home/away orientation and map incoming
            # scores/conferences onto it instead of creating a second card.
            hs,as_=as_,hs
            home_name,away_name=existing['home_team'],existing['away_team']
            home_conf,away_conf=away_conf,home_conf
        conn.execute("""UPDATE games SET
             home_team=?, away_team=?,
             home_score=COALESCE(?,home_score), away_score=COALESCE(?,away_score),
             status=?, venue=COALESCE(?,venue), source_url=COALESCE(?,source_url),
             source_name=COALESCE(?,source_name), source_updated_at=COALESCE(?,source_updated_at),
             start_time=COALESCE(?,start_time), current_period=COALESCE(?,current_period),
             contest_clock=COALESCE(?,contest_clock), external_id=COALESCE(?,external_id),
             home_conference=COALESCE(?,home_conference), away_conference=COALESCE(?,away_conference)
           WHERE id=?""",
          (home_name,away_name,hs,as_,g.get('status') or 'scheduled',g.get('venue'),
           g.get('source_url'),g.get('source_name'),g.get('source_updated_at'),g.get('start_time'),
           g.get('current_period'),g.get('contest_clock'),g.get('external_id'),home_conf,away_conf,
           existing['id']))
        return existing['id']

    cur=conn.execute("""INSERT INTO games(
         game_date,home_team,away_team,home_score,away_score,status,conference_game,venue,division,
         source_url,source_name,source_updated_at,start_time,current_period,contest_clock,external_id,
         home_conference,away_conference)
       VALUES(?,?,?,?,?,?,0,?,?,?,?,?,?,?,?,?,?,?)""",
      (g.get('game_date'),g.get('home_team'),g.get('away_team'),g.get('home_score'),g.get('away_score'),
       g.get('status') or 'scheduled',g.get('venue'),division,g.get('source_url'),g.get('source_name'),
       g.get('source_updated_at'),g.get('start_time'),g.get('current_period'),g.get('contest_clock'),
       g.get('external_id'),g.get('home_conference'),g.get('away_conference')))
    return cur.lastrowid


def sync_ncaa_season_schedule_fast(division, year=2026, recalc=False):
    """Populate the NCAA season calendar using schedule feeds, not scoreboards.

    The preferred 2026+ GraphQL schedule is one request.  If NCAA changes that
    response shape or the mirror is unavailable, fall back to the official
    Casablanca month schedules (Aug-Dec).  Either way, calendar clicks become
    local SQLite reads after the first successful warmup.
    """
    result=fetch_ncaa_schedule_alt_games(division,target_date=None,year=year)
    items=list(result.get('items') or []) if result.get('ok') else []
    errors=[]
    if result.get('error'): errors.append(str(result.get('error')))

    # The modern NCAA full-season payload has changed shape several times. If
    # the parser yields an implausibly small season, use the same NCAA payload to
    # discover real game dates and then read the authoritative date scoreboards.
    # This still uses NCAA data, but avoids depending on one fragile JSON shape.
    if len(items) < 200:
        try:
            from services.sources.ncaa import fetch_ncaa_schedule_dates, fetch_ncaa_scoreboard_date
            discovered=fetch_ncaa_schedule_dates(division,year)
            seen={(g.get('game_date'),_team_key(g.get('home_team')),_team_key(g.get('away_team'))) for g in items}
            dates=[d for d in discovered.get('dates',[]) if str(d).startswith(str(year)+'-')]
            import time as _time
            for idx,d in enumerate(dates):
                rr=fetch_ncaa_scoreboard_date(division,d)
                if not rr.get('ok'):
                    if rr.get('error'): errors.append(f'{d}: {rr.get("error")}')
                else:
                    for g in rr.get('items',[]):
                        key=(g.get('game_date'),_team_key(g.get('home_team')),_team_key(g.get('away_team')))
                        if key not in seen:
                            seen.add(key);items.append(g)
                if idx+1<len(dates):
                    _time.sleep(.23)
            if discovered.get('dates'):
                result={'ok':bool(items),'items':items,'transport':'NCAA season dates + exact NCAA scoreboards','errors':errors,
                        'schedule_dates':len(discovered.get('dates',[]))}
        except Exception as exc:
            errors.append(f'NCAA discovered-date fallback: {exc}')

    # Legacy month feeds are only a final compatibility fallback; NCAA has
    # deprecated some Casablanca transports, so they are no longer the primary
    # source for 2026 completeness.
    if not items:
        seen=set()
        for month in range(8,13):
            date_iso=f'{int(year):04d}-{month:02d}-01'
            mr=fetch_ncaa_month_schedule_games(division,date_iso)
            if not mr.get('ok'):
                if mr.get('error'):errors.append(f'{month:02d}: {mr.get("error")}')
                continue
            cache_items=[]
            try:
                from services.sources import ncaa as _ncaa_source
                cache_items=list((_ncaa_source._MONTH_SCHEDULE_CACHE.get((division,int(year),month)) or {}).get('items') or [])
            except Exception:
                cache_items=[]
            for g in cache_items:
                key=(g.get('game_date'),str(g.get('home_team')).lower(),str(g.get('away_team')).lower())
                if key not in seen:
                    seen.add(key);items.append(g)
        result={'ok':bool(items),'items':items,'transport':'NCAA legacy monthly schedule fallback','errors':errors}
    if not items:
        return result if isinstance(result,dict) else {'ok':False,'items':[],'error':'; '.join(errors)}
    with db() as conn:
        for g in items:
            _upsert_game(conn,g)
    result['ok']=True
    result['stored']=len(items)
    if recalc and result['stored']:
        recalc_prices()
    return result


def sync_ncaa_game_history(division, start_date='2026-08-01', end_date=None, recalc=True):
    """Import the complete 2026 NCAA season: played, live and scheduled games."""
    end_date = end_date or '2026-12-31'
    result = fetch_ncaa_scoreboard_history(division, start_date, end_date)
    if not result.get('ok'):
        return result
    with db() as conn:
        # Scoreboard data enriches the schedule. A successful response containing
        # zero games must never erase future fixtures already collected from
        # official school schedule pages.
        items = result.get('items', [])
        full_request = start_date <= '2026-08-01' and end_date >= '2026-12-31'
        exact_request = start_date == end_date
        # An exact-date NCAA refresh is a snapshot of that calendar day, not an
        # additive feed. Replace the day as a unit so cached aliases, launch
        # snapshots and older prototype rows can never coexist as duplicates.
        # Verified official zeros also clear phantom legacy games.
        requested_day=date.fromisoformat(start_date) if exact_request else None
        future_day=bool(requested_day and requested_day>date.today())
        replace_day = exact_request and not result.get('failures') and (
            bool(items) or (bool(result.get('authoritative_zero')) and not future_day)
        ) and bool(result.get('authoritative', True))
        if replace_day:
            conn.execute("DELETE FROM games WHERE division=? AND game_date=?",
                         (division,start_date))
        for g in items:
            _upsert_game(conn, g)
        # Record whether the requested full-season pass completed without transport failures.
        if start_date <= '2026-08-01' and end_date >= '2026-12-31':
            entity = f'games:{division}:2026'
            conn.execute("DELETE FROM source_status WHERE source='NCAA.com via ncaa-api' AND entity=?", (entity,))
            conn.execute(
                "INSERT INTO source_status(source,entity,status,detail,checked_at) VALUES(?,?,?,?,?)",
                (
                    'NCAA.com via ncaa-api',
                    entity,
                    'ok' if not result.get('failures') else 'partial',
                    f"{len(result.get('items', []))} games; {len(result.get('failures', []))} date failures; {result.get('dates_checked',0)} calendar dates checked; {result.get('schedule_dates',0)} schedule dates discovered; final-prototype-v3",
                    __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(timespec='seconds'),
                ),
            )
    result['stored'] = len(result.get('items', []))
    result['complete'] = not bool(result.get('failures'))
    # Team form is part of the universal valuation model, so newly verified
    # results should immediately update player/coach prices in every world.
    if recalc:
        recalc_prices()
    return result


def sync_registered_school_schedules(division):
    """Sync future and completed games from official school schedule pages.

    Legacy imports may only have a roster/player source URL. Those URLs are
    promoted to the team registry, then the related official schedule URL is
    discovered when possible. Missing coverage remains visible; nothing is
    fabricated.
    """
    from database import rows

    _backfill_team_sources_from_players(division)
    teams = rows(
        """SELECT school, schedule_url, official_url, roster_url
           FROM teams
           WHERE division=?
             AND COALESCE(schedule_url, official_url, roster_url, '') <> ''
           ORDER BY school""",
        (division,)
    )

    out = {
        'ok': False,
        'division': division,
        'teams_checked': 0,
        'games_stored': 0,
        'schedule_urls_discovered': 0,
        'teams_without_schedule': 0,
        'failures': []
    }

    with db() as conn:
        for team in teams:
            out['teams_checked'] += 1
            try:
                schedule_url = team.get('schedule_url')
                if not schedule_url:
                    start_url = team.get('official_url') or team.get('roster_url')
                    if start_url:
                        related = discover_related_urls(start_url)
                        schedule_url = related.get('schedule')
                        if schedule_url:
                            conn.execute(
                                "UPDATE teams SET schedule_url=? WHERE school=? AND division=?",
                                (schedule_url, team['school'], division)
                            )
                            out['schedule_urls_discovered'] += 1
                if not schedule_url:
                    out['teams_without_schedule'] += 1
                    continue

                candidates=[]
                def add_candidate(u):
                    if u and u not in candidates: candidates.append(u)
                add_candidate(schedule_url)
                if str(schedule_url).rstrip('/').endswith('/2026'):
                    add_candidate(str(schedule_url).rstrip('/')[:-5])
                else:
                    add_candidate(str(schedule_url).rstrip('/')+'/2026')
                result={'ok':False,'items':[]}
                used_url=schedule_url
                for candidate in candidates:
                    try:
                        rr=parse_official_schedule(candidate, team['school'], division)
                        if rr.get('items'):
                            result=rr;used_url=candidate;break
                    except Exception:
                        continue
                if used_url and used_url!=schedule_url:
                    conn.execute("UPDATE teams SET schedule_url=? WHERE school=? AND division=?",
                                 (used_url,team['school'],division))
                for g in result.get('items', []):
                    _upsert_game(conn, g)
                    out['games_stored'] += 1
            except Exception as exc:
                out['failures'].append({'school': team['school'], 'error': str(exc)[:240]})

    out['ok'] = out['games_stored'] > 0
    if out['games_stored']:
        recalc_prices()
    return out
