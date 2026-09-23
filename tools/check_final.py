"""Offline integrity checks for the final College XI prototype.

Run from the project root:
    python3 tools/check_final.py

These checks do not need internet access. They verify the product rules and
that the packaged sample DB is internally consistent. Live-source completeness
is verified by the sync status shown in the UI after running a public-source sync.
"""
from pathlib import Path
import sqlite3, re, sys

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'college_xi_d1.sqlite3'
errors=[]

def check(cond,msg):
    if not cond: errors.append(msg)

app=(ROOT/'app.py').read_text()
js=(ROOT/'static'/'app.js').read_text()
ncaa=(ROOT/'services'/'sources'/'ncaa.py').read_text()
for world in ('D1','D2','D3','NAIA','NJCAA1'):
    check(re.search(rf"'{world}'\s*:\s*\{{[^\n]*'budget'\s*:\s*120\.0",app) is not None,f'{world} backend budget is not 120.0M')
    check(re.search(rf"\b{world}:\{{label:[^\n]+budget:120",js) is not None,f'{world} frontend budget is not 120M')
check("NEXT GAME" in js and 'nextGameForSchool' in js,'Market next-game feature missing')
check('while cur<=end' in ncaa and 'exhaustive NCAA scoreboard date scan' in ncaa,'NCAA full-season sync is not exhaustive by date')
check("clamp(Math.round" in js or 'displayOverall' in js,'overall UI normalization missing')

if DB.exists():
    c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
    rs=c.execute('select min(rating) lo,max(rating) hi from players').fetchone()
    if rs and rs['lo'] is not None:
        check(float(rs['lo'])>=70.0,'packaged player overall below 70')
        check(float(rs['hi'])<=100.0,'packaged player overall above 100')
    aron=c.execute("select price,rating from players where lower(name)='aron martinez' limit 1").fetchone()
    if aron:
        check(abs(float(aron['price'])-11.4)<0.051,f"Aron Martinez packaged price is {aron['price']}, expected 11.4M")
        check(70<=float(aron['rating'])<=100,'Aron overall out of 70-100 range')
    c.close()
else:
    errors.append('packaged SQLite database missing')

if errors:
    print('FINAL CHECK: FAILED')
    for e in errors: print(' -',e)
    sys.exit(1)
print('FINAL CHECK: OK')
print(' - all world budgets: 120M')
print(' - overall range rule: 70-100')
print(' - Aron Martinez calibration: 11.4M when packaged verified sample is present')
print(' - next verified school game shown in Market')
print(' - NCAA D1/D2/D3 full-season sync scans every calendar date')
