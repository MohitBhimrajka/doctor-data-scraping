import pytest
from pathlib import Path
import json
from ..services.city_service import CityService
from ..models.city import CityInfo

@pytest.fixture
def city_service():
    """Create a CityService instance with test data."""
    # Create temporary test data
    test_data = {
        "cities": [
            {
                "name": "Mumbai",
                "tier": 1,
                "state": "Maharashtra",
                "population": 20000000,
                "is_capital": False,
                "aliases": ["Bombay"]
            },
            {
                "name": "Delhi",
                "tier": 1,
                "state": "Delhi",
                "population": 19000000,
                "is_capital": True,
                "aliases": ["New Delhi"]
            },
            {
                "name": "Pune",
                "tier": 2,
                "state": "Maharashtra",
                "population": 7000000,
                "is_capital": False,
                "aliases": ["Poona"]
            }
        ],
        "states": {
            "Maharashtra": {
                "capital": "Mumbai",
                "population": 120000000,
                "tier_1_cities": ["Mumbai", "Pune"],
                "tier_2_cities": ["Nagpur", "Thane"]
            },
            "Delhi": {
                "capital": "Delhi",
                "population": 20000000,
                "tier_1_cities": ["Delhi"],
                "tier_2_cities": ["Gurgaon", "Noida"]
            }
        }
    }
    
    # Create temporary data file
    data_dir = Path("test_data")
    data_dir.mkdir(exist_ok=True)
    data_file = data_dir / "indian_cities.json"
    
    with open(data_file, "w") as f:
        json.dump(test_data, f)
    
    # Create service instance
    service = CityService(data_file=str(data_file))
    
    yield service
    
    # Cleanup
    data_file.unlink()
    data_dir.rmdir()

def test_get_city_info(city_service):
    """Test getting city information."""
    # Test existing city
    city = city_service.get_city_info("Mumbai")
    assert city is not None
    assert city.name == "Mumbai"
    assert city.tier == 1
    assert city.state == "Maharashtra"
    assert city.population == 20000000
    assert not city.is_capital
    assert "Bombay" in city.aliases
    
    # Test non-existent city
    city = city_service.get_city_info("NonExistentCity")
    assert city is None

def test_search_cities(city_service):
    """Test searching cities."""
    # Test by state
    cities = city_service.search_cities(state="Maharashtra")
    assert len(cities) == 2
    assert all(city.state == "Maharashtra" for city in cities)
    
    # Test by tier
    cities = city_service.search_cities(tier=1)
    assert len(cities) == 2
    assert all(city.tier == 1 for city in cities)
    
    # Test by capital status
    cities = city_service.search_cities(is_capital=True)
    assert len(cities) == 1
    assert cities[0].name == "Delhi"
    
    # Test combination of filters
    cities = city_service.search_cities(state="Maharashtra", tier=2)
    assert len(cities) == 1
    assert cities[0].name == "Pune"

def test_get_cities_by_tier(city_service):
    """Test getting cities by tier."""
    # Test tier 1 cities
    tier1_cities = city_service.get_cities_by_tier(1)
    assert len(tier1_cities) == 2
    assert all(city.tier == 1 for city in tier1_cities)
    
    # Test tier 2 cities
    tier2_cities = city_service.get_cities_by_tier(2)
    assert len(tier2_cities) == 1
    assert all(city.tier == 2 for city in tier2_cities)
    
    # Test non-existent tier
    tier3_cities = city_service.get_cities_by_tier(3)
    assert len(tier3_cities) == 0

def test_get_capital_cities(city_service):
    """Test getting capital cities."""
    capitals = city_service.get_capital_cities()
    assert len(capitals) == 1
    assert capitals[0].name == "Delhi"
    assert capitals[0].is_capital

def test_get_cities_by_state(city_service):
    """Test getting cities by state."""
    # Test existing state
    maharashtra_cities = city_service.get_cities_by_state("Maharashtra")
    assert len(maharashtra_cities) == 2
    assert all(city.state == "Maharashtra" for city in maharashtra_cities)
    
    # Test non-existent state
    non_existent_cities = city_service.get_cities_by_state("NonExistentState")
    assert len(non_existent_cities) == 0

def test_city_aliases(city_service):
    """Test city alias functionality."""
    # Test getting city by alias
    city = city_service.get_city_info("Bombay")
    assert city is not None
    assert city.name == "Mumbai"
    
    # Test getting city by another alias
    city = city_service.get_city_info("Poona")
    assert city is not None
    assert city.name == "Pune"

def test_city_cache(city_service):
    """Test city cache functionality."""
    # First call should load from file
    city1 = city_service.get_city_info("Mumbai")
    
    # Second call should use cache
    city2 = city_service.get_city_info("Mumbai")
    
    # Both should be the same object (cached)
    assert city1 is city2

def test_invalid_data_file():
    """Test handling of invalid data file."""
    with pytest.raises(FileNotFoundError):
        CityService(data_file="non_existent_file.json")
    
    # Test with invalid JSON
    data_dir = Path("test_data")
    data_dir.mkdir(exist_ok=True)
    data_file = data_dir / "invalid_cities.json"
    
    with open(data_file, "w") as f:
        f.write("invalid json")
    
    with pytest.raises(json.JSONDecodeError):
        CityService(data_file=str(data_file))
    
    # Cleanup
    data_file.unlink()
    data_dir.rmdir() 