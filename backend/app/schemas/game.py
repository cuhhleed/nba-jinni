from __future__ import annotations

from pydantic import BaseModel, ConfigDict, computed_field, model_validator
from datetime import date
from typing import Annotated, Literal, Optional, Union
from pydantic import Field


class GameBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    home_team_id: int
    away_team_id: int
    season: str
    game_date: date
    status: int


def _split_team_stats(data: object) -> object:
    """
    Converts an ORM Game instance into a plain dict with home_team_stat / away_team_stat
    scalars split out of the Game.team_stats list. Called by model_validators on GameResult
    and GameWithTeamStats so the splitting logic lives in one place.

    home_team / away_team are passed through untouched — only included when the handler
    has eager-loaded them (GameResult needs them for standing; GameWithTeamStats does not).
    """
    if not hasattr(data, "team_stats"):
        return data
    home_stat = None
    away_stat = None
    for stat in data.team_stats:
        if stat.team_id == data.home_team_id:
            home_stat = stat
        elif stat.team_id == data.away_team_id:
            away_stat = stat
    payload = {
        "id": data.id,
        "home_team_id": data.home_team_id,
        "away_team_id": data.away_team_id,
        "season": data.season,
        "game_date": data.game_date,
        "status": data.status,
        "home_team_stat": home_stat,
        "away_team_stat": away_stat,
    }
    if "home_team" in data.__dict__:
        payload["home_team"] = data.home_team
    if "away_team" in data.__dict__:
        payload["away_team"] = data.away_team
    return payload


class GameWithTeams(GameBase):
    home_team: "TeamWithSeasonAverage"
    away_team: "TeamWithSeasonAverage"


class GamePreview(GameBase):
    """
    Returned by GET /games/{id} when the game has not yet been played (status != 3).
    Includes full team context (standing + season averages) for the preview widget.

    Discriminator strategy: Game.status is an int on the ORM model, which cannot be
    used directly as a Pydantic literal discriminator. We add a computed `kind` field
    that maps to the string literal "preview". The response union uses `kind` as the
    discriminator, letting clients narrow the type without extra round trips.
    """

    kind: Literal["preview"] = "preview"
    home_team: "TeamWithStandingAndAverage"
    away_team: "TeamWithStandingAndAverage"


class GameResult(GameBase):
    """
    Returned by GET /games/{id} when the game is completed (status == 3).
    Includes final team box-score stats split into home/away scalars.

    The model_validator reads the ORM Game.team_stats list (loaded via selectinload)
    and matches each TeamGameStat to home_team_id / away_team_id.
    If both stats are missing despite status==3, the handler raises HTTP 409.
    """

    kind: Literal["result"] = "result"
    home_team: "TeamWithStanding"
    away_team: "TeamWithStanding"
    home_team_stat: "TeamGameStatBase"
    away_team_stat: "TeamGameStatBase"

    @model_validator(mode="before")
    @classmethod
    def split_team_stats(cls, data: object) -> object:
        return _split_team_stats(data)


class GameWithTeamStats(GameBase):
    """
    Used by GET /teams/{team_id}/games and GET /games/h2h.
    Both home and away stats are optional — unplayed games will have nulls.
    """

    home_team_stat: Optional["TeamGameStatBase"] = None
    away_team_stat: Optional["TeamGameStatBase"] = None

    @model_validator(mode="before")
    @classmethod
    def split_team_stats(cls, data: object) -> object:
        return _split_team_stats(data)


class TeamScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    recent: list["GameWithTeamStats"]
    upcoming: list["GameBase"]


# Discriminated union for GET /games/{id}.
# Uses the computed `kind` field (Literal["preview"] | Literal["result"]) as the
# discriminator rather than the raw int `status`, since Pydantic requires string literals.
GameDetailResponse = Annotated[
    Union[GamePreview, GameResult],
    Field(discriminator="kind"),
]


from .team import TeamWithSeasonAverage, TeamWithStandingAndAverage, TeamWithStanding
from .team_game_stat import TeamGameStatBase

GameWithTeams.model_rebuild()
GamePreview.model_rebuild()
GameResult.model_rebuild()
GameWithTeamStats.model_rebuild()