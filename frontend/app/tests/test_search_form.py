import pytest
from unittest.mock import patch, MagicMock
import streamlit as st
from ..components.search_form import render_search_form
from ..utils.validation import validate_search_inputs

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit components."""
    with patch('streamlit.radio') as mock_radio, \
         patch('streamlit.text_input') as mock_text_input, \
         patch('streamlit.checkbox') as mock_checkbox, \
         patch('streamlit.button') as mock_button, \
         patch('streamlit.error') as mock_error:
        yield {
            'radio': mock_radio,
            'text_input': mock_text_input,
            'checkbox': mock_checkbox,
            'button': mock_button,
            'error': mock_error
        }

def test_render_search_form_single_city(mock_streamlit):
    """Test rendering search form in single city mode."""
    # Setup
    mock_streamlit['radio'].return_value = "Single City"
    mock_streamlit['text_input'].side_effect = ["Cardiologist", "Mumbai"]
    mock_streamlit['button'].return_value = True
    
    # Execute
    render_search_form()
    
    # Verify
    mock_streamlit['radio'].assert_called_once()
    assert mock_streamlit['text_input'].call_count == 2
    mock_streamlit['button'].assert_called_once()

def test_render_search_form_country_wide(mock_streamlit):
    """Test rendering search form in country-wide mode."""
    # Setup
    mock_streamlit['radio'].return_value = "Country-Wide"
    mock_streamlit['text_input'].return_value = "Cardiologist"
    mock_streamlit['checkbox'].side_effect = [True, True, True]
    mock_streamlit['button'].return_value = True
    
    # Execute
    render_search_form()
    
    # Verify
    mock_streamlit['radio'].assert_called_once()
    mock_streamlit['text_input'].assert_called_once()
    assert mock_streamlit['checkbox'].call_count == 3
    mock_streamlit['button'].assert_called_once()

def test_render_search_form_validation_error(mock_streamlit):
    """Test search form validation error handling."""
    # Setup
    mock_streamlit['radio'].return_value = "Single City"
    mock_streamlit['text_input'].side_effect = ["C", "M"]  # Invalid inputs
    mock_streamlit['button'].return_value = True
    
    # Execute
    render_search_form()
    
    # Verify
    mock_streamlit['error'].assert_called_once()

def test_render_search_form_button_disabled(mock_streamlit):
    """Test search button disabled state."""
    # Setup
    mock_streamlit['radio'].return_value = "Single City"
    mock_streamlit['text_input'].side_effect = ["", ""]  # Empty inputs
    mock_streamlit['button'].return_value = False
    
    # Execute
    render_search_form()
    
    # Verify
    mock_streamlit['button'].assert_called_once_with("Search", disabled=True) 