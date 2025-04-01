import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from ..models.doctor import Doctor
from ..services.discovery import DoctorDiscoveryService
from ..services.verification import DoctorVerificationService
from ..services.database import DatabaseService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
discovery_service = DoctorDiscoveryService()
verification_service = DoctorVerificationService()
database_service = DatabaseService()

@router.get("/search", response_model=List[Doctor])
async def search_doctors(
    specialization: str = Query(..., description="Doctor specialization"),
    city: str = Query(..., description="City to search in"),
    min_rating: Optional[float] = Query(None, description="Minimum rating threshold"),
    min_reviews: Optional[int] = Query(None, description="Minimum number of reviews"),
    limit: int = Query(10, description="Maximum number of results to return")
) -> List[Doctor]:
    """
    Search for doctors based on specialization and city.
    
    Args:
        specialization: Doctor specialization to search for
        city: City to search in
        min_rating: Optional minimum rating threshold
        min_reviews: Optional minimum number of reviews
        limit: Maximum number of results to return
        
    Returns:
        List of matching Doctor objects
    """
    try:
        # First try to get results from database
        results = database_service.search_doctors(
            specialization=specialization,
            city=city,
            min_rating=min_rating,
            min_reviews=min_reviews,
            limit=limit
        )
        
        # If not enough results, discover more doctors
        if len(results) < limit:
            discovered_doctors = await discovery_service.search_doctors(
                specialization=specialization,
                city=city
            )
            
            # Verify and save new doctors
            for doctor in discovered_doctors:
                if doctor.id not in [r.id for r in results]:
                    verified_doctor = await verification_service.verify_doctor(
                        doctor=doctor,
                        sources=doctor.contributing_sources
                    )
                    database_service.save_doctor(verified_doctor)
                    results.append(verified_doctor)
                    
                    if len(results) >= limit:
                        break
                        
        return results[:limit]
        
    except Exception as e:
        logger.error(f"Error searching doctors: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error searching for doctors"
        )

@router.get("/{doctor_id}", response_model=Doctor)
async def get_doctor(doctor_id: str) -> Doctor:
    """
    Get doctor by ID.
    
    Args:
        doctor_id: Unique identifier for the doctor
        
    Returns:
        Doctor object
        
    Raises:
        HTTPException: If doctor not found
    """
    try:
        doctor = database_service.get_doctor(doctor_id)
        if not doctor:
            raise HTTPException(
                status_code=404,
                detail=f"Doctor with ID {doctor_id} not found"
            )
        return doctor
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting doctor {doctor_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving doctor information"
        )

@router.get("/stats")
async def get_stats():
    """
    Get statistics about stored doctors.
    
    Returns:
        Dictionary containing various statistics
    """
    try:
        return database_service.get_doctor_stats()
        
    except Exception as e:
        logger.error(f"Error getting doctor stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving doctor statistics"
        )

@router.post("/cleanup")
async def cleanup_data(days: int = 30):
    """
    Clean up old doctor data.
    
    Args:
        days: Number of days to keep data for
        
    Returns:
        Success message
    """
    try:
        database_service.cleanup_old_data(days)
        return {"message": f"Successfully cleaned up data older than {days} days"}
        
    except Exception as e:
        logger.error(f"Error cleaning up data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error cleaning up old data"
        ) 