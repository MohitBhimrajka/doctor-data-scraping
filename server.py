from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from doctor_search_enhanced import Config, DoctorSearchApp
import asyncio
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Get frontend URL from environment variable
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],  # Use environment variable
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
    city: str
    specialization: str

class Doctor(BaseModel):
    name: str
    rating: float
    reviews: int
    locations: List[str]
    source: str
    specialization: str
    city: str
    timestamp: str

@app.get("/")
async def read_root():
    return {"message": "Doctor Search API is running"}

@app.post("/api/search", response_model=List[Doctor])
async def search_doctors(request: SearchRequest):
    try:
        logger.info(f"Received search request for {request.specialization} in {request.city}")
        doctors = await doctor_app.search_all_sources(request.city, request.specialization)
        return doctors
    except Exception as e:
        logger.error(f"Error processing search request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 