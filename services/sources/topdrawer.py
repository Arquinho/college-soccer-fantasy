import re
from bs4 import BeautifulSoup
from .common import fetch, now_iso
from urllib.parse import urljoin
from services.conferences import canonicalize_conference, fallback_conference_for_school

TDS_MEN_URL = "https://www.topdrawersoccer.com/college-soccer/men"
TDS_RANKINGS_URL = "https://www.topdrawersoccer.com/college-soccer-national-rankings/men"
TDS_PLAYER_URL = "https://www.topdrawersoccer.com/college-soccer/college-national-top-100/men/2026"
TDS_FRESHMAN_URL = "https://www.topdrawersoccer.com/college-soccer/college-national-freshmen-top-100/men"
TDS_STANDINGS_URL = "https://www.topdrawersoccer.com/college-soccer/college-soccer-conference-standings/men"
TDS_COMPOSITE_URL = "https://www.topdrawersoccer.com/college-soccer-composite-team-ranking/men"


TDS_SCOREBOARD_URLS = {
    "D1": "https://www.topdrawersoccer.com/college-soccer/college-scoreboard/men/divisionid-1",
    "D2": "https://www.topdrawersoccer.com/college-soccer/college-scoreboard/men/divisionid-2",
}

def _tds_clean_team(text):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    # Public score tables append record/conference metadata in a final parenthetical.
    # Keep genuine school qualifiers such as St. Thomas (Minn.) or Saint Mary's (CA).
    text = re.sub(r"\s+\(\d+\)\s*(?=\()", " ", text)
    text = re.sub(r"\s+\(\d+-\d+(?:-\d+)?(?:,.*)?\)\s*$", "", text)
    return text.strip()

def _tds_target_heading(date_iso):
    from datetime import date as _date
    dt=_date.fromisoformat(date_iso)
    return f"{dt.strftime('%A')}, {dt.strftime('%B')} {dt.day} {dt.year}"

def _parse_tds_scoreboard_html(html, division, date_iso, source_url):
    """Parse the public men's college score table for one exact calendar day.

    This is a *fallback* only. NCAA.com/official school schedules remain the
    authoritative source when available. No row is created unless the public
    page exposes two teams and a time/result.
    """
    soup=BeautifulSoup(html or '', 'lxml')
    wanted=_tds_target_heading(date_iso).lower()
    heading=None
    for tag in soup.find_all(['h1','h2','h3','h4','h5','strong','b','div','span','p']):
        txt=' '.join(tag.get_text(' ',strip=True).split())
        if txt.lower()==wanted:
            heading=tag;break
    if not heading:
        return []
    table=heading.find_next('table')
    if not table:
        return []
    items=[];seen=set()
    for tr in table.find_all('tr'):
        cells=[' '.join(x.get_text(' ',strip=True).split()) for x in tr.find_all(['th','td'])]
        if len(cells)<3: continue
        if cells[0].lower() in {'home','team','school'} or cells[1].lower() in {'score','time'}: continue
        home=_tds_clean_team(cells[0]); middle=cells[1].strip(); away=_tds_clean_team(cells[2])
        if not home or not away or home.lower()==away.lower(): continue
        # Avoid accidentally reading a following date's table if markup nests sections.
        key=(home.lower(),away.lower(),middle.lower())
        if key in seen: continue
        seen.add(key)
        hs=as_=None; status='scheduled'; start_time=None
        m=re.match(r'^\s*(\d+)\s*:\s*(\d+)',middle)
        if m:
            hs,as_=int(m.group(1)),int(m.group(2)); status='final'
        elif re.search(r'\b(?:AM|PM)\b',middle,re.I):
            start_time=middle; status=f'scheduled · {middle}'
        elif middle.strip() in {'-','—','–','TBD',''}:
            status='scheduled'
        else:
            # Do not synthesize a score/status from unknown public text.
            continue
        items.append({
            'game_date':date_iso,'home_team':home,'away_team':away,
            'home_score':hs,'away_score':as_,'status':status,'division':division,
            'venue':None,'source_url':source_url,'source_name':'TopDrawerSoccer (schedule fallback)',
            'source_updated_at':now_iso(),'external_id':None,'start_time':start_time,
            'current_period':None,'contest_clock':None,'home_conference':None,'away_conference':None,
        })
    return items

