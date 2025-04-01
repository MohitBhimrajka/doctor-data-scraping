import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from ..services.verification import DoctorVerificationService
from ..models.doctor import Doctor
from ..utils.gemini_client import GeminiClient

@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client."""
    client = MagicMock(spec=GeminiClient)
    client.generate_content_async = AsyncMock()
    return client

@pytest.fixture
def verification_service(mock_gemini_client):
    """Create a DoctorVerificationService with mock dependencies."""
    return DoctorVerificationService(client=mock_gemini_client)

@pytest.fixture
def sample_doctor():
    """Create a sample doctor for testing."""
    return Doctor(
        id="doc123",
        name="Dr. John Doe",
        specialization="Cardiologist",
        city="Mumbai",
        city_tier=1,
        rating=4.5,
        total_reviews=100,
        locations=["Hospital A", "Clinic B"],
        contributing_sources=["practo", "google"],
        profile_urls={},
        confidence_score=0.0,
        timestamp=datetime.now()
    )

@pytest.mark.asyncio
async def test_verify_doctor(verification_service, sample_doctor):
    """Test verifying a doctor."""
    # Mock the Gemini client response
    mock_response = """
    name: Dr. John Doe
    specialization: Cardiologist
    rating: 4.8
    total_reviews: 150
    locations: Hospital A, Clinic B, Clinic C
    """

    verification_service.client.generate = AsyncMock(return_value=mock_response)

    # Verify doctor
    verified_doctor = await verification_service.verify_doctor(
        doctor=sample_doctor,
        sources=["practo", "google"]
    )

    # Verify doctor data was updated
    assert verified_doctor.name == "Dr. John Doe"
    assert verified_doctor.specialization == "Cardiologist"
    assert verified_doctor.rating == 4.8
    assert verified_doctor.total_reviews == 150
    assert len(verified_doctor.locations) == 3

@pytest.mark.asyncio
async def test_verify_doctor_error_handling(verification_service, sample_doctor):
    """Test error handling during doctor verification."""
    verification_service.client.generate = AsyncMock(side_effect=Exception("API Error"))

    # Verify doctor should handle error gracefully
    verified_doctor = await verification_service.verify_doctor(
        doctor=sample_doctor,
        sources=["practo", "google"]
    )

    # Original doctor data should be preserved
    assert verified_doctor.name == sample_doctor.name
    assert verified_doctor.specialization == sample_doctor.specialization
    assert verified_doctor.rating == sample_doctor.rating
    assert verified_doctor.total_reviews == sample_doctor.total_reviews

def test_calculate_confidence_score(verification_service):
    """Test confidence score calculation."""
    # Test high confidence doctor
    high_confidence_doctor = Doctor(
        id="doc1",
        name="Dr. High Confidence",
        specialization="Cardiologist",
        city="Mumbai",
        city_tier=1,
        rating=4.8,
        total_reviews=1000,
        locations=["Hospital A", "Clinic B"],
        contributing_sources=["practo", "google", "justdial"],
        profile_urls={
            "practo": "https://practo.com/doctor/high-confidence",
            "google": "https://g.page/doctor-high-confidence"
        },
        confidence_score=0.0,
        timestamp=datetime.now()
    )

    high_score = verification_service.calculate_confidence_score(high_confidence_doctor)
    assert high_score > 0.8

    # Test low confidence doctor
    low_confidence_doctor = Doctor(
        id="doc2",
        name="Dr. Low Confidence",
        specialization="Cardiologist",
        city="Mumbai",
        city_tier=1,
        rating=3.0,
        total_reviews=10,
        locations=["Hospital A"],
        contributing_sources=["practo"],
        profile_urls={},
        confidence_score=0.0,
        timestamp=datetime.now()
    )

    low_score = verification_service.calculate_confidence_score(low_confidence_doctor)
    assert low_score < 0.5

def test_build_verification_prompt(verification_service, sample_doctor):
    """Test building verification prompt."""
    prompt = verification_service._build_verification_prompt(
        doctor=sample_doctor,
        sources=["practo", "google"]
    )

    # Verify prompt contains all necessary information
    assert sample_doctor.name in prompt
    assert sample_doctor.specialization in prompt
    assert sample_doctor.city in prompt
    assert str(sample_doctor.rating) in prompt
    assert str(sample_doctor.total_reviews) in prompt
    assert all(location in prompt for location in sample_doctor.locations)
    assert all(source in prompt for source in ["practo", "google"])

def test_parse_verification_response(verification_service):
    """Test parsing verification response."""
    response = """
    name: Dr. John Doe
    specialization: Cardiologist
    rating: 4.8
    total_reviews: 150
    locations: Hospital A, Clinic B, Clinic C
    """

    parsed_data = verification_service._parse_verification_response(response)

    assert parsed_data["name"] == "Dr. John Doe"
    assert parsed_data["specialization"] == "Cardiologist"
    assert parsed_data["rating"] == 4.8
    assert parsed_data["total_reviews"] == 150
    assert len(parsed_data["locations"]) == 3

def test_parse_verification_response_error_handling(verification_service):
    """Test error handling in response parsing."""
    # Test invalid response format
    invalid_response = "Invalid format"
    parsed_data = verification_service._parse_verification_response(invalid_response)
    assert parsed_data == {}

    # Test missing fields
    incomplete_response = """
    name: Dr. John Doe
    rating: 4.8
    """
    parsed_data = verification_service._parse_verification_response(incomplete_response)
    assert "name" in parsed_data
    assert "rating" in parsed_data
    assert "specialization" not in parsed_data

def test_update_doctor(verification_service, sample_doctor):
    """Test updating doctor with verified data."""
    verified_data = {
        "name": "Dr. John Smith",
        "specialization": "Cardiologist",
        "rating": 4.8,
        "total_reviews": 150,
        "locations": ["Hospital A", "Clinic B", "Clinic C"]
    }

    verification_service._update_doctor(sample_doctor, verified_data)

    assert sample_doctor.name == "Dr. John Smith"
    assert sample_doctor.rating == 4.8
    assert sample_doctor.total_reviews == 150
    assert len(sample_doctor.locations) == 3

def test_calculate_rating_consistency(verification_service):
    """Test rating consistency calculation."""
    # Test high consistency
    high_consistency_doctor = Doctor(
        id="doc1",
        name="Dr. High Consistency",
        specialization="Cardiologist",
        city="Mumbai",
        city_tier=1,
        rating=4.8,
        total_reviews=1000,
        locations=["Hospital A"],
        contributing_sources=["practo"],
        profile_urls={},
        confidence_score=0.0,
        timestamp=datetime.now()
    )

    high_score = verification_service._calculate_rating_consistency(high_consistency_doctor)
    assert high_score > 0.8

    # Test low consistency
    low_consistency_doctor = Doctor(
        id="doc2",
        name="Dr. Low Consistency",
        specialization="Cardiologist",
        city="Mumbai",
        city_tier=1,
        rating=2.5,
        total_reviews=10,
        locations=["Hospital A"],
        contributing_sources=["practo"],
        profile_urls={},
        confidence_score=0.0,
        timestamp=datetime.now()
    )

    low_score = verification_service._calculate_rating_consistency(low_consistency_doctor)
    assert low_score < 0.5

def test_check_priority_sources(verification_service):
    """Test checking priority sources."""
    # Test with priority sources
    priority_doctor = Doctor(
        id="doc1",
        name="Dr. Priority",
        specialization="Cardiologist",
        city="Mumbai",
        rating=4.5,
        total_reviews=100,
        locations=["Hospital A"],
        contributing_sources=["practo", "google"]
    )
    
    priority_score = verification_service._check_priority_sources(priority_doctor)
    assert priority_score == 1.0
    
    # Test with mixed sources
    mixed_doctor = Doctor(
        id="doc2",
        name="Dr. Mixed",
        specialization="Cardiologist",
        city="Mumbai",
        rating=4.5,
        total_reviews=100,
        locations=["Hospital B"],
        contributing_sources=["practo", "other"]
    )
    
    mixed_score = verification_service._check_priority_sources(mixed_doctor)
    assert 0 < mixed_score < 1.0
    
    # Test with no priority sources
    non_priority_doctor = Doctor(
        id="doc3",
        name="Dr. Non Priority",
        specialization="Cardiologist",
        city="Mumbai",
        rating=4.5,
        total_reviews=100,
        locations=["Hospital C"],
        contributing_sources=["other"]
    )
    
    non_priority_score = verification_service._check_priority_sources(non_priority_doctor)
    assert non_priority_score == 0.0 