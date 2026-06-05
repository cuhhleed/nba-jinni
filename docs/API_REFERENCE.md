## API Reference

Base URL: API Gateway endpoint (see Terraform outputs or GitHub Actions deployment logs).

### Live & Scores

| Method | Path                    | Description                                           |
| ------ | ----------------------- | ----------------------------------------------------- |
| `GET`  | `/games/live/today`     | Live scoreboard — all games today with current scores |
| `GET`  | `/games/live/{game_id}` | Live box score for a single game                      |

### Games

| Method | Path                                 | Description                                                                |
| ------ | ------------------------------------ | -------------------------------------------------------------------------- |
| `GET`  | `/games/{game_id}`                   | Game detail — returns `GamePreview` (upcoming) or `GameResult` (completed) |
| `GET`  | `/games/{game_id}/playerstats`       | Player box scores for a completed game                                     |
| `GET`  | `/games/h2h?team_a={id}&team_b={id}` | Head-to-head games between two teams (current season)                      |

### Teams

| Method | Path                                                      | Description                                  |
| ------ | --------------------------------------------------------- | -------------------------------------------- |
| `GET`  | `/teams`                                                  | All 30 teams                                 |
| `GET`  | `/teams/{team_id}`                                        | Team detail with current standing            |
| `GET`  | `/teams/{team_id}/roster`                                 | Active roster                                |
| `GET`  | `/teams/{team_id}/games`                                  | Schedule — 10 recent completed + 10 upcoming |
| `GET`  | `/teams/{team_id}/stats`                                  | Season average stats + last 5 games          |
| `GET`  | `/teams/{team_id}/season-average?type={regular\|playoff}` | Season averages by game type                 |

### Players

| Method | Path                                                                         | Description                                               |
| ------ | ---------------------------------------------------------------------------- | --------------------------------------------------------- |
| `GET`  | `/players`                                                                   | All active players                                        |
| `GET`  | `/players/search?q={query}`                                                  | Search by name (min 2 chars)                              |
| `GET`  | `/players/top/preview`                                                       | Top 3 players per stat category (pts, reb, ast, stl, blk) |
| `GET`  | `/players/top/recent-performances?type={regular\|playoff\|all}`              | Recent standout games                                     |
| `GET`  | `/players/{player_id}`                                                       | Player profile                                            |
| `GET`  | `/players/{player_id}/season-average?type={regular\|playoff}`                | Season averages                                           |
| `GET`  | `/players/{player_id}/last-5-games?type={regular\|playoff\|all}`             | Last 5 game logs                                          |
| `GET`  | `/players/{player_id}/vs-opponent?team_id={id}&type={regular\|playoff\|all}` | Stats vs a specific team                                  |

### Standings

| Method | Path                 | Description                                       |
| ------ | -------------------- | ------------------------------------------------- |
| `GET`  | `/standings`         | Full standings ordered by conference and rank     |
| `GET`  | `/standings/preview` | Top 10 teams by win percentage (cross-conference) |

### Health

| Method | Path      | Description                                               |
| ------ | --------- | --------------------------------------------------------- |
| `GET`  | `/health` | Returns `{"status":"healthy"}` — verifies DB connectivity |

---
