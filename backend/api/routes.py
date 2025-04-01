from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

from ..models.doctor import Doctor
from ..services.discovery import DoctorDiscoveryService
from ..services.database import DatabaseService
from ..services.verification import DoctorVerificationService

router = APIRouter(
    prefix="/api/v1",
    tags=["doctors"],
    responses={404: {"description": "Not found"}},
)

# Initialize services
discovery_service = DoctorDiscoveryService()
database_service = DatabaseService()
verification_service = DoctorVerificationService()

# Configure logger
logger = logging.getLogger(__name__)

@router.post("/search", response_model=List[Doctor])
async def search_doctors(
    specialization: str,
    city: Optional[str] = None,
    country: Optional[str] = "India",
    tiers: Optional[List[int]] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """
    Search for doctors based on specialization and location.
    
    Args:
        specialization: Doctor's specialization (e.g., "Cardiologist")
        city: City name (optional)
        country: Country name (defaults to India)
        tiers: List of city tiers to search in (optional)
        page: Page number for pagination
        page_size: Number of results per page
    
    Returns:
        List of doctors matching the criteria
    """
    try:
        # Search for doctors
        doctors = await discovery_service.search_doctors(
            specialization=specialization,
            city=city,
            country=country,
            tiers=tiers
        )
        
        # Verify doctors
        verified_doctors = []
        for doctor in doctors:
            try:
                verified_doctor = await verification_service.verify_doctor(
                    doctor=doctor,
                    sources=list(doctor.profile_urls.keys())
                )
                verified_doctors.append(verified_doctor)
            except Exception as e:
                # Log verification error but continue with other doctors
                logger.error(f"Error verifying doctor {doctor.name}: {str(e)}")
                verified_doctors.append(doctor)
        
        # Save verified doctors to database
        for doctor in verified_doctors:
            await database_service.save_doctor(doctor)
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_doctors = verified_doctors[start_idx:end_idx]
        
        return paginated_doctors
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching for doctors: {str(e)}"
        )

@router.get("/doctor/{doctor_id}", response_model=Doctor)
async def get_doctor(doctor_id: str):
    """
    Get doctor details by ID.
    
    Args:
        doctor_id: Unique identifier for the doctor
    
    Returns:
        Doctor details if found
    
    Raises:
        HTTPException: If doctor is not found
    """
    try:
        doctor = await database_service.get_doctor(doctor_id)
        if not doctor:
            raise HTTPException(
                status_code=404,
                detail=f"Doctor with ID {doctor_id} not found"
            )
        return doctor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving doctor: {str(e)}"
        )

@router.get("/stats")
async def get_doctor_stats():
    """
    Get statistics about doctors in the database.
    
    Returns:
        Dictionary containing various statistics
    """
    try:
        stats = await database_service.get_doctor_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving doctor statistics: {str(e)}"
        ) 