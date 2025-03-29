import os
import json
import time
import logging
import argparse
import asyncio
import pandas as pd
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator
from fuzzywuzzy import fuzz
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential
import sqlite3
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
import random
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import base64
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
    DELAY_BETWEEN_CALLS: float = 0.1
    MIN_RATING: float = 0.0
    MAX_RATING: float = 5.0
    FUZZY_MATCH_THRESHOLD: int = 85
    DB_PATH: str = "doctors.db"
    MAX_CONCURRENT_REQUESTS: int = 50
    BATCH_SIZE: int = 10

    def validate(self) -> bool:
        if not self.API_KEY:
            logger.error("GEMINI_API_KEY environment variable not set")
            return False
        return True

# --- Data Models ---
class Doctor(BaseModel):
    name: str
    reviews: int = Field(default=0, ge=0)
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    locations: List[str] = Field(default_factory=list)
    source: str
    specialization: str
    city: str
    timestamp: datetime = Field(default_factory=datetime.now)

    @validator('rating')
    def validate_rating(cls, v):
        if v < 0 or v > 5:
            raise ValueError('Rating must be between 0 and 5')
        return v

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
                    reviews INTEGER DEFAULT 0,
                    rating REAL DEFAULT 0.0,
                    locations TEXT,
                    source TEXT,
                    specialization TEXT,
                    city TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def save_doctors(self, doctors: List[Doctor]):
        with sqlite3.connect(self.db_path) as conn:
            for doctor in doctors:
                conn.execute("""
                    INSERT INTO doctors (name, reviews, rating, locations, source, specialization, city)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    doctor.name, doctor.reviews, doctor.rating,
                    json.dumps(doctor.locations), doctor.source, doctor.specialization, doctor.city
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
                doctors.append(Doctor(**data))
            return doctors

# --- Prompt Management ---
class PromptManager:
    @staticmethod
    def get_practo_prompt(location: str, specialization: str) -> List[str]:
        """Generate multiple prompts for Practo search"""
        return [
            f"""Use Google Search to find information about {specialization} doctors on Practo in {location}.
Search for: "site:practo.com {specialization} doctors in {location}"
For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Number of reviews (if mentioned)
- Rating or Score (e.g., 4.5 stars, 9/10 - provide the numerical value if possible)
- Location (specific clinic name, hospital, and area in {location})

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- reviews
- rating
- location

Include only doctors who are actively practicing in {location} and have at least a rating or reviews.
Focus on verified profiles and official Practo listings.""",
            
            f"""Search for top-rated {specialization} doctors on Practo in {location}.
Use these specific search queries:
1. "site:practo.com best {specialization} in {location} reviews"
2. "site:practo.com {specialization} doctors {location} verified"
3. "site:practo.com {specialization} {location} experience"

For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Number of reviews (if mentioned)
- Rating or Score (e.g., 4.5 stars, 9/10 - provide the numerical value if possible)
- Location (specific clinic name, hospital, and area in {location})

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- reviews
- rating
- location

Include only doctors who are actively practicing in {location} and have at least a rating or reviews.
Focus on verified profiles and official Practo listings.""",
            
            f"""Find experienced {specialization} doctors on Practo in {location}.
Use these specific search queries:
1. "site:practo.com {specialization} doctors {location} experience"
2. "site:practo.com {specialization} {location} patient reviews"
3. "site:practo.com {specialization} doctors {location} verified"

For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Number of reviews (if mentioned)
- Rating or Score (e.g., 4.5 stars, 9/10 - provide the numerical value if possible)
- Location (specific clinic name, hospital, and area in {location})

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- reviews
- rating
- location

Include only doctors who are actively practicing in {location} and have at least a rating or reviews.
Focus on verified profiles and official Practo listings."""
        ]

    @staticmethod
    def get_justdial_prompt(location: str, specialization: str) -> List[str]:
        """Generate multiple prompts for JustDial search"""
        return [
            f"""Use Google Search to find information about {specialization} doctors on JustDial in {location}.
Search for: "site:justdial.com {specialization} doctors in {location}"
For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Number of reviews (if mentioned)
- Rating or Score (e.g., 4.5 stars, 9/10 - provide the numerical value if possible)
- Location (specific clinic name, hospital, and area in {location})

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- reviews
- rating
- location

Include only doctors who are actively practicing in {location} and have at least a rating or reviews.
Focus on verified listings and official JustDial profiles.""",
            
            f"""Search for top-rated {specialization} doctors on JustDial in {location}.
Use these specific search queries:
1. "site:justdial.com best {specialization} in {location} reviews"
2. "site:justdial.com {specialization} doctors {location} verified"
3. "site:justdial.com {specialization} {location} experience"

For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Number of reviews (if mentioned)
- Rating or Score (e.g., 4.5 stars, 9/10 - provide the numerical value if possible)
- Location (specific clinic name, hospital, and area in {location})

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- reviews
- rating
- location

Include only doctors who are actively practicing in {location} and have at least a rating or reviews.
Focus on verified listings and official JustDial profiles."""
        ]

    @staticmethod
    def get_general_prompt(location: str, specialization: str) -> List[str]:
        """Generate multiple prompts for general search"""
        return [
            f"""Use Google Search to find information about {specialization} doctors in {location}.
Use these search queries:
1. "site:healthcare.gov {specialization} doctors in {location}"
2. "site:medicalcouncil.gov.in {specialization} {location}"
3. "best {specialization} in {location} reviews"

For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Number of reviews (if mentioned)
- Rating or Score (e.g., 4.5 stars, 9/10 - provide the numerical value if possible)
- Location (specific clinic name, hospital, and area in {location})

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- reviews
- rating
- location

Include only doctors who are actively practicing in {location} and have at least a rating or reviews.
Focus on verified and reliable sources like hospital websites, medical directories, and official medical council listings.""",
            
            f"""Search for experienced {specialization} doctors in {location}.
Use these specific search queries:
1. "site:indiamart.com {specialization} doctors {location}"
2. "site:indianyellowpages.com {specialization} {location}"
3. "site:healthcaremagic.com {specialization} doctors {location}"

For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Number of reviews (if mentioned)
- Rating or Score (e.g., 4.5 stars, 9/10 - provide the numerical value if possible)
- Location (specific clinic name, hospital, and area in {location})

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- reviews
- rating
- location

Include only doctors who are actively practicing in {location} and have at least a rating or reviews.
Focus on verified and reliable sources.""",
            
            f"""Find top-rated {specialization} doctors in {location}.
Use these specific search queries:
1. "site:lybrate.com {specialization} doctors {location}"
2. "site:credihealth.com {specialization} {location}"
3. "site:healthifyme.com {specialization} doctors {location}"

For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Number of reviews (if mentioned)
- Rating or Score (e.g., 4.5 stars, 9/10 - provide the numerical value if possible)
- Location (specific clinic name, hospital, and area in {location})

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- reviews
- rating
- location

Include only doctors who are actively practicing in {location} and have at least a rating or reviews.
Focus on verified and reliable sources."""
        ]

    @staticmethod
    def get_hospital_prompt(location: str, specialization: str) -> List[str]:
        """Generate multiple prompts for hospital websites"""
        return [
            f"""Search for {specialization} doctors in major hospitals in {location}.
Use these specific search queries:
1. "site:apollohospitals.com {specialization} doctors {location}"
2. "site:fortishealthcare.com {specialization} {location}"
3. "site:maxhealthcare.in {specialization} doctors {location}"
4. "site:manipalhospitals.com {specialization} {location}"

For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Number of reviews (if mentioned)
- Rating or Score (e.g., 4.5 stars, 9/10 - provide the numerical value if possible)
- Location (specific clinic name, hospital, and area in {location})

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- reviews
- rating
- location

Include only doctors who are actively practicing in {location} and have at least a rating or reviews.
Focus on verified and reliable sources."""
        ]

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
    def normalize_rating(rating_str: str) -> float:
        """Normalize rating to 0-5 scale"""
        try:
            if not rating_str or rating_str.strip() == '':
                return 0.0
                
            # Remove any non-numeric characters except decimal point and percentage
            rating_str = ''.join(c for c in rating_str if c.isdigit() or c in '.%')
            
            if not rating_str:
                return 0.0
            
            # Convert to float
            rating = float(rating_str.replace('%', ''))
            
            # Handle percentage ratings
            if '%' in rating_str:
                rating = rating / 20  # Convert percentage to 0-5 scale
            elif rating > 5:
                rating = 5.0  # Cap at 5.0
            
            return round(rating, 1)  # Round to 1 decimal place
        except Exception as e:
            logger.warning(f"Error normalizing rating '{rating_str}': {e}")
            return 0.0

    @staticmethod
    def standardize_doctor_data(data: List[Dict], source: str, specialization: str, city: str) -> List[Doctor]:
        """Standardize and validate doctor data"""
        standardized_data = []
        for item in data:
            try:
                # Clean and standardize the data
                name = (item.get("name") or item.get("Full Name") or item.get("Name", "")).strip()
                if not name:  # Skip if no name
                    continue
                
                # Handle reviews with better error handling
                reviews_str = str(item.get("reviews") or item.get("Number of reviews") or item.get("Number of Reviews", "0"))
                reviews_str = ''.join(filter(str.isdigit, reviews_str))
                reviews = int(reviews_str) if reviews_str else 0
                
                # Handle rating with better error handling
                rating_str = str(item.get("rating") or item.get("Rating or Score") or item.get("Rating", "0"))
                rating = DataProcessor.normalize_rating(rating_str)
                
                # Clean location
                location = (item.get("location") or item.get("Location", "")).strip()
                if not location:  # Skip if no location
                    continue
                
                doctor = Doctor(
                    name=name,
                    reviews=reviews,
                    rating=rating,
                    locations=[location],
                    source=source,
                    specialization=specialization,
                    city=city
                )
                
                if doctor.name and (doctor.rating > 0 or doctor.reviews > 0):
                    standardized_data.append(doctor)
            except Exception as e:
                logger.warning(f"Error standardizing doctor data: {e}")
                continue
                
        return standardized_data

    @staticmethod
    def deduplicate_doctors(doctors: List[Doctor], threshold: int) -> List[Doctor]:
        """Deduplicate doctors using fuzzy matching on names and merge locations"""
        unique_doctors = {}
        seen_names = set()

        for doctor in doctors:
            # Clean and standardize the name
            name = doctor.name.lower().strip()
            
            # Check if this name is similar to any existing one
            is_duplicate = False
            for seen_name in seen_names:
                if fuzz.ratio(name, seen_name) >= threshold:
                    # Found a duplicate, merge the locations
                    existing_doctor = unique_doctors[seen_name]
                    existing_doctor.locations.extend(doctor.locations)
                    existing_doctor.locations = list(set(existing_doctor.locations))  # Remove duplicates
                    # Update rating and reviews if the new entry has better stats
                    if doctor.rating > existing_doctor.rating or (doctor.rating == existing_doctor.rating and doctor.reviews > existing_doctor.reviews):
                        existing_doctor.rating = doctor.rating
                        existing_doctor.reviews = doctor.reviews
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_doctors[name] = doctor
                seen_names.add(name)

        return list(unique_doctors.values())

# --- API Client ---
class GeminiClient:
    def __init__(self, api_key: str, model_name: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    async def generate_content(self, prompt: str) -> str:
        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ]
            
            tools = [
                types.Tool(google_search=types.GoogleSearch())
            ]
            
            generate_content_config = types.GenerateContentConfig(
                tools=tools,
                response_mime_type="text/plain",
            )

            response = []
            async for chunk in self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.text:
                    response.append(chunk.text)

            return "".join(response)
        except Exception as e:
            logger.error(f"Error generating content with Gemini: {str(e)}")
            raise

# --- Main Application ---
class DoctorSearchApp:
    def __init__(self, config: Config):
        self.config = config
        self.gemini_client = GeminiClient(config.API_KEY, config.MODEL_NAME)
        self.prompt_manager = PromptManager()
        self.data_processor = DataProcessor()
        self.db = DatabaseManager(config.DB_PATH)
        self.logger = logging.getLogger(__name__)
        self.cache = {}

    async def search_all_sources(self, location: str, specialization: str) -> List[Doctor]:
        """Search for doctors across all sources in parallel"""
        cache_key = f"{location}_{specialization}"
        if cache_key in self.cache:
            self.logger.info(f"Using cached results for {cache_key}")
            return self.cache[cache_key]

        sources = ["Practo", "JustDial", "General", "Hospital"]
        
        # Process all sources in parallel
        results = await asyncio.gather(*[
            self.search_source(source, location, specialization)
            for source in sources
        ])
        
        # Flatten results
        all_doctors = []
        for source_results in results:
            all_doctors.extend(source_results)
        
        # Deduplicate doctors
        unique_doctors = self.data_processor.deduplicate_doctors(all_doctors, self.config.FUZZY_MATCH_THRESHOLD)
        
        self.cache[cache_key] = unique_doctors
        return unique_doctors

    async def search_source(self, source: str, location: str, specialization: str) -> List[Doctor]:
        """Search a specific source for doctors with parallel processing"""
        try:
            prompts = getattr(self.prompt_manager, f"get_{source.lower()}_prompt")(location, specialization)
            
            # Process all prompts in parallel
            results = await self.gemini_client.generate_content_batch(prompts)
            
            # Process results
            all_doctors = []
            for result in results:
                try:
                    doctors = self.data_processor.extract_json_from_response(result)
                    if doctors:
                        all_doctors.extend(
                            self.data_processor.standardize_doctor_data(
                                doctors, source, specialization, location
                            )
                        )
                except Exception as e:
                    self.logger.error(f"Error processing {source} results: {str(e)}")
                    continue
            
            return all_doctors
            
        except Exception as e:
            self.logger.error(f"Error searching {source}: {str(e)}")
            return []

    def display_results(self, doctors: List[Doctor]):
        """Display results in a rich table"""
        table = Table(title=f"Found {len(doctors)} Doctors")
        table.add_column("Name", style="cyan")
        table.add_column("Rating", style="green")
        table.add_column("Reviews", style="yellow")
        table.add_column("Locations", style="magenta")
        table.add_column("Source", style="blue")

        for doctor in sorted(doctors, key=lambda x: (x.rating, x.reviews), reverse=True):
            table.add_row(
                doctor.name,
                f"{doctor.rating:.1f}",
                str(doctor.reviews),
                ", ".join(doctor.locations),
                doctor.source
            )

        console.print(table)

    async def run(self, location: str, specialization: str):
        """Main execution flow"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Searching for doctors...", total=None)
            
            try:
                doctors = await self.search_all_sources(location, specialization)
                self.db.save_doctors(doctors)
                
                progress.update(task, completed=True)
                self.display_results(doctors)
                
                # Save to CSV
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"doctors_data_{location.lower().replace(' ', '_')}_{timestamp}.csv"
                pd.DataFrame([d.dict() for d in doctors]).to_csv(output_file, index=False)
                console.print(f"\nData saved to: {output_file}")
                
            except Exception as e:
                logger.error(f"Error during execution: {e}")
                console.print(f"[red]Error: {e}[/red]")

def main():
    parser = argparse.ArgumentParser(description="Search for doctor information")
    parser.add_argument("--city", required=True, help="City to search in")
    parser.add_argument("--specialization", required=True, help="Doctor specialization")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    
    args = parser.parse_args()
    
    config = Config()
    if not config.validate():
        console.print("[red]Configuration validation failed. Please check your environment variables.[/red]")
        return
    
    app = DoctorSearchApp(config)
    
    if args.test:
        # Run with test data
        test_doctors = [
            Doctor(
                name="Dr. Test Doctor",
                reviews=100,
                rating=4.5,
                locations=["Test Hospital"],
                source="Test",
                specialization=args.specialization,
                city=args.city
            )
        ]
        app.display_results(test_doctors)
    else:
        asyncio.run(app.run(args.city, args.specialization))

if __name__ == "__main__":
    main() 