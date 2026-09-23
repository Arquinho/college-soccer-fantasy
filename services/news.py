from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from database import db
from services.sources.common import fetch

NCAA_API_BASE = "https://ncaa-api.henrygd.me"

SOURCES = {
    "D1": {"source": "NCAA DI", "page": "https://www.ncaa.com/sports/soccer-men/d1", "rss": "https://www.ncaa.com/news/soccer-men/d1/rss.xml", "api": f"{NCAA_API_BASE}/news/soccer-men/d1"},
    "D2": {"source": "NCAA DII", "page": "https://www.ncaa.com/sports/soccer-men/d2", "rss": "https://www.ncaa.com/news/soccer-men/d2/rss.xml", "api": f"{NCAA_API_BASE}/news/soccer-men/d2"},
    "D3": {"source": "NCAA DIII", "page": "https://www.ncaa.com/sports/soccer-men/d3", "rss": "https://www.ncaa.com/news/soccer-men/d3/rss.xml", "api": f"{NCAA_API_BASE}/news/soccer-men/d3"},
    "NAIA": {"source": "NAIA", "page": "https://www.naia.org/sports/mens-soccer/"},
    "NJCAA1": {"source": "NJCAA", "page": "https://www.njcaa.org/sports/msoc/index"},
}

def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _iso_date(value):
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat(timespec="seconds")
    except Exception:
        return value

def _clean_html(value):
    if not value:
        return ""
    return " ".join(BeautifulSoup(str(value), "lxml").get_text(" ", strip=True).split())

def _category(title, raw=""):
    text = f"{title} {raw}".lower()
    if any(x in text for x in ("rank", "poll", "top 25")):
        return "rankings"
    if any(x in text for x in ("transfer", "commit", "signing")):
        return "transfers"
    if any(x in text for x in ("player", "goal", "assist", "hermann", "award")):
        return "players"
    if "conference" in text:
        return "conferences"
    return "news"

def _from_ncaa_api(division, cfg):
    payload = fetch(cfg["api"]).json()
    raw_items = payload.get("items") or payload.get("data") or payload.get("news") or []
    out = []
    for item in raw_items:
        title = (item.get("title") or "").strip()
        link = item.get("link") or item.get("url")
        if not title or not link:
            continue
        image = item.get("image") or item.get("image_url") or item.get("enclosure")
        if isinstance(image, dict):
            image = image.get("url")
        out.append({
            "title": title,
            "category": _category(title, item.get("category") or ""),
            "source": cfg["source"],
            "url": link,
            "image_url": image,
            "division": division,
            "published_at": _iso_date(item.get("pubDate") or item.get("published_at")),
            "updated_at": _now(),
            "icon": division,
        })
    return out

def _from_rss(division, cfg):
    response = fetch(cfg["rss"])
    soup = BeautifulSoup(response.text, "xml")
    out = []
    for item in soup.find_all("item"):
        title = item.title.get_text(" ", strip=True) if item.title else ""
        link = item.link.get_text(" ", strip=True) if item.link else ""
        if not title or not link:
            continue
        image = None
        media = item.find("media:content") or item.find("media:thumbnail") or item.find("enclosure")
        if media:
            image = media.get("url")
        if not image and item.description:
            img = BeautifulSoup(str(item.description), "lxml").find("img")
            image = img.get("src") if img else None
        category = item.category.get_text(" ", strip=True) if item.category else ""
        pub = item.pubDate.get_text(" ", strip=True) if item.pubDate else None
        out.append({
            "title": title,
            "category": _category(title, category),
            "source": cfg["source"],
            "url": link,
            "image_url": image,
            "division": division,
            "published_at": _iso_date(pub),
            "updated_at": _now(),
            "icon": division,
        })
    return out

