from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from doctor_search_enhanced import Config, DoctorSearchApp
import os

app = FastAPI()

# Configure CORS
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://doctor-search-ui.onrender.com",  # Render frontend URL
    os.getenv("FRONTEND_URL", "http://localhost:3000")  # Allow custom frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    city: str
    specialization: str

@app.post("/search")
async def search_doctors(request: SearchRequest):
    try:
        config = Config()
        if not config.validate():
            raise HTTPException(status_code=500, detail="Configuration validation failed")
        
        app = DoctorSearchApp(config)
        doctors = await app.search_all_sources(request.city, request.specialization)
        
        # Convert doctors to dict for JSON serialization
        return [doctor.model_dump() for doctor in doctors]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 