from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class LeaderboardEntry(BaseModel):
    """
    Schema untuk entry leaderboard.
    Mengembalikan data peringkat user dengan display_name yang diobfuscate.
    """
    rank: int = Field(..., example=1, description="Ranking position on the leaderboard")
    user_id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000", description="User UUID")
    display_name: str = Field(..., example="D***a", description="Obfuscated display name for privacy")
    theta_display: float = Field(..., example=1312.0, description="Display Elo rating (weighted average)")
    is_self: bool = Field(..., example=False, description="True if this entry belongs to the current user")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "rank": 1,
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "display_name": "D***a",
                "theta_display": 1312.0,
                "is_self": False
            }
        }
    )


class LeaderboardResponse(BaseModel):
    """
    Schema untuk response leaderboard yang berisi list entries.
    """
    entries: list[LeaderboardEntry]
    total: int = Field(..., description="Total number of users on leaderboard")
    limit: int = Field(..., description="Limit parameter used in query")
    offset: int = Field(..., description="Offset parameter used in query")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entries": [
                    {
                        "rank": 1,
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "display_name": "D***a",
                        "theta_display": 1312.0,
                        "is_self": False
                    }
                ],
                "total": 100,
                "limit": 20,
                "offset": 0
            }
        }
    )
