"""Offline smoke test for the delivery prototype."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app import app
from database import init_db

init_db()
client=app.test_client()
checks=[
    ('/',200),
    ('/api/health',200),
    ('/api/meta',200),
    ('/api/players?division=D1',200),
    ('/api/coaches?division=D1',200),
    ('/api/games?division=D1&since=2026-08-01&until=2026-12-31',200),
    ('/api/filters?division=D1',200),
    ('/api/dashboard?division=D1',200),
    ('/api/game-coverage?division=D1',200),
]
failed=[]
for url,expected in checks:
    r=client.get(url)
    ok=r.status_code==expected
    print(('OK  ' if ok else 'FAIL'),r.status_code,url)
    if not ok: failed.append((url,r.status_code))
if failed:
    raise SystemExit(f"Smoke test failed: {failed}")
print('SMOKE TEST: OK')
