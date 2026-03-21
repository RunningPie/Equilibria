from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class ProfileStats(BaseModel):
    """
    Schema untuk profile stats endpoint.
    Mengembalikan theta values per Tech Specs v4.2.
    """
    theta_individu: float = Field(..., example=1300.0, description="Individual Elo rating [0, 2000]")
    theta_social: float = Field(..., example=1300.0, description="Social Elo rating [0, 2000]")
    theta_display: float = Field(..., example=1300.0, description="Weighted average: (0.8 × θ_individu) + (0.2 × θ_social)")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "theta_individu": 1350.0,
                "theta_social": 1250.0,
                "theta_display": 1330.0
            }
        }
    )
