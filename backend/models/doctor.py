from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator
from fuzzywuzzy import fuzz
from config import FUZZY_MATCH_THRESHOLD

class Doctor(BaseModel):
    """Doctor information model."""
    id: str = Field(..., description="Unique identifier for the doctor")
    name: str = Field(..., description="Full name of the doctor")
    specialization: str = Field(..., description="Medical specialization of the doctor")
    city: str = Field(..., description="City where the doctor practices")
    city_tier: Optional[int] = Field(None, description="Tier of the city (1, 2, or 3)")
    rating: float = Field(..., description="Doctor's rating out of 5")
    total_reviews: int = Field(..., description="Total number of reviews received")
    locations: List[str] = Field(default_factory=list, description="List of practice locations")
    contributing_sources: List[str] = Field(default_factory=list, description="Sources that contributed to this data")
    profile_urls: Dict[str, str] = Field(default_factory=dict, description="URLs to doctor profiles on different platforms")
    confidence_score: float = Field(default=0.0, description="Confidence score for the data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of when the data was collected")

    def __init__(self, **data):
        super().__init__(**data)
        # Calculate initial confidence score if none was provided
        if self.confidence_score == 0.0 and 'confidence_score' not in data:
            self.confidence_score = self._calculate_initial_confidence()

    def _calculate_initial_confidence(self) -> float:
        """Calculate an initial confidence score based on available data."""
        try:
            # Rating factor (0.3)
            rating_score = 0.0
            if self.rating >= 4.5:
                rating_score = 1.0
            elif self.rating >= 4.0:
                rating_score = 0.8
            elif self.rating >= 3.5:
                rating_score = 0.6
            elif self.rating >= 3.0:
                rating_score = 0.4
            else:
                rating_score = 0.2

            # Review count factor (0.2)
            review_score = min(self.total_reviews / 1000, 1.0)

            # Source quality factor (0.2)
            priority_sources = ["practo", "google", "justdial"]
            doctor_sources = [s.lower() for s in self.contributing_sources]
            priority_count = sum(1 for s in priority_sources if s in doctor_sources)
            source_score = priority_count / len(self.contributing_sources) if self.contributing_sources else 0.0

            # Source diversity factor (0.15)
            source_diversity_score = min(len(self.contributing_sources) / 3, 1.0)

            # Location completeness factor (0.15)
            location_score = min(len(self.locations) / 3, 1.0)

            # Calculate weighted score
            weights = [0.3, 0.2, 0.2, 0.15, 0.15]
            scores = [rating_score, review_score, source_score, source_diversity_score, location_score]
            return sum(w * s for w, s in zip(weights, scores))

        except Exception:
            return 0.1  # Fallback to a minimal score

    @field_validator("rating")
    def validate_rating(cls, v: float) -> float:
        """Validate rating is between 0 and 5."""
        if not 0 <= v <= 5:
            raise ValueError("Rating must be between 0 and 5")
        return v

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty and properly formatted."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("total_reviews")
    def validate_total_reviews(cls, v: int) -> int:
        """Validate total_reviews is non-negative."""
        if v < 0:
            raise ValueError("Total reviews cannot be negative")
        return v

    def merge_with(self, other: 'Doctor') -> None:
        """
        Merge another doctor's data into this one.
        Used during the discovery phase for deduplication.
        """
        # Calculate quality scores for comparison
        current_quality = self.total_reviews + (self.rating * 10)
        other_quality = other.total_reviews + (other.rating * 10)

        # Update basic info if other record has better quality
        if other_quality > current_quality:
            self.name = other.name
            self.specialization = other.specialization
            # Don't update city/city_tier as they might be different

        # Merge locations with fuzzy matching
        for loc in other.locations:
            is_similar = False
            for existing_loc in self.locations:
                if fuzz.partial_ratio(loc.lower(), existing_loc.lower()) > FUZZY_MATCH_THRESHOLD:
                    is_similar = True
                    break
            if not is_similar and loc not in self.locations:
                # Basic validation for location
                if len(loc) > 5 and "consultation" not in loc.lower() and "online" not in loc.lower():
                    self.locations.append(loc)

        # Merge contributing sources
        for source in other.contributing_sources:
            if source not in self.contributing_sources:
                self.contributing_sources.append(source)

        # Update timestamp
        self.timestamp = datetime.now()

        # Reset rating/reviews/confidence as they need to be recalculated
        self.rating = 0.0
        self.total_reviews = 0
        self.confidence_score = 0.0
        self.profile_urls = {}

    def to_dict(self) -> Dict:
        """Convert doctor to dictionary format."""
        return {
            "id": self.id,
            "name": self.name,
            "specialization": self.specialization,
            "city": self.city,
            "city_tier": self.city_tier,
            "rating": self.rating,
            "total_reviews": self.total_reviews,
            "locations": self.locations,
            "contributing_sources": self.contributing_sources,
            "profile_urls": self.profile_urls,
            "confidence_score": self.confidence_score,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Doctor':
        """Create doctor from dictionary format."""
        # Convert timestamp string back to datetime if needed
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "doc123",
                "name": "Dr. John Doe",
                "specialization": "Cardiologist",
                "city": "Mumbai",
                "city_tier": 1,
                "rating": 4.5,
                "total_reviews": 100,
                "locations": ["Hospital A", "Clinic B"],
                "contributing_sources": ["practo", "google"],
                "profile_urls": {
                    "practo": "https://practo.com/doctor/john-doe",
                    "google": "https://g.page/doctor-john-doe"
                },
                "confidence_score": 0.85,
                "timestamp": "2024-03-15T10:30:00"
            }
        }
    } 