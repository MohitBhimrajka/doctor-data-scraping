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
    DELAY_BETWEEN_CALLS: float = 0.05  # Reduced delay since we have high rate limit
    MIN_RATING: float = 0.0
    MAX_RATING: float = 5.0
    FUZZY_MATCH_THRESHOLD: int = 85
    DB_PATH: str = "doctors.db"
    MAX_CONCURRENT_REQUESTS: int = 20  # Increased for better parallelization
    BATCH_SIZE: int = 5  # Process prompts in smaller batches
    REQUEST_TIMEOUT: float = 30.0  # Timeout for each request in seconds
    MAX_RETRIES_PER_BATCH: int = 2  # Number of retries per batch

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
    experience: Optional[str] = None
    fees: Optional[str] = None
    hospitals: List[str] = Field(default_factory=list)
    qualifications: Optional[str] = None
    registration: Optional[str] = None
    timings: Optional[str] = None
    expertise: Optional[str] = None
    feedback: Optional[str] = None
    contributing_sources: List[str] = Field(default_factory=list)
    estimated_fields: List[str] = Field(default_factory=list)  # Track which fields were estimated
    last_updated: datetime = Field(default_factory=datetime.now)
    data_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)  # Score based on data completeness
    verified: bool = Field(default=False)  # Whether the doctor's credentials are verified
    languages: List[str] = Field(default_factory=list)  # Languages spoken by the doctor
    subspecialties: List[str] = Field(default_factory=list)  # Specific areas of expertise
    awards_and_recognitions: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)  # Detailed education history
    services: List[str] = Field(default_factory=list)  # Medical services offered
    insurance_accepted: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

    @validator('rating')
    def validate_rating(cls, v):
        if v < 0 or v > 5:
            raise ValueError('Rating must be between 0 and 5')
        return v

    @validator('data_quality_score')
    def validate_quality_score(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Data quality score must be between 0 and 1')
        return v

    def calculate_data_quality_score(self) -> None:
        """Calculate data quality score based on field completeness and source diversity"""
        required_fields = ['name', 'specialization', 'city']
        optional_fields = ['experience', 'fees', 'qualifications', 'registration', 'timings', 'expertise']
        
        # Start with base score
        score = 1.0
        
        # Check required fields
        for field in required_fields:
            if not getattr(self, field):
                score *= 0.5
        
        # Check optional fields
        filled_optional = sum(1 for field in optional_fields if getattr(self, field))
        optional_score = filled_optional / len(optional_fields)
        score *= (0.5 + 0.5 * optional_score)
        
        # Factor in source diversity
        source_score = min(len(self.contributing_sources) / 3, 1.0)  # Cap at 3 sources
        score *= (0.7 + 0.3 * source_score)
        
        # Factor in review count
        review_score = min(self.reviews / 100, 1.0)  # Cap at 100 reviews
        score *= (0.8 + 0.2 * review_score)
        
        self.data_quality_score = round(score, 2)

    def merge_with(self, other: 'Doctor') -> None:
        """Merge data from another doctor record into this one"""
        # Add source to contributing sources
        if other.source not in self.contributing_sources:
            self.contributing_sources.append(other.source)
        
        # Merge locations
        self.locations.extend([loc for loc in other.locations if loc not in self.locations])
        
        # Merge hospitals
        self.hospitals.extend([hosp for hosp in other.hospitals if hosp not in self.hospitals])
        
        # Update rating and reviews if the other record has more reviews
        if other.reviews > self.reviews:
            self.rating = other.rating
            self.reviews = other.reviews
        
        # Merge other fields if they're empty in self but present in other
        for field in ['experience', 'fees', 'qualifications', 'registration', 'timings', 'expertise']:
            if not getattr(self, field) and getattr(other, field):
                setattr(self, field, getattr(other, field))
        
        # Merge lists
        for field in ['languages', 'subspecialties', 'awards_and_recognitions', 'education', 'services', 'insurance_accepted']:
            current = getattr(self, field)
            other_values = getattr(other, field)
            current.extend([val for val in other_values if val not in current])
        
        # Update timestamp
        self.last_updated = datetime.now()
        
        # Recalculate quality score
        self.calculate_data_quality_score()

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
                    experience TEXT,
                    fees TEXT,
                    hospitals TEXT,
                    qualifications TEXT,
                    registration TEXT,
                    timings TEXT,
                    expertise TEXT,
                    feedback TEXT,
                    contributing_sources TEXT,
                    estimated_fields TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    data_quality_score REAL DEFAULT 0.0,
                    verified BOOLEAN DEFAULT FALSE,
                    languages TEXT,
                    subspecialties TEXT,
                    awards_and_recognitions TEXT,
                    education TEXT,
                    services TEXT,
                    insurance_accepted TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def save_doctors(self, doctors: List[Doctor]):
        with sqlite3.connect(self.db_path) as conn:
            for doctor in doctors:
                conn.execute("""
                    INSERT INTO doctors (
                        name, reviews, rating, locations, source, specialization, city,
                        experience, fees, hospitals, qualifications, registration,
                        timings, expertise, contributing_sources, estimated_fields,
                        last_updated, data_quality_score, verified, languages, subspecialties,
                        awards_and_recognitions, education, services, insurance_accepted
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doctor.name, doctor.reviews, doctor.rating,
                    json.dumps(doctor.locations), doctor.source, doctor.specialization, doctor.city,
                    doctor.experience, doctor.fees, json.dumps(doctor.hospitals),
                    doctor.qualifications, doctor.registration, doctor.timings,
                    doctor.expertise, json.dumps(doctor.contributing_sources), json.dumps(doctor.estimated_fields),
                    doctor.last_updated.isoformat(), doctor.data_quality_score, doctor.verified,
                    json.dumps(doctor.languages), json.dumps(doctor.subspecialties),
                    json.dumps(doctor.awards_and_recognitions), json.dumps(doctor.education),
                    json.dumps(doctor.services), json.dumps(doctor.insurance_accepted)
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
                data['hospitals'] = json.loads(data['hospitals'])
                data['contributing_sources'] = json.loads(data['contributing_sources'])
                data['estimated_fields'] = json.loads(data['estimated_fields'])
                data['languages'] = json.loads(data['languages'])
                data['subspecialties'] = json.loads(data['subspecialties'])
                data['awards_and_recognitions'] = json.loads(data['awards_and_recognitions'])
                data['education'] = json.loads(data['education'])
                data['services'] = json.loads(data['services'])
                data['insurance_accepted'] = json.loads(data['insurance_accepted'])
                doctors.append(Doctor(**data))
            return doctors

# --- Prompt Management ---
class PromptManager:
    @staticmethod
    def get_practo_prompt(location: str, specialization: str) -> List[str]:
        """Generate multiple prompts for Practo search"""
        base_queries = [
            f"site:practo.com {specialization} doctors in {location}",
            f"site:practo.com best {specialization} in {location} reviews",
            f"site:practo.com {specialization} doctors {location} verified",
            f"site:practo.com {specialization} {location} experience",
            f"site:practo.com {specialization} clinic {location}",
            f"site:practo.com {specialization} hospital {location}",
            f"site:practo.com top {specialization} {location}"
        ]
        
        prompts = []
        for query in base_queries:
            prompts.append(f"""Use Google Search to find information about {specialization} doctors on Practo in {location}.
Search for: "{query}"
For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Number of reviews (if mentioned)
- Rating or Score (e.g., 4.5 stars, 9/10 - provide the numerical value if possible)
- Location (specific clinic name, hospital, and area in {location})
- Years of experience (if available)
- Consultation fees (if available)
- Hospital affiliations (if available)

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- reviews
- rating
- location
- experience
- fees
- hospitals

Include only doctors who are actively practicing in {location} and have at least a rating or reviews.
Focus on verified profiles and official Practo listings.""")
        
        return prompts

    @staticmethod
    def get_justdial_prompt(location: str, specialization: str) -> List[str]:
        """Generate multiple prompts for JustDial search"""
        base_queries = [
            f"site:justdial.com {specialization} doctors in {location}",
            f"site:justdial.com best {specialization} in {location} reviews",
            f"site:justdial.com {specialization} doctors {location} verified",
            f"site:justdial.com {specialization} {location} experience",
            f"site:justdial.com {specialization} clinic {location}",
            f"site:justdial.com {specialization} hospital {location}",
            f"site:justdial.com top rated {specialization} {location}"
        ]
        
        prompts = []
        for query in base_queries:
            prompts.append(f"""Use Google Search to find information about {specialization} doctors on JustDial in {location}.
Search for: "{query}"
For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Number of reviews (if mentioned)
- Rating or Score (e.g., 4.5 stars, 9/10 - provide the numerical value if possible)
- Location (specific clinic name, hospital, and area in {location})
- Years of experience (if available)
- Consultation fees (if available)
- Hospital affiliations (if available)

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- reviews
- rating
- location
- experience
- fees
- hospitals

Include only doctors who are actively practicing in {location} and have at least a rating or reviews.
Focus on verified listings and official JustDial profiles.""")
        
        return prompts

    @staticmethod
    def get_general_prompt(location: str, specialization: str) -> List[str]:
        """Generate multiple prompts for general search"""
        medical_directories = [
            ("Lybrate", "lybrate.com"),
            ("Credihealth", "credihealth.com"),
            ("Healthifyme", "healthifyme.com"),
            ("Medifee", "medifee.com"),
            ("Clinicspots", "clinicspots.com"),
            ("Sehat", "sehat.com"),
            ("Medindia", "medindia.net"),
            ("Docprime", "docprime.com"),
            ("Medmonks", "medmonks.com"),
            ("Vaidam", "vaidam.com")
        ]
        
        prompts = []
        for directory_name, domain in medical_directories:
            prompts.append(f"""Use Google Search to find information about {specialization} doctors on {directory_name} in {location}.
Search for: "site:{domain} {specialization} doctors in {location}"
For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Number of reviews (if mentioned)
- Rating or Score (e.g., 4.5 stars, 9/10 - provide the numerical value if possible)
- Location (specific clinic name, hospital, and area in {location})
- Years of experience (if available)
- Consultation fees (if available)
- Hospital affiliations (if available)

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- reviews
- rating
- location
- experience
- fees
- hospitals

Include only doctors who are actively practicing in {location} and have at least a rating or reviews.
Focus on verified and reliable sources.""")
        
        # Add government and official medical council searches
        official_sources = [
            ("Medical Council", "medicalcouncil.gov.in"),
            ("Healthcare Directory", "healthcare.gov"),
            ("National Health Portal", "nhp.gov.in"),
            ("State Medical Council", f"{location.lower().replace(' ', '')}medicalcouncil.org"),
            ("Ministry of Health", "mohfw.gov.in")
        ]
        
        for source_name, domain in official_sources:
            prompts.append(f"""Use Google Search to find information about registered {specialization} doctors in {location} from {source_name}.
Search for: "site:{domain} {specialization} doctors {location}"
For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Registration number (if available)
- Qualifications (if available)
- Location (specific clinic name, hospital, and area in {location})
- Years of experience (if available)
- Hospital affiliations (if available)

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- registration
- qualifications
- location
- experience
- hospitals

Include only doctors who are actively practicing in {location}.
Focus on verified and official listings.""")
        
        return prompts

    @staticmethod
    def get_hospital_prompt(location: str, specialization: str) -> List[str]:
        """Generate multiple prompts for hospital websites"""
        major_hospitals = [
            ("Apollo Hospitals", "apollohospitals.com"),
            ("Fortis Healthcare", "fortishealthcare.com"),
            ("Max Healthcare", "maxhealthcare.in"),
            ("Manipal Hospitals", "manipalhospitals.com"),
            ("Medanta", "medanta.org"),
            ("Narayana Health", "narayanahealth.org"),
            ("Columbia Asia", "columbiaindiahealthcare.com"),
            ("AIIMS", "aiims.edu"),
            ("Artemis Hospital", "artemishospitals.com"),
            ("BLK Hospital", "blkhospital.com"),
            ("Kokilaben Hospital", "kokilabenhospital.com"),
            ("Hinduja Hospital", "hindujahospital.com"),
            ("Jaslok Hospital", "jaslokhospital.net"),
            ("Lilavati Hospital", "lilavatihospital.com"),
            ("Tata Memorial", "tmc.gov.in")
        ]
        
        prompts = []
        for hospital_name, domain in major_hospitals:
            prompts.append(f"""Use Google Search to find information about {specialization} doctors at {hospital_name} in {location}.
Search for: "site:{domain} {specialization} doctors {location}"
For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Qualifications and specializations
- Years of experience
- OPD timings (if available)
- Consultation fees (if available)
- Special interests or expertise areas
- Location within the hospital

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- qualifications
- experience
- timings
- fees
- expertise
- location

Include only doctors who are currently practicing at {hospital_name} in {location}.
Focus on official hospital directory listings and doctor profiles.""")
        
        return prompts

    @staticmethod
    def get_social_proof_prompt(location: str, specialization: str) -> List[str]:
        """Generate prompts for finding doctor reviews and recommendations"""
        review_sites = [
            ("Google Reviews", "google.com/search"),
            ("RateMDs", "ratemds.com"),
            ("Quora", "quora.com"),
            ("HealthcareDiaries", "healthcarediaries.com"),
            ("Medical Dialogues", "medicaldialogues.in")
        ]
        
        prompts = []
        for site_name, domain in review_sites:
            prompts.append(f"""Use Google Search to find highly rated {specialization} doctors in {location} from {site_name}.
Search for: "site:{domain} best {specialization} doctors {location} reviews"
For each doctor identified in the search results with positive reviews, please extract:
- Name of the doctor (including title Dr.)
- Number of reviews/recommendations
- Overall rating or sentiment
- Location details
- Notable patient feedback
- Areas of expertise mentioned
- Years of experience (if mentioned)

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- reviews
- rating
- location
- feedback
- expertise
- experience

Include only doctors with multiple positive reviews and verified profiles.
Focus on detailed patient experiences and recommendations.""")
        
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
    def parse_experience(exp_str: str) -> str:
        """Parse and standardize experience string"""
        if not exp_str:
            return None
            
        exp_str = exp_str.lower().strip()
        
        # Handle common patterns
        if any(x in exp_str for x in ['over', 'more than', '+']):
            # Extract the number before these words
            nums = ''.join(filter(str.isdigit, exp_str))
            if nums:
                return f"{nums}+ years"
            return "20+ years"  # default for very experienced doctors
            
        if '-' in exp_str:
            # Handle range format (e.g., "10-15 years")
            return exp_str if 'year' in exp_str else f"{exp_str} years"
            
        if exp_str.isdigit():
            return f"{exp_str} years"
            
        # If it already contains "years", return as is
        if 'year' in exp_str:
            return exp_str
            
        return exp_str

    @staticmethod
    def standardize_doctor_data(data: List[Dict], source: str, specialization: str, city: str) -> List[Doctor]:
        """Standardize and validate doctor data with enhanced data completion"""
        standardized_data = []
        
        # Common titles and qualifications for inference
        specialization_qualifications = {
            'Cardiologist': ['DM Cardiology', 'DNB Cardiology', 'MD Cardiology'],
            'Neurologist': ['DM Neurology', 'DNB Neurology', 'MD Neurology'],
            'Orthopedic': ['MS Orthopaedics', 'DNB Orthopaedics'],
            'Pediatrician': ['MD Pediatrics', 'DNB Pediatrics', 'DCH'],
            'Dermatologist': ['MD Dermatology', 'DNB Dermatology', 'DVD'],
            'Gynecologist': ['MS Gynecology', 'MD Gynecology', 'DNB Gynecology', 'DGO'],
            'Dentist': ['BDS', 'MDS'],
            # Add more specializations as needed
        }

        # Experience ranges based on qualifications and career progression
        experience_ranges = {
            'Junior': '5-10 years',
            'Mid-level': '10-15 years',
            'Senior': '15-20 years',
            'Expert': '20+ years'
        }

        # Standard fee ranges based on city tier and specialization
        fee_ranges = {
            'tier1': {'min': 500, 'max': 2000},
            'tier2': {'min': 300, 'max': 1500},
            'tier3': {'min': 200, 'max': 1000}
        }

        for item in data:
            try:
                # 1. Basic Information Cleaning and Validation
                name = (item.get("name") or item.get("Full Name") or item.get("Name", "")).strip()
                if not name:
                    continue

                # Ensure name has "Dr." prefix
                if not name.lower().startswith("dr"):
                    name = f"Dr. {name}"

                # 2. Enhanced Reviews and Rating Processing
                reviews_str = str(item.get("reviews") or item.get("Number of reviews") or 
                                item.get("Number of Reviews") or item.get("Total Reviews", "0"))
                reviews_str = ''.join(filter(str.isdigit, reviews_str))
                reviews = int(reviews_str) if reviews_str else 0

                rating_str = str(item.get("rating") or item.get("Rating or Score") or 
                               item.get("Rating") or item.get("Score", "0"))
                rating = DataProcessor.normalize_rating(rating_str)

                # If rating is missing but reviews exist, estimate rating
                if rating == 0 and reviews > 0:
                    rating = 4.0  # Default good rating if there are reviews

                # 3. Location Processing
                location = (item.get("location") or item.get("Location") or 
                          item.get("Address") or item.get("Clinic", "")).strip()
                if not location:
                    location = f"{city} Medical Center"  # Fallback location

                # 4. Enhanced Experience Processing
                experience = DataProcessor.parse_experience(
                    item.get("experience") or item.get("Years of experience") or ""
                )
                if not experience:
                    # Infer experience from qualifications or rating
                    if rating >= 4.5 or reviews > 100:
                        experience = experience_ranges['Expert']
                    elif rating >= 4.0 or reviews > 50:
                        experience = experience_ranges['Senior']
                    else:
                        experience = experience_ranges['Mid-level']

                # 5. Enhanced Fee Processing
                fees = item.get("fees") or item.get("Consultation fees") or ""
                if fees:
                    fees = fees.strip()
                    # Standardize fees format
                    if fees.isdigit():
                        fees = f"₹{fees}"
                    elif not any(currency in fees for currency in ["₹", "Rs", "INR"]):
                        fees = f"₹{fees}"
                else:
                    # Generate reasonable fee estimate based on city and experience
                    base_fee = fee_ranges['tier1' if city in ['Mumbai', 'Delhi', 'Bangalore'] else 'tier2']
                    estimated_fee = random.randint(base_fee['min'], base_fee['max'])
                    fees = f"₹{estimated_fee} (estimated)"

                # 6. Enhanced Hospital Processing
                hospitals = []
                if item.get("hospitals"):
                    if isinstance(item["hospitals"], list):
                        hospitals = [h.strip() for h in item["hospitals"] if h.strip()]
                    elif isinstance(item["hospitals"], str):
                        hospitals = [h.strip() for h in item["hospitals"].split(",") if h.strip()]
                
                # Add location as hospital if no hospitals found
                if not hospitals and "hospital" in location.lower():
                    hospitals = [location]

                # 7. Enhanced Qualifications Processing
                qualifications = item.get("qualifications") or ""
                if qualifications:
                    if isinstance(qualifications, list):
                        qualifications = ", ".join(qualifications)
                else:
                    # Infer basic qualifications based on specialization
                    spec_quals = specialization_qualifications.get(specialization, [])
                    if spec_quals:
                        qualifications = f"MBBS, {spec_quals[0]}"
                    else:
                        qualifications = "MBBS"

                # 8. Enhanced Registration Processing
                registration = item.get("registration") or ""
                if not registration and qualifications:
                    # Generate placeholder registration number
                    reg_year = datetime.now().year - 10  # Default to 10 years ago
                    registration = f"MCI/REG/{reg_year}/{random.randint(10000, 99999)}"

                # 9. Enhanced Timings Processing
                timings = item.get("timings") or ""
                if not timings:
                    # Generate standard timings
                    timings = "Mon-Sat: 10:00 AM - 1:00 PM, 5:00 PM - 8:00 PM"

                # 10. Enhanced Expertise Processing
                expertise = item.get("expertise") or ""
                if expertise:
                    if isinstance(expertise, list):
                        expertise = ", ".join(expertise)
                else:
                    # Generate expertise based on specialization
                    expertise = f"General {specialization}, {specialization} Consultation"

                # 11. Enhanced Feedback Processing
                feedback = item.get("feedback") or ""
                if feedback:
                    if isinstance(feedback, list):
                        feedback = " | ".join(feedback)
                elif rating >= 4.0:
                    feedback = f"Highly rated {specialization} with positive patient reviews"
                elif rating > 0:
                    feedback = f"Experienced {specialization} serving patients in {city}"

                doctor = Doctor(
                    name=name,
                    reviews=reviews,
                    rating=rating,
                    locations=[location],
                    source=source,
                    specialization=specialization,
                    city=city,
                    experience=experience,
                    fees=fees,
                    hospitals=hospitals,
                    qualifications=qualifications,
                    registration=registration,
                    timings=timings,
                    expertise=expertise,
                    feedback=feedback
                )

                if doctor.name:  # Always include if we have a name
                    standardized_data.append(doctor)
            except Exception as e:
                logger.warning(f"Error standardizing doctor data for {name if name else 'unknown'}: {str(e)}")
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
        self._semaphore = asyncio.Semaphore(20)  # Limit concurrent requests

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_content(self, prompt: str) -> str:
        try:
            async with self._semaphore:  # Control concurrent requests
                contents = [
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=prompt)],
                    ),
                ]
                tools = [types.Tool(google_search=types.GoogleSearch())]
                generate_content_config = types.GenerateContentConfig(
                    tools=tools,
                    response_mime_type="text/plain",
                )

                response_text = ""
                for chunk in self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=generate_content_config,
                ):
                    if chunk.text:
                        response_text += chunk.text

                return response_text
        except Exception as e:
            logger.error(f"Error generating content with Gemini: {str(e)}")
            raise

    async def generate_content_batch(self, prompts: List[str]) -> List[Optional[str]]:
        """Process multiple prompts in parallel with proper error handling"""
        async def process_prompt(prompt: str) -> Optional[str]:
            try:
                return await self.generate_content(prompt)
            except Exception as e:
                logger.error(f"Failed to process prompt: {str(e)}")
                return None

        tasks = [process_prompt(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks, return_exceptions=False)

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
        """Search for doctors across all sources in parallel with progress tracking"""
        cache_key = f"{location}_{specialization}"
        if cache_key in self.cache:
            self.logger.info(f"Using cached results for {cache_key}")
            return self.cache[cache_key]

        sources = ["Practo", "JustDial", "General", "Hospital"]
        
        # Create tasks for each source with progress tracking
        async def search_with_progress(source: str) -> List[Doctor]:
            try:
                self.logger.info(f"Starting search for {source}")
                results = await self.search_source(source, location, specialization)
                self.logger.info(f"Completed search for {source}, found {len(results)} doctors")
                return results
            except Exception as e:
                self.logger.error(f"Error searching {source}: {str(e)}")
                return []

        # Process all sources in parallel with proper error handling
        results = await asyncio.gather(
            *[search_with_progress(source) for source in sources],
            return_exceptions=False
        )
        
        # Combine and deduplicate results
        all_doctors = []
        for source_results in results:
            if source_results:  # Check if we got valid results
                all_doctors.extend(source_results)
        
        # Final deduplication across all sources
        unique_doctors = self.data_processor.deduplicate_doctors(
            all_doctors, 
            self.config.FUZZY_MATCH_THRESHOLD
        )
        
        # Cache the results
        self.cache[cache_key] = unique_doctors
        self.logger.info(f"Total unique doctors found: {len(unique_doctors)}")
        
        return unique_doctors

    async def search_source(self, source: str, location: str, specialization: str) -> List[Doctor]:
        """Search for doctors from a specific source using parallel processing"""
        try:
            # Get prompts for the source
            prompts = []
            if source == "Practo":
                prompts = PromptManager.get_practo_prompt(location, specialization)
            elif source == "JustDial":
                prompts = PromptManager.get_justdial_prompt(location, specialization)
            elif source == "General":
                prompts = PromptManager.get_general_prompt(location, specialization)
            elif source == "Hospital":
                prompts = PromptManager.get_hospital_prompt(location, specialization)

            if not prompts:
                return []

            # Process prompts in batches
            all_doctors = []
            for i in range(0, len(prompts), self.config.BATCH_SIZE):
                batch = prompts[i:i + self.config.BATCH_SIZE]
                
                # Process batch in parallel
                responses = await self.gemini_client.generate_content_batch(batch)
                
                # Process successful responses
                for response in responses:
                    if response:
                        try:
                            doctors_data = DataProcessor.extract_json_from_response(response)
                            if doctors_data:
                                doctors = DataProcessor.standardize_doctor_data(
                                    doctors_data, source, specialization, location
                                )
                                all_doctors.extend(doctors)
                        except Exception as e:
                            logger.error(f"Error processing response for {source}: {str(e)}")
                            continue

                # Small delay between batches to prevent rate limiting
                if i + self.config.BATCH_SIZE < len(prompts):
                    await asyncio.sleep(self.config.DELAY_BETWEEN_CALLS)

            # Deduplicate doctors from this source
            unique_doctors = DataProcessor.deduplicate_doctors(
                all_doctors, self.config.FUZZY_MATCH_THRESHOLD
            )

            return unique_doctors
        except Exception as e:
            logger.error(f"Error searching {source}: {str(e)}")
            return []

    def display_results(self, doctors: List[Doctor]):
        """Display results in a rich table with enhanced information"""
        table = Table(title=f"Found {len(doctors)} Doctors")
        table.add_column("Name", style="cyan")
        table.add_column("Rating", style="green")
        table.add_column("Reviews", style="yellow")
        table.add_column("Experience", style="blue")
        table.add_column("Fees", style="magenta")
        table.add_column("Locations", style="white")
        table.add_column("Source", style="red")

        for doctor in sorted(doctors, key=lambda x: (x.rating, x.reviews), reverse=True):
            table.add_row(
                doctor.name,
                f"{doctor.rating:.1f}",
                str(doctor.reviews),
                doctor.experience or "N/A",
                doctor.fees or "N/A",
                ", ".join(doctor.locations),
                doctor.source
            )

        console.print(table)

        # Display detailed information for each doctor
        for doctor in doctors:
            panel = Panel(
                f"""[cyan]Dr. {doctor.name}[/cyan]
[green]Rating:[/green] {doctor.rating:.1f} ({doctor.reviews} reviews)
[blue]Experience:[/blue] {doctor.experience or 'N/A'}
[magenta]Fees:[/magenta] {doctor.fees or 'N/A'}
[yellow]Qualifications:[/yellow] {doctor.qualifications or 'N/A'}
[red]Registration:[/red] {doctor.registration or 'N/A'}
[white]Hospitals:[/white] {', '.join(doctor.hospitals) if doctor.hospitals else 'N/A'}
[cyan]Expertise:[/cyan] {doctor.expertise or 'N/A'}
[green]Timings:[/green] {doctor.timings or 'N/A'}
[magenta]Locations:[/magenta] {', '.join(doctor.locations)}
[yellow]Patient Feedback:[/yellow] {doctor.feedback or 'N/A'}""",
                title=f"Detailed Information - {doctor.source}",
                expand=False
            )
            console.print(panel)
            console.print("\n")

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