import os
import json
import time
import logging
import argparse
import asyncio
import pandas as pd
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator
from fuzzywuzzy import fuzz
from tenacity import retry, stop_after_attempt, wait_exponential
import sqlite3
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
import random
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('doctor_search.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize rich console for better UI
console = Console()

# Load environment variables
load_dotenv()

# --- Configuration ---
@dataclass
class Config:
    API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    MODEL_NAME: str = "gemini-2.0-flash"
    MAX_RETRIES: int = 3
    MIN_RATING: float = 0.0
    MAX_RATING: float = 5.0
    FUZZY_MATCH_THRESHOLD: int = 85
    DB_PATH: str = "doctors.db"
    MAX_CONCURRENT_REQUESTS: int = 450  # Higher parallelism for faster performance
    REQUEST_TIMEOUT: float = 45.0  # Increased timeout for more reliable completion

    def validate(self) -> bool:
        if not self.API_KEY:
            logger.error("GEMINI_API_KEY environment variable not set")
            return False
        return True

# --- Data Models ---
class Doctor(BaseModel):
    name: str
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    reviews: int = Field(default=0, ge=0)
    locations: List[str] = Field(default_factory=list)
    specialization: str
    city: str
    contributing_sources: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

    @validator('rating')
    def validate_rating(cls, v):
        if v < 0 or v > 5:
            raise ValueError('Rating must be between 0 and 5')
        return v

    def merge_with(self, other: 'Doctor') -> None:
        """Merge data from another doctor record into this one"""
        # Add contributing sources - avoid duplicates and ensure we only have valid source names
        valid_sources = ["practo", "justdial", "general", "hospital", "social"]
        
        # Clean up existing sources
        self.contributing_sources = [src.lower().strip() for src in self.contributing_sources 
                                    if src.lower().strip() in valid_sources]
        
        # Add new sources from other doctor
        for source in other.contributing_sources:
            source = source.lower().strip()
            if source in valid_sources and source not in self.contributing_sources:
                self.contributing_sources.append(source)
        
        # Merge locations - avoid duplicates and try to keep quality data
        # First clean up locations to normalize them
        cleaned_other_locations = []
        for loc in other.locations:
            # Skip very short or generic locations
            if len(loc) < 5 or any(term in loc.lower() for term in ["multiple locations", "online", "consultation"]):
                continue
            cleaned_other_locations.append(loc)
        
        # Add new unique locations
        for loc in cleaned_other_locations:
            # Check if this location is already covered by an existing one
            should_add = True
            for existing_loc in self.locations:
                similarity = fuzz.partial_ratio(loc.lower(), existing_loc.lower())
                if similarity >= 85:  # High threshold to avoid merging different but similar locations
                    # If they're very similar but the new one is more detailed, replace the existing one
                    if len(loc) > len(existing_loc) * 1.5:  # Significantly more detailed
                        self.locations.remove(existing_loc)
                        should_add = True
                        break
                    else:
                        should_add = False
                        break
            
            if should_add and loc not in self.locations:
                self.locations.append(loc)
        
        # Update rating and reviews if the other record has more reviews
        if other.reviews > self.reviews:
            self.rating = other.rating
            self.reviews = other.reviews
        # If review counts are equal, prioritize higher rating
        elif other.reviews == self.reviews and other.rating > self.rating:
            self.rating = other.rating
        
        # Update timestamp
        self.timestamp = datetime.now()

# --- Database Management ---
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS doctors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    rating REAL DEFAULT 0.0,
                    reviews INTEGER DEFAULT 0,
                    locations TEXT,
                    specialization TEXT,
                    city TEXT,
                    contributing_sources TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def save_doctors(self, doctors: List[Doctor]):
        with sqlite3.connect(self.db_path) as conn:
            for doctor in doctors:
                conn.execute("""
                    INSERT INTO doctors (
                        name, rating, reviews, locations,
                        specialization, city, contributing_sources, timestamp
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doctor.name, doctor.rating, doctor.reviews,
                    json.dumps(doctor.locations), doctor.specialization,
                    doctor.city, json.dumps(doctor.contributing_sources),
                    doctor.timestamp.isoformat()
                ))

    def get_doctors(self, city: str, specialization: str) -> List[Doctor]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM doctors 
                WHERE city = ? AND specialization = ?
                ORDER BY rating DESC, reviews DESC
            """, (city, specialization))
            rows = cursor.fetchall()
            doctors = []
            for row in rows:
                data = dict(zip([col[0] for col in cursor.description], row))
                data['locations'] = json.loads(data['locations'])
                data['contributing_sources'] = json.loads(data['contributing_sources'])
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                
                # Remove the ID field which is not in the Doctor model
                data.pop('id')
                
                doctors.append(Doctor(**data))
            return doctors

# --- Prompt Management ---
class PromptManager:
    @staticmethod
    def _add_json_instruction(prompt: str) -> str:
        """
        Add JSON specific instruction to each prompt to ensure consistent output format
        """
        json_instruction = (
            "Provide results in the following JSON format only: "
            "[{\"name\": \"Doctor Name\", \"rating\": 4.5, \"reviews\": 120, "
            "\"location\": [\"Specific address in requested city\", \"Another address in requested city\"]}]. "
            "Output only the JSON list with no explanatory text. "
            "IMPORTANT: Only include doctors whose PRIMARY practice location is in the specified city. "
            "Do NOT include doctors who primarily practice in other cities. "
            "For each doctor, provide specific clinic/hospital addresses, not generic locations."
        )
        return f"{prompt}. {json_instruction}"

    @staticmethod
    def get_practo_prompt(location: str, specialization: str) -> List[str]:
        """Generate prompts for Practo search"""
        prompts = []
        
        # Core pattern variations with explicit location focus
        base_patterns = [
            f"site:practo.com {specialization} doctor primarily practicing in {location} clinic address rating reviews",
            f"site:practo.com {specialization} doctor with main clinic in {location} address rating reviews", 
            f"site:practo.com best {specialization} doctors based permanently in {location} rating reviews address",
            f"site:practo.com {specialization} specialist with clinic established in {location} address ratings",
            f"site:practo.com top rated {specialization} doctors only practicing in {location} address reviews"
        ]
        
        # Add negative constraints to exclude other cities
        other_cities = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune"]
        other_cities = [city for city in other_cities if city.lower() != location.lower()]
        
        for pattern in base_patterns:
            prompts.append(PromptManager._add_json_instruction(pattern))
            
            # Add a negative constraint version
            city_exclusion = " ".join([f"-{city}" for city in other_cities[:3]])
            prompts.append(PromptManager._add_json_instruction(f"{pattern} {city_exclusion}"))
        
        return prompts

    @staticmethod
    def get_justdial_prompt(location: str, specialization: str) -> List[str]:
        """Generate prompts for JustDial search"""
        prompts = []
        
        # Core pattern variations with explicit location focus
        base_patterns = [
            f"site:justdial.com {specialization} doctors primarily based in {location} clinic address rating reviews",
            f"site:justdial.com best {specialization} clinics established in {location} exact address ratings",
            f"site:justdial.com {specialization} specialist with permanent clinic in {location} address ratings"
        ]
        
        # Add negative constraints to exclude other cities
        other_cities = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune"]
        other_cities = [city for city in other_cities if city.lower() != location.lower()]
        
        for pattern in base_patterns:
            prompts.append(PromptManager._add_json_instruction(pattern))
            
            # Add a negative constraint version
            city_exclusion = " ".join([f"-{city}" for city in other_cities[:3]])
            prompts.append(PromptManager._add_json_instruction(f"{pattern} {city_exclusion}"))
        
        return prompts

    @staticmethod
    def get_general_prompt(location: str, specialization: str) -> List[str]:
        """Generate prompts for general search (Google, Bing, etc.)"""
        prompts = []
        
        # Core queries for general search with explicit location focus
        base_patterns = [
            f"{specialization} doctor with permanent clinic in {location} exact street address rating reviews",
            f"best {specialization} doctors primarily practicing in {location} clinic address ratings",
            f"top rated {specialization} specialists based in {location} hospital/clinic address reviews"
        ]
        
        # Add negative constraints to exclude other cities
        other_cities = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune"]
        other_cities = [city for city in other_cities if city.lower() != location.lower()]
        
        for pattern in base_patterns:
            prompts.append(PromptManager._add_json_instruction(pattern))
            
            # Add a negative constraint version
            city_exclusion = " ".join([f"-{city}" for city in other_cities[:3]])
            prompts.append(PromptManager._add_json_instruction(f"{pattern} {city_exclusion}"))
        
        return prompts

    @staticmethod
    def get_hospital_prompt(location: str, specialization: str) -> List[str]:
        """Generate prompts for hospital websites"""
        prompts = []
        
        # List of major hospital chains
        hospitals = [
            "apollo", "fortis", "manipal", "max", "medanta", "aiims", 
            "kokilaben", "narayana", "jaslok", "lilavati"
        ]
        
        # Generate hospital-specific queries with location focus
        for hospital in hospitals:
            base_patterns = [
                f"site:{hospital}hospitals.com {specialization} doctor at {hospital} {location} branch exact address rating",
                f"site:{hospital}.com {specialization} specialist practicing at {hospital} {location} location address"
            ]
            for pattern in base_patterns:
                prompts.append(PromptManager._add_json_instruction(pattern))
        
        return prompts

    @staticmethod
    def get_social_proof_prompt(location: str, specialization: str) -> List[str]:
        """Generate prompts for social proof and review sites"""
        prompts = []
        
        # Core pattern variations for social proof with location focus
        base_patterns = [
            f"site:google.com/maps {specialization} doctor clinics in {location} exact address rating reviews",
            f"site:yelp.com top {specialization} doctors permanently based in {location} clinic address ratings",
            f"site:healthgrades.com {specialization} specialists with established practice in {location} address"
        ]
        
        # Add negative constraints to exclude other cities
        other_cities = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune"]
        other_cities = [city for city in other_cities if city.lower() != location.lower()]
        
        for pattern in base_patterns:
            prompts.append(PromptManager._add_json_instruction(pattern))
            
            # Add a negative constraint version
            city_exclusion = " ".join([f"-{city}" for city in other_cities[:3]])
            prompts.append(PromptManager._add_json_instruction(f"{pattern} {city_exclusion}"))
        
        return prompts

# --- Data Processing ---
class DataProcessor:
    @staticmethod
    def extract_json_from_response(response: str) -> Optional[List[Dict]]:
        """Extract JSON data from various response formats"""
        try:
            if "```json" in response:
                parts = response.split("```json", 1)
                json_str = parts[1].split("```", 1)[0].strip()
            elif response.strip().startswith('['):
                json_str = response.strip()
            else:
                start_index = response.find('[')
                end_index = response.rfind(']')
                if start_index != -1 and end_index > start_index:
                    json_str = response[start_index:end_index + 1]
                else:
                    return None

            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Error extracting JSON: {e}")
            return None

    @staticmethod
    def is_location_in_city(location: str, city: str, specialization: str = None) -> bool:
        """
        Check if a location is likely in the specified city.
        Returns True if the location appears to be in the city, False otherwise.
        Uses a more sophisticated approach to handle common location types.
        For rare specialists, applies more lenient validation to increase result count.
        """
        if not location or not city:
            return False
            
        # Normalize strings for comparison
        location_lower = location.lower()
        city_lower = city.lower()
        
        # Skip extremely generic locations
        generic_locations = [
            "multiple locations", "available online", "teleconsultation", "tele consultation",
            "consultation available", "multiple branches", "across india", "pan india", 
            "all over india", "all major cities", "tele medicine", "available for video consultation",
            "online consultation", "virtual consultation", "many locations", "visiting consultant",
            "all over", "available at", "visit for consultation"
        ]
        
        # For very specific/rare specializations, we're more lenient with generic locations
        rare_specialties = [
            "neurologist", "endocrinologist", "rheumatologist", "hematologist", 
            "nephrologist", "oncologist", "radiologist", "gastroenterologist"
        ]
        is_rare_specialty = specialization and specialization.lower() in rare_specialties
        
        # If it's a rare specialty, only skip the most generic locations
        if is_rare_specialty:
            # Use a more limited list of generic locations to filter out
            very_generic = ["across india", "pan india", "all over india", "all major cities"]
            if any(generic in location_lower for generic in very_generic):
                return False
        else:
            # For common specialties, apply stricter filtering
            if any(generic in location_lower for generic in generic_locations):
                return False
        
        # City variants - account for common ways to refer to the same city
        city_variants = {
            "delhi": ["delhi", "new delhi", "delhi ncr", "ncr"],
            "mumbai": ["mumbai", "bombay", "navi mumbai", "thane"],
            "bangalore": ["bangalore", "bengaluru"],
            "hyderabad": ["hyderabad", "secunderabad"],
            "chennai": ["chennai", "madras"],
            "kolkata": ["kolkata", "calcutta"],
            "pune": ["pune"],
            "ahmedabad": ["ahmedabad"],
            "jaipur": ["jaipur"],
            "lucknow": ["lucknow"],
            "chandigarh": ["chandigarh"],
            "gurgaon": ["gurgaon", "gurugram"]
        }
        
        # Get variants for the requested city
        requested_city_variants = []
        for city_key, variants in city_variants.items():
            if city_lower in variants:
                requested_city_variants = variants
                break
        
        if not requested_city_variants:
            requested_city_variants = [city_lower]
        
        # Check if any of the city variants appear in the location
        for variant in requested_city_variants:
            if variant in location_lower:
                return True
                
        # If the city is Delhi, also check for Delhi NCR cities
        if city_lower == "delhi":
            ncr_cities = ["gurgaon", "gurugram", "noida", "faridabad", "ghaziabad"]
            for ncr_city in ncr_cities:
                if ncr_city in location_lower:
                    # For Delhi, we'll accept NCR cities
                    return True
                    
        # Handle special case for Delhi NCR region
        if "delhi ncr" in location_lower or "ncr" in location_lower:
            if city_lower == "delhi":
                return True
        
        # For rare specialties, we're more lenient with locations in other cities
        # as these doctors may travel between cities or have limited practitioners
        if is_rare_specialty:
            # If it's a hospital or medical center name without clear city indication,
            # accept it for rare specialists
            medical_indicators = ["hospital", "clinic", "medical", "healthcare", "centre", "center"]
            if any(indicator in location_lower for indicator in medical_indicators):
                # If it looks like a medical facility without obvious city conflicts, accept it
                return True
                
        # If another non-NCR city is mentioned and it's not the requested city
        for city_key, variants in city_variants.items():
            # Skip if this is the requested city
            if city_lower in variants:
                continue
                
            # If we're looking for Delhi, we accept NCR cities, so skip checking those
            if city_lower == "delhi" and city_key in ["gurgaon"]:
                continue
                
            # If this city variant appears in the location
            for variant in variants:
                if variant in location_lower:
                    # Check if it's mentioning travel/visit to this city
                    travel_indicators = ["visit", "travels to", "also available in", "consultation in"]
                    if any(indicator in location_lower for indicator in travel_indicators):
                        # This indicates the doctor might still be primarily in the requested city
                        continue
                    
                    # For rare specialists, allow some flexibility if they appear to 
                    # practice in multiple cities
                    if is_rare_specialty and "also" in location_lower:
                        continue
                        
                    # No travel indicators but another city mentioned
                    return False
        
        # If the location doesn't contain the city but doesn't have any conflicting cities either,
        # we'll accept it, assuming it's a specific location (like hospital/clinic name) within the city
        return True

    @staticmethod
    def standardize_doctor_data(data: List[Dict], source: str, specialization: str, city: str) -> List[Doctor]:
        """
        Standardize and clean doctor data from various sources
        Focus only on core fields: name, rating, reviews, locations
        Apply strict location validation
        """
        standardized_doctors = []
        
        # Normalize source name to ensure consistency
        normalized_source = source.lower().strip()
        valid_sources = ["practo", "justdial", "general", "hospital", "social"]
        if normalized_source not in valid_sources:
            normalized_source = "general"
        
        for item in data:
            try:
                # Skip entries without a name
                if not item.get('name'):
                    continue
                
                # Clean and standardize doctor name
                name = item.get('name', '').strip()
                if not name.lower().startswith('dr') and not name.lower().startswith('prof'):
                    name = f"Dr. {name}"
                
                # Standardize rating
                rating_value = 0.0
                if 'rating' in item:
                    try:
                        rating_str = str(item['rating']).replace('/5', '').replace('/10', '').strip()
                        rating_value = float(rating_str)
                        if '/10' in str(item['rating']):
                            rating_value /= 2  # Convert 10-scale to 5-scale
                        rating_value = min(max(rating_value, 0), 5)  # Ensure in range 0-5
                    except (ValueError, TypeError):
                        pass
                
                # Standardize reviews count
                reviews_count = 0
                if 'reviews' in item:
                    try:
                        reviews_str = str(item['reviews']).replace('+', '').replace('reviews', '').strip()
                        reviews_count = int(reviews_str)
                    except (ValueError, TypeError):
                        pass
                
                # Process locations - ensure it's a list
                locations = []
                if 'location' in item:
                    if isinstance(item['location'], list):
                        locations.extend(item['location'])
                    elif isinstance(item['location'], str):
                        locations.append(item['location'])
                
                # Clean locations and validate they're in the specified city
                cleaned_locations = []
                valid_location_found = False
                
                for loc in locations:
                    if loc and isinstance(loc, str):
                        # Remove very short locations and apply basic cleaning
                        loc = loc.strip()
                        
                        # Remove generic location descriptors that don't add value
                        generic_terms = ['near', 'opposite', 'behind', 'next to', 'in front of', 'across from', 'located at']
                        for term in generic_terms:
                            if loc.lower().startswith(term):
                                loc = loc[len(term):].strip()
                        
                        # Keep only reasonable length locations (not too short, not too long)
                        if 3 < len(loc) < 150 and loc not in cleaned_locations:
                            # Check if this location is likely in the specified city
                            if DataProcessor.is_location_in_city(loc, city, specialization):
                                cleaned_locations.append(loc)
                                valid_location_found = True
                
                # Skip doctors with no valid locations in the specified city
                if not valid_location_found:
                    continue
                
                # Create doctor object with only the core fields
                doctor = Doctor(
                    name=name,
                    rating=rating_value,
                    reviews=reviews_count,
                    locations=cleaned_locations,
                    specialization=specialization,
                    city=city,
                    contributing_sources=[normalized_source]
                )
                
                standardized_doctors.append(doctor)
                
            except Exception as e:
                logger.error(f"Error standardizing doctor data: {str(e)}")
                continue
        
        return standardized_doctors

    @staticmethod
    def deduplicate_doctors(doctors: List[Doctor], threshold: int) -> List[Doctor]:
        """
        Deduplicate doctors based on name similarity and location context
        Only merge if they have similar locations or appear to be the same person
        Uses a more sophisticated approach to handle common cases of duplication
        """
        if not doctors:
            return []
        
        # Sort doctors by rating (highest first) and then by number of reviews to prioritize better profiles
        sorted_doctors = sorted(doctors, key=lambda x: (x.rating, x.reviews, len(x.locations)), reverse=True)
        
        # Use first doctor as seed for the result list
        result = [sorted_doctors[0]]
        
        # Compare each doctor to those already in the result
        for current in sorted_doctors[1:]:
            is_duplicate = False
            best_match_idx = -1
            best_match_score = 0
            
            for idx, existing in enumerate(result):
                # Compare names for similarity - case insensitive and normalize spaces
                current_name = ' '.join(current.name.lower().split())
                existing_name = ' '.join(existing.name.lower().split())
                
                # Direct match - definitely the same doctor
                if current_name == existing_name:
                    best_match_idx = idx
                    best_match_score = 100
                    break
                
                # Check for prefix matches (e.g., "Dr. John Smith" vs "John Smith")
                # Remove common prefixes for comparison
                prefixes = ["dr.", "dr ", "prof.", "prof ", "professor"]
                clean_current = current_name
                clean_existing = existing_name
                
                for prefix in prefixes:
                    if clean_current.startswith(prefix):
                        clean_current = clean_current[len(prefix):].strip()
                    if clean_existing.startswith(prefix):
                        clean_existing = clean_existing[len(prefix):].strip()
                
                # After removing prefixes, check for exact match
                if clean_current == clean_existing:
                    best_match_idx = idx
                    best_match_score = 100
                    break
                
                # Use fuzzy matching for more complex cases
                name_similarity = fuzz.ratio(clean_current, clean_existing)
                
                # Only consider it a potential match if similarity is above threshold
                if name_similarity >= threshold and name_similarity > best_match_score:
                    # For high similarity matches, check if specialization and city match
                    if current.specialization == existing.specialization and current.city == existing.city:
                        best_match_idx = idx
                        best_match_score = name_similarity
            
            # If we found a match, determine if we should merge
            if best_match_idx >= 0:
                existing = result[best_match_idx]
                merge_compatible = False
                
                # Case 1: Perfect name match - always merge
                if best_match_score == 100:
                    merge_compatible = True
                # Case 2: High similarity match - check location compatibility
                elif best_match_score >= threshold + 10:  # Higher threshold for location check
                    # If either has no locations, assume compatible
                    if not current.locations or not existing.locations:
                        merge_compatible = True
                    else:
                        # Check if at least one location from each doctor seems similar
                        for curr_loc in current.locations:
                            curr_loc_lower = curr_loc.lower()
                            for exist_loc in existing.locations:
                                exist_loc_lower = exist_loc.lower()
                                
                                # Look for common identifiable segments in locations
                                loc_similarity = fuzz.partial_ratio(curr_loc_lower, exist_loc_lower)
                                
                                # Also check for common hospital/area names that might indicate same doctor
                                common_segments = [
                                    "hospital", "medical", "clinic", "centre", "center", 
                                    "institute", "aiims", "apollo", "fortis", "max", "medanta"
                                ]
                                
                                has_common_segment = False
                                for segment in common_segments:
                                    if segment in curr_loc_lower and segment in exist_loc_lower:
                                        has_common_segment = True
                                        break
                                
                                if loc_similarity >= 70 or has_common_segment:
                                    merge_compatible = True
                                    break
                            if merge_compatible:
                                break
                        
                        # If no location match but high name similarity and same specialization/city,
                        # likely the same doctor with different practice locations
                        if not merge_compatible and best_match_score >= 95:
                            merge_compatible = True
                
                # If compatible, merge the doctors
                if merge_compatible:
                    result[best_match_idx].merge_with(current)
                    is_duplicate = True
            
            # If not a duplicate or not compatible for merging, add to results
            if not is_duplicate:
                result.append(current)
        
        return result

# --- API Client ---
class GeminiClient:
    def __init__(self, api_key: str, model_name: str):
        """Initialize the Gemini client with API key and model name"""
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.request_counter = 0
        self.rate_limit = 60  # Keep track of requests to respect rate limits
        self.last_request_time = time.time()
        self.logger = logging.getLogger(__name__)
        self.semaphore = asyncio.Semaphore(360)  # Increased parallelism for better performance
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_content(self, prompt: str) -> Optional[str]:
        """
        Generate content using Gemini API with built-in retry logic
        """
        # Rate limiting protection - lightweight version
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < 1 and self.request_counter >= self.rate_limit:
            wait_time = 1.0
            self.logger.info(f"Rate limit approached, waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            self.request_counter = 0
            
        try:
            async with self.semaphore:
                # Update request tracking
                self.request_counter += 1
                self.last_request_time = time.time()
                
                # Prepare content for the API
                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt),
                        ],
                    )
                ]
                
                # Generate content config - optimized for speed
                generate_content_config = types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=8192,
                    top_p=0.95,
                    top_k=64,
                    response_mime_type="text/plain",
                )
                
                # Call the Gemini API using asyncio.to_thread for non-blocking execution
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.model_name,
                    contents=contents,
                    config=generate_content_config,
                )
                
                # Extract text from response
                if response and hasattr(response, 'text'):
                    return response.text
                elif response and hasattr(response, 'parts') and response.parts:
                    return "".join(part.text for part in response.parts if hasattr(part, 'text'))
                return None
            
        except Exception as e:
            self.logger.error(f"Error generating content: {type(e).__name__}: {str(e)}")
            # Re-raise the exception so the retry decorator can handle it
            raise
    
    async def generate_content_batch(self, prompts: List[str]) -> List[Optional[str]]:
        """
        Generate content for multiple prompts in parallel with high throughput.
        Returns a list of responses with None values for failed requests.
        """
        if not prompts:
            return []
        
        # Create tasks for all prompts for maximum parallelism
        tasks = [self.generate_content(prompt) for prompt in prompts]
        
        # Use gather to run all tasks concurrently
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results to handle exceptions
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Error in batch processing: {type(result).__name__}: {str(result)}")
                    processed_results.append(None)
                else:
                    processed_results.append(result)
            
            success_count = sum(1 for r in processed_results if r is not None)
            self.logger.info(f"Batch complete: {success_count}/{len(prompts)} successful")
            
            return processed_results
        except Exception as e:
            self.logger.error(f"Error in batch processing: {type(e).__name__}: {str(e)}")
            # Return a list of None values matching the length of prompts
            return [None] * len(prompts)

