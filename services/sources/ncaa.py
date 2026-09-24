import json
import re
from urllib.parse import quote
from bs4 import BeautifulSoup
from .common import fetch, now_iso

NCAA_GOALS_URL = "https://www.ncaa.com/stats/soccer-men/d1/current/individual/573"
NCAA_RANKINGS_URL = "https://www.ncaa.com/rankings/soccer-men/d1/united-soccer-coaches"
NCAA_API_BASE = "https://ncaa-api.henrygd.me"
NCAA_GQL_URL = "https://sdataprod.ncaa.com/"
NCAA_GQL_SCOREBOARD_HASH = "7287cda610a9326931931080cb3a604828febe6fe3c9016a7e4a36db99efdb7c"
NCAA_GQL_SCHEDULE_HASH = "a25ad021179ce1d97fb951a49954dc98da150089f9766e7e85890e439516ffbf"
_SCHEDULE_ALT_CACHE = {}
_MONTH_SCHEDULE_CACHE = {}

def _coerce_json_object(value):
    """Unwrap JSON-string responses returned by compatibility transports."""
    current=value
    for _ in range(3):
        if isinstance(current,str):
            try:
                current=json.loads(current)
                continue
            except Exception:
                return None
        break
    return current if isinstance(current,(dict,list)) else None

# Verified from NCAA.com's current D1 United Soccer Coaches table on 2026-09-09.
# This is only a transport fallback. A live NCAA/API response always replaces it.
_D1_OFFICIAL_FALLBACK = [
    (1,"Stanford","1",6,195,"4-0-0"),(2,"Maryland","4",1,193,"3-0-0"),
    (3,"SMU","5",0,182,"3-0-0"),(4,"Ohio State","22",0,176,"3-0-0"),
    (5,"Georgetown","6",1,174,"3-0-1"),(6,"Indiana","14",0,156,"3-0-1"),
    (7,"San Diego","2",0,149,"2-1-0"),(8,"Michigan State","24",0,145,"4-0-0"),
    (9,"Akron","10",0,137,"2-0-1"),(10,"Oregon State","25",0,125,"2-0-1"),
    (11,"Vermont","7",0,121,"2-0-1"),(12,"UCLA","17",0,111,"2-0-1"),
    (13,"South Carolina","NR",0,105,"3-0-0"),(14,"High Point","9",0,103,"2-1-0"),
    (15,"Marshall","12",0,86,"1-0-1"),(16,"Hofstra","13",0,79,"2-0-1"),
    (17,"Wisconsin","23",0,70,"3-0-0"),(18,"Clemson","16",0,66,"2-1-0"),
    (19,"Florida Atlantic","NR",0,54,"2-0-2"),(20,"Cornell","NR",0,48,"1-0-0"),
    (21,"UC Santa Barbara","NR",0,36,"1-0-1"),(22,"Louisville","NR",0,33,"3-0-0"),
    (23,"Creighton","NR",0,11,"2-0-1"),(23,"Princeton","NR",0,11,"0-0-1"),
    (25,"Charlotte","18",0,7,"1-0-2"),
]


def _division_slug(division):
    return {"D1":"d1","D2":"d2","D3":"d3"}.get(division)


def _clean_key(value):
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _value(row, *names):
    norm = {_clean_key(k): v for k, v in (row or {}).items()}
    for name in names:
        key = _clean_key(name)
        if key in norm:
            return norm[key]
    return None


def _rank_number(value):
    m = re.search(r"\d+", str(value or ""))
    return int(m.group()) if m else None


def fetch_ncaa_goal_leaders():
    try:
        r = fetch(NCAA_GOALS_URL)
        soup = BeautifulSoup(r.text, "lxml")
        leaders = []
        for table in soup.find_all("table"):
            headers = [x.get_text(" ", strip=True).lower() for x in table.find_all("th")]
            if "name" not in headers or "goals" not in headers:
                continue
            for tr in table.find_all("tr"):
                cells = [x.get_text(" ", strip=True) for x in tr.find_all(["th", "td"])]
                if len(cells) < 5 or not cells[0].isdigit():
                    continue
                leaders.append({"rank": int(cells[0]), "name": cells[1], "team": cells[2],
                    "class_year": cells[3], "games": cells[4] if len(cells) > 4 else None,
                    "goals": cells[-1], "source": "NCAA", "source_url": NCAA_GOALS_URL,
                    "updated_at": now_iso()})
        return {"ok": True, "items": leaders}
    except Exception as exc:
        return {"ok": False, "items": [], "error": str(exc)}


def fetch_ncaa_rankings_raw():
    return fetch_ncaa_rankings("D1")


def _parse_rankings_api(payload, division, source_url):
    out = []
    for row in (payload or {}).get("data", []) or []:
        rank_raw = _value(row, "RANK", "Rank")
        school = _value(row, "SCHOOL", "School")
        rank = _rank_number(rank_raw)
        if rank is None or not school:
            continue
        prev = _value(row, "PREV", "Previous")
        votes = _value(row, "1ST VOTES", "1st Votes", "First Votes")
        points = _value(row, "TOTAL POINTS", "Points", "Total Points")
        record = _value(row, "W-L-T", "Record", "W L T")
        try: votes_i = int(str(votes).strip()) if str(votes or '').strip() else None
        except Exception: votes_i = None
        try: points_f = float(str(points).replace(',', '').strip()) if str(points or '').strip() else None
        except Exception: points_f = None
        out.append({
            "rank": rank, "rank_label": str(rank_raw or rank).strip(), "school": str(school).strip(),
            "previous": str(prev).strip() if prev not in (None, '') else None,
            "first_votes": votes_i, "total_points": points_f, "score": points_f,
            "overall_record": str(record).strip() if record not in (None, '') else None,
            "source": "NCAA / United Soccer Coaches", "source_url": source_url,
            "source_updated_text": (payload or {}).get("updated") or None, "updated_at": now_iso(),
        })
    # responsive copies can duplicate rows; ties are valid, so key by rank+school
    unique, seen = [], set()
    for x in out:
        key = (x["rank"], x["school"].lower())
        if key not in seen:
            seen.add(key); unique.append(x)
    return unique


