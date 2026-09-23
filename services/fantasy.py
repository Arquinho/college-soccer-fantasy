FORMATIONS = {
    "4-3-3": {"GK": 1, "DF": 4, "MF": 3, "FW": 3},
    "4-4-2": {"GK": 1, "DF": 4, "MF": 4, "FW": 2},
    "3-5-2": {"GK": 1, "DF": 3, "MF": 5, "FW": 2},
    "3-4-3": {"GK": 1, "DF": 3, "MF": 4, "FW": 3},
}


def normalize_position(value):
    v = (value or "").strip().upper()
    if v in {"GK", "GOALKEEPER"}:
        return "GK"
    if v in {"D", "DF", "DEFENDER", "BACK"}:
        return "DF"
    if v in {"M", "MF", "MIDFIELDER"}:
        return "MF"
    if v in {"F", "FW", "FORWARD", "STRIKER"}:
        return "FW"
    return v


def fantasy_points(stats, position):
    """Prototype scoring. Easy to tune from one function."""
    p = normalize_position(position)
    minutes = float(stats.get("minutes", 0) or 0)
    pts = 0.0
    if minutes > 0:
        pts += 1.0
    if minutes >= 60:
        pts += 1.0
    pts += float(stats.get("goals", 0) or 0) * (6 if p in {"GK", "DF"} else 5 if p == "MF" else 4)
    pts += float(stats.get("assists", 0) or 0) * 3
    pts += float(stats.get("game_winners", 0) or 0) * 1
    pts -= float(stats.get("yellow_cards", 0) or 0) * 1
    pts -= float(stats.get("red_cards", 0) or 0) * 3
    if p == "GK":
        pts += float(stats.get("saves", 0) or 0) * 0.5
        pts += float(stats.get("shutouts", 0) or 0) * 4
        pts -= max(float(stats.get("goals_against", 0) or 0) - 1, 0) * 0.5
    if p == "DF":
        pts += float(stats.get("shutouts", 0) or 0) * 3
    return round(pts, 1)