# --- Main Application ---
class DoctorSearchApp:
    def __init__(self, config: Config):
        """Initialize the Doctor Search App with configuration"""
        self.config = config
        self.gemini_client = GeminiClient(config.API_KEY, config.MODEL_NAME)
        self.db_manager = DatabaseManager(config.DB_PATH)
        self.prompt_manager = PromptManager()
        self.data_processor = DataProcessor()
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        
        # Define city tiers for India - Expanded city list
        self.india_cities = {
            "tier1": [
                "mumbai", "delhi", "bangalore", "hyderabad", "chennai", 
                "kolkata", "pune", "ahmedabad", "surat", "jaipur"
            ],
            "tier2": [
                "lucknow", "kanpur", "nagpur", "indore", "thane", "bhopal", 
                "visakhapatnam", "pimpri-chinchwad", "patna", "vadodara", 
                "ghaziabad", "ludhiana", "agra", "nashik", "faridabad", 
                "meerut", "rajkot", "kalyan-dombivli", "vasai-virar", 
                "varanasi", "srinagar", "aurangabad", "dhanbad", "amritsar", 
                "navi-mumbai", "allahabad", "ranchi", "howrah", "coimbatore", 
                "jabalpur", "gwalior", "vijayawada", "jodhpur", "madurai", "raipur"
            ],
            "tier3": [
                "kota", "chandigarh", "guwahati", "solapur", "hubli-dharwad", 
                "bareilly", "moradabad", "mysore", "gurgaon", "aligarh", 
                "jalandhar", "tiruchirappalli", "bhubaneswar", "salem", "mira-bhayandar", 
                "warangal", "jalgaon", "guntur", "thiruvananthapuram", "bhiwandi", 
                "saharanpur", "gorakhpur", "bikaner", "amravati", "noida", 
                "jamshedpur", "bhilai", "cuttack", "firozabad", "kochi", 
                "nellore", "bhavnagar", "dehradun", "durgapur", "asansol", 
                "rourkela", "nanded", "kolhapur", "ajmer", "akola", "gulbarga", 
                "jamnagar", "ujjain", "loni", "siliguri", "jhansi", 
                "ulhasnagar", "jammu", "sangli-miraj", "mangalore", "erode"
            ]
        }

    async def search_all_sources(self, location: str, specialization: str) -> List[Doctor]:
        """
        Search all sources for doctors based on location and specialization
        """
        # Define base sources
        base_sources = ["practo", "justdial", "general", "hospital", "social"]
        
        # Add secondary sources with location variations to increase results
        # This helps find doctors in nearby areas or with different spellings
        location_variants = self._get_location_variants(location)
        secondary_sources = []
        
        # Only add secondary sources for major cities with known variants
        if location_variants:
            for variant in location_variants:
                if variant != location:  # Skip the base location
                    secondary_sources.append(("general", variant, specialization))
        
        all_doctors = []
        
        # Create progress context
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            # Search each source concurrently
            async def search_with_progress(source: str, loc: str = None, spec: str = None) -> List[Doctor]:
                search_loc = loc or location
                search_spec = spec or specialization
                task = progress.add_task(f"Searching {source} ({search_loc})...", total=1)
                
                try:
                    doctors = await self.search_source(source, search_loc, search_spec)
                    progress.update(task, completed=1, description=f"[green]Found {len(doctors)} doctors from {source} ({search_loc})")
                    return doctors
                except Exception as e:
                    logger.error(f"Error searching {source} ({search_loc}): {str(e)}")
                    progress.update(task, completed=1, description=f"[red]Error searching {source} ({search_loc})")
                    return []
            
            # Execute primary searches concurrently
            primary_tasks = [search_with_progress(source) for source in base_sources]
            primary_results = await asyncio.gather(*primary_tasks)
            
            # Add all primary results
            for doctors in primary_results:
                all_doctors.extend(doctors)
                
            # If we found fewer than 10 doctors with primary sources, try secondary sources
            if len(all_doctors) < 10 and secondary_sources:
                console.print("[yellow]Found limited results. Searching additional locations...[/yellow]")
                secondary_tasks = [search_with_progress(source, loc, spec) for source, loc, spec in secondary_sources]
                secondary_results = await asyncio.gather(*secondary_tasks)
                
                # Add secondary results
                for doctors in secondary_results:
                    all_doctors.extend(doctors)
            
            # Deduplicate across all sources
            if all_doctors:
                pre_dedup_count = len(all_doctors)
                all_doctors = DataProcessor.deduplicate_doctors(all_doctors, self.config.FUZZY_MATCH_THRESHOLD)
                post_dedup_count = len(all_doctors)
                
                # Save to database
                self.db_manager.save_doctors(all_doctors)
                
                dedup_info = f"(removed {pre_dedup_count - post_dedup_count} duplicates)"
                console.print(f"[bold green]Found {len(all_doctors)} unique doctors after deduplication {dedup_info}[/bold green]")
            else:
                console.print("[yellow]No doctors found matching your search criteria[/yellow]")
            
            return all_doctors
            
    def _get_location_variants(self, location: str) -> List[str]:
        """Get variations of a location name to increase search coverage"""
        location = location.lower().strip()
        
        # Define known variants for major cities
        variants = {
            "delhi": ["delhi", "new delhi", "delhi ncr"],
            "mumbai": ["mumbai", "bombay"], 
            "bangalore": ["bangalore", "bengaluru"],
            "hyderabad": ["hyderabad", "secunderabad"],
            "chennai": ["chennai", "madras"],
            "kolkata": ["kolkata", "calcutta"],
            "pune": ["pune", "pimpri-chinchwad"],
            "jaipur": ["jaipur"],
            "ahmedabad": ["ahmedabad"],
            "surat": ["surat"],
            "lucknow": ["lucknow"]
        }
        
        # Return variants for the given location
        for city, city_variants in variants.items():
            if location in city_variants:
                return city_variants
                
        # If not a major city, return just the original location
        return [location]

    async def search_source(self, source: str, location: str, specialization: str) -> List[Doctor]:
        """
        Search a specific source for doctors based on location and specialization
        """
        logger.info(f"Searching {source} for {specialization} doctors in {location}")
        
        # Get prompts for the specified source
        if source == "practo":
            prompts = PromptManager.get_practo_prompt(location, specialization)
        elif source == "justdial":
            prompts = PromptManager.get_justdial_prompt(location, specialization)
        elif source == "general":
            prompts = PromptManager.get_general_prompt(location, specialization)
        elif source == "hospital":
            prompts = PromptManager.get_hospital_prompt(location, specialization)
        elif source == "social":
            prompts = PromptManager.get_social_proof_prompt(location, specialization)
        else:
            logger.warning(f"Unknown source: {source}")
            return []
        
        # Limit the number of prompts to avoid excessive API calls
        # but ensure we use enough for good coverage, increased for comprehensive results
        max_prompts = 50  # Increased from 25 to maximize results
        if len(prompts) > max_prompts:
            # Randomly sample to maintain diversity but reduce count
            prompts = random.sample(prompts, max_prompts)
        
        logger.info(f"Generated {len(prompts)} prompts for {source}")
        
        try:
            # Process all prompts in one batch with high parallelism
            responses = await self.gemini_client.generate_content_batch(prompts)
            
            # Process responses
            raw_data = []
            for response in responses:
                if response:
                    try:
                        # Extract JSON data from the Gemini response
                        extracted_data = DataProcessor.extract_json_from_response(response)
                        if extracted_data:
                            raw_data.extend(extracted_data)
                    except Exception as e:
                        logger.error(f"Error processing response: {str(e)}")
                        continue
            
            logger.info(f"Extracted {len(raw_data)} raw doctor records from {source}")
            
            # Standardize and deduplicate the data
            doctors = DataProcessor.standardize_doctor_data(raw_data, source, specialization, location)
            unique_doctors = DataProcessor.deduplicate_doctors(doctors, self.config.FUZZY_MATCH_THRESHOLD)
            
            logger.info(f"Found {len(unique_doctors)} unique doctors from {source}")
            
            return unique_doctors
            
        except Exception as e:
            logger.error(f"Error searching {source}: {str(e)}")
            return []

    def display_results(self, doctors: List[Doctor]):
        """Display search results in a table format focusing on core fields"""
        if not doctors:
            console.print("[yellow]No doctors found matching the search criteria[/yellow]")
            return
        
        table = Table(
            title=f"Found {len(doctors)} Doctors",
            show_header=True,
            header_style="bold green"
        )
        
        # Define columns for the table
        table.add_column("Name")
        table.add_column("Rating", justify="center")
        table.add_column("Reviews", justify="center")
        table.add_column("Primary Location")
        table.add_column("Secondary Location")
        table.add_column("Sources", justify="center")
        
        # Add rows to the table
        for doctor in doctors:
            primary_location = doctor.locations[0] if doctor.locations else "N/A"
            secondary_location = doctor.locations[1] if len(doctor.locations) > 1 else "N/A"
            
            # Format sources cleanly
            sources = "; ".join(sorted(set(src.lower() for src in doctor.contributing_sources)))
            
            table.add_row(
                doctor.name,
                f"{doctor.rating:.1f} ⭐",
                str(doctor.reviews),
                primary_location,
                secondary_location,
                sources
            )
        
        console.print(table)

    async def search_countrywide(self, country: str, specialization: str) -> List[Doctor]:
        """
        Search for doctors across multiple cities in a country
        Currently only supports India with tiered city approach
        Always searches all tiers regardless of result counts to maximize coverage
        Implements throttling to prevent rate limiting issues
        """
        if country.lower() != "india":
            logger.warning(f"Countrywide search not supported for {country}")
            return []
        
        all_doctors = []
        
        # Create progress context
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            main_task = progress.add_task(f"[cyan]Searching across India for {specialization} doctors...", total=100)
            
            # Search Tier 1 cities (major metros)
            tier1_count = len(self.india_cities["tier1"])
            tier1_task = progress.add_task(f"[blue]Searching Tier 1 cities...", total=tier1_count, parent=main_task)
            
            tier1_cities = self.india_cities["tier1"]
            tier1_results = []
            
            for city in tier1_cities:
                city_task = progress.add_task(f"Searching {city.title()}", parent=tier1_task)
                try:
                    # Search all sources for this city with a retry mechanism
                    doctors = await self.search_city_with_retry(city, specialization)
                    if doctors:
                        tier1_results.extend(doctors)
                        progress.update(city_task, completed=1, description=f"[green]Found {len(doctors)} doctors in {city.title()}")
                    else:
                        progress.update(city_task, completed=1, description=f"[yellow]No doctors found in {city.title()}")
                    
                    # Add a delay between city searches to avoid rate limiting
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error searching {city}: {str(e)}")
                    progress.update(city_task, completed=1, description=f"[red]Error searching {city.title()}")
                
                progress.update(tier1_task, advance=1)
            
            all_doctors.extend(tier1_results)
            progress.update(main_task, advance=40)  # 40% progress after Tier 1
            
            # Add a delay before starting Tier 2 searches to avoid rate limiting
            await asyncio.sleep(2)
            
            # Always search Tier 2 cities (smaller but significant cities)
            # Select a subset to avoid too many API calls but still get good coverage
            tier2_sample = random.sample(self.india_cities["tier2"], min(6, len(self.india_cities["tier2"])))
            tier2_count = len(tier2_sample)
            tier2_task = progress.add_task(f"[blue]Searching Tier 2 cities...", total=tier2_count, parent=main_task)
            
            tier2_results = []
            for city in tier2_sample:
                city_task = progress.add_task(f"Searching {city.title()}", parent=tier2_task)
                try:
                    doctors = await self.search_city_with_retry(city, specialization)
                    if doctors:
                        tier2_results.extend(doctors)
                        progress.update(city_task, completed=1, description=f"[green]Found {len(doctors)} doctors in {city.title()}")
                    else:
                        progress.update(city_task, completed=1, description=f"[yellow]No doctors found in {city.title()}")
                    
                    # Add a delay between city searches to avoid rate limiting
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error searching {city}: {str(e)}")
                    progress.update(city_task, completed=1, description=f"[red]Error searching {city.title()}")
                
                progress.update(tier2_task, advance=1)
            
            all_doctors.extend(tier2_results)
            progress.update(main_task, advance=30)  # 70% progress after Tier 2
            
            # Add a delay before starting Tier 3 searches to avoid rate limiting
            await asyncio.sleep(2)
            
            # Always search Tier 3 cities for comprehensive coverage
            tier3_sample = random.sample(self.india_cities["tier3"], min(4, len(self.india_cities["tier3"])))
            tier3_count = len(tier3_sample)
            tier3_task = progress.add_task(f"[blue]Searching Tier 3 cities...", total=tier3_count, parent=main_task)
            
            tier3_results = []
            for city in tier3_sample:
                city_task = progress.add_task(f"Searching {city.title()}", parent=tier3_task)
                try:
                    doctors = await self.search_city_with_retry(city, specialization)
                    if doctors:
                        tier3_results.extend(doctors)
                        progress.update(city_task, completed=1, description=f"[green]Found {len(doctors)} doctors in {city.title()}")
                    else:
                        progress.update(city_task, completed=1, description=f"[yellow]No doctors found in {city.title()}")
                    
                    # Add a delay between city searches to avoid rate limiting
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error searching {city}: {str(e)}")
                    progress.update(city_task, completed=1, description=f"[red]Error searching {city.title()}")
                
                progress.update(tier3_task, advance=1)
            
            all_doctors.extend(tier3_results)
            progress.update(main_task, advance=30)  # 100% progress after Tier 3
            
            # Deduplicate across all cities
            if all_doctors:
                pre_dedup_count = len(all_doctors)
                all_doctors = DataProcessor.deduplicate_doctors(all_doctors, self.config.FUZZY_MATCH_THRESHOLD)
                post_dedup_count = len(all_doctors)
                
                # Save to database
                self.db_manager.save_doctors(all_doctors)
                
                tier_summary = f"Tier 1: {len(tier1_results)}, Tier 2: {len(tier2_results)}, Tier 3: {len(tier3_results)}"
                dedup_info = f"(removed {pre_dedup_count - post_dedup_count} duplicates)"
                console.print(f"[bold green]Found {len(all_doctors)} unique doctors across India after deduplication {dedup_info}[/bold green]")
                console.print(f"[bold blue]City tier summary: {tier_summary}[/bold blue]")
            else:
                console.print("[yellow]No doctors found matching your search criteria in India[/yellow]")
            
            return all_doctors

    async def search_city_with_retry(self, city: str, specialization: str, max_retries: int = 3) -> List[Doctor]:
        """
        Searches a city with retry logic and reduced batch size to avoid rate limiting
        """
        for attempt in range(max_retries):
            try:
                # Use all available sources to ensure consistent results with single city search
                if attempt == 0:
                    # First attempt - use all sources to match single city search results
                    sources = ["practo", "justdial", "general", "hospital", "social"]
                else:
                    # Subsequent attempts - try fewer sources if the first attempt failed
                    sources = ["general", "practo"]
                
                doctors = []
                for source in sources:
                    source_doctors = await self._search_source_safely(city, specialization, source)
                    doctors.extend(source_doctors)
                    # Add a small delay between sources to avoid rate limiting
                    await asyncio.sleep(0.5)
                
                # Deduplicate the results for this city
                if doctors:
                    return DataProcessor.deduplicate_doctors(doctors, self.config.FUZZY_MATCH_THRESHOLD)
                else:
                    # No doctors found in this city after trying all sources
                    return []
                
            except Exception as retry_error:
                logger.error(f"Retry {attempt+1} failed for {city}: {str(retry_error)}")
                # Exponential backoff - wait longer between retries
                await asyncio.sleep(2 ** attempt)
        
        # All retries failed
        logger.error(f"All retries failed for {city}")
        return []

    async def _search_source_safely(self, city: str, specialization: str, source: str) -> List[Doctor]:
        """
        Helper method to safely search a specific source with error handling
        """
        doctors = []
        try:
            # Get prompts with a reduced count
            prompts = []
            if source == "practo":
                prompts = PromptManager.get_practo_prompt(city, specialization)[:10]  # Limit prompts
            elif source == "justdial":
                prompts = PromptManager.get_justdial_prompt(city, specialization)[:10]  # Limit prompts
            elif source == "general":
                prompts = PromptManager.get_general_prompt(city, specialization)[:15]  # Limit prompts
            else:
                return []
            
            if not prompts:
                return []
            
            # Process in smaller batches to avoid rate limiting
            batch_size = 5  # Smaller batch size for reliability
            
            for i in range(0, len(prompts), batch_size):
                batch = prompts[i:i+batch_size]
                try:
                    # Process the batch
                    responses = await self.gemini_client.generate_content_batch(batch)
                    raw_data = []
                    
                    for response in responses:
                        if response:
                            try:
                                # Extract JSON data from the response
                                extracted_data = DataProcessor.extract_json_from_response(response)
                                if extracted_data:
                                    raw_data.extend(extracted_data)
                            except Exception as extract_error:
                                logger.debug(f"Extraction error: {str(extract_error)}")
                                continue
                    
                    # Standardize and add to doctors list
                    if raw_data:
                        batch_doctors = DataProcessor.standardize_doctor_data(raw_data, source, specialization, city)
                        doctors.extend(batch_doctors)
                    
                    # Add a small delay between batches
                    await asyncio.sleep(0.5)
                except Exception as batch_error:
                    logger.warning(f"Batch processing error in {city} ({source}): {str(batch_error)}")
                    # Continue with next batch rather than failing the whole source
                    await asyncio.sleep(1)  # Longer delay after an error
        except Exception as source_error:
            logger.warning(f"Source error in {city} ({source}): {str(source_error)}")
        
        return doctors

    async def search_tier(self, tier: str, specialization: str) -> List[Doctor]:
        """
        Search for doctors in all cities of a specific tier.
        
        Args:
            tier: The tier to search ('tier1', 'tier2', or 'tier3')
            specialization: The medical specialization to search for
        
        Returns:
            List of unique doctors found across all cities in the specified tier
        """
        if tier not in self.india_cities:
            logger.error(f"Invalid tier: {tier}")
            return []
        
        all_doctors = []
        
        # Create progress context
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            main_task = progress.add_task(f"[cyan]Searching {tier} cities for {specialization} doctors...", total=100)
            
            # Get list of cities in this tier
            tier_cities = self.india_cities[tier]
            tier_count = len(tier_cities)
            tier_task = progress.add_task(f"[blue]Searching {tier} cities...", total=tier_count, parent=main_task)
            
            tier_results = []
            
            for city in tier_cities:
                city_task = progress.add_task(f"Searching {city.title()}", parent=tier_task)
                try:
                    # Use search_all_sources directly for consistent results with single city search
                    doctors = await self.search_all_sources(city, specialization)
                    
                    if doctors:
                        tier_results.extend(doctors)
                        progress.update(city_task, completed=1, description=f"[green]Found {len(doctors)} doctors in {city.title()}")
                    else:
                        progress.update(city_task, completed=1, description=f"[yellow]No doctors found in {city.title()}")
                    
                    # Add a delay between city searches to avoid rate limiting
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error searching {city}: {str(e)}")
                    progress.update(city_task, completed=1, description=f"[red]Error searching {city.title()}")
                
                progress.update(tier_task, advance=1)
            
            all_doctors.extend(tier_results)
            progress.update(main_task, advance=100)  # 100% progress
            
            # Deduplicate across all cities
            if all_doctors:
                pre_dedup_count = len(all_doctors)
                all_doctors = DataProcessor.deduplicate_doctors(all_doctors, self.config.FUZZY_MATCH_THRESHOLD)
                post_dedup_count = len(all_doctors)
                
                # Save to database
                self.db_manager.save_doctors(all_doctors)
                
                tier_summary = f"{tier}: {len(tier_results)}"
                dedup_info = f"(removed {pre_dedup_count - post_dedup_count} duplicates)"
                console.print(f"[bold green]Found {len(all_doctors)} unique doctors across {tier} cities after deduplication {dedup_info}[/bold green]")
                console.print(f"[bold blue]Tier summary: {tier_summary}[/bold blue]")
            else:
                console.print(f"[yellow]No doctors found matching your search criteria in {tier} cities[/yellow]")
            
            return all_doctors

    async def search_custom_cities(self, cities: List[str], specialization: str) -> List[Doctor]:
        """
        Search for doctors in a custom list of cities.
        
        Args:
            cities: List of city names to search in
            specialization: The medical specialization to search for
        
        Returns:
            List of unique doctors found across all specified cities
        """
        if not cities:
            logger.error("No cities provided for custom search")
            return []
        
        all_doctors = []
        
        # Create progress context
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            main_task = progress.add_task(f"[cyan]Searching {len(cities)} custom cities for {specialization} doctors...", total=100)
            cities_task = progress.add_task(f"[blue]Searching custom cities...", total=len(cities), parent=main_task)
            
            custom_results = []
            
            for city in cities:
                city_task = progress.add_task(f"Searching {city.title()}", parent=cities_task)
                try:
                    # Use search_all_sources directly for consistent results with single city search
                    doctors = await self.search_all_sources(city, specialization)
                    
                    if doctors:
                        custom_results.extend(doctors)
                        progress.update(city_task, completed=1, description=f"[green]Found {len(doctors)} doctors in {city.title()}")
                    else:
                        progress.update(city_task, completed=1, description=f"[yellow]No doctors found in {city.title()}")
                    
                    # Add a delay between city searches to avoid rate limiting
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error searching {city}: {str(e)}")
                    progress.update(city_task, completed=1, description=f"[red]Error searching {city.title()}")
                
                progress.update(cities_task, advance=1)
                progress.update(main_task, advance=100 // len(cities))
            
            all_doctors.extend(custom_results)
            progress.update(main_task, completed=100)  # Ensure 100% progress
            
            # Deduplicate across all cities
            if all_doctors:
                pre_dedup_count = len(all_doctors)
                all_doctors = DataProcessor.deduplicate_doctors(all_doctors, self.config.FUZZY_MATCH_THRESHOLD)
                post_dedup_count = len(all_doctors)
                
                # Save to database
                self.db_manager.save_doctors(all_doctors)
                
                dedup_info = f"(removed {pre_dedup_count - post_dedup_count} duplicates)"
                console.print(f"[bold green]Found {len(all_doctors)} unique doctors across custom cities after deduplication {dedup_info}[/bold green]")
                console.print(f"[bold blue]Searched in: {', '.join(cities)}[/bold blue]")
            else:
                console.print(f"[yellow]No doctors found matching your search criteria in the specified cities[/yellow]")
            
            return all_doctors

    async def run(self, location: str, specialization: str):
        """Main execution flow"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[green]Searching for doctors...", total=1)
            
            try:
                # Search for doctors
                doctors = await self.search_countrywide(location, specialization)
                
                # Display results
                self.display_results(doctors)
                
                # Save to database
                self.db_manager.save_doctors(doctors)
                
                progress.update(task, completed=True)
                return doctors
                
            except Exception as e:
                logger.error(f"Error in app execution: {str(e)}")
                progress.update(task, description=f"[red]Error: {str(e)}")
                return []

def main():
    """Main entry point for the CLI application"""
    parser = argparse.ArgumentParser(description="Doctor Search CLI")
    parser.add_argument("--city", required=True, help="City name")
    parser.add_argument("--specialization", required=True, help="Doctor specialization")
    
    args = parser.parse_args()
    
    config = Config()
    if not config.validate():
        console.print("[red]Error: API key not configured. Please set GEMINI_API_KEY environment variable.[/red]")
        return
    
    app = DoctorSearchApp(config)
    asyncio.run(app.run(args.city, args.specialization))

if __name__ == "__main__":
    main() 