def _parse_rankings_html(html, source_url):
    text = (html or '').lower()
    if "verify that you're not a robot" in text or "javascript is disabled" in text:
        return [], None
    soup = BeautifulSoup(html, "lxml")
    updated_el = soup.select_one('.rankings-last-updated')
    updated = updated_el.get_text(" ", strip=True) if updated_el else None
    items=[]
    for table in soup.find_all('table'):
        headers=[x.get_text(' ',strip=True) for x in table.find_all('th')]
        if not headers or not any('rank' in h.lower() for h in headers): continue
        keys=[_clean_key(h) for h in headers]
        for tr in table.find_all('tr'):
            cells=[x.get_text(' ',strip=True) for x in tr.find_all(['th','td'])]
            if len(cells)<2: continue
            row={keys[i]:cells[i] for i in range(min(len(keys),len(cells)))}
            rank_raw=row.get('rank'); rank=_rank_number(rank_raw); school=row.get('school')
            if rank is None or not school: continue
            def rv(*ks):
                for k in ks:
                    if _clean_key(k) in row:return row[_clean_key(k)]
            pts=rv('total points','points')
            try: pts=float(str(pts).replace(',','')) if pts not in (None,'') else None
            except: pts=None
            fv=rv('1st votes','first votes')
            try: fv=int(fv) if fv not in (None,'') else None
            except: fv=None
            items.append({'rank':rank,'rank_label':str(rank_raw),'school':school,'previous':rv('prev','previous'),
                          'first_votes':fv,'total_points':pts,'score':pts,'overall_record':rv('w-l-t','record'),
                          'source':'NCAA / United Soccer Coaches','source_url':source_url,
                          'source_updated_text':updated,'updated_at':now_iso()})
    unique=[];seen=set()
    for x in items:
        k=(x['rank'],x['school'].lower())
        if k not in seen: seen.add(k);unique.append(x)
    return unique, updated


def fetch_ncaa_rankings(division):
    """Return only the United Soccer Coaches table published on NCAA.com.

    Never substitutes TopDrawerSoccer or a fantasy-derived ranking.
    """
    slug=_division_slug(division)
    if not slug:
        return {"ok":False,"items":[],"error":"NCAA rankings support D1/D2/D3 only"}
    ncaa_url=f"https://www.ncaa.com/rankings/soccer-men/{slug}/united-soccer-coaches"
    api_url=f"{NCAA_API_BASE}/rankings/soccer-men/{slug}/united-soccer-coaches"
    errors=[]
    try:
        payload=fetch(api_url).json()
        items=_parse_rankings_api(payload, division, ncaa_url)
        if items:
            return {"ok":True,"items":items,"source_url":ncaa_url,"transport":"ncaa-api",
                    "updated":payload.get('updated'),"updated_at":now_iso()}
        errors.append('NCAA API returned no ranking rows')
    except Exception as exc:
        errors.append(f"NCAA API: {exc}")
    try:
        r=fetch(ncaa_url)
        items,updated=_parse_rankings_html(r.text,ncaa_url)
        if items:
            return {"ok":True,"items":items,"source_url":ncaa_url,"transport":"NCAA.com",
                    "updated":updated,"updated_at":now_iso()}
        errors.append('NCAA.com returned no parseable ranking rows')
    except Exception as exc:
        errors.append(f"NCAA.com: {exc}")
    if division=='D1':
        items=[]
        for rank,school,prev,votes,points,record in _D1_OFFICIAL_FALLBACK:
            items.append({'rank':rank,'rank_label':str(rank),'school':school,'previous':prev,'first_votes':votes,
                          'total_points':points,'score':points,'overall_record':record,
                          'source':'NCAA / United Soccer Coaches','source_url':ncaa_url,
                          'source_updated_text':'Through Games AUG. 30, 2026','updated_at':now_iso()})
        return {"ok":True,"items":items,"source_url":ncaa_url,"transport":"verified NCAA fallback",
                "updated":"Through Games AUG. 30, 2026","warning":"; ".join(errors),"updated_at":now_iso()}
    return {"ok":False,"items":[],"error":"; ".join(errors),"source_url":ncaa_url}


def fetch_ncaa_stat_leaders(division, statistic_label, max_pages=50):
    slug=_division_slug(division)
    if not slug:
        return {"ok":False,"items":[],"error":"NCAA national stats are available here only for D1/D2/D3"}
    # The NCAA selector lives on the division stats landing page.  The old
    # /current/individual route returns 404 unless a statistic id is appended.
    # Resolve the current statistic URL from the landing page, then paginate the
    # official leaderboard so every athlete with a published value is cached.
    base=f"https://www.ncaa.com/stats/soccer-men/{slug}"
    try:
        r=fetch(base); soup=BeautifulSoup(r.text,"lxml"); target=None; wanted=statistic_label.strip().lower()
        for opt in soup.find_all("option"):
            txt=opt.get_text(" ",strip=True).lower(); val=opt.get("value")
            if txt==wanted and val: target=val; break
        if not target:
            for a in soup.find_all("a",href=True):
                if a.get_text(" ",strip=True).lower()==wanted: target=a["href"]; break
        # Stable NCAA IDs for the two leaderboards used by the evaluation
        # dashboard.  Keep these only as a fallback in case the selector markup
        # changes; the live selector remains the primary source of truth.
        if not target and wanted == "total goals":
            target=f"/stats/soccer-men/{slug}/current/individual/573"
        if not target and wanted == "total assists":
            target=f"/stats/soccer-men/{slug}/current/individual/568"
        if not target:return {"ok":False,"items":[],"error":f"Statistic not found: {statistic_label}"}
        if target.startswith("/"): target="https://www.ncaa.com"+target
        elif not target.startswith("http"): target="https://www.ncaa.com/"+target.lstrip("/")
        items=[]; seen=set()
        for page in range(1,max_pages+1):
            url=target if page==1 else target.rstrip("/") + f"/p{page}"
            rr=fetch(url); ss=BeautifulSoup(rr.text,"lxml"); found=0
            for table in ss.find_all("table"):
                headers=[x.get_text(" ",strip=True).lower() for x in table.find_all("th")]
                if "name" not in headers or "team" not in headers: continue
                for tr in table.find_all("tr"):
                    cells=[x.get_text(" ",strip=True) for x in tr.find_all(["th","td"])]
                    if len(cells)<4: continue
                    rank_txt=cells[0].strip()
                    if not (rank_txt.isdigit() or rank_txt=="-"): continue
                    name=cells[1].strip(); team=cells[2].strip()
                    if not name or not team: continue
                    try: value=float(cells[-1].replace("%","").strip())
                    except: continue
                    key=(name.lower(),team.lower())
                    if key in seen: continue
                    seen.add(key); found+=1; games=None
                    if len(cells)>=6:
                        try: games=float(cells[-2])
                        except: games=None
                    items.append({"rank":int(rank_txt) if rank_txt.isdigit() else None,"name":name,"team":team,
                        "class_year":cells[3] if len(cells)>4 else None,"games":games,"value":value,
                        "source":"NCAA","source_url":url,"updated_at":now_iso()})
            if found==0: break
        return {"ok":True,"items":items,"statistic":statistic_label}
    except Exception as exc:
        return {"ok":False,"items":[],"error":str(exc),"statistic":statistic_label}



