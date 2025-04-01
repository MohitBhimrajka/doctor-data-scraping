import pytest
from pathlib import Path
import json
from datetime import datetime, timedelta
from ..services.database import DatabaseService
from ..models.doctor import Doctor

@pytest.fixture
def database_service(tmp_path):
    """Create a DatabaseService instance with temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return DatabaseService(data_dir=str(data_dir))

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
        profile_urls={"practo": "https://practo.com/doctor123", "google": "https://g.page/doctor123"}
    )

def test_save_and_get_doctor(database_service, sample_doctor):
    """Test saving and retrieving a doctor."""
    # Save doctor
    database_service.save_doctor(sample_doctor)
    
    # Get doctor
    retrieved_doctor = database_service.get_doctor(sample_doctor.id)
    
    # Verify doctor data
    assert retrieved_doctor is not None
    assert retrieved_doctor.id == sample_doctor.id
    assert retrieved_doctor.name == sample_doctor.name
    assert retrieved_doctor.specialization == sample_doctor.specialization
    assert retrieved_doctor.city == sample_doctor.city
    assert retrieved_doctor.rating == sample_doctor.rating
    assert retrieved_doctor.total_reviews == sample_doctor.total_reviews
    assert retrieved_doctor.locations == sample_doctor.locations
    assert retrieved_doctor.contributing_sources == sample_doctor.contributing_sources

def test_get_nonexistent_doctor(database_service):
    """Test retrieving a non-existent doctor."""
    doctor = database_service.get_doctor("nonexistent")
    assert doctor is None

def test_search_doctors(database_service):
    """Test searching doctors with various filters."""
    # Create sample doctors
    doctors = [
        Doctor(
            id=f"doc{i}",
            name=f"Dr. Doctor {i}",
            specialization="Cardiologist",
            city="Mumbai",
            city_tier=1,
            rating=4.5,
            total_reviews=100,
            locations=[f"Hospital {i}"],
            contributing_sources=["practo"],
            profile_urls={"practo": f"https://practo.com/doctor{i}"}
        )
        for i in range(5)
    ]
    
    # Add some variation
    doctors[1].specialization = "Neurologist"
    doctors[2].city = "Delhi"
    doctors[3].rating = 3.5
    doctors[4].total_reviews = 50
    
    # Print initial setup for debugging
    print("\nTest doctors setup:")
    for i, doctor in enumerate(doctors):
        print(f"Doctor {i}: spec={doctor.specialization}, city={doctor.city}, " +
              f"rating={doctor.rating}, reviews={doctor.total_reviews}")
    
    # Expected results for combined filter:
    # doc0: Cardiologist, Mumbai, 4.5 rating, 100 reviews - MATCH
    # doc1: Neurologist, Mumbai, 4.5 rating, 100 reviews - NO MATCH (wrong specialization)
    # doc2: Cardiologist, Delhi, 4.5 rating, 100 reviews - NO MATCH (wrong city)
    # doc3: Cardiologist, Mumbai, 3.5 rating, 100 reviews - NO MATCH (rating too low)
    # doc4: Cardiologist, Mumbai, 4.5 rating, 50 reviews - NO MATCH (not enough reviews)
    
    # Save all doctors
    for doctor in doctors:
        database_service.save_doctor(doctor)
    
    # Test specialization filter
    results = database_service.search_doctors(specialization="Cardiologist")
    assert len(results) == 4
    assert all(d.specialization == "Cardiologist" for d in results)
    
    # Test city filter
    results = database_service.search_doctors(city="Mumbai")
    assert len(results) == 4  # docs 0, 1, 3, 4 are in Mumbai
    assert all(d.city == "Mumbai" for d in results)
    
    # Test rating filter
    results = database_service.search_doctors(min_rating=4.0)
    assert len(results) == 4  # docs 0, 1, 2, 4 have rating >= 4.0
    assert all(d.rating >= 4.0 for d in results)
    
    # Test reviews filter
    results = database_service.search_doctors(min_reviews=75)
    assert len(results) == 4  # docs 0, 1, 2, 3 have reviews >= 75
    assert all(d.total_reviews >= 75 for d in results)
    
    # Test limit
    results = database_service.search_doctors(limit=2)
    assert len(results) == 2
    
    # Test combination of filters
    results = database_service.search_doctors(
        specialization="Cardiologist",
        city="Mumbai",
        min_rating=4.0,
        min_reviews=75
    )
    
    # Expected match is only doc0, since:
    # - doc0 meets all criteria
    # - doc1 is not a Cardiologist
    # - doc2 is not in Mumbai
    # - doc3 has rating < 4.0
    # - doc4 has reviews < 75
    print("\nExpected 1 match for combined filter (doc0).")
    print(f"Got {len(results)} matches.")
    
    for i, doc in enumerate(results):
        print(f"Result {i}: id={doc.id}, spec={doc.specialization}, city={doc.city}, " +
              f"rating={doc.rating}, reviews={doc.total_reviews}")
    
    assert len(results) == 1  # Only doc0 matches all criteria
    assert all(
        d.specialization == "Cardiologist"
        and d.city == "Mumbai"
        and d.rating >= 4.0
        and d.total_reviews >= 75
        for d in results
    )

def test_get_doctor_stats(database_service):
    """Test getting doctor statistics."""
    # Create sample doctors
    doctors = [
        Doctor(
            id=f"doc{i}",
            name=f"Dr. Doctor {i}",
            specialization="Cardiologist" if i % 2 == 0 else "Neurologist",
            city="Mumbai" if i % 3 == 0 else "Delhi",
            city_tier=1 if i % 3 == 0 else 2,
            rating=4.5,
            total_reviews=100,
            locations=[f"Hospital {i}"],
            contributing_sources=["practo"],
            profile_urls={"practo": f"https://practo.com/doctor{i}"}
        )
        for i in range(6)
    ]
    
    # Save all doctors
    for doctor in doctors:
        database_service.save_doctor(doctor)
    
    # Get stats
    stats = database_service.get_doctor_stats()
    
    # Verify stats
    assert stats["total_doctors"] == 6
    assert len(stats["specializations"]) == 2
    assert stats["specializations"]["Cardiologist"] == 3
    assert stats["specializations"]["Neurologist"] == 3
    assert len(stats["cities"]) == 2
    assert stats["cities"]["Mumbai"] == 2
    assert stats["cities"]["Delhi"] == 4
    assert stats["avg_rating"] == 4.5
    assert stats["avg_reviews"] == 100
    assert 0 <= stats["avg_confidence"] <= 1

def test_cleanup_old_data(database_service):
    """Test cleaning up old doctor data."""
    # Create sample doctors with different timestamps
    now = datetime.now()
    doctors = [
        Doctor(
            id=f"doc{i}",
            name=f"Dr. Doctor {i}",
            specialization="Cardiologist",
            city="Mumbai",
            city_tier=1,
            rating=4.5,
            total_reviews=100,
            locations=[f"Hospital {i}"],
            contributing_sources=["practo"],
            profile_urls={"practo": f"https://practo.com/doctor{i}"},
            timestamp=now - timedelta(days=i * 10)  # Each doctor is 10 days older than the previous
        )
        for i in range(5)
    ]
    
    # Save all doctors
    for doctor in doctors:
        database_service.save_doctor(doctor)
    
    # Clean up data older than 20 days
    database_service.cleanup_old_data(days=20)
    
    # Verify only recent doctors remain
    remaining_doctors = database_service.search_doctors()
    assert len(remaining_doctors) == 3  # Only doctors 0, 1, and 2 should remain
    assert all(
        (now - d.timestamp).days <= 20
        for d in remaining_doctors
    )

def test_persistence(database_service, sample_doctor):
    """Test data persistence between service instances."""
    # Save doctor with first instance
    database_service.save_doctor(sample_doctor)
    
    # Create new instance
    new_service = DatabaseService(data_dir=database_service.data_dir)
    
    # Retrieve doctor with new instance
    retrieved_doctor = new_service.get_doctor(sample_doctor.id)
    
    # Verify doctor data persisted
    assert retrieved_doctor is not None
    assert retrieved_doctor.id == sample_doctor.id
    assert retrieved_doctor.name == sample_doctor.name
    assert retrieved_doctor.specialization == sample_doctor.specialization
    assert retrieved_doctor.city == sample_doctor.city
    assert retrieved_doctor.rating == sample_doctor.rating
    assert retrieved_doctor.total_reviews == sample_doctor.total_reviews
    assert retrieved_doctor.locations == sample_doctor.locations
    assert retrieved_doctor.contributing_sources == sample_doctor.contributing_sources 