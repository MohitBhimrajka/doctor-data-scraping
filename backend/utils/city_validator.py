from typing import Dict, List, Any
from ..models.city import CityInfo

class CityValidator:
    @staticmethod
    def validate_city_data(city_data: Dict[str, Any]) -> List[str]:
        """Validate city data structure and return list of errors."""
        errors = []
        
        # Required fields
        required_fields = ['name', 'tier', 'state', 'population', 'is_capital']
        for field in required_fields:
            if field not in city_data:
                errors.append(f"Missing required field: {field}")
                
        # Field type validation
        if 'name' in city_data and not isinstance(city_data['name'], str):
            errors.append("Field 'name' must be a string")
            
        if 'tier' in city_data:
            if not isinstance(city_data['tier'], int):
                errors.append("Field 'tier' must be an integer")
            elif city_data['tier'] not in [1, 2, 3]:
                errors.append("Field 'tier' must be 1, 2, or 3")
                
        if 'state' in city_data and not isinstance(city_data['state'], str):
            errors.append("Field 'state' must be a string")
            
        if 'population' in city_data:
            if not isinstance(city_data['population'], int):
                errors.append("Field 'population' must be an integer")
            elif city_data['population'] <= 0:
                errors.append("Field 'population' must be positive")
                
        if 'is_capital' in city_data and not isinstance(city_data['is_capital'], bool):
            errors.append("Field 'is_capital' must be a boolean")
            
        if 'aliases' in city_data:
            if not isinstance(city_data['aliases'], list):
                errors.append("Field 'aliases' must be a list")
            elif not all(isinstance(alias, str) for alias in city_data['aliases']):
                errors.append("All aliases must be strings")
                
        return errors
        
    @staticmethod
    def validate_state_data(state_data: Dict[str, Any]) -> List[str]:
        """Validate state data structure and return list of errors."""
        errors = []
        
        # Required fields
        required_fields = ['capital', 'tier_1_cities', 'tier_2_cities', 'tier_3_cities']
        for field in required_fields:
            if field not in state_data:
                errors.append(f"Missing required field: {field}")
                
        # Field type validation
        if 'capital' in state_data and not isinstance(state_data['capital'], str):
            errors.append("Field 'capital' must be a string")
            
        for tier_field in ['tier_1_cities', 'tier_2_cities', 'tier_3_cities']:
            if tier_field in state_data:
                if not isinstance(state_data[tier_field], list):
                    errors.append(f"Field '{tier_field}' must be a list")
                elif not all(isinstance(city, str) for city in state_data[tier_field]):
                    errors.append(f"All cities in '{tier_field}' must be strings")
                    
        return errors
        
    @staticmethod
    def validate_city_info(city: CityInfo) -> List[str]:
        """Validate CityInfo object and return list of errors."""
        errors = []
        
        # Name validation
        if not city.name or not city.name.strip():
            errors.append("City name cannot be empty")
            
        # Tier validation
        if city.tier not in [1, 2, 3]:
            errors.append("City tier must be 1, 2, or 3")
            
        # State validation
        if not city.state or not city.state.strip():
            errors.append("State name cannot be empty")
            
        # Population validation
        if city.population <= 0:
            errors.append("Population must be positive")
            
        # Aliases validation
        if not all(alias.strip() for alias in city.aliases):
            errors.append("Aliases cannot contain empty strings")
            
        return errors 