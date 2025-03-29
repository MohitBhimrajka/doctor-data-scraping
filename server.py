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
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the doctor search app
config = Config()
if not config.validate():
    logger.error("Configuration validation failed. Please check your environment variables.")
    raise RuntimeError("Configuration validation failed")

doctor_app = DoctorSearchApp(config)

class SearchRequest(BaseModel):
    city: str = Field(..., min_length=1, description="City to search for doctors")
    specialization: str = Field(..., min_length=1, description="Doctor specialization")

class Doctor(BaseModel):
    name: str
    rating: float
    reviews: int
    locations: List[str]
    source: str
    specialization: str
    city: str
    timestamp: str

class SearchResponse(BaseModel):
    success: bool
    data: Optional[List[Doctor]] = None
    error: Optional[str] = None
    metadata: dict = {
        "total": 0,
        "timestamp": "",
        "query": {
            "city": "",
            "specialization": ""
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

@app.post("/api/search", response_model=SearchResponse)
async def search_doctors(request: SearchRequest):
    start_time = datetime.now()
    try:
        logger.info(f"Received search request for {request.specialization} in {request.city}")
        
        # Validate input
        if not request.city.strip() or not request.specialization.strip():
            raise HTTPException(
                status_code=400,
                detail="City and specialization cannot be empty"
            )
        
        # Search for doctors
        doctors_data = await doctor_app.search_all_sources(request.city, request.specialization)
        
        # Convert Doctor objects (with datetime) to dicts (with isoformat string timestamp)
        response_data = []
        for doc in doctors_data:
            doc_dict = doc.dict()  # Use Pydantic's dict() method
            doc_dict['timestamp'] = doc.timestamp.isoformat()  # Explicit conversion
            response_data.append(Doctor(**doc_dict))  # Validate against response model
        
        # Prepare response
        response = SearchResponse(
            success=True,
            data=response_data,  # Use the converted data
            metadata={
                "total": len(response_data),
                "timestamp": datetime.now().isoformat(),
                "query": {
                    "city": request.city,
                    "specialization": request.specialization
                }
            }
        )
        
        # Log performance
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Search completed in {duration:.2f} seconds. Found {len(response_data)} doctors.")
        
        return response
        
    except HTTPException as he:
        logger.error(f"HTTP error during search: {str(he)}")
        return SearchResponse(
            success=False,
            error=str(he.detail),
            metadata={
                "total": 0,
                "timestamp": datetime.now().isoformat(),
                "query": {
                    "city": request.city,
                    "specialization": request.specialization
                }
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error during search: {str(e)}")
        return SearchResponse(
            success=False,
            error="An unexpected error occurred while searching for doctors",
            metadata={
                "total": 0,
                "timestamp": datetime.now().isoformat(),
                "query": {
                    "city": request.city,
                    "specialization": request.specialization
                }
            }
        )

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