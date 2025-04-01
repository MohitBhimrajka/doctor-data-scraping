from typing import Dict, List, Optional
import httpx
from datetime import datetime
import json

class APIClient:
    """Client for interacting with the Doctor Search API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the API client.
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            timeout=300.0,  # 5 minutes timeout for long-running searches
            headers={"Content-Type": "application/json"}
        )
    
    async def search_doctors(
        self,
        specialization: str,
        city: Optional[str] = None,
        country: Optional[str] = "India",
        tiers: Optional[List[int]] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Dict:
        """Search for doctors based on criteria.
        
        Args:
            specialization: Doctor's specialization
            city: City name (optional)
            country: Country name (defaults to India)
            tiers: List of city tiers to search in
            page: Page number for pagination
            page_size: Number of results per page
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            # Prepare query parameters
            params = {
                "specialization": specialization,
                "page": page,
                "page_size": page_size
            }
            
            # Add optional parameters
            if city:
                params["city"] = city
            if country:
                params["country"] = country
            if tiers:
                params["tiers"] = tiers
            
            # Make API request
            response = await self.client.post(
                f"{self.base_url}/api/v1/search",
                json=params
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Convert timestamp strings to datetime objects
            for doctor in data:
                if "timestamp" in doctor:
                    doctor["timestamp"] = datetime.fromisoformat(doctor["timestamp"])
            
            return {
                "doctors": data,
                "total": len(data),
                "page": page,
                "page_size": page_size
            }
            
        except httpx.HTTPError as e:
            if e.response.status_code == 404:
                return {"doctors": [], "total": 0, "page": page, "page_size": page_size}
            raise Exception(f"API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Error searching doctors: {str(e)}")
    
    async def get_doctor(self, doctor_id: str) -> Dict:
        """Get doctor details by ID.
        
        Args:
            doctor_id: Unique identifier for the doctor
            
        Returns:
            Dictionary containing doctor details
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/doctor/{doctor_id}"
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Convert timestamp string to datetime
            if "timestamp" in data:
                data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            
            return data
            
        except httpx.HTTPError as e:
            if e.response.status_code == 404:
                raise Exception(f"Doctor with ID {doctor_id} not found")
            raise Exception(f"API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Error retrieving doctor: {str(e)}")
    
    async def get_stats(self) -> Dict:
        """Get statistics about doctors in the database.
        
        Returns:
            Dictionary containing various statistics
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/stats"
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            raise Exception(f"API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Error retrieving statistics: {str(e)}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

