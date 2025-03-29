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
    phone_numbers: List[str] = Field(default_factory=list)
    source_urls: List[str] = Field(default_factory=list)
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
        
        # Merge phone numbers
        self.phone_numbers.extend([phone for phone in other.phone_numbers if phone not in self.phone_numbers])
        
        # Merge source URLs
        self.source_urls.extend([url for url in other.source_urls if url not in self.source_urls])
        
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
                    phone_numbers TEXT,
                    source_urls TEXT,
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
                        name, rating, reviews, locations, phone_numbers, source_urls,
                        specialization, city, contributing_sources, timestamp
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doctor.name, doctor.rating, doctor.reviews,
                    json.dumps(doctor.locations), json.dumps(doctor.phone_numbers),
                    json.dumps(doctor.source_urls), doctor.specialization,
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
                data['phone_numbers'] = json.loads(data['phone_numbers'])
                data['source_urls'] = json.loads(data['source_urls'])
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
            "\"location\": [\"Address 1\", \"Address 2\"], "
            "\"phone_number\": [\"+1234567890\"], "
            "\"url\": [\"https://example.com/profile\"]}]. "
            "Output only the JSON list with no explanatory text."
        )
        return f"{prompt}. {json_instruction}"

    @staticmethod
    def get_practo_prompt(location: str, specialization: str) -> List[str]:
        """Generate prompts for Practo search"""
        prompts = []
        
        # Core pattern variations
        base_patterns = [
            f"site:practo.com {specialization} doctor in {location} rating reviews phone number address",
            f"site:practo.com {specialization} clinic {location} contact number ratings address",
            f"site:practo.com dr name {specialization} {location} profile link phone ratings reviews",
            f"site:practo.com best {specialization} doctors {location} contact info ratings",
            f"site:practo.com top rated {specialization} {location} phone number address reviews",
            f"site:practo.com {specialization} specialist {location} profile URL rating",
            f"site:practo.com experienced {specialization} {location} contact details rating",
            f"site:practo.com {specialization} physician {location} phone ratings reviews profile",
            f"site:practo.com {specialization} consultation {location} doctor contact rating",
            f"site:practo.com {specialization} medical {location} doctor profile phone number",
        ]
        
        # Generate more detailed queries
        for pattern in base_patterns:
            prompts.append(PromptManager._add_json_instruction(pattern))
            
            # Add variations with common doctor prefixes
            for prefix in ["Dr.", "Doctor", "Prof. Dr.", "Dr", "MD"]:
                prompts.append(PromptManager._add_json_instruction(f"{pattern} {prefix}"))
            
            # Add variations with specific location types
            for loc_type in ["hospital", "clinic", "medical center", "healthcare", "practice"]:
                prompts.append(PromptManager._add_json_instruction(f"{pattern} {loc_type}"))
        
        # Add specific rating-focused queries
        rating_patterns = [
            f"site:practo.com highly rated {specialization} doctor {location} contact",
            f"site:practo.com 5 star {specialization} {location} doctor phone number",
            f"site:practo.com best reviewed {specialization} doctor {location} contact information",
            f"site:practo.com top {specialization} doctor {location} rating phone address"
        ]
        for pattern in rating_patterns:
            prompts.append(PromptManager._add_json_instruction(pattern))
        
        # Add specific contact-focused queries
        contact_patterns = [
            f"site:practo.com {specialization} doctor {location} multiple locations contact numbers",
            f"site:practo.com {specialization} {location} clinic address phone consultation",
            f"site:practo.com {specialization} doctor {location} office phone numbers profile"
        ]
        for pattern in contact_patterns:
            prompts.append(PromptManager._add_json_instruction(pattern))
        
        return prompts

    @staticmethod
    def get_justdial_prompt(location: str, specialization: str) -> List[str]:
        """Generate prompts for JustDial search"""
        prompts = []
        
        # Core pattern variations
        base_patterns = [
            f"site:justdial.com {specialization} doctors in {location} rating reviews phone contact",
            f"site:justdial.com best {specialization} clinics {location} contact details ratings",
            f"site:justdial.com {specialization} specialist {location} phone number address ratings",
            f"site:justdial.com top {specialization} doctors {location} rating reviews location",
            f"site:justdial.com {specialization} physician {location} phone number office location",
            f"site:justdial.com {specialization} doctor near {location} contact information ratings",
            f"site:justdial.com {specialization} medical service {location} doctor profile phone",
            f"site:justdial.com find {specialization} doctor {location} direct number reviews",
            f"site:justdial.com {specialization} healthcare provider {location} rating contact",
            f"site:justdial.com {specialization} clinic {location} doctor listing reviews phone"
        ]
        
        # Generate more detailed queries
        for pattern in base_patterns:
            prompts.append(PromptManager._add_json_instruction(pattern))
            
        return prompts

    @staticmethod
    def get_general_prompt(location: str, specialization: str) -> List[str]:
        """Generate prompts for general search (Google, Bing, etc.)"""
        prompts = []
        
        # Core queries for general search
        base_patterns = [
            f"{specialization} doctor in {location} rating reviews phone address",
            f"best {specialization} in {location} contact information ratings",
            f"top rated {specialization} doctor {location} phone number reviews",
            f"{specialization} specialist {location} contact details rating",
            f"find {specialization} clinic {location} doctor phone ratings",
            f"{specialization} medical center {location} doctor contact information",
            f"recommended {specialization} doctor {location} phone address reviews",
            f"experienced {specialization} in {location} contact rating",
            f"{specialization} doctor near {location} phone ratings reviews",
            f"{specialization} healthcare provider {location} contact details rating"
        ]
        
        # Generate more detailed queries
        for pattern in base_patterns:
            prompts.append(PromptManager._add_json_instruction(pattern))
            
            # Add variations with common doctor prefixes
            for prefix in ["Dr.", "Doctor", "Prof. Dr.", "MD"]:
                prompts.append(PromptManager._add_json_instruction(f"{prefix} {pattern}"))
            
            # Add variations with location and rating specifics
            for loc_type in ["clinic", "hospital", "practice", "center", "chamber"]:
                prompts.append(PromptManager._add_json_instruction(f"{pattern} {loc_type}"))
        
        # Add search engine variations
        for site in ["", "site:healthgrades.com", "site:zocdoc.com", "site:google.com/maps"]:
            for pattern in base_patterns[:3]:  # Use only the first few base patterns
                if site:
                    prompts.append(PromptManager._add_json_instruction(f"{site} {pattern}"))
        
        # Add specific rating-focused queries
        rating_patterns = [
            f"highest rated {specialization} in {location} contact information",
            f"5 star {specialization} doctor {location} phone address",
            f"best reviewed {specialization} clinic {location} contact",
            f"{specialization} doctor with most reviews in {location} phone"
        ]
        for pattern in rating_patterns:
            prompts.append(PromptManager._add_json_instruction(pattern))
        
        # Add specific contact-focused queries
        contact_patterns = [
            f"{specialization} doctor {location} multiple office locations phone",
            f"{specialization} {location} clinic address contact numbers",
            f"contact details for {specialization} doctors in {location} ratings"
        ]
        for pattern in contact_patterns:
            prompts.append(PromptManager._add_json_instruction(pattern))
        
        return prompts

    @staticmethod
    def get_hospital_prompt(location: str, specialization: str) -> List[str]:
        """Generate prompts for hospital websites"""
        prompts = []
        
        # List of major hospital chains
        hospitals = [
            "apollo", "fortis", "manipal", "max", "medanta", "aiims", 
            "kokilaben", "narayana", "jaslok", "lilavati", "columbia asia",
            "care", "bm birla", "sterling", "ruby hall", "hinduja", "artemis",
            "kauvery", "cmc vellore", "wockhardt", "rainbow", "kims"
        ]
        
        # Generate hospital-specific queries
        for hospital in hospitals:
            base_patterns = [
                f"site:{hospital}hospitals.com {specialization} doctor {location} contact rating",
                f"site:{hospital}.com {specialization} specialist {location} phone reviews",
                f"site:{hospital}hospital.com {specialization} doctor profile {location} contact",
                f"site:{hospital}health.com {specialization} physician {location} rating phone"
            ]
            for pattern in base_patterns:
                prompts.append(PromptManager._add_json_instruction(pattern))
        
        # Generate general hospital-related queries
        general_patterns = [
            f"site:hospitals.com {specialization} doctor {location} contact information ratings",
            f"hospital {specialization} department {location} doctor contact ratings",
            f"medical center {specialization} doctor {location} phone directory ratings",
            f"healthcare facility {specialization} expert {location} contact details",
            f"multispecialty hospital {specialization} {location} doctor phone address",
            f"hospital directory {specialization} doctors {location} contact ratings"
        ]
        for pattern in general_patterns:
            prompts.append(PromptManager._add_json_instruction(pattern))
        
        return prompts

    @staticmethod
    def get_social_proof_prompt(location: str, specialization: str) -> List[str]:
        """Generate prompts for social proof and review sites"""
        prompts = []
        
        # Core pattern variations for social proof
        base_patterns = [
            f"site:google.com/maps {specialization} doctor {location} reviews rating phone address",
            f"site:yelp.com {specialization} doctor {location} review rating contact",
            f"site:facebook.com {specialization} doctor {location} rating reviews contact",
            f"site:quora.com recommended {specialization} in {location} contact rating",
            f"site:reddit.com r/askdocs best {specialization} {location} contact reviews",
            f"site:healthgrades.com {specialization} {location} phone rating reviews",
            f"site:ratemds.com {specialization} doctor {location} phone contact ratings"
        ]
        
        for pattern in base_patterns:
            prompts.append(PromptManager._add_json_instruction(pattern))
        
        # Additional socially-derived patterns
        social_patterns = [
            f"most reviewed {specialization} doctor {location} phone contact address",
            f"patient recommended {specialization} doctor {location} contact rating",
            f"trusted {specialization} doctor {location} ratings contact information",
            f"well-rated {specialization} clinic {location} phone address reviews"
        ]
        for pattern in social_patterns:
            prompts.append(PromptManager._add_json_instruction(pattern))
        
        # Add specific review-focused queries
        review_patterns = [
            f"site:google.com/maps {specialization} {location} 5 star doctor phone contact",
            f"site:yelp.com highest rated {specialization} {location} contact information",
            f"best reviewed {specialization} doctor {location} practice phone location"
        ]
        for pattern in review_patterns:
            prompts.append(PromptManager._add_json_instruction(pattern))
        
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
    def standardize_doctor_data(data: List[Dict], source: str, specialization: str, city: str) -> List[Doctor]:
        """
        Standardize and clean doctor data from various sources
        Focus only on core fields: name, rating, reviews, locations, phone_numbers, source_urls
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
                
                # Clean locations more thoroughly
                cleaned_locations = []
                generic_terms = ['near', 'opposite', 'behind', 'next to', 'in front of', 'across from', 'located at']
                for loc in locations:
                    if loc and isinstance(loc, str):
                        # Remove very short locations and apply basic cleaning
                        loc = loc.strip()
                        # Remove generic location descriptors that don't add value
                        for term in generic_terms:
                            if loc.lower().startswith(term):
                                loc = loc[len(term):].strip()
                        
                        # Keep only reasonable length locations (not too short, not too long)
                        if 3 < len(loc) < 150 and loc not in cleaned_locations:
                            cleaned_locations.append(loc)
                
                # Process phone numbers - ensure it's a list
                phone_numbers = []
                for field in ['phone', 'phone_number', 'contact', 'mobile', 'telephone', 'phone_numbers']:
                    if field in item and item[field]:
                        if isinstance(item[field], list):
                            phone_numbers.extend(item[field])
                        elif isinstance(item[field], str):
                            # Split by common separators
                            for number in item[field].split(','):
                                phone_numbers.append(number.strip())
                
                # Clean phone numbers more thoroughly
                cleaned_phones = []
                for phone in phone_numbers:
                    if phone and isinstance(phone, str):
                        # Normalize format - remove all non-digit characters except + for country code
                        digits_only = ''.join(c for c in phone if c.isdigit() or c == '+')
                        
                        # Handle country codes - if no + prefix and length > 10, assume it needs one
                        if not digits_only.startswith('+') and len(digits_only) > 10:
                            # For Indian numbers (assume most common case)
                            if digits_only.startswith('91') and len(digits_only) >= 12:
                                digits_only = '+' + digits_only
                            elif len(digits_only) == 10:  # Likely a local number without country code
                                digits_only = '+91' + digits_only  # Add India country code by default
                        
                        # Filter invalid numbers (too short)
                        if len(digits_only) >= 7 and digits_only not in cleaned_phones:
                            cleaned_phones.append(digits_only)
                
                # Process source URLs - ensure it's a list
                source_urls = []
                for field in ['url', 'source_url', 'profile_url', 'link', 'website', 'source_urls']:
                    if field in item and item[field]:
                        if isinstance(item[field], list):
                            source_urls.extend(item[field])
                        elif isinstance(item[field], str):
                            source_urls.append(item[field])
                
                # Clean source URLs with strict validation
                cleaned_urls = []
                url_prefixes = ['http://', 'https://']
                for url in source_urls:
                    if url and isinstance(url, str):
                        url = url.strip()
                        
                        # Add proper prefix if missing
                        has_valid_prefix = any(url.startswith(prefix) for prefix in url_prefixes)
                        if not has_valid_prefix:
                            if url.startswith('www.'):
                                url = 'https://' + url
                            else:
                                url = 'https://' + url
                        
                        # Basic URL validation using string pattern checks
                        has_domain = '.' in url.split('//')[-1]
                        has_no_spaces = ' ' not in url
                        reasonable_length = 10 <= len(url) <= 500
                        
                        if has_domain and has_no_spaces and reasonable_length and url not in cleaned_urls:
                            cleaned_urls.append(url)
                
                # Create doctor object with only the core fields
                doctor = Doctor(
                    name=name,
                    rating=rating_value,
                    reviews=reviews_count,
                    locations=cleaned_locations,
                    phone_numbers=cleaned_phones,
                    source_urls=cleaned_urls,
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
        Deduplicate doctors based on name similarity and merge their data
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
                    # Found a duplicate, merge data
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
        Generate content using Google's Gemini API (Corrected with native async)
        """
        logger.debug(f"Generating content with prompt: {prompt[:100]}...")
        try:
            async with self.semaphore:
                # Get the model instance
                model = genai.GenerativeModel(model_name=self.model_name)
                
                # Call the native async method ON THE MODEL
                response = await model.generate_content_async(
                    contents=prompt,
                    generation_config=types.GenerationConfig(
                        temperature=0.2,
                        top_p=0.95,
                        top_k=64,
                        max_output_tokens=8192,
                    ),
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
                
                # Check if the response has content
                if response and hasattr(response, 'text'):
                    return response.text
                elif response and hasattr(response, 'parts'):
                    return "".join(part.text for part in response.parts)
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
        table.add_column("Locations")
        table.add_column("Phone Numbers")
        table.add_column("Source URLs")
        
        # Add rows to the table
        for doctor in doctors:
            table.add_row(
                doctor.name,
                f"{doctor.rating:.1f} ⭐",
                str(doctor.reviews),
                "\n".join(doctor.locations[:2]) + ("..." if len(doctor.locations) > 2 else ""),
                "\n".join(doctor.phone_numbers[:2]) + ("..." if len(doctor.phone_numbers) > 2 else ""),
                "\n".join(doctor.source_urls[:2]) + ("..." if len(doctor.source_urls) > 2 else "")
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