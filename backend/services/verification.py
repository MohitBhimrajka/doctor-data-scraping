import logging
from typing import List, Dict, Optional
from datetime import datetime
from ..models.doctor import Doctor
from ..config import (
    VERIFICATION_MODEL_NAME,
    RATING_SOURCE_WEIGHTS,
    MAX_RETRIES,
    REQUEST_TIMEOUT
)
from ..utils.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class DoctorVerificationService:
    """Service for verifying and validating doctor information."""

    def __init__(self, client: Optional[GeminiClient] = None):
        """Initialize the service."""
        self.client = client or GeminiClient(model_name=VERIFICATION_MODEL_NAME)

    async def verify_doctor(
        self,
        doctor: Doctor,
        sources: List[str]
    ) -> Doctor:
        """
        Verify doctor information using multiple sources.

        Args:
            doctor: Doctor object to verify
            sources: List of sources to check

        Returns:
            Updated Doctor object with verified information
        """
        try:
            # Build verification prompt
            prompt = self._build_verification_prompt(doctor, sources)

            # Get verification response
            response = await self.client.generate(prompt)

            # Parse response and update doctor
            verified_data = self._parse_verification_response(response)
            if verified_data:
                self._update_doctor(doctor, verified_data)

            # Calculate confidence score
            doctor.confidence_score = self.calculate_confidence_score(doctor)

            return doctor

        except Exception as e:
            logger.error(f"Error verifying doctor {doctor.name}: {str(e)}")
            return doctor

    def _build_verification_prompt(self, doctor: Doctor, sources: List[str]) -> str:
        """Build prompt for doctor verification."""
        return f"""
        Verify the following doctor information across {', '.join(sources)}:

        Name: {doctor.name}
        Specialization: {doctor.specialization}
        City: {doctor.city}
        Rating: {doctor.rating}
        Total Reviews: {doctor.total_reviews}
        Locations: {', '.join(doctor.locations)}
        Sources: {', '.join(doctor.contributing_sources)}

        Please provide verified information in the following format:
        name: Verified name
        specialization: Verified specialization
        rating: Verified rating (0-5)
        total_reviews: Verified number of reviews
        locations: Comma-separated list of verified locations
        """

    def _parse_verification_response(self, response: str) -> Dict:
        """Parse verification response into dictionary."""
        try:
            data = {}
            for line in response.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()

                    # Convert numeric values
                    if key in ['rating', 'total_reviews']:
                        try:
                            value = float(value) if key == 'rating' else int(value)
                        except ValueError:
                            continue

                    # Convert locations to list
                    if key == 'locations':
                        value = [loc.strip() for loc in value.split(',')]

                    data[key] = value

            return data

        except Exception as e:
            logger.error(f"Error parsing verification response: {str(e)}")
            return {}

    def _update_doctor(self, doctor: Doctor, verified_data: Dict) -> None:
        """Update doctor with verified data."""
        try:
            if 'name' in verified_data:
                doctor.name = verified_data['name']
            if 'specialization' in verified_data:
                doctor.specialization = verified_data['specialization']
            if 'rating' in verified_data:
                doctor.rating = verified_data['rating']
            if 'total_reviews' in verified_data:
                doctor.total_reviews = verified_data['total_reviews']
            if 'locations' in verified_data:
                doctor.locations = verified_data['locations']

            # Update timestamp
            doctor.timestamp = datetime.now()

        except Exception as e:
            logger.error(f"Error updating doctor: {str(e)}")

    def calculate_confidence_score(self, doctor: Doctor) -> float:
        """Calculate confidence score for doctor data."""
        try:
            # Rating consistency (0.3)
            rating_score = self._calculate_rating_consistency(doctor)

            # Review count weight (0.2)
            review_score = min(doctor.total_reviews / 1000, 1.0)

            # Source diversity (0.2)
            source_score = min(len(doctor.contributing_sources) / 3, 1.0)

            # Location completeness (0.15)
            location_score = min(len(doctor.locations) / 3, 1.0)

            # Profile completeness (0.15)
            profile_score = min(len(doctor.profile_urls) / 3, 1.0)

            # Calculate weighted average
            weights = [0.3, 0.2, 0.2, 0.15, 0.15]
            scores = [rating_score, review_score, source_score, location_score, profile_score]
            return sum(w * s for w, s in zip(weights, scores))

        except Exception as e:
            logger.error(f"Error calculating confidence score: {str(e)}")
            return 0.0

    def _calculate_rating_consistency(self, doctor: Doctor) -> float:
        """Calculate rating consistency score."""
        try:
            # Base score on rating value
            if doctor.rating >= 4.5:
                return 1.0
            elif doctor.rating >= 4.0:
                return 0.8
            elif doctor.rating >= 3.5:
                return 0.6
            elif doctor.rating >= 3.0:
                return 0.4
            else:
                return 0.2

        except Exception as e:
            logger.error(f"Error calculating rating consistency: {str(e)}")
            return 0.0 