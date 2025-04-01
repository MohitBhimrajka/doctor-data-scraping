import pytest
from datetime import datetime
from ..models.doctor import Doctor

def test_doctor_creation():
    """Test creating a Doctor instance with valid data."""
    doctor = Doctor(
        id="doc123",
        name="Dr. John Doe",
        specialization="Cardiologist",
        city="Mumbai",
        rating=4.5,
        total_reviews=100,
        locations=["Hospital A", "Clinic B"],
        contributing_sources=["practo", "google"]
    )
    
    assert doctor.id == "doc123"
    assert doctor.name == "Dr. John Doe"
    assert doctor.specialization == "Cardiologist"
    assert doctor.city == "Mumbai"
    assert doctor.rating == 4.5
    assert doctor.total_reviews == 100
    assert doctor.locations == ["Hospital A", "Clinic B"]
    assert doctor.contributing_sources == ["practo", "google"]
    assert isinstance(doctor.timestamp, datetime)
    assert 0 <= doctor.confidence_score <= 1

def test_doctor_validation():
    """Test validation of Doctor fields."""
    # Test invalid rating
    with pytest.raises(ValueError):
        Doctor(
            id="doc123",
            name="Dr. John Doe",
            specialization="Cardiologist",
            city="Mumbai",
            rating=6.0,  # Invalid rating
            total_reviews=100,
            locations=["Hospital A"],
            contributing_sources=["practo"]
        )
    
    # Test negative reviews
    with pytest.raises(ValueError):
        Doctor(
            id="doc123",
            name="Dr. John Doe",
            specialization="Cardiologist",
            city="Mumbai",
            rating=4.5,
            total_reviews=-10,  # Invalid reviews
            locations=["Hospital A"],
            contributing_sources=["practo"]
        )
    
    # Test empty name
    with pytest.raises(ValueError):
        Doctor(
            id="doc123",
            name="",  # Invalid name
            specialization="Cardiologist",
            city="Mumbai",
            rating=4.5,
            total_reviews=100,
            locations=["Hospital A"],
            contributing_sources=["practo"]
        )

def test_doctor_serialization():
    """Test Doctor serialization to and from dictionary."""
    doctor = Doctor(
        id="doc123",
        name="Dr. John Doe",
        specialization="Cardiologist",
        city="Mumbai",
        rating=4.5,
        total_reviews=100,
        locations=["Hospital A", "Clinic B"],
        contributing_sources=["practo", "google"]
    )
    
    # Test to dict
    doctor_dict = doctor.dict()
    assert isinstance(doctor_dict, dict)
    assert doctor_dict["id"] == "doc123"
    assert doctor_dict["name"] == "Dr. John Doe"
    assert doctor_dict["specialization"] == "Cardiologist"
    assert doctor_dict["city"] == "Mumbai"
    assert doctor_dict["rating"] == 4.5
    assert doctor_dict["total_reviews"] == 100
    assert doctor_dict["locations"] == ["Hospital A", "Clinic B"]
    assert doctor_dict["contributing_sources"] == ["practo", "google"]
    assert "timestamp" in doctor_dict
    assert "confidence_score" in doctor_dict
    
    # Test from dict
    new_doctor = Doctor(**doctor_dict)
    assert new_doctor.id == doctor.id
    assert new_doctor.name == doctor.name
    assert new_doctor.specialization == doctor.specialization
    assert new_doctor.city == doctor.city
    assert new_doctor.rating == doctor.rating
    assert new_doctor.total_reviews == doctor.total_reviews
    assert new_doctor.locations == doctor.locations
    assert new_doctor.contributing_sources == doctor.contributing_sources
    assert new_doctor.timestamp == doctor.timestamp
    assert new_doctor.confidence_score == doctor.confidence_score

def test_doctor_update():
    """Test updating Doctor fields."""
    doctor = Doctor(
        id="doc123",
        name="Dr. John Doe",
        specialization="Cardiologist",
        city="Mumbai",
        rating=4.5,
        total_reviews=100,
        locations=["Hospital A"],
        contributing_sources=["practo"]
    )
    
    # Update fields
    doctor.name = "Dr. John Smith"
    doctor.rating = 4.8
    doctor.total_reviews = 150
    doctor.locations.append("Clinic B")
    doctor.contributing_sources.append("google")
    
    assert doctor.name == "Dr. John Smith"
    assert doctor.rating == 4.8
    assert doctor.total_reviews == 150
    assert doctor.locations == ["Hospital A", "Clinic B"]
    assert doctor.contributing_sources == ["practo", "google"]

def test_doctor_confidence_score():
    """Test confidence score calculation."""
    # Test with high confidence factors
    doctor = Doctor(
        id="doc123",
        name="Dr. John Doe",
        specialization="Cardiologist",
        city="Mumbai",
        rating=4.8,
        total_reviews=1000,
        locations=["Hospital A", "Clinic B"],
        contributing_sources=["practo", "google", "justdial"]
    )
    
    assert doctor.confidence_score > 0.8  # Should have high confidence
    
    # Test with low confidence factors
    doctor = Doctor(
        id="doc124",
        name="Dr. Jane Smith",
        specialization="Cardiologist",
        city="Mumbai",
        rating=3.5,
        total_reviews=10,
        locations=["Clinic C"],
        contributing_sources=["other"]
    )
    
    assert doctor.confidence_score < 0.5  # Should have lower confidence 