def fetch_tds_scoreboard_date(division, date_iso):
    """Secondary public schedule fallback for NCAA D1/D2.

    The main www host occasionally returns a gateway error, so the public admin
    mirror is tried only if needed. This function never overrides verified NCAA
    rows; it exists to prevent an empty calendar when NCAA's date endpoint is
    temporarily unavailable.
    """
    base=TDS_SCOREBOARD_URLS.get(division)
    if not base:
        return {'ok':False,'items':[],'error':'TopDrawer schedule fallback supports D1/D2 only'}
    urls=[base,base.replace('://www.','://admin.')]
    errors=[]
    for url in urls:
        try:
            r=fetch(url,timeout=5)
            items=_parse_tds_scoreboard_html(r.text,division,date_iso,url)
            if items:
                return {'ok':True,'items':items,'date':date_iso,'transport':'TopDrawerSoccer public scoreboard','source_url':url}
            errors.append(f'{url}: date/table not found')
        except Exception as exc:
            errors.append(f'{url}: {exc}')
    return {'ok':False,'items':[],'date':date_iso,'error':'; '.join(errors)}


def fetch_tds_top25():
    """Reads the publicly visible DI ranking table only."""
    try:
        r = fetch(TDS_MEN_URL)
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for table in soup.find_all("table"):
            text = table.get_text(" ", strip=True).lower()
            if "overall" not in text or "conf" not in text:
                continue
            for tr in table.find_all("tr"):
                cells = [x.get_text(" ", strip=True) for x in tr.find_all(["th", "td"])]
                if len(cells) >= 4 and cells[0].isdigit():
                    items.append({
                        "rank": int(cells[0]),
                        "school": cells[1],
                        "overall_record": cells[2],
                        "conference_record": cells[3],
                        "source": "TopDrawerSoccer",
                        "source_url": TDS_MEN_URL,
                        "updated_at": now_iso(),
                    })
            if items:
                break
        return {"ok": True, "items": items[:25]}
    except Exception as exc:
        return {"ok": False, "items": [], "error": str(exc)}


def fetch_tds_player_rankings():
    """Only parses rows visible on the public page; does not bypass gated content."""
    try:
        r = fetch(TDS_PLAYER_URL)
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for tr in soup.find_all("tr"):
            cells = [x.get_text(" ", strip=True) for x in tr.find_all(["th", "td"])]
            if len(cells) >= 5 and cells[0].isdigit():
                items.append({
                    "rank": int(cells[0]),
                    "name": re.sub(r"\s+", " ", cells[1]).strip(),
                    "conference": cells[2],
                    "school": cells[3],
                    "position": cells[4],
                    "source": "TopDrawerSoccer",
                    "source_url": TDS_PLAYER_URL,
                })
        return {"ok": True, "items": items}
    except Exception as exc:
        return {"ok": False, "items": [], "error": str(exc)}


def _parse_player_table(url, category):
    try:
        r = fetch(url)
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for tr in soup.find_all("tr"):
            cells = [x.get_text(" ", strip=True) for x in tr.find_all(["th", "td"])]
            if len(cells) >= 5 and cells[0].isdigit():
                items.append({
                    "rank": int(cells[0]), "name": re.sub(r"\s+", " ", cells[1]).strip(),
                    "conference": cells[2], "school": cells[3], "position": cells[4],
                    "category": category, "source": "TopDrawerSoccer", "source_url": url
                })
        return {"ok": True, "items": items}
    except Exception as exc:
        return {"ok": False, "items": [], "error": str(exc)}


def fetch_tds_freshman_rankings():
    return _parse_player_table(TDS_FRESHMAN_URL, "freshman_top100")


def fetch_tds_composite():
    try:
        r = fetch(TDS_COMPOSITE_URL)
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for tr in soup.find_all("tr"):
            cells = [x.get_text(" ", strip=True) for x in tr.find_all(["th", "td"])]
            if len(cells) >= 2 and cells[0].isdigit():
                items.append({"rank": int(cells[0]), "school": cells[1], "source": "TopDrawerSoccer Composite", "source_url": TDS_COMPOSITE_URL})
        return {"ok": True, "items": items}
    except Exception as exc:
        return {"ok": False, "items": [], "error": str(exc)}


