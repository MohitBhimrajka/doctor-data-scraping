from typing import Dict, List, Optional
from ..models.city import CityInfo

class CityCache:
    def __init__(self):
        self._name_cache: Dict[str, CityInfo] = {}
        self._state_cache: Dict[str, List[CityInfo]] = {}
        self._tier_cache: Dict[int, List[CityInfo]] = {}
        self._capital_cities: Optional[List[CityInfo]] = None
        
    def add_city(self, city: CityInfo) -> None:
        """Add a city to all relevant caches."""
        # Add to name cache (including aliases)
        self._name_cache[city.name.lower()] = city
        for alias in city.aliases:
            self._name_cache[alias.lower()] = city
            
        # Add to state cache
        state_key = city.state.lower()
        if state_key not in self._state_cache:
            self._state_cache[state_key] = []
        self._state_cache[state_key].append(city)
        
        # Add to tier cache
        if city.tier not in self._tier_cache:
            self._tier_cache[city.tier] = []
        self._tier_cache[city.tier].append(city)
        
        # Reset capital cities cache
        self._capital_cities = None
        
    def get_city_by_name(self, name: str) -> Optional[CityInfo]:
        """Get city by name or alias from cache."""
        return self._name_cache.get(name.lower())
        
    def get_cities_by_state(self, state: str) -> List[CityInfo]:
        """Get cities by state from cache."""
        return self._state_cache.get(state.lower(), [])
        
    def get_cities_by_tier(self, tier: int) -> List[CityInfo]:
        """Get cities by tier from cache."""
        return self._tier_cache.get(tier, [])
        
    def get_capital_cities(self) -> List[CityInfo]:
        """Get capital cities from cache."""
        if self._capital_cities is None:
            self._capital_cities = [
                city for city in self._name_cache.values()
                if city.is_capital
            ]
        return self._capital_cities
        
    def clear(self) -> None:
        """Clear all caches."""
        self._name_cache.clear()
        self._state_cache.clear()
        self._tier_cache.clear()
        self._capital_cities = None
        
    def is_empty(self) -> bool:
        """Check if cache is empty."""
        return len(self._name_cache) == 0 