from typing import Dict, Optional, List

def validate_search_inputs(
    specialization: str,
    city: Optional[str] = None,
    country: Optional[str] = None,
    tiers: Optional[List[int]] = None
) -> Dict:
    """Validate search input parameters.
    
    Args:
        specialization: Doctor's specialization
        city: City name (optional)
        country: Country name (optional)
        tiers: List of city tiers (optional)
        
    Returns:
        Dictionary containing validated parameters
        
    Raises:
        ValueError: If validation fails
    """
    # Validate specialization
    if not specialization or len(specialization.strip()) < 2:
        raise ValueError("Specialization must be at least 2 characters long")
    
    # Validate city if provided
    if city:
        if len(city.strip()) < 2:
            raise ValueError("City name must be at least 2 characters long")
    
    # Validate country if provided
    if country:
        if country.lower() != "india":
            raise ValueError("Currently only India is supported")
    
    # Validate tiers if provided
    if tiers:
        if not all(isinstance(tier, int) for tier in tiers):
            raise ValueError("Tiers must be integers")
        if not all(1 <= tier <= 3 for tier in tiers):
            raise ValueError("Tiers must be between 1 and 3")
    
    return {
        "specialization": specialization.strip(),
        "city": city.strip() if city else None,
        "country": "India",  # Default to India
        "tiers": tiers
    }

def validate_doctor_data(doctor: Dict) -> bool:
    """Validate doctor data structure.
    
    Args:
        doctor: Doctor data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        "name", "specialization", "city", "rating",
        "total_reviews", "locations", "contributing_sources",
        "profile_urls", "confidence_score", "timestamp"
    ]
    
    # Check required fields
    if not all(field in doctor for field in required_fields):
        return False
    
    # Validate field types
    try:
        assert isinstance(doctor["name"], str)
        assert isinstance(doctor["specialization"], str)
        assert isinstance(doctor["city"], str)
        assert isinstance(doctor["rating"], (int, float))
        assert isinstance(doctor["total_reviews"], int)
        assert isinstance(doctor["locations"], list)
        assert isinstance(doctor["contributing_sources"], list)
        assert isinstance(doctor["profile_urls"], dict)
        assert isinstance(doctor["confidence_score"], (int, float))
        assert isinstance(doctor["timestamp"], str)  # ISO format string
        return True
    except AssertionError:
        return False

