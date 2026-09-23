import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .common import fetch, now_iso
from services.fantasy import normalize_position

CLASS_MAP = {
    "fr.": "Fr.", "freshman": "Fr.",
    "so.": "So.", "sophomore": "So.",
    "jr.": "Jr.", "junior": "Jr.",
    "sr.": "Sr.", "senior": "Sr.",
    "5th": "5th", "fifth year": "5th",
    "gr.": "Gr.", "graduate": "Gr.",
}


def _clean_class(value):
    key = (value or "").strip().lower()
    return CLASS_MAP.get(key, value.strip() if value else None)


def _coach_role(title):
    t = (title or "").lower()
    if "associate" in t and "head" in t and "coach" in t:
        return "Assistant Coach"
    if "head" in t and "coach" in t:
        return "Head Coach"
    if "assistant" in t and "coach" in t:
        return "Assistant Coach"
    return None


def parse_sidearm_roster(url, school, conference=None):
    """Generic parser for common SIDEARM-style roster tables/cards."""
    response = fetch(url)
    soup = BeautifulSoup(response.text, "lxml")
    players, coaches, seen = [], [], set()

    # Prefer actual roster table when present.
    for table in soup.find_all("table"):
        headers = [x.get_text(" ", strip=True) for x in table.find_all("th")]
        lowered = [h.lower() for h in headers]
        if not any("name" == h or h.startswith("name") for h in lowered):
            continue
        for tr in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
            if len(cells) < 3:
                continue
            # Heuristic table shape: No, Name, Pos, Ht, Wt, Yr...
            name = cells[1].strip() if len(cells) > 1 else ""
            pos = normalize_position(cells[2] if len(cells) > 2 else "")
            if not name or pos not in {"GK", "DF", "MF", "FW"}:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            class_year = None
            for cell in cells[3:7]:
                if cell.strip().lower() in CLASS_MAP:
                    class_year = _clean_class(cell)
                    break
            players.append({
                "name": re.sub(r"^\d+\s+|\s+\d+$", "", name).strip(),
                "school": school,
                "position": pos,
                "class_year": class_year,
                "jersey": cells[0] if cells and cells[0].isdigit() else None,
                "conference": conference,
                "source_url": url,
                "source_name": "official_school",
                "source_updated_at": now_iso(),
            })

    # Coaching tables are usually especially consistent.
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for tr in rows:
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
            if len(cells) < 2:
                continue
            role = _coach_role(cells[-1])
            if not role:
                continue
            name = cells[-2].strip()
            if name and name.lower() not in {"name", "view full bio", "full bio"}:
                coaches.append({
                    "name": name,
                    "school": school,
                    "role": role,
                    "conference": conference,
                    "source_url": url,
                })

    return {"players": players, "coaches": coaches, "url": url}


