from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from dotenv import load_dotenv
from doctor_search_enhanced import Config, DoctorSearchApp
import asyncio
import logging
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Doctor Search API",
    description="API for searching doctors across multiple sources",
    version="1.0.0"
)

# Get frontend URL from environment variable
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize the doctor search app
config = Config()
if not config.validate():
    logger.error("Configuration validation failed. Please check your environment variables.")
    raise Exception("Configuration validation failed")

doctor_app = DoctorSearchApp(config)

class SearchRequest(BaseModel):
    city: str = Field(..., min_length=1, description="City to search for doctors")
    specialization: str = Field(..., min_length=1, description="Doctor specialization")

class DoctorResponse(BaseModel):
    name: str
    reviews: int
    rating: float
    locations: List[str]
    source: str
    specialization: str
    city: str
    experience: Optional[str]
    fees: Optional[str]
    hospitals: List[str]
    qualifications: Optional[str]
    registration: Optional[str]
    timings: Optional[str]
    expertise: Optional[str]
    feedback: Optional[str]
    contributing_sources: List[str] = Field(default_factory=list)
    estimated_fields: List[str] = Field(default_factory=list)
    last_updated: datetime
    data_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    verified: bool = Field(default=False)
    languages: List[str] = Field(default_factory=list)
    subspecialties: List[str] = Field(default_factory=list)
    awards_and_recognitions: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    insurance_accepted: List[str] = Field(default_factory=list)
    timestamp: datetime

class SearchResponse(BaseModel):
    success: bool
    data: Optional[List[DoctorResponse]] = None
    error: Optional[str] = None
    metadata: dict = {
        "total": 0,
        "timestamp": "",
        "query": {
            "city": "",
            "specialization": ""
        },
        "sources_used": List[str],  # Track all sources queried
        "search_duration": float,    # Search duration in seconds
        "data_quality": {
            "average_score": float,
            "complete_profiles": int,
            "verified_profiles": int
        }
    }

@app.get("/")
async def read_root():
    return {
        "status": "ok",
        "message": "Doctor Search API is running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/search")
async def search_doctors(request: SearchRequest):
    try:
        logger.info(f"Searching for {request.specialization} in {request.city}")
        
        # Validate input
        if not request.city.strip() or not request.specialization.strip():
            raise HTTPException(
                status_code=400,
                detail="City and specialization cannot be empty"
            )
        
        # Execute search
        doctors = await doctor_app.search_all_sources(request.city, request.specialization)
        
        # Convert to response format
        response_data = []
        for doc in doctors:
            try:
                doc_dict = doc.model_dump()  # Use Pydantic's model_dump() method
                # Convert datetime to string if present
                if 'timestamp' in doc_dict:
                    doc_dict['timestamp'] = doc_dict['timestamp'].isoformat()
                response_data.append(DoctorResponse(**doc_dict))
            except Exception as e:
                logger.error(f"Error converting doctor data: {str(e)}")
                continue
        
        # Prepare response
        response = SearchResponse(
            success=True,
            data=response_data,
            metadata={
                "total": len(response_data),
                "timestamp": datetime.now().isoformat(),
                "query": {
                    "city": request.city,
                    "specialization": request.specialization
                },
                "sources_used": [],
                "search_duration": 0.0,
                "data_quality": {
                    "average_score": 0.0,
                    "complete_profiles": 0,
                    "verified_profiles": 0
                }
            }
        )
        
        logger.info(f"Search completed in {len(response_data)} doctors.")
        return response
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"message": "An error occurred during the search", "error": str(e)}
        )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error handler caught: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "An unexpected error occurred",
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "path": request.url.path
            }
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 