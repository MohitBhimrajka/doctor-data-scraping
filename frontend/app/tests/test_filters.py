import pytest
from unittest.mock import patch, MagicMock
import streamlit as st
from ..components.filters import render_filters, apply_filters

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit components."""
    with patch('streamlit.selectbox') as mock_selectbox, \
         patch('streamlit.slider') as mock_slider, \
         patch('streamlit.number_input') as mock_number_input, \
         patch('streamlit.date_input') as mock_date_input, \
         patch('streamlit.checkbox') as mock_checkbox:
        yield {
            'selectbox': mock_selectbox,
            'slider': mock_slider,
            'number_input': mock_number_input,
            'date_input': mock_date_input,
            'checkbox': mock_checkbox
        }

@pytest.fixture
def sample_doctors():
    """Sample doctor data for testing."""
    return [
        {
            'id': '1',
            'name': 'Dr. A',
            'rating': 4.5,
            'reviews': 100,
            'confidence': 0.8,
            'city_tier': 1,
            'last_updated': '2024-01-01'
        },
        {
            'id': '2',
            'name': 'Dr. B',
            'rating': 3.8,
            'reviews': 50,
            'confidence': 0.6,
            'city_tier': 2,
            'last_updated': '2024-01-02'
        }
    ]

def test_render_filters(mock_streamlit):
    """Test rendering filters component."""
    # Setup
    mock_streamlit['selectbox'].return_value = "Rating (High to Low)"
    mock_streamlit['slider'].side_effect = [4.0, 0.7]
    mock_streamlit['number_input'].return_value = 10
    mock_streamlit['date_input'].return_value = ['2024-01-01', '2024-01-31']
    mock_streamlit['checkbox'].return_value = True
    
    # Execute
    render_filters()
    
    # Verify
    mock_streamlit['selectbox'].assert_called_once()
    assert mock_streamlit['slider'].call_count == 2
    mock_streamlit['number_input'].assert_called_once()
    mock_streamlit['date_input'].assert_called_once()
    mock_streamlit['checkbox'].assert_called_once()

def test_apply_filters_rating(sample_doctors):
    """Test applying rating filter."""
    # Setup
    st.session_state.min_rating = 4.0
    
    # Execute
    filtered_results = apply_filters(sample_doctors)
    
    # Verify
    assert len(filtered_results) == 1
    assert filtered_results[0]['name'] == 'Dr. A'

def test_apply_filters_confidence(sample_doctors):
    """Test applying confidence filter."""
    # Setup
    st.session_state.min_confidence = 0.7
    
    # Execute
    filtered_results = apply_filters(sample_doctors)
    
    # Verify
    assert len(filtered_results) == 1
    assert filtered_results[0]['name'] == 'Dr. A'

def test_apply_filters_city_tier(sample_doctors):
    """Test applying city tier filter."""
    # Setup
    st.session_state.selected_tiers = [1]
    
    # Execute
    filtered_results = apply_filters(sample_doctors)
    
    # Verify
    assert len(filtered_results) == 1
    assert filtered_results[0]['name'] == 'Dr. A'

def test_apply_filters_date_range(sample_doctors):
    """Test applying date range filter."""
    # Setup
    st.session_state.date_range = ['2024-01-01', '2024-01-01']
    
    # Execute
    filtered_results = apply_filters(sample_doctors)
    
    # Verify
    assert len(filtered_results) == 1
    assert filtered_results[0]['name'] == 'Dr. A'

def test_apply_filters_multiple(sample_doctors):
    """Test applying multiple filters."""
    # Setup
    st.session_state.min_rating = 4.0
    st.session_state.min_confidence = 0.7
    st.session_state.selected_tiers = [1]
    
    # Execute
    filtered_results = apply_filters(sample_doctors)
    
    # Verify
    assert len(filtered_results) == 1
    assert filtered_results[0]['name'] == 'Dr. A' 