def parse_sidearm_stats(url):
    """Parse cumulative player/goalkeeper tables from common athletics-site vendors.

    SIDEARM, PrestoSports and several custom sites use different labels for the
    same columns. We normalize those labels, merge field-player + goalkeeper
    rows, and only persist rows that identify a real player and at least games or
    minutes. No numbers are inferred from fantasy values.
    """
    response = fetch(url)
    soup = BeautifulSoup(response.text, "lxml")
    aliases={
        'PLAYER':'PLAYER','NAME':'PLAYER','STUDENT-ATHLETE':'PLAYER','ATHLETE':'PLAYER','GOALIE':'PLAYER','GOALKEEPER':'PLAYER',
        'GP':'GP','GAMES':'GP','GAMES PLAYED':'GP','G':'G','GOALS':'G','A':'A','ASSISTS':'A','PTS':'PTS','POINTS':'PTS',
        'GS':'GS','STARTS':'GS','GAMES STARTED':'GS','MIN':'MIN','MINUTES':'MIN','MINUTES PLAYED':'MIN',
        'SH':'SH','SHOTS':'SH','SOG':'SOG','SHOTS ON GOAL':'SOG','GW':'GW','GAME WINNERS':'GW','GAME-WINNING GOALS':'GW',
        'SV':'SV','SAVES':'SV','GA':'GA','GOALS AGAINST':'GA','SHO':'SHO','SO':'SHO','SHUTOUTS':'SHO','CLEAN SHEETS':'SHO',
        'YC':'YC','YELLOW CARDS':'YC','RC':'RC','RED CARDS':'RC','YC-RC':'YC-RC'
    }
    def canon(text):
        x=re.sub(r'\s+',' ',str(text or '').replace('\xa0',' ').strip().upper())
        x=re.sub(r'\([^)]*\)','',x).strip()
        return aliases.get(x,x)
    def number(raw, default=0.0):
        txt=str(raw or '').strip().replace(',','')
        if ':' in txt and re.match(r'^\d+:\d+',txt):
            a,b=txt.split(':',1)
            try:return float(a)+float(b)/60.0
            except Exception:return default
        m=re.search(r'-?\d+(?:\.\d+)?',txt)
        try:return float(m.group()) if m else default
        except Exception:return default
    gathered=[]
    for table in soup.find_all('table'):
        header_rows=table.find_all('tr')[:4]
        headers=[]
        for hr in header_rows:
            hs=[canon(x.get_text(' ',strip=True)) for x in hr.find_all('th')]
            if len(hs)>len(headers):headers=hs
        if not headers:continue
        if 'PLAYER' not in headers:continue
        if not any(x in headers for x in ('GP','MIN','G','A','SV','GA','SHO')):continue
        for tr in table.find_all('tr'):
            cells=[c.get_text(' ',strip=True) for c in tr.find_all(['th','td'])]
            if len(cells)<3:continue
            # Some responsive tables repeat a leading rank/jersey cell. Align from
            # the right when there is one extra cell; otherwise require a safe map.
            hs=headers
            if len(cells)!=len(hs):
                if len(cells)==len(hs)+1:cells=cells[-len(hs):]
                elif len(cells)<len(hs):continue
                else:cells=cells[:len(hs)]
            rec=dict(zip(hs,cells))
            name=str(rec.get('PLAYER','')).strip()
            name=re.sub(r'^#?\d+\s+|\s+#?\d+$','',name).strip()
            if ',' in name:
                last,first=[x.strip() for x in name.split(',',1)];name=f'{first} {last}'.strip()
            if not name or name.lower() in {'player','goalie','goalkeeper','total','totals','opponents'}:continue
            gp=int(number(rec.get('GP'),0)); mins=number(rec.get('MIN'),0)
            if gp<=0 and mins<=0 and not any(number(rec.get(x),0)>0 for x in ('G','A','SV','SHO')):continue
            yc=int(number(rec.get('YC'),0));rc=int(number(rec.get('RC'),0))
            card=str(rec.get('YC-RC',''))
            if '-' in card:
                try:yc,rc=[int(number(x,0)) for x in card.split('-',1)]
                except Exception:pass
            gathered.append({
                'name':name,'games':gp,'starts':int(number(rec.get('GS'),0)),'minutes':mins,
                'goals':int(number(rec.get('G'),0)),'assists':int(number(rec.get('A'),0)),'points':int(number(rec.get('PTS'),0)),
                'shots':int(number(rec.get('SH'),0)),'shots_on_goal':int(number(rec.get('SOG'),0)),
                'yellow_cards':yc,'red_cards':rc,'game_winners':int(number(rec.get('GW'),0)),
                'saves':int(number(rec.get('SV'),0)),'goals_against':int(number(rec.get('GA'),0)),'shutouts':number(rec.get('SHO'),0),
                'source_url':url,'source_name':'official_school','source_updated_at':now_iso(),
            })
    # Merge a player's field and goalkeeper rows when a site splits the tables.
    best={}
    numeric=['games','starts','minutes','goals','assists','points','shots','shots_on_goal','yellow_cards','red_cards','game_winners','saves','goals_against','shutouts']
    for item in gathered:
        key=re.sub(r'[^a-z0-9]','',item['name'].lower())
        if key not in best:best[key]=item.copy();continue
        cur=best[key]
        for k in numeric:cur[k]=max(float(cur.get(k,0) or 0),float(item.get(k,0) or 0))
        for k in ('games','starts','goals','assists','points','shots','shots_on_goal','yellow_cards','red_cards','game_winners','saves','goals_against'):
            cur[k]=int(cur[k])
    return list(best.values())


