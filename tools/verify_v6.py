"""Dependency-free delivery checks for v6."""
from pathlib import Path
import py_compile, re, sys
ROOT=Path(__file__).resolve().parents[1]
errors=[]
def ok(cond,msg):
    if not cond: errors.append(msg)
for f in [ROOT/'app.py',ROOT/'database.py',ROOT/'services'/'sync.py',ROOT/'services'/'conferences.py']:
    try: py_compile.compile(str(f),doraise=True)
    except Exception as e: errors.append(f'{f.name}: {e}')
html=(ROOT/'static'/'index.html').read_text()
js=(ROOT/'static'/'app.js').read_text()
css=(ROOT/'static'/'styles.css').read_text()
ok('id="loginScreen"' in html,'Login screen missing')
ok('id="demoLogin"' in html,'Demo login missing')
ok("sessionStorage.getItem('cxi_v6_authenticated')" in js,'Fresh-session login gate missing')
ok('fallbackNews' in js and 'assets/news_lead.jpg' in js,'News image fallback missing')
ok('nextGameForSchool' in js,'Next-match logic missing')
ok('marketVisibleCount:60' in js,'Batched market rendering missing')
ok('function showNotifications' in js,'Notifications flow missing')
ok('function openProfile' in js,'Profile flow missing')
ok('.boot-overlay' in css,'Startup loading UI missing')
if errors:
    print('V6 VERIFY: FAILED')
    for e in errors: print(' -',e)
    sys.exit(1)
print('V6 VERIFY: OK')