def _record_from_standing_row(row, prefix):
    """Build W-L-T from NCAA standing-row columns, tolerating header variants."""
    w=_value(row, f"{prefix} W", f"{prefix} Wins", f"{prefix} Win")
    l=_value(row, f"{prefix} L", f"{prefix} Losses", f"{prefix} Loss")
    t=_value(row, f"{prefix} T", f"{prefix} Ties", f"{prefix} Tie")
    vals=[]
    for v in (w,l,t):
        txt=str(v or '').strip()
        if txt=='': txt='0'
        m=re.search(r"-?\d+",txt)
        vals.append(m.group(0) if m else '0')
    return '-'.join(vals)


def fetch_ncaa_standings(division):
    """Fetch the NCAA men's-soccer all-conference standings table.

    The NCAA standings endpoint returns every conference in one payload.  We
    normalize the conference label so ranking, market and schedule filters use
    the same names (for example Atlantic Coast / acc -> ACC).
    """
    from services.conferences import canonicalize_conference
    slug=_division_slug(division)
    if not slug:
        return {"ok":False,"items":[],"error":"NCAA standings support D1/D2/D3 only"}
    source_url=f"https://www.ncaa.com/standings/soccer-men/{slug}"
    api_url=f"{NCAA_API_BASE}/standings/soccer-men/{slug}"
    errors=[]
    try:
        payload=fetch(api_url).json()
        out=[]
        for group in (payload or {}).get('data',[]) or []:
            conf=canonicalize_conference(group.get('conference'))
            if not conf: continue
            for r in group.get('standings',[]) or []:
                school=_value(r,'School','Team')
                if not school: continue
                out.append({
                    'conference':conf,'school':str(school).strip(),
                    'conference_record':_record_from_standing_row(r,'Conference'),
                    'overall_record':_record_from_standing_row(r,'Overall'),
                    'source':'NCAA','source_url':source_url,
                    'updated_at':now_iso(),'updated_text':payload.get('updated') or None,
                })
        if out:
            return {'ok':True,'items':out,'source_url':source_url,'updated':payload.get('updated'),'transport':'ncaa-api'}
        errors.append('NCAA standings API returned no rows')
    except Exception as exc:
        errors.append(f'NCAA standings API: {exc}')

    # Direct NCAA HTML fallback. This is deliberately conservative and only
    # records rows attached to an explicit conference heading.
    try:
        rr=fetch(source_url); soup=BeautifulSoup(rr.text,'lxml'); out=[]
        for heading in soup.select('.standings-conference'):
            conf=canonicalize_conference(heading.get_text(' ',strip=True))
            table=heading.find_next('table')
            if not conf or not table: continue
            headers=[x.get_text(' ',strip=True) for x in table.select('thead th')]
            for tr in table.select('tbody tr'):
                cells=[x.get_text(' ',strip=True) for x in tr.find_all('td')]
                if not cells: continue
                school=cells[0].strip()
                if not school: continue
                # NCAA soccer standings use conference and overall W/L/T groups.
                nums=[c for c in cells[1:] if re.fullmatch(r'\d+(?:\.\d+)?',c.strip())]
                # When exact subheaders are unavailable, read the first W/L/T and
                # next W/L/T triplets; if layout differs we keep the source row but
                # do not invent numbers.
                conf_rec=overall_rec=None
                ints=[c.strip() for c in cells[1:] if re.fullmatch(r'\d+',c.strip())]
                if len(ints)>=6:
                    conf_rec='-'.join(ints[:3]); overall_rec='-'.join(ints[3:6])
                out.append({'conference':conf,'school':school,'conference_record':conf_rec,
                            'overall_record':overall_rec,'source':'NCAA','source_url':source_url,
                            'updated_at':now_iso()})
        if out:
            return {'ok':True,'items':out,'source_url':source_url,'transport':'NCAA.com'}
    except Exception as exc:
        errors.append(f'NCAA.com standings: {exc}')
    return {'ok':False,'items':[],'error':'; '.join(errors),'source_url':source_url}


def fetch_ncaa_upcoming_window(division, start_date=None, days=10):
    """Fast upcoming-game fetch used by market cards.

    Instead of scanning the entire Aug-Dec calendar, this uses the one-request
    2026 schedule-alt payload to discover dates in the next few days and validates
    only those dates through the NCAA scoreboard. This makes NEXT MATCH populate
    quickly while the full-season sync can continue in the background.
    """
    from datetime import date as _date, timedelta
    slug=_division_slug(division)
    if not slug:
        return {'ok':False,'items':[],'error':'NCAA quick schedule supports D1/D2/D3 only'}
    start=_date.fromisoformat(start_date) if start_date else _date.today()
    end=start+timedelta(days=max(1,int(days)))
    dates=set(); errors=[]
    try:
        payload=fetch(f'{NCAA_API_BASE}/schedule-alt/soccer-men/{slug}/2026').json()
        _extract_schedule_dates(payload,dates)
    except Exception as exc:
        errors.append(f'schedule-alt: {exc}')
    candidates=sorted(d for d in dates if start.isoformat()<=d<=end.isoformat())
    if not candidates:
        # Fallback to a short contiguous window rather than the full season.
        candidates=[(start+timedelta(days=i)).isoformat() for i in range(0,min(int(days),7)+1)]
    items=[]; failures=[]
    for d in candidates:
        result=fetch_ncaa_scoreboard_date(division,d)
        if result.get('ok'): items.extend(result.get('items',[]))
        else: failures.append({'date':d,'error':result.get('error')})
    unique={}
    for item in items:
        unique[(item['game_date'],item['home_team'].lower(),item['away_team'].lower())]=item
    return {'ok':bool(unique) or not failures,'items':list(unique.values()),'dates_checked':len(candidates),
            'failures':failures,'errors':errors,'strategy':'fast upcoming NCAA window'}

def _score_int(value):
    try:
        if value is None or value == "": return None
        return int(str(value).strip())
    except Exception:return None


def _bool(v):
    return v is True or str(v).lower() in ('true','1','yes')