def discover_related_urls(official_or_roster_url):
    """Find roster/schedule/stats endpoints for one official athletics site.

    The rule is identical for every school.  Most SIDEARM sites use the same
    ``/sports/mens-soccer/{roster|schedule|stats}`` path family, so derive those
    deterministic siblings first and then let links on the page override them.
    This prevents one manually configured school from having better data access
    than the rest of the division.
    """
    out = {"roster": None, "schedule": None, "stats": None}
    raw = str(official_or_roster_url or '').strip()
    if not raw:
        return out

    # Universal SIDEARM/Presto-style sibling URLs.  Preserve an explicit season
    # suffix when the source already has one (e.g. /roster/2026).
    m = re.search(r"(/sports/[^/?#]*soccer[^/?#]*/)(roster|schedule|stats)(/2026)?(?:[/?#].*)?$", raw, re.I)
    if m:
        root = raw[:m.start()] + m.group(1)
        suffix = m.group(3) or ''
        out['roster'] = root + 'roster' + suffix
        out['schedule'] = root + 'schedule' + suffix
        out['stats'] = root + 'stats' + suffix
    else:
        # Common no-season form; links discovered below can replace these.
        for token in ('/roster','/schedule','/stats'):
            if token in raw.lower():
                idx = raw.lower().find(token)
                base = raw[:idx]
                tail = raw[idx+len(token):]
                season = '/2026' if '/2026' in tail else ''
                out['roster'] = base + '/roster' + season
                out['schedule'] = base + '/schedule' + season
                out['stats'] = base + '/stats' + season
                break

    try:
        response = fetch(raw)
        soup = BeautifulSoup(response.text, "lxml")
        for a in soup.find_all("a", href=True):
            label = a.get_text(" ", strip=True).lower()
            href = urljoin(raw, a["href"])
            hlow = href.lower()
            if "soccer" not in hlow:
                continue
            if "roster" in label or "/roster" in hlow:
                out["roster"] = href
            if "schedule" in label or "/schedule" in hlow:
                out["schedule"] = href
            if label in {"stats","statistics"} or "/stats" in hlow:
                out["stats"] = href
    except Exception:
        # The deterministic sibling URLs above are still useful when the roster
        # page blocks a discovery request; the actual parser will validate them.
        pass
    return out


def parse_official_schedule(url, school, division="D1"):
    """Best-effort parser for official school schedule pages (SIDEARM/Presto-like markup).

    Only rows with a confidently parsed opponent and date are returned. Scores are never guessed.
    """
    from datetime import datetime
    response = fetch(url)
    soup = BeautifulSoup(response.text, "lxml")
    candidates = soup.select("li.sidearm-schedule-game, div.sidearm-schedule-game, [class*='schedule-game'], tr")
    items, seen = [], set()
    month_re = re.compile(r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+(\d{1,2})(?:,\s*(\d{4}))?\b", re.I)
    iso_re = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")
    score_re = re.compile(r"\b(?:W|L|T)?\s*,?\s*(\d{1,2})\s*[-–]\s*(\d{1,2})\b", re.I)
    for node in candidates:
        text = " ".join(node.stripped_strings)
        if not text or len(text) > 1200:
            continue
        date_iso = None
        time_node = node.find("time")
        if time_node and time_node.get("datetime"):
            raw = time_node.get("datetime")[:10]
            if iso_re.match(raw): date_iso = raw
        if not date_iso:
            mi = iso_re.search(text)
            if mi: date_iso = mi.group(0)
        if not date_iso:
            mm = month_re.search(text)
            if mm:
                try:
                    year = int(mm.group(3) or 2026)
                    date_iso = datetime.strptime(f"{mm.group(1)} {mm.group(2)} {year}", "%b %d %Y").date().isoformat()
                except Exception:
                    try: date_iso = datetime.strptime(f"{mm.group(1)} {mm.group(2)} {year}", "%B %d %Y").date().isoformat()
                    except Exception: date_iso = None
        if not date_iso:
            continue
        opp = None
        for sel in [".sidearm-schedule-game-opponent-name", ".sidearm-schedule-game-opponent-text", "[class*='opponent'] a", "[class*='opponent']"]:
            el = node.select_one(sel)
            if el:
                opp = el.get_text(" ", strip=True)
                if opp: break
        if not opp:
            links = [a.get_text(" ", strip=True) for a in node.find_all("a") if a.get_text(" ", strip=True)]
            links = [x for x in links if x.lower() not in {"recap","box score","history","video","live stats","tickets"}]
            if links: opp = max(links, key=len)
        if not opp or opp.lower() == school.lower():
            continue
        opp = re.sub(r"^(vs\.?|at)\s+", "", opp, flags=re.I).strip()
        if not opp or len(opp) < 2:
            continue
        at_away = bool(re.search(r"\bat\b", text, re.I)) and not bool(re.search(r"\bvs\.?\b", text, re.I))
        sm = score_re.search(text)
        hs = as_ = None
        status = "scheduled"
        if sm:
            first, second = int(sm.group(1)), int(sm.group(2))
            status = "final"
            # W/L scores on team schedule pages are listed from the school's perspective.
            school_score, opp_score = first, second
            if at_away:
                hs, as_ = opp_score, school_score
            else:
                hs, as_ = school_score, opp_score
        home, away = (opp, school) if at_away else (school, opp)
        key = (date_iso, home.lower(), away.lower())
        if key in seen: continue
        seen.add(key)
        items.append({"game_date":date_iso,"home_team":home,"away_team":away,"home_score":hs,"away_score":as_,"status":status,"division":division,"source_url":url,"source_name":"official_school","source_updated_at":now_iso()})
    return {"ok": True, "items": items, "school": school, "url": url}
