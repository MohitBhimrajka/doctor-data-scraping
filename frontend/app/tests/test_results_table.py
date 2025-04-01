import pytest
from unittest.mock import patch, MagicMock
import streamlit as st
import pandas as pd
from ..components.results_table import render_results_table
from ..components.doctor_profile import render_doctor_profile, render_doctor_comparison

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit components."""
    with patch('streamlit.tabs') as mock_tabs, \
         patch('streamlit.dataframe') as mock_dataframe, \
         patch('streamlit.multiselect') as mock_multiselect, \
         patch('streamlit.button') as mock_button, \
         patch('streamlit.plotly_chart') as mock_plotly_chart, \
         patch('streamlit.empty') as mock_empty:
        yield {
            'tabs': mock_tabs,
            'dataframe': mock_dataframe,
            'multiselect': mock_multiselect,
            'button': mock_button,
            'plotly_chart': mock_plotly_chart,
            'empty': mock_empty
        }

@pytest.fixture
def sample_doctors():
    """Sample doctor data for testing."""
    return [
        {
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
            'last_updated': '2024-01-01'
        },
        {
            'id': '2',
            'name': 'Dr. B',
            'specialization': 'Cardiologist',
            'city': 'Delhi',
            'rating': 3.8,
            'reviews': 50,
            'confidence': 0.6,
            'city_tier': 2,
            'locations': ['Hospital C'],
            'sources': ['Source 3'],
            'last_updated': '2024-01-02'
        }
    ]

def test_render_results_table_empty(mock_streamlit):
    """Test rendering empty results table."""
    # Setup
    mock_streamlit['tabs'].return_value = [MagicMock(), MagicMock(), MagicMock()]
    
    # Execute
    render_results_table([])
    
    # Verify
    mock_streamlit['empty'].assert_called_once()
    mock_streamlit['dataframe'].assert_not_called()

def test_render_results_table_list_view(mock_streamlit, sample_doctors):
    """Test rendering results table in list view."""
    # Setup
    mock_streamlit['tabs'].return_value = [MagicMock(), MagicMock(), MagicMock()]
    mock_streamlit['tabs'].return_value[0].__enter__.return_value = MagicMock()
    
    # Execute
    render_results_table(sample_doctors)
    
    # Verify
    mock_streamlit['dataframe'].assert_called_once()
    df = mock_streamlit['dataframe'].call_args[0][0]
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2

def test_render_results_table_analytics(mock_streamlit, sample_doctors):
    """Test rendering analytics view."""
    # Setup
    mock_streamlit['tabs'].return_value = [MagicMock(), MagicMock(), MagicMock()]
    mock_streamlit['tabs'].return_value[1].__enter__.return_value = MagicMock()
    
    # Execute
    render_results_table(sample_doctors)
    
    # Verify
    assert mock_streamlit['plotly_chart'].call_count >= 3  # At least 3 charts

def test_render_results_table_comparison(mock_streamlit, sample_doctors):
    """Test rendering comparison view."""
    # Setup
    mock_streamlit['tabs'].return_value = [MagicMock(), MagicMock(), MagicMock()]
    mock_streamlit['tabs'].return_value[2].__enter__.return_value = MagicMock()
    mock_streamlit['multiselect'].return_value = ['1', '2']
    
    # Execute
    render_results_table(sample_doctors)
    
    # Verify
    mock_streamlit['multiselect'].assert_called_once()
    mock_streamlit['plotly_chart'].assert_called()

def test_render_doctor_profile(mock_streamlit, sample_doctors):
    """Test rendering doctor profile."""
    # Setup
    doctor = sample_doctors[0]
    
    # Execute
    render_doctor_profile(doctor)
    
    # Verify
    mock_streamlit['plotly_chart'].assert_called_once()  # Radar chart
    mock_streamlit['dataframe'].assert_called()  # Locations and sources tables

def test_render_doctor_comparison(mock_streamlit, sample_doctors):
    """Test rendering doctor comparison."""
    # Setup
    doctors = sample_doctors
    
    # Execute
    render_doctor_comparison(doctors)
    
    # Verify
    mock_streamlit['dataframe'].assert_called_once()  # Comparison table
    assert mock_streamlit['plotly_chart'].call_count >= 4  # Multiple charts for comparison

def test_render_results_table_export(mock_streamlit, sample_doctors):
    """Test export functionality."""
    # Setup
    mock_streamlit['tabs'].return_value = [MagicMock(), MagicMock(), MagicMock()]
    mock_streamlit['tabs'].return_value[0].__enter__.return_value = MagicMock()
    mock_streamlit['button'].side_effect = [True, False, False]  # Excel export
    
    # Execute
    render_results_table(sample_doctors)
    
    # Verify
    assert mock_streamlit['button'].call_count >= 3  # Export buttons 