def _display_start_time(value):
    """Normalize NCAA time strings for a single, consistent Eastern display."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    raw=str(value or '').strip()
    if not raw:
        return ''
    # Full timestamps can be converted safely to U.S. Eastern time.
    if 'T' in raw:
        try:
            dt=datetime.fromisoformat(raw.replace('Z','+00:00'))
            if dt.tzinfo is not None:
                dt=dt.astimezone(ZoneInfo('America/New_York'))
                return dt.strftime('%I:%M %p').lstrip('0')+' ET'
        except Exception:
            pass
    # NCAA often returns an Eastern 24-hour clock (18:00, 22:00).
    m=re.fullmatch(r'(\d{1,2}):(\d{2})(?::\d{2})?',raw)
    if m:
        h=int(m.group(1)); minute=int(m.group(2))
        suffix='AM' if h<12 else 'PM'; hh=h%12 or 12
        return f'{hh}:{minute:02d} {suffix} ET'
    m=re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)',raw,re.I)
    if m:
        return f"{int(m.group(1))}:{m.group(2)} {m.group(3).upper()} ET"
    return raw


def _game_status(state, period='', clock='', start_time='', final_message=''):
    state=str(state or '').strip().lower()
    if state in {'final','f','finished','complete'}:
        suffix=str(final_message or '').strip()
        return 'final' + ((f' · {suffix}') if suffix and suffix.lower()!='final' else '')
    if state in {'live','i','in','inprogress'}:
        bits=[str(x).strip() for x in (period,clock) if str(x or '').strip() and str(x).strip()!='0:00']
        return 'live' + ((' · '+' · '.join(bits)) if bits else '')
    return 'scheduled' + ((f' · {start_time}') if str(start_time or '').strip() else '')


def _normalize_ncaa_date(value):
    """Normalize NCAA date strings so an upstream response cannot be mislabeled.

    The GraphQL/proxy payloads normally include startDate.  Earlier prototype
    builds forced every returned contest onto the requested date, which could
    make a stale/cached response look like today's schedule.
    """
    raw=str(value or '').strip()
    if not raw:
        return None
    m=re.search(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b",raw)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m=re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b",raw)
    if m:
        return f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    # Legacy Casablanca schedules also use MM-DD-YYYY.
    m=re.search(r"\b(\d{1,2})-(\d{1,2})-(20\d{2})\b",raw)
    if m:
        return f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return None


def _name_from_team_blob(team):
    if isinstance(team,str):
        return team.strip() or None
    if not isinstance(team,dict):
        return None
    names=team.get('names') if isinstance(team.get('names'),dict) else {}
    for key in ('nameShort','shortName','displayName','schoolName','name','name6Char','seoname','teamName','school','fullName'):
        val=team.get(key)
        if isinstance(val,str) and val.strip(): return val.strip()
    for key in ('full','short','char6','seo','display'):
        val=names.get(key)
        if isinstance(val,str) and val.strip(): return val.strip()
    for key in ('team','school','organization','contestant'):
        nested=team.get(key)
        if isinstance(nested,(dict,str)):
            val=_name_from_team_blob(nested)
            if val:return val
    return None

def _team_role(team):
    if not isinstance(team,dict):return ''
    if _bool(team.get('isHome')):return 'home'
    if team.get('isHome') is False:return 'away'
    for key in ('homeAway','contestantType','designation','side','role','location'):
        value=str(team.get(key) or '').strip().lower()
        if value in ('home','h','host'):return 'home'
        if value in ('away','a','visitor','visiting','road'):return 'away'
    return ''

def _schedule_date_from_dict(obj, inherited=None):
    if not isinstance(obj,dict): return inherited
    # Prefer explicit NCAA calendar/display dates over UTC timestamps.
    for key in ('contestDate','gameDate','scheduleDate','displayDate','date','eventDate','day'):
        if key in obj:
            d=_normalize_ncaa_date(obj.get(key))
            if d:return d
    for key in ('startDate','startDateTime','startDatetime','start','startTimeUtc','startTimeUTC'):
        if key in obj:
            d=_normalize_ncaa_date(obj.get(key))
            if d:return d
    # GraphQL wrappers occasionally rename the date field.  Accept any scalar
    # value that visibly contains a 2026 calendar date; do not infer dates from
    # array position or requested UI date.
    for value in obj.values():
        if isinstance(value,(str,int,float)):
            d=_normalize_ncaa_date(value)
            if d:return d
    return inherited


def _schedule_game_from_dict(obj, division, inherited_date=None):
    if not isinstance(obj,dict): return None
    game_date=_schedule_date_from_dict(obj,inherited_date)
    home=away=None

    # NCAA schedule/scoreboard payloads have used several labels over time.
    # Support both modern contestants/competitors and legacy teams arrays.
    arrays=[]
    for key in ('teams','contestants','competitors','participants','sides','teamBoxscore','contestTeams','organizations'):
        value=obj.get(key)
        if isinstance(value,list) and len(value)>=2: arrays.append(value)
    # Schema-tolerant fallback: any two-element list whose entries look like
    # team blobs can represent the home/away contestants.
    for value in obj.values():
        if not isinstance(value,list) or len(value)!=2 or value in arrays:
            continue
        if all(_name_from_team_blob(x) for x in value):
            arrays.append(value)
    for arr in arrays:
        h=next((x for x in arr if _team_role(x)=='home'),None)
        a=next((x for x in arr if _team_role(x)=='away'),None)
        if h is not None and a is not None:
            home,away=h,a;break
        # Two-team schedule arrays sometimes omit the role but preserve home/away order.
        if home is None and len(arr)==2 and all(isinstance(x,(dict,str)) for x in arr):
            names=[_name_from_team_blob(x) for x in arr]
            if all(names):
                home,away=arr[0],arr[1]

    # Direct home/away objects or strings.
    for hk,ak in (('homeTeam','awayTeam'),('home','away'),('homeContestant','awayContestant'),
                  ('homeParticipant','awayParticipant'),('homeCompetitor','awayCompetitor')):
        if home is None and isinstance(obj.get(hk),(dict,str)): home=obj.get(hk)
        if away is None and isinstance(obj.get(ak),(dict,str)): away=obj.get(ak)

    # Flat name fields appear in some schedule transforms.
    if home is None:
        for key in ('homeTeamName','homeName','homeSchool'):
            if isinstance(obj.get(key),str):home=obj.get(key);break
    if away is None:
        for key in ('awayTeamName','awayName','awaySchool','visitorTeamName','visitorName'):
            if isinstance(obj.get(key),str):away=obj.get(key);break

    home_name=_name_from_team_blob(home); away_name=_name_from_team_blob(away)
    if not home_name or not away_name or not game_date:return None

    def get_nested_score(blob):
        if not isinstance(blob,dict):return None
        value=blob.get('score')
        if isinstance(value,dict):
            value=value.get('score') or value.get('value') or value.get('displayValue')
        return _score_int(value)

    start=_display_start_time(obj.get('startTime') or obj.get('time') or obj.get('startTimeEastern') or obj.get('displayTime') or obj.get('timeText') or '')
    period=str(obj.get('currentPeriod') or obj.get('period') or '').strip()
    clock=str(obj.get('contestClock') or obj.get('clock') or '').strip()
    state=obj.get('gameState') or obj.get('status') or obj.get('state') or ''
    if isinstance(state,dict):state=state.get('type') or state.get('name') or state.get('description') or ''
    final_message=obj.get('finalMessage') or ''
    contest_id=obj.get('contestId') or obj.get('gameID') or obj.get('gameId') or obj.get('id')
    url=obj.get('url') or obj.get('gameUrl') or obj.get('contestUrl') or ''
    if isinstance(url,str) and url.startswith('/'):url='https://www.ncaa.com'+url
    if not url and contest_id:url=f'https://www.ncaa.com/game/{contest_id}'
    def conf(blob):
        if not isinstance(blob,dict):return None
        cs=blob.get('conferences')
        if isinstance(cs,list) and cs:
            c=cs[0] or {}; return c.get('conferenceName') or c.get('conferenceSeo')
        return blob.get('conferenceName') or blob.get('conferenceSeo') or blob.get('conference')
    return {
        'game_date':game_date,'home_team':home_name,'away_team':away_name,
        'home_score':get_nested_score(home),'away_score':get_nested_score(away),
        'status':_game_status(state,period,clock,start,final_message),'division':division,
        'venue':obj.get('venueName') or obj.get('venue') or obj.get('broadcasterName') or None,
        'source_url':url or None,'source_name':'NCAA.com (season schedule)',
        'source_updated_at':now_iso(),'external_id':str(contest_id) if contest_id not in (None,'') else None,
        'start_time':start or None,'current_period':period or None,'contest_clock':clock or None,
        'home_conference':conf(home),'away_conference':conf(away),
    }

def _parse_schedule_alt_payload(payload, division, target_date=None):
    """Extract games from NCAA's 2026+ full-season GraphQL schedule payload.

    NCAA has changed the nesting of this response more than once. The walker is
    intentionally schema-tolerant: it only accepts dictionaries that visibly
    contain a home and away team plus an explicit/inherited calendar date.
    """
    items=[];seen=set()
    def walk(value,inherited_date=None):
        if isinstance(value,dict):
            local_date=_schedule_date_from_dict(value,inherited_date)
            game=_schedule_game_from_dict(value,division,local_date)
            if game and (target_date is None or game['game_date']==target_date):
                key=(game['game_date'],game['home_team'].lower(),game['away_team'].lower())
                if key not in seen:
                    seen.add(key);items.append(game)
            for child in value.values():
                if isinstance(child,(dict,list)):walk(child,local_date)
        elif isinstance(value,list):
            for child in value:walk(child,inherited_date)
    walk(payload,None)
    return items


def fetch_ncaa_month_schedule_games(division, date_iso):
    """Fetch one NCAA calendar month from the official Casablanca schedule feed.

    Unlike the live scoreboard this endpoint is a schedule source, so future
    dates are available even before games are live.  One month is cached for
    fifteen minutes and date clicks become local filtering after the first hit.
    """
    import time
    slug=_division_slug(division)
    if not slug:
        return {'ok':False,'items':[],'error':'NCAA month schedule supports D1/D2/D3 only'}
    try:
        y,m,_=date_iso.split('-')
    except Exception:
        return {'ok':False,'items':[],'error':'Invalid date'}
    key=(division,int(y),int(m)); cached=_MONTH_SCHEDULE_CACHE.get(key)
    source_url=f'https://data.ncaa.com/casablanca/schedule/soccer-men/{slug}/{y}/{m}/schedule-all-conf.json'
    if cached and time.time()-cached['ts']<900:
        items=[x for x in cached['items'] if x.get('game_date')==date_iso]
        return {'ok':True,'items':items,'all_count':len(cached['items']),'transport':'NCAA official monthly schedule cache','source_url':source_url,'cached':True}
    try:
        payload=_coerce_json_object(fetch(source_url,timeout=5).json())
        if payload is None:
            raise RuntimeError('NCAA month schedule returned an unsupported payload')
        parsed=_parse_schedule_alt_payload(payload,division,None)
        if not parsed:
            raise RuntimeError('NCAA month schedule contained no parseable games')
        # Rewrite source metadata so the UI links to NCAA, not an internal API.
        for g in parsed:
            g['source_name']='NCAA.com (official monthly schedule)'
            if not g.get('source_url'):
                gd=(g.get('game_date') or date_iso).replace('-','/')
                g['source_url']=f'https://www.ncaa.com/scoreboard/soccer-men/{slug}/{gd}/all-conf'
        _MONTH_SCHEDULE_CACHE[key]={'ts':time.time(),'items':parsed}
        items=[x for x in parsed if x.get('game_date')==date_iso]
        return {'ok':True,'items':items,'all_count':len(parsed),'transport':'NCAA official monthly schedule','source_url':source_url,'cached':False}
    except Exception as exc:
        return {'ok':False,'items':[],'error':str(exc),'source_url':source_url}


def fetch_ncaa_schedule_alt_games(division, target_date=None, year=2026):
    """Read NCAA's 2026+ full-season schedule once, parse it, and cache it.

    A key detail for this prototype: a transport response that is valid JSON but
    contains an unfamiliar wrapper is *not* treated as a verified empty season.
    We try the direct NCAA GraphQL transport as well before falling back.
    """
    import time
    slug=_division_slug(division)
    if not slug:return {'ok':False,'items':[],'error':'NCAA season schedule supports D1/D2/D3 only'}
    cache_key=(division,int(year)); cached=_SCHEDULE_ALT_CACHE.get(cache_key)
    if cached and time.time()-cached['ts']<900:
        all_items=cached['items']
        selected=[x for x in all_items if not target_date or x.get('game_date')==target_date]
        return {'ok':True,'items':selected,'all_count':len(all_items),'transport':cached.get('transport','NCAA season schedule cache'),'cached':True}

    errors=[]; candidates=[]
    url=f'{NCAA_API_BASE}/schedule-alt/soccer-men/{slug}/{year}'
    try:
        payload=_coerce_json_object(fetch(url,timeout=7).json())
        if payload is not None:candidates.append(('ncaa-api / NCAA full-season schedule',payload))
        else:errors.append('schedule-alt mirror returned a non-JSON object')
    except Exception as exc:
        errors.append(f'schedule-alt mirror: {exc}')

    div_code={'D1':1,'D2':2,'D3':3}[division]
    extensions={'persistedQuery':{'version':1,'sha256Hash':NCAA_GQL_SCHEDULE_HASH}}
    variables={'sportCode':'MSO','division':div_code,'seasonYear':int(year)}
    try:
        r=fetch(NCAA_GQL_URL,params={
            'queryName':'NCAA_schedules_today_web',
            'extensions':json.dumps(extensions,separators=(',',':')),
            'variables':json.dumps(variables,separators=(',',':')),
        },timeout=7)
        payload=_coerce_json_object(r.json())
        if payload is not None:candidates.append(('NCAA direct full-season GraphQL',payload))
        else:errors.append('direct season schedule returned a non-JSON object')
    except Exception as exc:
        errors.append(f'direct season schedule: {exc}')

    best=[];best_transport=None
    for transport,payload in candidates:
        parsed=_parse_schedule_alt_payload(payload,division,None)
        if len(parsed)>len(best):best=parsed;best_transport=transport
    if not best:
        return {'ok':False,'items':[],'error':'; '.join(errors+['NCAA season payload contained no parseable games'])}
    _SCHEDULE_ALT_CACHE[cache_key]={'ts':time.time(),'items':best,'transport':best_transport}
    selected=[x for x in best if not target_date or x.get('game_date')==target_date]
    return {'ok':True,'items':selected,'all_count':len(best),'transport':best_transport,'source_url':url,'cached':False}

def _parse_proxy_scoreboard(payload, division, date_iso, slug):
    items=[]
    for wrap in (payload or {}).get('games',[]) or []:
        g=(wrap or {}).get('game',wrap or {});home=g.get('home') or {};away=g.get('away') or {}
        hn=home.get('names') or {}; an=away.get('names') or {}
        home_name=hn.get('full') or hn.get('short') or hn.get('char6') or hn.get('seo')
        away_name=an.get('full') or an.get('short') or an.get('char6') or an.get('seo')
        if not home_name or not away_name: continue
        # The scoreboard endpoint is already scoped to the requested NCAA calendar date.
        # startDate can be represented in UTC and may therefore be the following
        # calendar day for evening ET/PT matches. Trust the requested scoreboard
        # date instead of discarding valid games because of a timezone rollover.
        period=str(g.get('currentPeriod') or '').strip(); clock=str(g.get('contestClock') or '').strip(); start=_display_start_time(g.get('startTime') or '')
        game_url=g.get('url') or ''
        if game_url.startswith('/'):game_url='https://www.ncaa.com'+game_url
        elif not game_url:
            gid=g.get('gameID'); game_url=f'https://www.ncaa.com/game/{gid}' if gid else f'https://www.ncaa.com/scoreboard/soccer-men/{slug}/{date_iso.replace("-","/")}/all-conf'
        hc=((home.get('conferences') or [{}])[0] or {}); ac=((away.get('conferences') or [{}])[0] or {})
        items.append({'game_date':date_iso,'home_team':str(home_name).strip(),'away_team':str(away_name).strip(),
            'home_score':_score_int(home.get('score')),'away_score':_score_int(away.get('score')),
            'status':_game_status(g.get('gameState'),period,clock,start,g.get('finalMessage')),'division':division,
            'venue':g.get('network') or None,'source_url':game_url,'source_name':'NCAA.com',
            'source_updated_at':(payload or {}).get('updated_at') or now_iso(),'external_id':str(g.get('gameID') or '') or None,
            'start_time':start or None,'current_period':period or None,'contest_clock':clock or None,
            'home_conference':hc.get('conferenceName') or hc.get('conferenceSeo') or None,
            'away_conference':ac.get('conferenceName') or ac.get('conferenceSeo') or None})
    return items


def _parse_gql_scoreboard(payload, division, date_iso, slug):
    items=[]
    contests=((payload or {}).get('data') or {}).get('contests') or []
    for contest in contests:
        teams=contest.get('teams') or []
        home=next((t for t in teams if _bool(t.get('isHome'))),None)
        away=next((t for t in teams if not _bool(t.get('isHome'))),None)
        if not home or not away: continue
        home_name=home.get('nameShort') or home.get('name6Char') or home.get('seoname')
        away_name=away.get('nameShort') or away.get('name6Char') or away.get('seoname')
        if not home_name or not away_name: continue
        # NCAA's contest startDate may roll into the next UTC day for a game
        # that belongs to this scoreboard date in U.S. local time. The GraphQL
        # request itself is date-scoped, so keep every returned contest here.
        start=_display_start_time(contest.get('startTime') or ''); period=str(contest.get('currentPeriod') or '').strip();clock=str(contest.get('contestClock') or '').strip()
        url=contest.get('url') or ''
        if url.startswith('/'):url='https://www.ncaa.com'+url
        if not url and contest.get('contestId'):url=f"https://www.ncaa.com/game/{contest.get('contestId')}"
        items.append({'game_date':date_iso,'home_team':str(home_name).strip(),'away_team':str(away_name).strip(),
            'home_score':_score_int(home.get('score')),'away_score':_score_int(away.get('score')),
            'status':_game_status(contest.get('gameState'),period,clock,start,contest.get('finalMessage')),
            'division':division,'venue':contest.get('broadcasterName') or None,'source_url':url,
            'source_name':'NCAA.com (direct scoreboard)','source_updated_at':now_iso(),
            'external_id':str(contest.get('contestId') or '') or None,'start_time':start or None,
            'current_period':period or None,'contest_clock':clock or None,
            'home_conference':home.get('conferenceSeo') or None,'away_conference':away.get('conferenceSeo') or None})
    return items


def _fetch_ncaa_gql_scoreboard(division,date_iso):
    """Fetch one exact NCAA scoreboard date from NCAA's GraphQL transport.

    NCAA has used two contestDate representations in its web clients.  The
    maintained ncaa-api currently forwards YYYY/MM/DD while other NCAA clients
    expose MM/DD/YYYY.  Trying both is cheap and prevents adjacent calendar days
    from appearing empty when NCAA changes the accepted representation.
    """
    slug=_division_slug(division); div_code={'D1':1,'D2':2,'D3':3}[division]
    y,m,d=date_iso.split('-')
    date_candidates=[f'{y}/{m}/{d}',f'{m}/{d}/{y}']
    extensions={'persistedQuery':{'version':1,'sha256Hash':NCAA_GQL_SCOREBOARD_HASH}}
    errors=[]; empty_payload=None
    for contest_date in date_candidates:
        variables={'sportCode':'MSO','division':div_code,'seasonYear':int(y),'contestDate':contest_date}
        try:
            # Let requests encode the JSON query parameters. This is more robust
            # than concatenating braces/slashes into the URL by hand.
            r=fetch(NCAA_GQL_URL,params={
                'extensions':json.dumps(extensions,separators=(',',':')),
                'variables':json.dumps(variables,separators=(',',':')),
            },timeout=4)
            payload=r.json()
            contests=((payload.get('data') or {}).get('contests')) if isinstance(payload,dict) else None
            if payload.get('errors') or not isinstance(contests,list):
                raise RuntimeError('Invalid NCAA scoreboard response')
            items=_parse_gql_scoreboard(payload,division,date_iso,slug)
            if items:
                return {'ok':True,'items':items,'date':date_iso,'transport':'NCAA direct GraphQL','contest_date':contest_date,'source_url':f'https://www.ncaa.com/scoreboard/soccer-men/{slug}/{date_iso.replace("-","/")}/all-conf'}
            empty_payload=payload
        except Exception as exc:
            errors.append(f'{contest_date}: {exc}')
    if empty_payload is not None:
        return {'ok':True,'items':[],'date':date_iso,'transport':'NCAA direct GraphQL','source_url':f'https://www.ncaa.com/scoreboard/soccer-men/{slug}/{date_iso.replace("-","/")}/all-conf','warnings':errors}
    raise RuntimeError('; '.join(errors) or 'NCAA GraphQL unavailable')

def _parse_ncaa_scoreboard_html(html,division,date_iso,slug):
    """Best-effort official NCAA HTML fallback for scoreboard pages.

    NCAA has used several game-card class names.  We intentionally support the
    common variants rather than depending on one fragile selector.  Nothing is
    created unless two team names are visible in the official page markup.
    """
    soup=BeautifulSoup(html or '', 'lxml')
    cards=[]
    selectors=['.gamePod','.gamepod','[class*=gamePod]','[class*=scoreboard-game]','[class*=game-card]']
    for sel in selectors:
        found=soup.select(sel)
        if found:
            cards=found;break
    items=[];seen=set()
    def texts(card,selectors):
        for sel in selectors:
            vals=[x.get_text(' ',strip=True) for x in card.select(sel) if x.get_text(' ',strip=True)]
            if len(vals)>=2:return vals
        return []
    for card in cards:
        names=texts(card,['.gamePod-game-team-name','[class*=team-name]','[class*=teamName]'])
        if len(names)<2:continue
        # NCAA cards are conventionally away first, home second.
        away_name,home_name=names[0],names[1]
        key=(home_name.lower(),away_name.lower())
        if key in seen:continue
        seen.add(key)
        scores=texts(card,['.gamePod-game-team-score','[class*=team-score]','[class*=teamScore]'])
        away_score=_score_int(scores[0]) if len(scores)>0 else None
        home_score=_score_int(scores[1]) if len(scores)>1 else None
        status_el=card.select_one('.gamePod-status,[class*=game-status],[class*=gameStatus],[class*=status]')
        status_txt=status_el.get_text(' ',strip=True) if status_el else ''
        time_el=card.select_one('time,.gamePod-game-time,[class*=game-time],[class*=start-time]')
        start=_display_start_time(time_el.get_text(' ',strip=True) if time_el else '')
        st='final' if 'final' in status_txt.lower() else ('live' if any(x in status_txt.lower() for x in ('live','half','period')) else 'scheduled')
        if st=='scheduled' and start:st=f'scheduled · {start}'
        link=card.find('a',href=True);href=(link.get('href') if link else '') or ''
        if href.startswith('/'):href='https://www.ncaa.com'+href
        items.append({'game_date':date_iso,'home_team':home_name,'away_team':away_name,
            'home_score':home_score,'away_score':away_score,'status':st,'division':division,
            'venue':None,'source_url':href or f'https://www.ncaa.com/scoreboard/soccer-men/{slug}/{date_iso.replace("-","/")}/all-conf',
            'source_name':'NCAA.com','source_updated_at':now_iso(),'external_id':None,
            'start_time':start or None,'current_period':None,'contest_clock':None,
            'home_conference':None,'away_conference':None})
    return items

def _fetch_ncaa_html_scoreboard(division,date_iso):
    slug=_division_slug(division)
    url=f'https://www.ncaa.com/scoreboard/soccer-men/{slug}/{date_iso.replace("-","/")}/all-conf'
    r=fetch(url,timeout=3)
    items=_parse_ncaa_scoreboard_html(r.text,division,date_iso,slug)
    return {'ok':True,'items':items,'date':date_iso,'transport':'NCAA.com HTML','source_url':url}


def fetch_ncaa_scoreboard_date(division, date_iso):
    """Fetch one exact NCAA.com scoreboard date with fast fallbacks.

    The compatibility API mirrors NCAA.com's scoreboard and is deliberately
    tried first because it normalizes NCAA's current GraphQL response. NCAA's
    own GraphQL is the second authoritative path. Each network attempt has a
    short timeout so one unavailable transport cannot make a calendar click wait
    20-30 seconds.
    """
    slug=_division_slug(division)
    if not slug:
        return {'ok':False,'items':[],'error':'NCAA scoreboard supports D1/D2/D3 only'}
    y,m,d=date_iso.split('-')
    api_url=f'{NCAA_API_BASE}/scoreboard/soccer-men/{slug}/{y}/{m}/{d}/all-conf'
    source_url=f'https://www.ncaa.com/scoreboard/soccer-men/{slug}/{y}/{m}/{d}/all-conf'
    errors=[]; zero_seen=False

    # 1) NCAA official GraphQL. This is the same transport used by the current
    # NCAA scoreboard and should be preferred over third-party mirrors.
    try:
        direct=_fetch_ncaa_gql_scoreboard(division,date_iso)
        if direct.get('items'):
            direct['authoritative']=True
            return direct
        zero_seen=True
    except Exception as exc:
        errors.append(f'NCAA direct: {exc}')

    # 2) Maintained compatibility mirror of NCAA.com's GraphQL data.
    try:
        payload=fetch(api_url,timeout=4).json()
        items=_parse_proxy_scoreboard(payload,division,date_iso,slug)
        if items:
            return {'ok':True,'items':items,'date':date_iso,'api_url':api_url,'transport':'ncaa-api / NCAA scoreboard','source_url':source_url,'authoritative':True}
        zero_seen=True
    except Exception as exc:
        errors.append(f'ncaa-api: {exc}')

    # 3) NCAA HTML is a last resort. Keep the timeout short; the current page is
    # often client-rendered, so this fallback should never block the UI.
    try:
        html_result=_fetch_ncaa_html_scoreboard(division,date_iso)
        if html_result.get('items'):
            html_result['authoritative']=True
            return html_result
        zero_seen=True
    except Exception as exc:
        errors.append(f'NCAA HTML: {exc}')

    # 4) Official NCAA monthly schedule.  This feed is designed for future
    # fixtures and is usually the fastest reliable source when the scoreboard is
    # empty before kickoff.
    try:
        month=fetch_ncaa_month_schedule_games(division,date_iso)
        if month.get('items'):
            month['date']=date_iso
            month['authoritative']=True
            return month
        if not month.get('ok'):
            errors.append(f"NCAA month schedule: {month.get('error')}")
    except Exception as exc:
        errors.append(f'NCAA month schedule: {exc}')

    # 5) Official NCAA full-season schedule fallback. This is only used when
    # the exact-date scoreboard and official monthly schedule both return no
    # fixtures. The parser now requires an explicit/inherited calendar date plus
    # two visible team identities, so it can safely fill future schedule dates
    # that the live scoreboard has not published yet.
    try:
        season=fetch_ncaa_schedule_alt_games(division,target_date=date_iso,year=int(y))
        if season.get('items'):
            season['date']=date_iso
            season['authoritative']=True
            return season
        if not season.get('ok'):
            errors.append(f"NCAA full-season schedule: {season.get('error')}")
    except Exception as exc:
        errors.append(f'NCAA full-season schedule: {exc}')

    # 6) Small bundled verified snapshot for the launch/demo week. This is a
    # safety net for transport outages, not fabricated data; live NCAA/official
    # school rows always take precedence above.
    try:
        from .verified_schedule import fetch_verified_schedule_snapshot
        snap=fetch_verified_schedule_snapshot(division,date_iso)
        if snap.get('items'):
            snap['warnings']=errors
            snap['authoritative']=True
            return snap
    except Exception as exc:
        errors.append(f'verified snapshot: {exc}')

    if zero_seen:
        # An empty past/today scoreboard is meaningful: the date can genuinely
        # have no games and an exact refresh may clear stale prototype rows.
        # For FUTURE dates, however, an empty live scoreboard is not proof that
        # the schedule is empty.  Preserve any cached fixtures and let the
        # monthly/full-season schedule path fill that date instead.
        from datetime import date as _date
        if date_iso <= _date.today().isoformat():
            return {'ok':True,'items':[],'date':date_iso,'transport':'verified zero after official exact-date transports','source_url':source_url,'warnings':errors,'authoritative':True,'authoritative_zero':True}
        return {'ok':False,'items':[],'date':date_iso,'error':'; '.join(errors) or 'Future NCAA scoreboard is empty; cached schedule preserved','api_url':api_url,'authoritative':False,'authoritative_zero':False}
    return {'ok':False,'items':[],'date':date_iso,'error':'; '.join(errors) or 'No verified NCAA response','api_url':api_url}


def _extract_schedule_dates(value, out):
    """Recursively pull real 2026 ISO dates from the NCAA schedule JSON."""
    if isinstance(value, dict):
        for k,v in value.items():
            if isinstance(v,str):
                for m in re.finditer(r"\b(2026)[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b",v):
                    out.add(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
                for m in re.finditer(r"\b(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])/(2026)\b",v):
                    out.add(f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}")
            _extract_schedule_dates(v,out)
    elif isinstance(value, list):
        for v in value:_extract_schedule_dates(v,out)
    elif isinstance(value,str):
        for m in re.finditer(r"\b(2026)[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b",value):
            out.add(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
        for m in re.finditer(r"\b(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])/(2026)\b",value):
            out.add(f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}")


def fetch_ncaa_schedule_dates(division, year=2026):
    """Use NCAA's schedule endpoint to discover every men's-soccer game date.

    The route returns game dates by sport/division/month. We still validate each
    candidate through the scoreboard before anything is stored.
    """
    slug=_division_slug(division)
    if not slug:return {'ok':False,'dates':[],'error':'NCAA schedule supports D1/D2/D3 only'}
    dates=set();errors=[]
    # Current GraphQL-backed full-season schedule first.
    try:
        payload=fetch(f'{NCAA_API_BASE}/schedule-alt/soccer-men/{slug}/{year}').json()
        _extract_schedule_dates(payload,dates)
    except Exception as exc:
        errors.append(f'schedule-alt: {exc}')
    # Legacy month route is still useful as an independent completeness check.
    for month in range(8,13):
        url=f'{NCAA_API_BASE}/schedule/soccer-men/{slug}/{year}/{month:02d}'
        try:
            payload=fetch(url).json();_extract_schedule_dates(payload,dates)
        except Exception as exc:
            errors.append(f'{month:02d}: {exc}')
    return {'ok':bool(dates),'dates':sorted(dates),'errors':errors,'source':'NCAA schedule API + schedule-alt'}


def fetch_ncaa_scoreboard_history(division, start_date, end_date):
    """Fetch every NCAA scoreboard date in the requested interval.

    Earlier prototype builds trusted the schedule endpoint to provide a complete
    list of dates. In practice that route can omit dates for soccer, which is why
    the UI could show games on Sept. 9 but nothing on nearby dates. The final
    prototype deliberately validates *every calendar day* against the NCAA
    scoreboard. At roughly 0.22 s between requests this stays below the public
    API's 5 req/s limit while favoring completeness over speed.
    """
    from datetime import date as _date, timedelta
    import time
    start=_date.fromisoformat(start_date); end=_date.fromisoformat(end_date)
    all_items=[]; failures=[]; checked=[]

    # Exact-date clicks are the latency-sensitive path. Do not make an extra
    # schedule-discovery request before asking for the selected scoreboard day.
    # The NCAA scoreboard request alone is authoritative for that calendar date.
    if start == end:
        iso=start.isoformat(); checked.append(iso)
        result=fetch_ncaa_scoreboard_date(division,iso)
        if result.get('ok'):
            all_items.extend(result.get('items',[]))
        else:
            failures.append({'date':iso,'error':result.get('error')})
        unique={}
        for item in all_items:
            unique[(item['game_date'],item['home_team'].lower(),item['away_team'].lower())]=item
        return {
            'ok':bool(unique) or not failures,
            'items':list(unique.values()),
            'failures':failures,
            'start':start_date,
            'end':end_date,
            'dates_checked':1,
            'schedule_dates':0,
            'schedule_discovery':{'ok':True,'dates':[],'skipped_for_exact_date':True},
            'strategy':'exact NCAA scoreboard date',
            'authoritative':result.get('authoritative',True),
            'authoritative_zero':bool(result.get('authoritative_zero')),
            'transport':result.get('transport'),
            'source_url':result.get('source_url'),
        }

    # Full-range sync: schedule discovery is diagnostics only and never decides
    # which calendar days are skipped.
    schedule=fetch_ncaa_schedule_dates(division,2026)
    cur=start
    candidate=[]
    while cur<=end:
        candidate.append(cur)
        cur+=timedelta(days=1)

    for i,cur in enumerate(candidate):
        iso=cur.isoformat(); checked.append(iso)
        result=fetch_ncaa_scoreboard_date(division,iso)
        if result.get('ok'):
            all_items.extend(result.get('items',[]))
        else:
            failures.append({'date':iso,'error':result.get('error')})
        if i+1<len(candidate):
            time.sleep(0.22)

    unique={}
    for item in all_items:
        unique[(item['game_date'],item['home_team'].lower(),item['away_team'].lower())]=item
    return {
        'ok':bool(unique) or not failures,
        'items':list(unique.values()),
        'failures':failures,
        'start':start_date,
        'end':end_date,
        'dates_checked':len(checked),
        'schedule_dates':len(schedule.get('dates',[]) if schedule.get('ok') else []),
        'schedule_discovery':schedule,
        'strategy':'exhaustive NCAA scoreboard date scan',
    }

