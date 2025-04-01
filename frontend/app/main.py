import streamlit as st
import asyncio
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

# Import components
from components.search_form import render_search_form
from components.filters import render_filters, apply_filters
from components.results_table import render_results_table
from components.doctor_profile import render_doctor_profile, render_doctor_comparison

# Import services
from services.api_client import APIClient

# Import utilities
from utils.formatting import format_doctor_data, format_stats
from utils.validation import validate_search_inputs, validate_doctor_data
from utils.ui_utils import (
    add_loading_animation,
    add_tooltip,
    add_aria_label,
    apply_theme,
    add_high_contrast_mode,
    add_error_message,
    add_help_text
)
from utils.performance import (
    Cache,
    RequestQueue,
    debounce,
    VirtualScroll,
    optimize_chart_data,
    memoize
)
from utils.error_handling import (
    ErrorTracker,
    retry_on_failure,
    handle_api_error,
    graceful_degradation,
    ErrorBoundary,
    log_error,
    show_error_message
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize API client with error handling
api_client = APIClient()

# Initialize performance utilities
cache = Cache(ttl=300)  # 5 minutes cache
request_queue = RequestQueue(max_concurrent=3)
error_tracker = ErrorTracker()

# Initialize session state
if 'search_mode' not in st.session_state:
    st.session_state.search_mode = "single_city"
if 'city' not in st.session_state:
    st.session_state.city = ""
if 'selected_tiers' not in st.session_state:
    st.session_state.selected_tiers = [1, 2, 3]
if 'specialization' not in st.session_state:
    st.session_state.specialization = ""
if 'doctors' not in st.session_state:
    st.session_state.doctors = []
if 'stats' not in st.session_state:
    st.session_state.stats = {}
if 'loading' not in st.session_state:
    st.session_state.loading = False
if 'error' not in st.session_state:
    st.session_state.error = None
if 'page' not in st.session_state:
    st.session_state.page = 1
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'is_dark_mode' not in st.session_state:
    st.session_state.is_dark_mode = False
if 'high_contrast' not in st.session_state:
    st.session_state.high_contrast = False

# Page config
st.set_page_config(
    page_title="Doctor Discovery",
    page_icon="👨‍⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stButton>button {
        width: 100%;
        margin-top: 10px;
    }
    .stTextInput>div>div>input {
        background-color: #f0f2f6;
    }
    .stSelectbox>div>div>select {
        background-color: #f0f2f6;
    }
    @media (max-width: 768px) {
        .stApp {
            padding: 0 10px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("Settings")
    
    # Theme toggle
    st.session_state.is_dark_mode = st.toggle(
        "Dark Mode",
        value=st.session_state.is_dark_mode,
        help="Toggle dark/light theme"
    )
    
    # High contrast mode
    st.session_state.high_contrast = st.toggle(
        "High Contrast Mode",
        value=st.session_state.high_contrast,
        help="Toggle high contrast mode for better accessibility"
    )
    
    # Favorites section
    st.subheader("Favorites")
    if st.session_state.favorites:
        for doctor in st.session_state.favorites:
            with st.expander(doctor['name']):
                st.write(f"Specialization: {doctor['specialization']}")
                st.write(f"City: {doctor['city']}")
                if st.button("Remove", key=f"remove_{doctor['id']}"):
                    st.session_state.favorites.remove(doctor)
                    st.rerun()
    else:
        st.info("No favorites added yet")
    
    # Search history
    st.subheader("Recent Searches")
    if 'search_history' in st.session_state:
        for search in st.session_state.search_history[-5:]:
            st.write(f"{search['specialization']} in {search['city']}")
    
    # Help section
    st.subheader("Help")
    st.markdown("""
        - Use the search form to find doctors
        - Click on doctor names to view details
        - Use filters to refine results
        - Add doctors to favorites for quick access
    """)

# Main content
st.title("Doctor Discovery")

# Apply theme
apply_theme(st.container(), st.session_state.is_dark_mode)
if st.session_state.high_contrast:
    add_high_contrast_mode(st.container())

# Search form with loading state
with st.form("search_form"):
    with add_loading_animation(st.container(), "Loading search form..."):
        render_search_form()

# Error handling
if st.session_state.error:
    show_error_message(st.session_state.error)
    st.session_state.error = None

# Results section with virtual scrolling
if st.session_state.doctors:
    # Filters
    filtered_doctors = apply_filters(st.session_state.doctors)
    
    # Virtual scrolling
    virtual_scroll = VirtualScroll(filtered_doctors, page_size=10)
    current_page = virtual_scroll.get_page(st.session_state.page - 1)
    
    # Results table with loading state
    with add_loading_animation(st.container(), "Loading results..."):
        render_results_table(current_page)
    
    # Pagination
    total_pages = virtual_scroll.get_total_pages()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("Previous", disabled=st.session_state.page == 1):
            st.session_state.page -= 1
            st.rerun()
    with col2:
        st.write(f"Page {st.session_state.page} of {total_pages}")
    with col3:
        if st.button("Next", disabled=st.session_state.page == total_pages):
            st.session_state.page += 1
            st.rerun()

# Stats section with caching
@memoize
def get_stats():
    return api_client.get_stats()

if st.button("Show Statistics"):
    with add_loading_animation(st.container(), "Loading statistics..."):
        try:
            stats = get_stats()
            formatted_stats = format_stats(stats)
            st.write(formatted_stats)
        except Exception as e:
            log_error(e, {"context": "stats"})
            show_error_message(e)

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>Doctor Discovery v1.0 | Made with ❤️</p>
        <p>© 2024 All rights reserved</p>
    </div>
""", unsafe_allow_html=True)

