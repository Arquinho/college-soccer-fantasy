"""Best-effort public registry of NCAA D1 men's soccer programs.

The 2026 conference table is read from the public Wikipedia list. This gives the
prototype a complete school/conference registry; official athletics URLs are
filled by the legacy import or later team-specific sync.
"""
from bs4 import BeautifulSoup
from services.sources.common import fetch, now_iso

URL = "https://en.wikipedia.org/wiki/List_of_NCAA_Division_I_men%27s_soccer_programs"

def fetch_registry():
    try:
        r = fetch(URL)
        soup = BeautifulSoup(r.text, "lxml")
        target = None
        for table in soup.find_all("table"):
            headers = [x.get_text(" ", strip=True).lower() for x in table.find_all("th")]
            if "institution" in headers and "conference" in headers:
                target = table; break
        if target is None:
            return {"ok":False,"items":[],"error":"program table not found"}
        items=[]
        for tr in target.find_all("tr"):
            td=tr.find_all("td")
            if len(td) < 6: continue
            school=" ".join(td[0].get_text(" ",strip=True).split())
            conf=" ".join(td[-1].get_text(" ",strip=True).split())
            if school and conf:
                items.append({"school":school,"conference":conf,"source_url":URL,"updated_at":now_iso()})
        return {"ok":True,"items":items}
    except Exception as exc:
        return {"ok":False,"items":[],"error":str(exc)}
