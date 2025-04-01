import pytest
import streamlit as st
from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def mock_streamlit():
    """Mock Streamlit session state and components."""
    # Mock session state
    if not hasattr(st, 'session_state'):
        st.session_state = {}
    
    # Mock common Streamlit components
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr('streamlit.radio', MagicMock())
        mp.setattr('streamlit.text_input', MagicMock())
        mp.setattr('streamlit.checkbox', MagicMock())
        mp.setattr('streamlit.button', MagicMock())
        mp.setattr('streamlit.error', MagicMock())
        mp.setattr('streamlit.success', MagicMock())
        mp.setattr('streamlit.warning', MagicMock())
        mp.setattr('streamlit.info', MagicMock())
        mp.setattr('streamlit.empty', MagicMock())
        mp.setattr('streamlit.dataframe', MagicMock())
        mp.setattr('streamlit.plotly_chart', MagicMock())
        mp.setattr('streamlit.selectbox', MagicMock())
        mp.setattr('streamlit.slider', MagicMock())
        mp.setattr('streamlit.number_input', MagicMock())
        mp.setattr('streamlit.date_input', MagicMock())
        mp.setattr('streamlit.multiselect', MagicMock())
        mp.setattr('streamlit.tabs', MagicMock())
        yield st

@pytest.fixture(autouse=True)
def clear_session_state():
    """Clear session state before each test."""
    if hasattr(st, 'session_state'):
        st.session_state.clear() 