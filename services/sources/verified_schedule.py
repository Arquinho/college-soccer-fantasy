"""Small verified schedule snapshots used only as a transport safety net.

These rows are not synthetic fixtures.  They are copied from public 2026 men's
college-soccer schedules and are only returned when the live NCAA transports and
public college-soccer schedule fallbacks fail.  The normal path remains NCAA / 
official school data and replaces/enriches these cached rows whenever available.
"""
from .common import now_iso

# D1 fixtures independently visible in current public sources for the dates that
# are in the demo's initial calendar window.  Times are normalized to U.S.
# Eastern time for the app UI.
_D1 = {
    "2026-09-23": [
        {"home_team":"Massachusetts","away_team":"FDU","start_time":"3:00 PM ET","source_url":"https://www.ncaa.com/scoreboard/soccer-men/d1/2026/09/23/all-conf","source_name":"NCAA.com (verified schedule snapshot)"},
        {"home_team":"Sacramento St.","away_team":"UC Riverside","start_time":"4:00 PM ET","source_url":"https://www.ncaa.com/scoreboard/soccer-men/d1/2026/09/23/all-conf","source_name":"NCAA.com (verified schedule snapshot)"},
        {"home_team":"Georgia St.","away_team":"UNC Asheville","start_time":"6:00 PM ET","source_url":"https://www.ncaa.com/scoreboard/soccer-men/d1/2026/09/23/all-conf","source_name":"NCAA.com (verified schedule snapshot)"},
        {"home_team":"Holy Cross","away_team":"Stonehill","start_time":"6:00 PM ET","source_url":"https://www.ncaa.com/scoreboard/soccer-men/d1/2026/09/23/all-conf","source_name":"NCAA.com (verified schedule snapshot)"},
        {"home_team":"UAB","away_team":"Gardner-Webb","start_time":"7:00 PM ET","source_url":"https://www.ncaa.com/scoreboard/soccer-men/d1/2026/09/23/all-conf","source_name":"NCAA.com (verified schedule snapshot)"},
        {"home_team":"Radford","away_team":"VMI","start_time":"7:00 PM ET","source_url":"https://www.ncaa.com/scoreboard/soccer-men/d1/2026/09/23/all-conf","source_name":"NCAA.com (verified schedule snapshot)"},
        {"home_team":"UC San Diego","away_team":"Cal St. Fullerton","start_time":"10:00 PM ET","source_url":"https://www.ncaa.com/scoreboard/soccer-men/d1/2026/09/23/all-conf","source_name":"NCAA.com (verified schedule snapshot)"},
        {"home_team":"Oregon St.","away_team":"Seattle U","start_time":"10:00 PM ET","source_url":"https://www.ncaa.com/scoreboard/soccer-men/d1/2026/09/23/all-conf","source_name":"NCAA.com (verified schedule snapshot)"},
    ],
    "2026-09-24": [
        {
            "home_team": "UC Irvine",
            "away_team": "California Baptist",
            "start_time": "9:00 PM ET",
            "source_url": "https://ucirvinesports.com/sports/mens-soccer/schedule",
            "source_name": "UC Irvine Athletics (official schedule)",
        },
    ],
    "2026-09-25": [
        {"home_team":"Indiana","away_team":"Penn State","start_time":"1:00 PM ET","source_url":"https://gopsusports.com/sports/mens-soccer/schedule?path=msoc","source_name":"Penn State Athletics (official schedule)"},
        {"home_team":"Florida International","away_team":"Memphis","start_time":"7:00 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"Duke","away_team":"Elon","start_time":"7:00 PM ET","source_url":"https://goduke.com/sports/mens-soccer/schedule","source_name":"Duke Athletics (official schedule)"},
        {"home_team":"NC State","away_team":"Wake Forest","start_time":"7:00 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"Pittsburgh","away_team":"Louisville","start_time":"7:00 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"Akron","away_team":"Georgetown","start_time":"7:00 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"Maryland","away_team":"UCLA","start_time":"7:00 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"Michigan State","away_team":"Wisconsin","start_time":"7:00 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"Bowling Green","away_team":"Western Michigan","start_time":"7:00 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"George Mason","away_team":"Ohio State","start_time":"7:00 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"Clemson","away_team":"Boston College","start_time":"7:00 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"High Point","away_team":"Guilford","start_time":"7:00 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"Notre Dame","away_team":"Syracuse","start_time":"7:00 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"Belmont","away_team":"St. Thomas (MN)","start_time":"7:30 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"Northwestern","away_team":"Michigan","start_time":"7:30 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"Missouri State","away_team":"South Florida","start_time":"8:00 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/scores?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"UIC","away_team":"Bradley","start_time":"8:00 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"Pacific","away_team":"California","start_time":"10:00 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"Cal Poly","away_team":"UC Santa Barbara","start_time":"10:00 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"Stanford","away_team":"Virginia","start_time":"10:00 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
        {"home_team":"Washington","away_team":"Rutgers","start_time":"10:30 PM ET","source_url":"https://www.foxsports.com/soccer/ncaa-mens-soccer/schedule?date=2026-09-25","source_name":"FOX Sports college soccer schedule (support fallback)"},
    ],
}


def fetch_verified_schedule_snapshot(division, date_iso):
    if division != "D1":
        return {"ok": False, "items": [], "date": date_iso, "error": "No bundled snapshot for this world"}
    raw = _D1.get(date_iso) or []
    items=[]
    for idx,row in enumerate(raw,1):
        x=dict(row)
        x.update({
            "game_date": date_iso,
            "home_score": None,
            "away_score": None,
            "status": f"scheduled · {x.get('start_time')}" if x.get("start_time") else "scheduled",
            "division": division,
            "venue": None,
            "source_updated_at": now_iso(),
            "external_id": f"verified-snapshot-{date_iso}-{idx}",
            "current_period": None,
            "contest_clock": None,
            "home_conference": None,
            "away_conference": None,
        })
        items.append(x)
    return {"ok": bool(items), "items": items, "date": date_iso,
            "transport": "bundled verified current-week schedule snapshot"}
