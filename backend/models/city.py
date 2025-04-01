from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

class CityInfo(BaseModel):
    """City information model."""
    name: str = Field(..., description="Name of the city")
    state: str = Field(..., description="State where the city is located")
    country: str = Field(default="India", description="Country where the city is located")
    population: int = Field(..., description="Population of the city")
    coordinates: Dict[str, float] = Field(..., description="Latitude and longitude coordinates")
    tier: str = Field(..., description="Tier of the city (Tier 1, 2, or 3)")
    is_capital: bool = Field(default=False, description="Whether the city is a state capital")
    hospitals: List[str] = Field(default_factory=list, description="List of major hospitals")
    specialties: List[str] = Field(default_factory=list, description="List of medical specialties available")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Mumbai",
                "state": "Maharashtra",
                "country": "India",
                "population": 12478447,
                "coordinates": {"latitude": 19.0760, "longitude": 72.8777},
                "tier": "Tier 1",
                "is_capital": False,
                "hospitals": ["Kokilaben Dhirubhai Ambani Hospital", "Lilavati Hospital"],
                "specialties": ["Cardiology", "Neurology", "Orthopedics"]
            }
        }
    ) 