def _article_image(url):
    """Best-effort hero image from an official soccer article page."""
    if not url:
        return None
    try:
        response=fetch(url)
        soup=BeautifulSoup(response.text,"lxml")
        for attrs in (
            {"property":"og:image"}, {"name":"twitter:image"},
            {"property":"twitter:image"}, {"name":"og:image"},
        ):
            node=soup.find("meta",attrs=attrs)
            if node and node.get("content"):
                return urljoin(url,node.get("content"))
        for sel in ("article img","main img",".article-body img",".content img"):
            img=soup.select_one(sel)
            if img:
                src=img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                if src:return urljoin(url,src)
    except Exception:
        return None
    return None


def _enrich_missing_images(items, limit=12):
    checked=0
    for item in items:
        if item.get("image_url") or checked>=limit:
            continue
        checked+=1
        item["image_url"]=_article_image(item.get("url"))
    return items

def _image_for(a, base):
    node = a
    for _ in range(6):
        if not node:
            break
        img = node.find("img") if hasattr(node, "find") else None
        if img:
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or img.get("data-original")
            if src:
                return urljoin(base, src)
        node = node.parent
    return None

def _from_page(division, cfg):
    response = fetch(cfg["page"])
    soup = BeautifulSoup(response.text, "lxml")
    out, seen = [], set()
    for sel in ("article a", ".views-row a", ".node-title a", "h2 a", "h3 a"):
        for a in soup.select(sel):
            title = " ".join(a.get_text(" ", strip=True).split())
            href = a.get("href")
            if not title or len(title) < 18 or not href:
                continue
            href = urljoin(cfg["page"], href)
            if "ncaa.com" not in href and division in {"D1", "D2", "D3"}:
                continue
            key = title.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "title": title,
                "category": _category(title),
                "source": cfg["source"],
                "url": href,
                "image_url": _image_for(a, cfg["page"]),
                "division": division,
                "published_at": None,
                "updated_at": _now(),
                "icon": division,
            })
            if len(out) >= 20:
                return out
    return out

def _fetch_division(division):
    cfg = SOURCES[division]
    errors = []
    if division in {"D1", "D2", "D3"}:
        for method in (_from_rss, _from_ncaa_api, _from_page):
            try:
                items = method(division, cfg)
                if items:
                    return items, errors
            except Exception as exc:
                errors.append(str(exc))
    else:
        try:
            items = _from_page(division, cfg)
            if items:
                return items, errors
        except Exception as exc:
            errors.append(str(exc))
    return [], errors

def sync_news(division=None):
    """Refresh current official news. NCAA worlds use the NCAA men's-soccer RSS feed.

    Existing news is replaced only after a successful fetch, so a temporary network
    failure never wipes out the last verified snapshot.
    """
    divisions = [division] if division in SOURCES else list(SOURCES)
    all_items, errors = [], []
    for div in divisions:
        items, errs = _fetch_division(div)
        errors.extend([f"{div}: {x}" for x in errs])
        if not items:
            continue
        # RSS/news APIs frequently omit artwork even though the official article
        # has an Open Graph hero image. Enrich only the first cards so dashboard
        # refreshes stay responsive.
        items = _enrich_missing_images(items, 8)
        cfg = SOURCES[div]
        with db() as conn:
            conn.execute("DELETE FROM news WHERE division=? AND source=?", (div, cfg["source"]))
            for n in items[:30]:
                conn.execute("""INSERT INTO news(title,category,source,url,image_url,division,published_at,updated_at,icon)
                    VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(title,source) DO UPDATE SET
                    category=excluded.category,url=excluded.url,image_url=COALESCE(excluded.image_url,news.image_url),division=excluded.division,
                    published_at=COALESCE(excluded.published_at,news.published_at),updated_at=excluded.updated_at,icon=excluded.icon""",
                    (n["title"], n["category"], n["source"], n["url"], n["image_url"], n["division"], n["published_at"], n["updated_at"], n["icon"]))
        all_items.extend(items)
    return {"ok": bool(all_items), "items": all_items, "errors": errors}
