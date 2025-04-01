import pytest
from datetime import datetime
from ..utils.formatting import format_doctor_data, format_excel_data, format_stats
from ..utils.validation import validate_search_inputs, validate_doctor_data

@pytest.fixture
def sample_doctor():
    """Sample doctor data for testing."""
    return {
        'id': '1',
        'name': 'Dr. A',
        'specialization': 'Cardiologist',
        'city': 'Mumbai',
        'rating': 4.5,
        'reviews': 100,
        'confidence': 0.8,
        'city_tier': 1,
        'locations': ['Hospital A', 'Hospital B'],
        'sources': ['Source 1', 'Source 2'],
        'last_updated': '2024-01-01T00:00:00Z'
    }

@pytest.fixture
def sample_stats():
    """Sample statistics data for testing."""
    return {
        'total_doctors': 1000,
        'total_specializations': 50,
        'total_cities': 100,
        'average_rating': 4.2,
        'average_reviews': 75,
        'top_specializations': [
            {'name': 'Cardiologist', 'count': 100},
            {'name': 'Dentist', 'count': 80}
        ],
        'top_cities': [
            {'name': 'Mumbai', 'count': 150},
            {'name': 'Delhi', 'count': 120}
        ]
    }

def test_format_doctor_data(sample_doctor):
    """Test formatting doctor data for display."""
    # Execute
    formatted = format_doctor_data(sample_doctor)
    
    # Verify
    assert formatted['Name'] == 'Dr. A'
    assert formatted['Specialization'] == 'Cardiologist'
    assert formatted['City'] == 'Mumbai'
    assert formatted['Rating'] == 4.5
    assert formatted['Reviews'] == 100
    assert formatted['Confidence'] == '80%'
    assert formatted['Locations'] == 'Hospital A, Hospital B'
    assert formatted['Sources'] == 'Source 1, Source 2'
    assert isinstance(formatted['Last Updated'], datetime)

def test_format_excel_data(sample_doctor):
    """Test formatting doctor data for Excel export."""
    # Execute
    formatted = format_excel_data([sample_doctor])[0]
    
    # Verify
    assert formatted['Name'] == 'Dr. A'
    assert formatted['Specialization'] == 'Cardiologist'
    assert formatted['City'] == 'Mumbai'
    assert formatted['City Tier'] == 'Tier 1'
    assert formatted['Rating'] == 4.5
    assert formatted['Reviews'] == 100
    assert formatted['Confidence'] == 0.8
    assert formatted['Locations'] == 'Hospital A, Hospital B'
    assert formatted['Sources'] == 'Source 1, Source 2'
    assert formatted['Profile URLs'] == 'Source 1, Source 2'

def test_format_stats(sample_stats):
    """Test formatting statistics data."""
    # Execute
    formatted = format_stats(sample_stats)
    
    # Verify
    assert formatted['Total Doctors'] == 1000
    assert formatted['Total Specializations'] == 50
    assert formatted['Total Cities'] == 100
    assert formatted['Average Rating'] == 4.2
    assert formatted['Average Reviews'] == 75
    assert formatted['Top Specializations'] == 'Cardiologist (100), Dentist (80)'
    assert formatted['Top Cities'] == 'Mumbai (150), Delhi (120)'

def test_validate_search_inputs_single_city():
    """Test validating search inputs for single city mode."""
    # Execute
    validated = validate_search_inputs(
        specialization='Cardiologist',
        city='Mumbai',
        country='India'
    )
    
    # Verify
    assert validated['specialization'] == 'Cardiologist'
    assert validated['city'] == 'Mumbai'
    assert validated['country'] == 'India'
    assert 'tiers' not in validated

def test_validate_search_inputs_country_wide():
    """Test validating search inputs for country-wide mode."""
    # Execute
    validated = validate_search_inputs(
        specialization='Cardiologist',
        country='India',
        tiers=[1, 2]
    )
    
    # Verify
    assert validated['specialization'] == 'Cardiologist'
    assert validated['country'] == 'India'
    assert validated['tiers'] == [1, 2]
    assert 'city' not in validated

def test_validate_search_inputs_invalid():
    """Test validating invalid search inputs."""
    # Test invalid specialization
    with pytest.raises(ValueError, match="Specialization must be at least 3 characters"):
        validate_search_inputs(specialization='C', city='Mumbai', country='India')
    
    # Test invalid city
    with pytest.raises(ValueError, match="City must be at least 2 characters"):
        validate_search_inputs(specialization='Cardiologist', city='M', country='India')
    
    # Test invalid country
    with pytest.raises(ValueError, match="Only India is supported"):
        validate_search_inputs(specialization='Cardiologist', city='Mumbai', country='USA')
    
    # Test invalid tiers
    with pytest.raises(ValueError, match="Tiers must be integers between 1 and 3"):
        validate_search_inputs(specialization='Cardiologist', country='India', tiers=[0, 4])

def test_validate_doctor_data_valid(sample_doctor):
    """Test validating valid doctor data."""
    # Execute
    is_valid = validate_doctor_data(sample_doctor)
    
    # Verify
    assert is_valid is True

def test_validate_doctor_data_invalid():
    """Test validating invalid doctor data."""
    # Test missing required field
    invalid_doctor = {
        'id': '1',
        'name': 'Dr. A',
        'specialization': 'Cardiologist'
    }
    assert validate_doctor_data(invalid_doctor) is False
    
    # Test invalid type
    invalid_doctor = {
        'id': '1',
        'name': 'Dr. A',
        'specialization': 'Cardiologist',
        'city': 'Mumbai',
        'rating': '4.5',  # Should be float
        'reviews': 100,
        'confidence': 0.8,
        'city_tier': 1,
        'locations': ['Hospital A'],
        'sources': ['Source 1'],
        'last_updated': '2024-01-01T00:00:00Z'
    }
    assert validate_doctor_data(invalid_doctor) is False 