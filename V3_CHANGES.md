# Delivery Candidate v3 — requested refinements

This candidate focuses on NCAA men's college soccer only.

## Rankings
- National NCAA men's soccer statistical leaders are loaded from verified public NCAA men's soccer leaderboards when available.
- Top scorers can be filtered by conference without replacing the national list with one local school.
- Conference standings support an all-conferences view and individual conference filtering.
- Public men's college soccer standings are cached locally after refresh so the interface is responsive on later visits.

## Conference normalization
- Conference aliases are normalized to one current display name (for example ACC and Big Ten).
- Known current D1 affiliations are repaired on startup and during refresh. Stanford, SMU and Louisville resolve to ACC.
- Conference normalization is propagated to teams, players, coaches, games, standings and ranking/stat records.

## Dashboard news
- News refresh attempts to load the official article social/hero image (Open Graph/Twitter/article image) and stores it in the news cache.
- The dashboard already renders `image_url` as the article card image, so verified images appear after refresh when the source exposes one.

## Faster next match
- World load now performs a short upcoming NCAA men's soccer schedule window instead of a full-season scan.
- The market and player detail cards update Next Match as soon as the short schedule request finishes.
- Full-season schedule import remains available from Games & Results / manual sync.

## Soccer-only overall model
Overall is clamped from 75 to 99 and uses only soccer data from the current season when available:
- games, starts, minutes and average minutes (importance to the team)
- goals and assists
- shots and shots on goal
- game-winning goals
- goalkeeper saves, save percentage, goals against and shutouts
- discipline (yellow/red cards)
- smaller context adjustments for verified national/stat rank, team rank and conference/team strength

No basketball box-score categories are used.
