import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from ..services.discovery import DoctorDiscoveryService
from ..services.city_service import CityService
from ..services.verification import DoctorVerificationService
from ..models.doctor import Doctor
from ..models.city import CityInfo
from ..utils.gemini_client import GeminiClient

@pytest.fixture
def mock_city_service():
    """Create a mock city service."""
    service = MagicMock(spec=CityService)
    service.get_city_by_name.return_value = CityInfo(
        name="Mumbai",
        state="Maharashtra",
        country="India",
        population=12478447,
        coordinates={"latitude": 19.0760, "longitude": 72.8777},
        tier=1,
        is_capital=False,
        hospitals=["Hospital A", "Hospital B"],
        specialties=["Cardiology", "Neurology"]
    )
    return service

@pytest.fixture
def mock_verification_service():
    """Create a mock verification service."""
    service = MagicMock(spec=DoctorVerificationService)
    return service

@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client."""
    client = MagicMock(spec=GeminiClient)
    client.generate_content_async = AsyncMock()
    return client

@pytest.fixture
def discovery_service(mock_city_service, mock_verification_service, mock_gemini_client):
    """Create a DoctorDiscoveryService with mock dependencies."""
    return DoctorDiscoveryService(
        city_service=mock_city_service,
        verification_service=mock_verification_service,
        client=mock_gemini_client
    )

@pytest.mark.asyncio
async def test_search_doctors(discovery_service):
    """Test searching for doctors."""
    # Mock the Gemini client response
    mock_response = """
    [
        {
            "name": "Dr. John Doe",
            "specialization": "Cardiologist",
            "city": "Mumbai",
            "rating": 4.5,
            "total_reviews": 100,
            "locations": ["Hospital A", "Clinic B"],
            "contributing_sources": ["practo"],
            "profile_urls": {
                "practo": "https://practo.com/doctor/john-doe"
            }
        },
        {
            "name": "Dr. Jane Smith",
            "specialization": "Cardiologist",
            "city": "Mumbai",
            "rating": 4.8,
            "total_reviews": 150,
            "locations": ["Hospital C"],
            "contributing_sources": ["google"],
            "profile_urls": {
                "google": "https://g.page/jane-smith"
            }
        }
    ]
    """

    # Mock parse_response to return actual dictionaries instead of strings
    discovery_service.client.parse_response = lambda x: [
        {
            "name": "Dr. John Doe",
            "specialization": "Cardiologist",
            "city": "Mumbai",
            "rating": 4.5,
            "total_reviews": 100,
            "locations": ["Hospital A", "Clinic B"],
            "contributing_sources": ["practo"],
            "profile_urls": {
                "practo": "https://practo.com/doctor/john-doe"
            }
        },
        {
            "name": "Dr. Jane Smith",
            "specialization": "Cardiologist",
            "city": "Mumbai",
            "rating": 4.8,
            "total_reviews": 150,
            "locations": ["Hospital C"],
            "contributing_sources": ["google"],
            "profile_urls": {
                "google": "https://g.page/jane-smith"
            }
        }
    ]
    discovery_service.client.generate_structured = AsyncMock(return_value=mock_response)

    # Override the _get_search_sources method for test
    discovery_service._get_search_sources = lambda: ["test-source"]
    
    # Search for doctors with test_mode enabled
    doctors = await discovery_service.search_doctors(
        specialization="Cardiologist",
        city="Mumbai",
        test_mode=True
    )

    # Verify results
    assert len(doctors) == 2
    assert doctors[0].name == "Dr. John Doe"
    assert doctors[1].name == "Dr. Jane Smith"

def test_build_search_query(discovery_service):
    """Test building search query."""
    query = discovery_service._build_search_query(
        specialization="Cardiologist",
        city="Mumbai",
        country="India"
    )
    assert "Cardiologist" in query
    assert "Mumbai" in query
    assert "India" in query

@pytest.mark.asyncio
async def test_process_source(discovery_service):
    """Test processing a single source."""
    # Mock the Gemini client response
    mock_response = """
    [
        {
            "name": "Dr. John Doe",
            "specialization": "Cardiologist",
            "city": "Mumbai",
            "rating": 4.5,
            "total_reviews": 100,
            "locations": ["Hospital A", "Clinic B"],
            "contributing_sources": ["practo"],
            "profile_urls": {
                "practo": "https://practo.com/doctor/john-doe"
            }
        }
    ]
    """

    # Mock parse_response to return actual dictionaries instead of strings
    discovery_service.client.parse_response = lambda x: [
        {
            "name": "Dr. John Doe",
            "specialization": "Cardiologist",
            "city": "Mumbai",
            "rating": 4.5,
            "total_reviews": 100,
            "locations": ["Hospital A", "Clinic B"],
            "contributing_sources": ["practo"],
            "profile_urls": {
                "practo": "https://practo.com/doctor/john-doe"
            }
        }
    ]
    discovery_service.client.generate_structured = AsyncMock(return_value=mock_response)

    # Process source
    doctors = await discovery_service.process_source(
        source="practo",
        query="Find doctors in Mumbai"
    )

    # Verify results
    assert len(doctors) == 1
    assert doctors[0].name == "Dr. John Doe"
    assert doctors[0].specialization == "Cardiologist"

@pytest.mark.asyncio
async def test_process_source_error_handling(discovery_service):
    """Test error handling in source processing."""
    discovery_service.client.generate_structured = AsyncMock(side_effect=Exception("API Error"))

    # Process source should handle error gracefully
    doctors = await discovery_service.process_source(
        source="practo",
        query="Find doctors in Mumbai"
    )

    assert len(doctors) == 0

def test_parse_source_response(discovery_service):
    """Test parsing source response."""
    response = """
    [
        {
            "name": "Dr. John Doe",
            "specialization": "Cardiologist",
            "city": "Mumbai",
            "rating": 4.5,
            "total_reviews": 100,
            "locations": ["Hospital A", "Clinic B"],
            "contributing_sources": ["practo"],
            "profile_urls": {
                "practo": "https://practo.com/doctor/john-doe"
            }
        }
    ]
    """

    # Mock parse_response to return actual dictionaries
    discovery_service.client.parse_response = lambda x: [
        {
            "name": "Dr. John Doe",
            "specialization": "Cardiologist",
            "city": "Mumbai",
            "rating": 4.5,
            "total_reviews": 100,
            "locations": ["Hospital A", "Clinic B"],
            "contributing_sources": ["practo"],
            "profile_urls": {
                "practo": "https://practo.com/doctor/john-doe"
            }
        }
    ]

    doctors = discovery_service._parse_source_response(response, "practo")

    assert len(doctors) == 1
    assert doctors[0].name == "Dr. John Doe"
    assert doctors[0].specialization == "Cardiologist"

def test_extract_doctor_info(discovery_service):
    """Test extracting doctor information."""
    data = {
        "name": "Dr. John Doe",
        "specialization": "Cardiologist",
        "city": "Mumbai",
        "rating": 4.5,
        "total_reviews": 100,
        "locations": ["Hospital A", "Clinic B"],
        "contributing_sources": ["practo"],
        "profile_urls": {
            "practo": "https://practo.com/doctor/john-doe"
        }
    }

    doctor = discovery_service._extract_doctor_info(data, "practo")

    assert doctor is not None
    assert hasattr(doctor, 'name')
    assert doctor.name == "Dr. John Doe"
    assert doctor.specialization == "Cardiologist"
    assert doctor.city == "Mumbai"
    assert doctor.rating == 4.5
    assert doctor.total_reviews == 100
    assert "practo" in doctor.profile_urls

def test_get_search_sources(discovery_service):
    """Test getting search sources."""
    sources = discovery_service._get_search_sources()
    
    assert isinstance(sources, list)
    assert len(sources) > 0
    assert all(isinstance(source, str) for source in sources)
    assert any("practo" in source.lower() for source in sources)
    assert any("google" in source.lower() for source in sources)

def test_parse_source_response_error_handling(discovery_service):
    """Test error handling in response parsing."""
    # Test invalid JSON
    invalid_response = "Invalid JSON"
    doctors = discovery_service._parse_source_response(invalid_response, "practo")
    assert isinstance(doctors, list)
    assert len(doctors) == 0
    
    # Test missing required fields
    incomplete_response = """
    [
        {
            "name": "Dr. John Doe",
            "rating": 4.5
        }
    ]
    """
    doctors = discovery_service._parse_source_response(incomplete_response, "practo")
    assert isinstance(doctors, list)
    assert len(doctors) == 0

def test_extract_doctor_info_error_handling(discovery_service):
    """Test error handling in doctor info extraction."""
    # Test missing required fields
    incomplete_data = {
        "name": "Dr. John Doe",
        "rating": 4.5
    }
    
    doctor = discovery_service._extract_doctor_info(incomplete_data, "practo")
    assert doctor is None
    
    # Test invalid rating
    invalid_data = {
        "name": "Dr. John Doe",
        "specialization": "Cardiologist",
        "city": "Mumbai",
        "rating": 6.0,  # Invalid rating
        "reviews": 100,
        "locations": ["Hospital A"],
        "contributing_sources": ["practo"]
    }
    
    doctor = discovery_service._extract_doctor_info(invalid_data, "practo")
    assert doctor is None 