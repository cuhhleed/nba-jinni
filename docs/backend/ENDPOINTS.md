# NBAJinni Web Pages to Endpoints

The purpose of this document is to reverse engineer NBAJinni's backend endpoints from my vision of the website's web pages. The goal is to break down the mappings of our website and its various pages. More specifically, **what** information I want to display, **how** the subsets of this information are accessed and, most importantly, **when** they are accessed.

## Front Page

The home page should contain enough information to pull the user into our other various pages. We'll want it to sort of have a collection of widgets. This should also make it easier to break down what endpoints we'll need.

### Upcoming games --- `"/games/upcoming"`

This is the center piece of our home page, a simple display listing the upcoming games in the next 2-3 days, keeping the number of games displayed short. Keeping this display fresh throughout the day can be a challenge, as the NBA.com API does not give exact game times, we'll need to think of other ways to keep this up to date.

### Standings Preview --- `"/standings/preview"`

This is a simple widget containing a preview of standings. What exactly it will preview here is unclear, it should be enough to fill the empty space but not put the whole NBA table in it. Perhaps we could display only playoff spots (ranks 1-8) in each conference or top 5 for each. Having a separate endpoint for a preview where we only fetch a few rows from the standing table is a good way to keep things lean.

### Top Players --- `"/players/top/preview`

This widget could also show a preview of the top performing players in the current season. Perhaps display the top 3 players in each statistic in a scroll-able window. Unsure whether it would be better to have it this with one endpoint that returns the top 3 for all categories in a map of lists, or rather have this as multiple endpoints like `"/players/top/preview/{statistic}"`.

## Teams Page

Simply display a list of all NBA teams with brief information (name, logo, city) and the ability to select a team and open a Team page.

### Teams list --- `"/teams"`

Probably the only endpoint we'll need on this page. Just fetching the list of basic team information.

## Team Page

This page goes into much more detail for a selected team. It should also have some navigation to view the team's roster or games/schedule, though it should not display this information immediately or possibly on this page at all. From a list of games you can navigate to a specific game page, as with the roster you can navigate to a specific player page.

### Team Details --- `"/team/{team_id}"`

It'll obviously be headed with the basic information, but will also need standings information (conference rank, record, win streak, etc.) as well as statistics (this season's average).

### Roster --- `"/teams/{team_id}/roster"`

List of the team's players with basic player info (name, position, age, etc.). Allows the selection of a player to open their player page.

### Games --- `"/teams/{team_id}/games"`

Lists the team's games for the season. For this, we'll need to incorporate final results for past games, but that can be handled by this next endpoint.

### All Game Stats --- `"/teams/{team_id}/allgamestats"`

List game stats for all games played this season. This should help in showing a comprehensive list of games and the result of past games.

## Game Page

This page displays information of a specific game. The status of the game will dictate what information is displayed. Future games show a comparison of both team's performance this season, as well as a game log of previous match-ups between the teams. Completed games would rather display the game result, both teams' stats, and player stats.

### Game Details --- `"/games/{game_id}"`

For future games, both team's season averages are displayed in comparison, as well as their standing information. For a past game, both team's stats for the game is shown instead.

### Head-to-head Match-up History --- `"/games/h2h/{team_id}?opponent="`

For future games, we can also show the game history between both teams.

### Game Player Stats --- `"/games/{game_id}/playerstats

For a past game, player box scores will be displayed as well.

## Player Page

This page will show detailed information about a specific player. Immediately on display would be average stats for the current season and the last 5 games. Below that should be a section to toggle between other stat lists like recent stats vs their next opponent, past season averages, etc. There would also be basic information about the player and their team.

### Player Details --- `"/players/{player_id}"`

Gives basic player details as well as their team's basic details.

### Player Season Averages --- `"/players/{player_id}/season-averages"`

Fetch all season averages, this can be used for both needing the single season average and already having historical averages.

### Player Last 5 Games --- `"/players-{player_id}/last-5-games"`

Fetch the last 5 games played by the player

### Player vs Team --- `"/players/{player_id}/vs-opponent?team_id=`

Get historical stats for the player against a specific team.

## Standings Page

This page should simply display standing info by conference.

### Standings --- `"/standings"`

Get Standings data for all teams, basically the entire standings table.