def _tds_standing_rows(soup, source_url, fallback_conference=None):
    items=[]
    known={'ASUN','America East','American Athletic','Atlantic 10','ACC','Big East','Big South','Big Ten','Big West',
           'CAA','CUSA','Horizon League','Independent','Ivy League','MAAC','MAC','Missouri Valley','NEC','OVC',
           'Patriot League','SoCon','Summit League','Sun Belt','WCC','WAC'}
    explicit=fallback_conference
    h1=soup.find('h1')
    if h1:
        txt=' '.join(h1.get_text(' ',strip=True).split())
        m=re.search(r"Men(?:'s|’s)\s+(.+?)\s+Conference$",txt,re.I)
        if m: explicit=canonicalize_conference(m.group(1).strip())
    for table in soup.find_all('table'):
        table_text=table.get_text(' ',strip=True).lower()
        if 'conf' not in table_text and 'overall' not in table_text:
            continue
        conf=explicit
        if not conf:
            # On the all-conference page the league name is a short label just
            # before each table. Walk backward until a recognized men's-soccer
            # conference name is found.
            for node in table.find_all_previous(string=True,limit=80):
                txt=' '.join(str(node).split()).strip(' :')
                if not txt or len(txt)>55: continue
                c=canonicalize_conference(txt)
                if c in known:
                    conf=c;break
        local=[]
        for tr in table.find_all('tr'):
            cells=[' '.join(x.get_text(' ',strip=True).split()) for x in tr.find_all(['th','td'])]
            if len(cells)<3: continue
            offset=1 if re.fullmatch(r'\d+',cells[0] or '') else 0
            if len(cells)<offset+3: continue
            school=cells[offset].strip()
            conf_rec=cells[offset+1].strip()
            overall=cells[offset+2].strip()
            if not school or school.lower() in {'team','school','gold','graphite'}: continue
            if not (re.search(r'\d+\s*-\s*\d+',conf_rec) or re.search(r'\d+\s*-\s*\d+',overall)): continue
            fixed=fallback_conference_for_school(school,'D1') or conf
            if not fixed: continue
            local.append({'conference':fixed,'school':school,'conference_record':conf_rec,
                          'overall_record':overall,'source':'TopDrawerSoccer','source_url':source_url})
        if local: items.extend(local)
    return items

def fetch_tds_standings():
    """Import current men's college-soccer conference tables exposed publicly by TDS.

    The overview renders one conference at a time. We discover public conference
    profile URLs from its select/options/links and read each Conference Standings
    table. No gated/private pages are accessed.
    """
    errors=[]; items=[]; seen=set(); urls=[]
    try:
        for seed in (TDS_STANDINGS_URL,TDS_MEN_URL):
            try:
                r=fetch(seed); soup=BeautifulSoup(r.text,'lxml')
                for x in _tds_standing_rows(soup,seed):
                    key=(x['conference'].lower(),x['school'].lower())
                    if key not in seen: seen.add(key);items.append(x)
                for a in soup.find_all('a',href=True):
                    href=a.get('href') or ''
                    if '/college-conferences/conference-details/men/' in href:
                        urls.append(urljoin(seed,href))
                for opt in soup.find_all('option'):
                    val=opt.get('value') or opt.get('data-url') or ''
                    if '/college-conferences/conference-details/men/' in val:
                        urls.append(urljoin(seed,val))
                pattern=r"[\"']([^\"']*?/college-soccer/college-conferences/conference-details/men/[^\"']+)[\"']"
                for m in re.findall(pattern,r.text):
                    urls.append(urljoin(seed,m))
            except Exception as exc:
                errors.append(f'{seed}: {exc}')
        clean=[]
        for u in urls:
            u=u.split('#')[0]
            u=re.sub(r'/tab-(?:articles|videos|commitments|schedule).*$', '/tab-articles', u)
            if u not in clean: clean.append(u)
        # The public all-standings page normally contains every conference. Only
        # fan out to individual profiles when that single-page parse is incomplete.
        found_confs={x['conference'] for x in items}
        profiles=[] if len(found_confs)>=15 else clean[:45]
        for u in profiles:
            try:
                rr=fetch(u); ss=BeautifulSoup(rr.text,'lxml')
                for x in _tds_standing_rows(ss,u):
                    key=(x['conference'].lower(),x['school'].lower())
                    if key not in seen: seen.add(key);items.append(x)
            except Exception as exc:
                errors.append(f'{u}: {exc}')
        return {'ok':bool(items),'items':items,'errors':errors,'profiles_checked':len(profiles)}
    except Exception as exc:
        return {'ok':False,'items':items,'errors':errors,'error':str(exc)}

