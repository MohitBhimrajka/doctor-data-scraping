import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Load environment variables from .env file
load_dotenv()

def clean_env_value(value: str | None, default: str = "") -> str:
    """Clean environment variable value."""
    if value is None:
        return default
    return value.strip().strip('"').strip("'")

# Base Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

def parse_json_env_var(var_name: str, default_value: Dict[str, Any]) -> Dict[str, Any]:
    """Parse JSON string from environment variable with fallback to default value."""
    try:
        value = clean_env_value(os.getenv(var_name))
        if not value:
            return default_value
        return json.loads(value)
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse {var_name} from environment: {e}")
        return default_value

def validate_config() -> None:
    """Validate required configuration values."""
    required_vars = ["GEMINI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# API Configuration
GEMINI_API_KEY = clean_env_value(os.getenv("GEMINI_API_KEY"))
API_HOST = clean_env_value(os.getenv("API_HOST", "0.0.0.0"))
API_PORT = int(clean_env_value(os.getenv("API_PORT", "8000")))
REQUEST_TIMEOUT = int(clean_env_value(os.getenv("REQUEST_TIMEOUT", "30")))
MAX_RETRIES = int(clean_env_value(os.getenv("MAX_RETRIES", "3")))

# Database Configuration
DATABASE_URL = clean_env_value(os.getenv("DATABASE_URL", "sqlite:///./doctors.db"))

# Search Configuration
FUZZY_MATCH_THRESHOLD = float(clean_env_value(os.getenv("FUZZY_MATCH_THRESHOLD", "0.8")))
MAX_RESULTS = int(clean_env_value(os.getenv("MAX_RESULTS", "100")))

# Cache Configuration
CACHE_TTL = int(clean_env_value(os.getenv("CACHE_TTL", "3600")))

# API Rate Limiting
RATE_LIMIT_REQUESTS = int(clean_env_value(os.getenv("RATE_LIMIT_REQUESTS", "100")))
RATE_LIMIT_PERIOD = int(clean_env_value(os.getenv("RATE_LIMIT_PERIOD", "3600")))
MAX_CONCURRENT_REQUESTS = int(clean_env_value(os.getenv("MAX_CONCURRENT_REQUESTS", "5")))

# Logging Configuration
LOG_LEVEL = clean_env_value(os.getenv("LOG_LEVEL", "INFO"))
LOG_FILE = clean_env_value(os.getenv("LOG_FILE", "app.log"))
LOG_FORMAT = clean_env_value(os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

# Development Mode
DEBUG = clean_env_value(os.getenv("DEBUG", "false")).lower() == "true"

# Security
ALLOWED_ORIGINS = clean_env_value(os.getenv("ALLOWED_ORIGINS", "http://localhost:8501")).split(",")

# Gemini API Configuration
GEMINI_MODEL_NAME = clean_env_value(os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro"))
DISCOVERY_MODEL_NAME = clean_env_value(os.getenv("DISCOVERY_MODEL_NAME", "gemini-1.0-pro"))
VERIFICATION_MODEL_NAME = clean_env_value(os.getenv("VERIFICATION_MODEL_NAME", "gemini-1.0-pro"))

# Discovery Configuration
DISCOVERY_PROMPT_TEMPLATE = """
Search for doctors with the following criteria:
{search_criteria}

Please provide:
1. Doctor's name
2. Specialization
3. City and state
4. Rating and total reviews
5. Hospital/clinic locations
6. Profile URLs
"""

DISCOVERY_TEMPERATURE = 0.2
DISCOVERY_TOP_K = 1
DISCOVERY_TOP_P = 0.8
DISCOVERY_MAX_OUTPUT_TOKENS = 1024
DISCOVERY_STOP_SEQUENCES = ["END"]
DISCOVERY_SAFETY_SETTINGS = {
    "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM",
    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM",
    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM"
}

# Verification Configuration
VERIFICATION_PROMPT_TEMPLATE = """
Verify the following doctor information:
{doctor_info}

Sources:
{source_info}

Please analyze the information and provide:
1. Verification status (VERIFIED/UNVERIFIED)
2. Confidence score (0-1)
3. Any discrepancies found
4. Suggested corrections
"""

VERIFICATION_TEMPERATURE = 0.2
VERIFICATION_TOP_K = 1
VERIFICATION_TOP_P = 0.8
VERIFICATION_MAX_OUTPUT_TOKENS = 1024
VERIFICATION_STOP_SEQUENCES = ["END"]
VERIFICATION_SAFETY_SETTINGS = {
    "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM",
    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM",
    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM"
}

# Priority Sources
PRIORITY_SOURCES = ["practo", "google"]

# Data Configuration
DATA_DIR = clean_env_value(os.getenv("DATA_DIR", "data"))

# Search Configuration
MAX_SEARCH_RESULTS = int(clean_env_value(os.getenv("MAX_SEARCH_RESULTS", "10")))
MIN_RATING_THRESHOLD = float(clean_env_value(os.getenv("MIN_RATING_THRESHOLD", "4.0")))
MIN_REVIEWS_THRESHOLD = int(clean_env_value(os.getenv("MIN_REVIEWS_THRESHOLD", "10")))

# Confidence Weights
CONFIDENCE_WEIGHTS = parse_json_env_var(
    "CONFIDENCE_WEIGHTS",
    {
        "num_sources": 0.3,
        "total_reviews": 0.2,
        "rating_consistency": 0.3,
        "priority_source_found": 0.2
    }
)

# Rating Source Weights
RATING_SOURCE_WEIGHTS = {
    "practo": 0.4,
    "google": 0.3,
    "justdial": 0.2,
    "other": 0.1
}

# Validate configuration on import
validate_config() 