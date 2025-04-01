import asyncio
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from ..models.doctor import Doctor
from ..models.city import CityInfo
from ..config import (
    DISCOVERY_MODEL_NAME,
    MAX_CONCURRENT_REQUESTS,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RATING_SOURCE_WEIGHTS
)
from ..services.city_service import CityService
from ..services.verification import DoctorVerificationService
from ..utils.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class DoctorDiscoveryService:
    """Service for discovering and aggregating doctor information."""

    def __init__(
        self,
        city_service: Optional[CityService] = None,
        verification_service: Optional[DoctorVerificationService] = None,
        client: Optional[GeminiClient] = None
    ):
        """Initialize the service."""
        self.city_service = city_service or CityService()
        self.verification_service = verification_service or DoctorVerificationService()
        self.client = client or GeminiClient(model_name=DISCOVERY_MODEL_NAME)
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def search_doctors(
        self,
        specialization: str,
        city: str,
        country: str = "India"
    ) -> List[Doctor]:
        """
        Search for doctors by specialization and city.

        Args:
            specialization: Medical specialization
            city: City name
            country: Country name (default: India)

        Returns:
            List of Doctor objects
        """
        try:
            # Get city information
            city_info = self.city_service.get_city_by_name(city)
            if not city_info:
                logger.error(f"City not found: {city}")
                return []

            # Build search query
            query = self._build_search_query(
                specialization=specialization,
                city=city,
                country=country
            )

            # Process sources concurrently
            sources = ["practo", "google", "justdial"]
            tasks = [
                self.process_source(source, query)
                for source in sources
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Flatten and deduplicate results
            doctors = []
            seen_ids = set()
            for source_doctors in results:
                if isinstance(source_doctors, Exception):
                    logger.error(f"Error processing source: {str(source_doctors)}")
                    continue
                for doctor in source_doctors:
                    if doctor.id not in seen_ids:
                        seen_ids.add(doctor.id)
                        doctors.append(doctor)

            # Sort by confidence score
            doctors.sort(key=lambda x: x.confidence_score, reverse=True)
            return doctors

        except Exception as e:
            logger.error(f"Error in search_doctors: {str(e)}")
            return []

    def _build_search_query(
        self,
        specialization: str,
        city: str,
        country: str
    ) -> str:
        """Build search query for doctor discovery."""
        return f"Find doctors in {city}, {country} specializing in {specialization}"

    async def process_source(
        self,
        source: str,
        query: str
    ) -> List[Doctor]:
        """
        Process a single source to get doctor information.

        Args:
            source: Source name (e.g., "practo", "google")
            query: Search query

        Returns:
            List of Doctor objects
        """
        retries = 0
        while retries < MAX_RETRIES:
            try:
                async with self.semaphore:
                    response = await self.client.generate_structured(
                        prompt=query,
                        timeout=REQUEST_TIMEOUT
                    )
                return self._parse_source_response(response, source)
            except Exception as e:
                retries += 1
                if retries == MAX_RETRIES:
                    logger.error(f"Error processing source {source}: {str(e)}")
                    return []
                await asyncio.sleep(1)  # Wait before retrying

    def _parse_source_response(self, response: str, source: str) -> List[Doctor]:
        """Parse source response into Doctor objects."""
        try:
            # Parse response into list of dictionaries
            data = self.client.parse_response(response)
            if not isinstance(data, list):
                data = [data]

            # Convert to Doctor objects
            doctors = []
            for item in data:
                doctor = self._extract_doctor_info(item, source)
                if doctor:
                    doctors.append(doctor)
            return doctors

        except Exception as e:
            logger.error(f"Error parsing source response: {str(e)}")
            return []

    def _extract_doctor_info(self, data: dict, source: str) -> Optional[Doctor]:
        """Extract doctor information from source data."""
        try:
            # Get city information
            city = data.get("city")
            if not city:
                return None

            city_info = self.city_service.get_city_by_name(city)
            if not city_info:
                return None

            # Create Doctor object
            return Doctor(
                id=f"{source}_{data.get('name', '').lower().replace(' ', '_')}",
                name=data.get("name", ""),
                specialization=data.get("specialization", ""),
                city=city,
                city_tier=city_info.tier,
                rating=float(data.get("rating", 0.0)),
                total_reviews=int(data.get("total_reviews", 0)),
                locations=data.get("locations", []),
                contributing_sources=[source],
                profile_urls=data.get("profile_urls", {}),
                confidence_score=0.0,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error extracting doctor info: {str(e)}")
            return None

    def _clean_doctor_name(self, name: str) -> str:
        """Clean and standardize doctor name."""
        name = name.strip()
        prefixes = ['dr.', 'dr ', 'prof.', 'prof ']
        
        # Remove any existing prefix
        lower_name = name.lower()
        for prefix in prefixes:
            if lower_name.startswith(prefix):
                name = name[len(prefix):].strip()
                break
        
        # Add standard prefix
        return f"Dr. {name}"

    def _parse_rating(self, rating: Any) -> float:
        """Parse and validate rating."""
        try:
            rating = float(str(rating).replace('out of 5.0', '').strip())
            return min(max(rating, 0.0), 5.0)
        except (ValueError, TypeError):
            return 0.0

    def _parse_reviews(self, reviews: Any) -> int:
        """Parse and validate review count."""
        try:
            if isinstance(reviews, str):
                # Remove any text and convert to number
                reviews = ''.join(c for c in reviews if c.isdigit())
            return max(int(reviews), 0)
        except (ValueError, TypeError):
            return 0

    def _clean_locations(self, locations: List[str]) -> List[str]:
        """Clean and validate location list."""
        if not isinstance(locations, list):
            return []
            
        # Clean each location
        cleaned = []
        for loc in locations:
            if isinstance(loc, str) and loc.strip():
                cleaned.append(loc.strip())
        
        return cleaned

    def _calculate_initial_confidence(self, info: Dict) -> float:
        """Calculate initial confidence score."""
        score = 0.0
        
        # Base confidence from rating and reviews
        if info['rating'] > 0:
            score += min(info['rating'] / 5.0 * 0.3, 0.3)  # Up to 30% from rating
            
        if info['reviews'] > 0:
            score += min(info['reviews'] / 1000 * 0.2, 0.2)  # Up to 20% from reviews
            
        # Additional confidence from data completeness
        if info['locations']:
            score += 0.1  # 10% for having location information
            
        if info['profile_urls']:
            score += 0.1  # 10% for having profile URLs
            
        # Source-specific confidence
        source = info['contributing_sources'][0]
        source_weight = RATING_SOURCE_WEIGHTS.get(source, 0.1)
        score += source_weight
        
        return min(score, 1.0)  # Ensure score is between 0 and 1 