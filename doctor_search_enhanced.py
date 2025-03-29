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
    MAX_CONCURRENT_REQUESTS: int = 200  # Significantly increased for better parallelization
    REQUEST_TIMEOUT: float = 30.0  # Timeout for each request in seconds

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
        # Add contributing sources 
        for source in other.contributing_sources:
            if source not in self.contributing_sources:
                self.contributing_sources.append(source)
        
        # Merge locations
        self.locations.extend([loc for loc in other.locations if loc not in self.locations])
        
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
    def is_location_in_city(location: str, city: str) -> bool:
        """
        Check if a location is likely in the specified city.
        Returns True if the location appears to be in the city, False otherwise.
        """
        if not location or not city:
            return False
            
        # Normalize strings for comparison
        location_lower = location.lower()
        city_lower = city.lower()
        
        # Check if city name is in the location
        if city_lower in location_lower:
            return True
            
        # List of major cities (case insensitive) to check against
        major_cities = ["delhi", "mumbai", "bangalore", "bengaluru", "chennai", "kolkata", 
                        "hyderabad", "pune", "ahmedabad", "jaipur", "lucknow", "kanpur", 
                        "nagpur", "indore", "thane", "bhopal", "visakhapatnam", "patna"]
        
        # If another major city is mentioned (and it's not the requested city)
        for other_city in major_cities:
            if other_city != city_lower and other_city in location_lower:
                # Check if it's mentioning travel/visit to other city
                travel_indicators = ["visit", "travels to", "also available in", "consultation in"]
                for indicator in travel_indicators:
                    if indicator in location_lower:
                        # This indicates the doctor might still be primarily in the requested city
                        return True
                # No travel indicators but another city mentioned
                return False
                
        # Check for generic/non-specific location terms
        generic_locations = [
            "multiple locations", "available online", "teleconsultation", 
            "consultation available", "multiple branches", "across india",
            "pan india", "all over india", "all major cities"
        ]
        
        for generic in generic_locations:
            if generic in location_lower:
                return False
                
        # If we've reached here and no other city is mentioned, assume it's in the requested city
        return True

    @staticmethod
    def standardize_doctor_data(data: List[Dict], source: str, specialization: str, city: str) -> List[Doctor]:
        """
        Standardize and clean doctor data from various sources
        Focus only on core fields: name, rating, reviews, locations
        Apply strict location validation
        """
        standardized_doctors = []
        
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
                            if DataProcessor.is_location_in_city(loc, city):
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
                    contributing_sources=[source]
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
        Only merge if they have similar locations
        """
        if not doctors:
            return []
        
        # Sort doctors by rating (highest first) to prioritize better profiles
        sorted_doctors = sorted(doctors, key=lambda x: (x.rating, x.reviews), reverse=True)
        
        # Use first doctor as seed for the result list
        result = [sorted_doctors[0]]
        
        # Compare each doctor to those already in the result
        for current in sorted_doctors[1:]:
            is_duplicate = False
            
            for idx, existing in enumerate(result):
                # Compare names for similarity
                name_similarity = fuzz.ratio(current.name.lower(), existing.name.lower())
                
                if name_similarity >= threshold:
                    # Check if locations are compatible before merging
                    location_compatible = False
                    
                    # If either has no locations, assume compatible
                    if not current.locations or not existing.locations:
                        location_compatible = True
                    else:
                        # Check if at least one location from each doctor seems similar
                        for curr_loc in current.locations:
                            for exist_loc in existing.locations:
                                loc_similarity = fuzz.partial_ratio(curr_loc.lower(), exist_loc.lower())
                                if loc_similarity >= 70:  # Threshold for location similarity
                                    location_compatible = True
                                    break
                            if location_compatible:
                                break
                    
                    if location_compatible:
                        # Found a duplicate with compatible locations, merge data
                        result[idx].merge_with(current)
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                # Not a duplicate, add to results
                result.append(current)
        
        return result

# --- API Client ---
class GeminiClient:
    def __init__(self, api_key: str, model_name: str):
        """Initialize the Gemini client with API key and model name"""
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)
        self.semaphore = asyncio.Semaphore(200)  # Significantly increased for better parallelization

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_content(self, prompt: str) -> str:
        """
        Generate content using Google's Gemini API
        """
        logger.debug(f"Generating content with prompt: {prompt[:100]}...")
        try:
            async with self.semaphore:
                # Format the content using the proper types
                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt),
                        ],
                    )
                ]
                
                # Create generation config
                generation_config = types.GenerateContentConfig(
                    temperature=0.2,
                    top_p=0.95,
                    top_k=64,
                    max_output_tokens=8192,
                    response_mime_type="text/plain",
                    safety_settings=[
                        {
                            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                            "threshold": "BLOCK_ONLY_HIGH"
                        },
                        {
                            "category": "HARM_CATEGORY_HATE_SPEECH",
                            "threshold": "BLOCK_ONLY_HIGH"
                        },
                        {
                            "category": "HARM_CATEGORY_HARASSMENT",
                            "threshold": "BLOCK_ONLY_HIGH"
                        },
                        {
                            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            "threshold": "BLOCK_ONLY_HIGH"
                        }
                    ]
                )
                
                # Use asyncio.to_thread to call the synchronous method in a separate thread
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.model_name,
                    contents=contents,
                    config=generation_config,
                )
                
                # Check if the response has content
                if response and hasattr(response, 'text'):
                    return response.text
                elif response and hasattr(response, 'parts') and response.parts:
                    return "".join(part.text for part in response.parts if hasattr(part, 'text'))
                else:
                    logger.warning(f"Empty or unexpected response structure from Gemini API for prompt: {prompt[:50]}...")
                    return ""
                
        except Exception as e:
            logger.error(f"Error generating content: {type(e).__name__}: {str(e)}")
            raise  # Let tenacity handle the retry

    async def generate_content_batch(self, prompts: List[str]) -> List[Optional[str]]:
        """Generate content for multiple prompts in parallel"""
        tasks = []
        
        for prompt in prompts:
            # Use the async method directly rather than a nested function
            tasks.append(self.generate_content(prompt))
        
        # Use asyncio.gather to run all tasks concurrently
        results = []
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results to handle exceptions
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error in batch processing: {type(result).__name__}: {str(result)}")
                    processed_results.append(None)
                else:
                    processed_results.append(result)
            
            return processed_results
        except Exception as e:
            logger.error(f"Error in batch processing: {type(e).__name__}: {str(e)}")
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

    async def search_all_sources(self, location: str, specialization: str) -> List[Doctor]:
        """
        Search all sources for doctors based on location and specialization
        """
        sources = ["practo", "justdial", "general", "hospital", "social"]
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
            async def search_with_progress(source: str) -> List[Doctor]:
                task = progress.add_task(f"Searching {source}...", total=1)
                
                try:
                    doctors = await self.search_source(source, location, specialization)
                    progress.update(task, completed=1, description=f"[green]Found {len(doctors)} doctors from {source}")
                    return doctors
                except Exception as e:
                    logger.error(f"Error searching {source}: {str(e)}")
                    progress.update(task, completed=1, description=f"[red]Error searching {source}")
                    return []
            
            # Execute all searches concurrently
            tasks = [search_with_progress(source) for source in sources]
            results = await asyncio.gather(*tasks)
            
            # Combine all results
            for doctors in results:
                all_doctors.extend(doctors)
            
            # Deduplicate across all sources
            if all_doctors:
                all_doctors = DataProcessor.deduplicate_doctors(all_doctors, self.config.FUZZY_MATCH_THRESHOLD)
                
                # Save to database
                self.db_manager.save_doctors(all_doctors)
            
            console.print(f"[bold green]Found {len(all_doctors)} unique doctors after deduplication[/bold green]")
            
            return all_doctors

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
        
        # Add rows to the table
        for doctor in doctors:
            primary_location = doctor.locations[0] if doctor.locations else "N/A"
            secondary_location = doctor.locations[1] if len(doctor.locations) > 1 else "N/A"
            
            table.add_row(
                doctor.name,
                f"{doctor.rating:.1f} ⭐",
                str(doctor.reviews),
                primary_location,
                secondary_location
            )
        
        console.print(table)

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
                doctors = await self.search_all_sources(location, specialization)
                
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