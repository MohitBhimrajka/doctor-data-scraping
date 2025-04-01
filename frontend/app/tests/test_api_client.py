import pytest
from unittest.mock import patch, MagicMock
import httpx
from datetime import datetime
from ..services.api_client import APIClient

@pytest.fixture
def mock_httpx():
    """Mock httpx client."""
    with patch('httpx.AsyncClient') as mock_client:
        yield mock_client

@pytest.fixture
def api_client(mock_httpx):
    """Create API client with mocked httpx."""
    client = APIClient()
    yield client
    client.close()

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

@pytest.mark.asyncio
async def test_search_doctors(api_client, mock_httpx, sample_doctor):
    """Test searching doctors."""
    # Setup
    mock_response = MagicMock()
    mock_response.json.return_value = {'doctors': [sample_doctor]}
    mock_response.status_code = 200
    mock_httpx.return_value.get.return_value.__aenter__.return_value = mock_response
    
    # Execute
    result = await api_client.search_doctors(
        specialization='Cardiologist',
        city='Mumbai',
        country='India',
        tiers=[1, 2],
        page=1,
        page_size=10
    )
    
    # Verify
    assert result['doctors'] == [sample_doctor]
    mock_httpx.return_value.get.assert_called_once()

@pytest.mark.asyncio
async def test_get_doctor(api_client, mock_httpx, sample_doctor):
    """Test getting doctor details."""
    # Setup
    mock_response = MagicMock()
    mock_response.json.return_value = sample_doctor
    mock_response.status_code = 200
    mock_httpx.return_value.get.return_value.__aenter__.return_value = mock_response
    
    # Execute
    result = await api_client.get_doctor('1')
    
    # Verify
    assert result == sample_doctor
    mock_httpx.return_value.get.assert_called_once()

@pytest.mark.asyncio
async def test_get_stats(api_client, mock_httpx, sample_stats):
    """Test getting statistics."""
    # Setup
    mock_response = MagicMock()
    mock_response.json.return_value = sample_stats
    mock_response.status_code = 200
    mock_httpx.return_value.get.return_value.__aenter__.return_value = mock_response
    
    # Execute
    result = await api_client.get_stats()
    
    # Verify
    assert result == sample_stats
    mock_httpx.return_value.get.assert_called_once()

@pytest.mark.asyncio
async def test_search_doctors_404(api_client, mock_httpx):
    """Test handling 404 error in search."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_httpx.return_value.get.return_value.__aenter__.return_value = mock_response
    
    # Execute
    result = await api_client.search_doctors(specialization='Invalid')
    
    # Verify
    assert result['doctors'] == []
    mock_httpx.return_value.get.assert_called_once()

@pytest.mark.asyncio
async def test_get_doctor_404(api_client, mock_httpx):
    """Test handling 404 error in get doctor."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_httpx.return_value.get.return_value.__aenter__.return_value = mock_response
    
    # Execute and verify
    with pytest.raises(ValueError, match="Doctor not found"):
        await api_client.get_doctor('invalid_id')

@pytest.mark.asyncio
async def test_search_doctors_error(api_client, mock_httpx):
    """Test handling general error in search."""
    # Setup
    mock_httpx.return_value.get.side_effect = httpx.RequestError("Network error")
    
    # Execute
    result = await api_client.search_doctors(specialization='Cardiologist')
    
    # Verify
    assert result['doctors'] == []
    mock_httpx.return_value.get.assert_called_once()

@pytest.mark.asyncio
async def test_get_doctor_error(api_client, mock_httpx):
    """Test handling general error in get doctor."""
    # Setup
    mock_httpx.return_value.get.side_effect = httpx.RequestError("Network error")
    
    # Execute and verify
    with pytest.raises(Exception, match="Network error"):
        await api_client.get_doctor('1')

@pytest.mark.asyncio
async def test_get_stats_error(api_client, mock_httpx):
    """Test handling general error in get stats."""
    # Setup
    mock_httpx.return_value.get.side_effect = httpx.RequestError("Network error")
    
    # Execute and verify
    with pytest.raises(Exception, match="Network error"):
        await api_client.get_stats() 