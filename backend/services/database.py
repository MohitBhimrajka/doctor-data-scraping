import logging
from typing import List, Optional, Dict
from datetime import datetime
import json
import os
from pathlib import Path
from ..models.doctor import Doctor

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.doctors_file = self.data_dir / "doctors.json"
        self._ensure_data_dir()
        self._load_doctors()

    def _ensure_data_dir(self) -> None:
        """Ensure data directory exists."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating data directory: {str(e)}")
            raise

    def _load_doctors(self) -> None:
        """Load doctors from JSON file."""
        try:
            if self.doctors_file.exists():
                with open(self.doctors_file, "r") as f:
                    data = json.load(f)
                    self.doctors = {
                        doctor_id: Doctor(**doctor_data)
                        for doctor_id, doctor_data in data.items()
                    }
            else:
                self.doctors = {}
        except Exception as e:
            logger.error(f"Error loading doctors: {str(e)}")
            self.doctors = {}

    def _save_doctors(self) -> None:
        """Save doctors to JSON file."""
        try:
            data = {
                doctor_id: doctor.dict()
                for doctor_id, doctor in self.doctors.items()
            }
            with open(self.doctors_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving doctors: {str(e)}")
            raise

    def get_doctor(self, doctor_id: str) -> Optional[Doctor]:
        """
        Get doctor by ID.
        
        Args:
            doctor_id: Unique identifier for the doctor
            
        Returns:
            Doctor object if found, None otherwise
        """
        return self.doctors.get(doctor_id)

    def save_doctor(self, doctor: Doctor) -> None:
        """
        Save or update doctor information.
        
        Args:
            doctor: Doctor object to save
        """
        try:
            self.doctors[doctor.id] = doctor
            self._save_doctors()
        except Exception as e:
            logger.error(f"Error saving doctor {doctor.id}: {str(e)}")
            raise

    def search_doctors(
        self,
        specialization: Optional[str] = None,
        city: Optional[str] = None,
        min_rating: Optional[float] = None,
        min_reviews: Optional[int] = None,
        limit: int = 10
    ) -> List[Doctor]:
        """
        Search doctors with filters.
        
        Args:
            specialization: Doctor specialization to filter by
            city: City to filter by
            min_rating: Minimum rating threshold
            min_reviews: Minimum number of reviews
            limit: Maximum number of results to return
            
        Returns:
            List of matching Doctor objects
        """
        try:
            results = []
            
            for doctor in self.doctors.values():
                # Apply filters
                if specialization and doctor.specialization.lower() != specialization.lower():
                    continue
                    
                if city and doctor.city.lower() != city.lower():
                    continue
                    
                if min_rating and doctor.rating < min_rating:
                    continue
                    
                if min_reviews and doctor.reviews < min_reviews:
                    continue
                    
                results.append(doctor)
                
            # Sort by confidence score and rating
            results.sort(
                key=lambda x: (x.confidence_score, x.rating),
                reverse=True
            )
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching doctors: {str(e)}")
            return []

    def get_doctor_stats(self) -> Dict:
        """
        Get statistics about stored doctors.
        
        Returns:
            Dictionary containing various statistics
        """
        try:
            stats = {
                "total_doctors": len(self.doctors),
                "specializations": {},
                "cities": {},
                "avg_rating": 0.0,
                "avg_reviews": 0,
                "avg_confidence": 0.0
            }
            
            if not self.doctors:
                return stats
                
            total_rating = 0.0
            total_reviews = 0
            total_confidence = 0.0
            
            for doctor in self.doctors.values():
                # Count specializations
                stats["specializations"][doctor.specialization] = \
                    stats["specializations"].get(doctor.specialization, 0) + 1
                    
                # Count cities
                stats["cities"][doctor.city] = \
                    stats["cities"].get(doctor.city, 0) + 1
                    
                # Sum ratings and reviews
                total_rating += doctor.rating
                total_reviews += doctor.reviews
                total_confidence += doctor.confidence_score
                
            # Calculate averages
            stats["avg_rating"] = total_rating / len(self.doctors)
            stats["avg_reviews"] = total_reviews / len(self.doctors)
            stats["avg_confidence"] = total_confidence / len(self.doctors)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating doctor stats: {str(e)}")
            return {}

    def cleanup_old_data(self, days: int = 30) -> None:
        """
        Remove doctor data older than specified days.
        
        Args:
            days: Number of days to keep data for
        """
        try:
            current_time = datetime.now()
            old_doctors = []
            
            for doctor_id, doctor in self.doctors.items():
                age = (current_time - doctor.timestamp).days
                if age > days:
                    old_doctors.append(doctor_id)
                    
            for doctor_id in old_doctors:
                del self.doctors[doctor_id]
                
            if old_doctors:
                self._save_doctors()
                logger.info(f"Removed {len(old_doctors)} old doctor records")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
            raise 