"""College Soccer Fantasy valuation + overall models.

Everything here is soccer-specific.  No basketball-style box-score categories are
used. Prices are fantasy credits (C$), never USD or wagering values.
"""
CLASS_BONUS={"Fr.":0.0,"Freshman":0.0,"So.":0.25,"Sophomore":0.25,"Jr.":0.5,"Junior":0.5,"Sr.":0.75,"Senior":0.75,"5th":0.9,"Fifth Year":0.9,"Gr.":0.9,"Graduate":0.9}
def clamp(v,a,b): return max(a,min(b,v))


def _n(d,key):
    try:return float((d or {}).get(key,0) or 0)
    except Exception:return 0.0


def compute_player_overall(player,current=None,team_rank=None,national_stat_rank=None,conference_strength=0.0,team_strength=0.0):
    """Return a soccer-only 75-99 overall for the current season.

    Core inputs: games/starts/minutes, goals, assists, shots, shots on goal,
    game-winning goals, goalkeeper saves/goals-against/shutouts, discipline,
    plus small verified team/conference context. Missing data is neutral rather
    than treated as elite production.
    """
    current=current or {}
    games=max(_n(current,'games'),0.0); starts=max(_n(current,'starts'),0.0); minutes=max(_n(current,'minutes'),0.0)
    goals=_n(current,'goals'); assists=_n(current,'assists'); shots=_n(current,'shots'); sog=_n(current,'shots_on_goal')
    gw=_n(current,'game_winners'); saves=_n(current,'saves'); ga=_n(current,'goals_against'); shutouts=_n(current,'shutouts')
    yellow=_n(current,'yellow_cards'); red=_n(current,'red_cards')
    pos=str((player or {}).get('position') or '').upper()

    # 75 is a genuine roster-level floor. Playing time raises the rating before
    # production, reflecting the user's requirement that importance to the school matters.
    score=75.0
    if games>0:
        avg_minutes=minutes/games if minutes>0 else 0.0
        start_rate=starts/games if starts>0 else 0.0
        score += clamp(games/10.0,0,1)*1.8
        score += clamp(avg_minutes/90.0,0,1)*3.7
        score += clamp(start_rate,0,1)*2.2
    elif minutes>0:
        score += clamp(minutes/700.0,0,1)*4.0

    # Rate stats stay meaningful at different points in the season; totals keep
    # national leaders from being undervalued when school-minute data is missing.
    per90=90.0/minutes if minutes>0 else (1.0/max(games,1.0))
    g_rate=goals*per90; a_rate=assists*per90; sh_rate=shots*per90; sog_rate=sog*per90

    if pos in {'FW','F','FORWARD'}:
        score += clamp(goals/8.0,0,1)*4.8 + clamp(g_rate/1.0,0,1)*2.7
        score += clamp(assists/7.0,0,1)*2.4 + clamp(a_rate/.75,0,1)*1.2
        score += clamp(sog_rate/3.0,0,1)*1.0 + clamp(gw/3.0,0,1)*1.0
    elif pos in {'MF','M','MIDFIELDER'}:
        score += clamp(goals/6.0,0,1)*3.3 + clamp(g_rate/.65,0,1)*1.7
        score += clamp(assists/7.0,0,1)*3.3 + clamp(a_rate/.75,0,1)*1.7
        score += clamp(sog_rate/2.3,0,1)*.8 + clamp(gw/3.0,0,1)*.7
    elif pos in {'DF','D','DEFENDER'}:
        score += clamp(goals/4.0,0,1)*2.3 + clamp(assists/5.0,0,1)*1.9
        score += clamp(shutouts/max(games,1.0),0,1)*3.0
        score += clamp(gw/2.0,0,1)*.7 + clamp(sog_rate/1.4,0,1)*.6
    elif pos in {'GK','GOALKEEPER'}:
        save_pct=saves/(saves+ga) if (saves+ga)>0 else 0.0
        score += clamp(saves/max(games,1.0)/5.5,0,1)*3.0
        score += clamp((save_pct-.55)/.30,0,1)*3.6
        score += clamp(shutouts/max(games,1.0),0,1)*3.2
        score += clamp(minutes/900.0,0,1)*1.4
    else:
        score += clamp(goals/6.0,0,1)*2.5 + clamp(assists/6.0,0,1)*2.5

    # Verified context is intentionally smaller than individual production.
    if team_rank:
        score += clamp((26-float(team_rank))/25.0,0,1)*2.6
    if national_stat_rank:
        score += clamp((101-float(national_stat_rank))/100.0,0,1)*2.8
    score += clamp(float(conference_strength or 0),0,1)*1.8
    score += clamp(float(team_strength or 0),0,1)*1.3

    # Soccer discipline is a small negative signal.
    score -= min(2.5,yellow*.12 + red*.75)
    return round(clamp(score,75.0,99.0),1)


def compute_player_value(player,current=None,history=None,team_rank=None,tds_player_rank=None,conference_strength=0.0,team_strength=0.0):
    current=current or {}; history=history or []
    games=max(float(current.get('games',0) or 0),1.0); minutes=float(current.get('minutes',0) or 0); starts=float(current.get('starts',0) or 0)
    goals=float(current.get('goals',0) or 0); assists=float(current.get('assists',0) or 0); saves=float(current.get('saves',0) or 0); shutouts=float(current.get('shutouts',0) or 0)
    yellow=float(current.get('yellow_cards',0) or 0); red=float(current.get('red_cards',0) or 0)
    mpg=minutes/games; start_rate=starts/games; p90=90.0/minutes if minutes>0 else 0
    g90,a90,sv90=goals*p90,assists*p90,saves*p90
    pos=(player.get('position') or '').upper(); value=4.35+CLASS_BONUS.get(player.get('class_year'),0.15)
    value+=clamp(mpg/90,0,1)*2.55+clamp(start_rate,0,1)*1.25
    if pos in {'FW','F','FORWARD'}: value+=clamp(g90,0,1.2)*4.1+clamp(a90,0,1)*2.3
    elif pos in {'MF','M','MIDFIELDER'}: value+=clamp(g90,0,.8)*3.2+clamp(a90,0,1)*3.0
    elif pos in {'DF','D','DEFENDER'}: value+=clamp(g90,0,.5)*2.7+clamp(a90,0,.7)*2.0+clamp(shutouts/games,0,1)*.85
    elif pos in {'GK','GOALKEEPER'}: value+=clamp(sv90/6,0,1.2)*2.2+clamp(shutouts/games,0,1)*1.8
    career_minutes=sum(float(s.get('minutes',0) or 0) for s in history); career_prod=sum(float(s.get('goals',0) or 0)+float(s.get('assists',0) or 0) for s in history)
    value+=clamp(career_minutes/3000,0,1)*.75+clamp(career_prod/25,0,1)*.55
    if team_rank: value+=clamp((26-float(team_rank))/25,0,1)*1.0
    if tds_player_rank: value+=clamp((101-float(tds_player_rank))/100,0,1)*.8
    value+=clamp(float(conference_strength or 0),0,1)*.75
    value+=clamp(float(team_strength or 0),0,1)*.90
    value-=yellow*.05+red*.35
    return round(clamp(value,5.0,16.0),1)


def compute_coach_value(team_rank=None,wins=0,games=0,conference_strength=0.0,role='Head Coach'):
    value=4.5
    if games: value+=clamp(wins/games,0,1)*2.3
    if team_rank: value+=clamp((26-float(team_rank))/25,0,1)*1.6
    value+=clamp(float(conference_strength or 0),0,1)*.9
    if role!='Head Coach': value-=0.8
    return round(clamp(value,4.0,10.0),1)
