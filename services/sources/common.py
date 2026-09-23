import time
from datetime import datetime, timezone
import requests
from config import USER_AGENT, REQUEST_TIMEOUT, REQUEST_DELAY_SECONDS

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Cache-Control": "no-cache",
}
_SESSION = requests.Session()
_SESSION.headers.update(HEADERS)
_last_request = 0.0


def fetch(url, params=None, timeout=None):
    global _last_request
    wait = REQUEST_DELAY_SECONDS - (time.time() - _last_request)
    if wait > 0:
        time.sleep(wait)
    response = _SESSION.get(url, params=params, timeout=(timeout or REQUEST_TIMEOUT))
    _last_request = time.time()
    response.raise_for_status()
    return response


def now_iso():
    return datetime.now(timezone.utc).isoformat()
