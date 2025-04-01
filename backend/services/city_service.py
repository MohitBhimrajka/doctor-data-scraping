import json
from typing import List, Optional, Dict
from pathlib import Path
from models.city import CityInfo
from config import DATA_DIR

class CityService:
    def __init__(self, data_file: str = None):
        if data_file is None:
            data_file = str(Path(DATA_DIR) / "indian_cities.json")
        self.data_file = Path(data_file)
        self._load_data()
        
    def _load_data(self) -> None:
        """Load city data from JSON file."""
        if not self.data_file.exists():
            raise FileNotFoundError(f"City data file not found: {self.data_file}")
            
        with open(self.data_file, 'r') as f:
            data = json.load(f)
            self.cities = [CityInfo(**city) for city in data['cities']]
            self.states = data['states']
            
    def get_city_by_name(self, name: str) -> Optional[CityInfo]:
        """Get city information by name (case-insensitive)."""
        name = name.lower().strip()
        for city in self.cities:
            if (city.name.lower() == name or 
                name in [alias.lower() for alias in city.aliases]):
                return city
        return None
        
    def get_cities_by_state(self, state: str) -> List[CityInfo]:
        """Get all cities in a state."""
        state = state.lower().strip()
        return [city for city in self.cities 
                if city.state.lower() == state]
                
    def get_cities_by_tier(self, tier: int) -> List[CityInfo]:
        """Get all cities of a specific tier."""
        return [city for city in self.cities if city.tier == tier]
        
    def get_capital_cities(self) -> List[CityInfo]:
        """Get all capital cities."""
        return [city for city in self.cities if city.is_capital]
        
    def get_state_info(self, state: str) -> Optional[Dict]:
        """Get information about a state including its cities by tier."""
        state = state.lower().strip()
        for state_name, info in self.states.items():
            if state_name.lower() == state:
                return info
        return None
        
    def search_cities(self, query: str = "", state: str = None, tier: int = None, is_capital: bool = None) -> List[CityInfo]:
        """
        Search cities by query, state, tier, or capital status.
        
        Args:
            query: Text to search in name or alias (case-insensitive)
            state: Filter by state name
            tier: Filter by city tier
            is_capital: Filter by capital status
        
        Returns:
            List of matching cities
        """
        results = self.cities.copy()
        
        # Filter by query if provided
        if query:
            query = query.lower().strip()
            results = [
                city for city in results
                if (query in city.name.lower() or
                    any(query in alias.lower() for alias in city.aliases))
            ]
        
        # Filter by state if provided
        if state:
            state = state.lower().strip()
            results = [city for city in results if city.state.lower() == state]
        
        # Filter by tier if provided
        if tier is not None:
            results = [city for city in results if city.tier == tier]
        
        # Filter by capital status if provided
        if is_capital is not None:
            results = [city for city in results if city.is_capital == is_capital]
        
        return results
        
    def get_cities_by_population_range(self, min_population: int, max_population: int) -> List[CityInfo]:
        """Get cities within a specific population range."""
        return [city for city in self.cities 
                if min_population <= city.population <= max_population]
                
    def get_cities_by_tier_and_state(self, tier: int, state: str) -> List[CityInfo]:
        """Get cities of a specific tier in a state."""
        state = state.lower().strip()
        return [city for city in self.cities 
                if city.tier == tier and city.state.lower() == state] 