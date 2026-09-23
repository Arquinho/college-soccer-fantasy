# V7 launch-focus changes

- Launch scope reduced to NCAA Division I and NJCAA Division I.
- Dashboard news no longer uses local screenshot-style fallback artwork; official article artwork is fetched from the source in the background.
- Live & Today is capped at five games: live games first, then remaining games from the current date only.
- Added a five-player "Players to watch" panel sourced from verified 2026 production / NCAA scoring leaders.
- Selected lineup players now use a distinct blue treatment on the pitch and in the market; selected cards show SELECTED.
- D1 national ranking ships with a source-backed warm snapshot so the page is populated immediately.
- D1 NCAA scoring leaders ship with a source-backed warm snapshot so the Players tab and prospect card do not start blank.
- D1 news, rankings, standings and upcoming schedule warm in a daemon thread after the web server has started, never before the first page response.
- Games & Results renders the local cache immediately, then expands its local window and refreshes the selected date asynchronously.
