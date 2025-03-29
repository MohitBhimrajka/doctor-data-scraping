import streamlit as st
import httpx
import pandas as pd
import os
from dotenv import load_dotenv
import json
from typing import List, Dict, Any
import asyncio
import logging
from datetime import datetime
import pathlib
import re

# Create logs directory if it doesn't exist
log_dir = pathlib.Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'streamlit_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set up the backend URL
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
logger.info(f"Using backend API URL: {BACKEND_API_URL}")

# Define specializations dictionary
specializations = {
    'cardiologist': 'Cardiologist',
    'dermatologist': 'Dermatologist',
    'endocrinologist': 'Endocrinologist',
    'gastroenterologist': 'Gastroenterologist',
    'neurologist': 'Neurologist',
    'oncologist': 'Oncologist',
    'ophthalmologist': 'Ophthalmologist',
    'orthopedist': 'Orthopedist',
    'pediatrician': 'Pediatrician',
    'psychiatrist': 'Psychiatrist',
    'pulmonologist': 'Pulmonologist',
    'rheumatologist': 'Rheumatologist',
    'urologist': 'Urologist',
    'dentist': 'Dentist',
    'general_physician': 'General Physician'
}

# Supervity brand colors
COLORS = {
    "navy_blue": "#000b37",  # For titles/headers
    "lime_green": "#85c20b",  # For buttons or accents
    "light_gray": "#f0f0f0",  # For background
    "dark_gray": "#333333",   # For text
}

# Custom CSS
def apply_custom_css():
    st.markdown(f"""
    <style>
    .title {{
        color: {COLORS['navy_blue']};
        font-weight: bold;
        font-size: 2.5rem;
        margin-bottom: 1rem;
        text-align: center;
    }}
    .subtitle {{
        color: {COLORS['dark_gray']};
        font-size: 1.2rem;
        margin-bottom: 2rem;
        text-align: center;
    }}
    .stButton > button {{
        background-color: {COLORS['lime_green']};
        color: white;
        font-weight: bold;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        border: none;
        transition: all 0.3s ease;
    }}
    .stButton > button:hover {{
        background-color: {COLORS['navy_blue']};
        color: white;
        transform: translateY(-2px);
    }}
    .results-count {{
        font-size: 1.2rem;
        color: {COLORS['navy_blue']};
        margin: 1rem 0;
        padding: 0.5rem;
        background-color: {COLORS['light_gray']};
        border-radius: 5px;
        text-align: center;
    }}
    .debug-info {{
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        margin-top: 2rem;
        font-family: monospace;
        font-size: 0.8rem;
    }}
    .download-section {{
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 5px;
        margin-top: 1.5rem;
        border: 1px solid #ddd;
    }}
    .download-title {{
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        color: {COLORS['navy_blue']};
    }}
    </style>
    """, unsafe_allow_html=True)

async def search_doctors(city: str, specialization: str) -> Dict[str, Any]:
    """
    Make an asynchronous API call to the backend to search for doctors
    """
    try:
        logger.info(f"Searching for {specialization} in {city}")
        
        # Create the payload for the POST request
        payload = {
            "city": city,
            "specialization": specialization
        }
        
        logger.info(f"Sending request to {BACKEND_API_URL}/api/search with payload: {payload}")
        
        # Make the API call
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_API_URL}/api/search",
                json=payload,
                timeout=120.0  # Increased timeout as search can take time
            )
            
            # Log the raw response for debugging
            logger.info(f"Got response with status code: {response.status_code}")
            
            # Check if the request was successful
            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.info(f"Search successful. Found {result.get('metadata', {}).get('total', 0)} doctors")
                    
                    # Verify the structure of the response
                    if 'data' not in result or result['data'] is None:
                        logger.warning(f"API returned success but no data field or empty data: {result}")
                        result['data'] = []
                    
                    return result
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response: {response.text[:200]}")
                    return {
                        "success": False,
                        "error": "Failed to parse JSON response from backend",
                        "data": [],
                        "metadata": {"total": 0}
                    }
            else:
                logger.error(f"API call failed with status code {response.status_code}: {response.text[:200]}")
                return {
                    "success": False,
                    "error": f"API call failed with status code {response.status_code}",
                    "data": [],
                    "metadata": {"total": 0}
                }
                
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to connect to the backend: {str(e)}",
            "data": [],
            "metadata": {"total": 0}
        }
    except Exception as e:
        logger.error(f"Unexpected error during API call: {type(e).__name__} - {str(e)}")
        return {
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}",
            "data": [],
            "metadata": {"total": 0}
        }

def run_async(coroutine):
    """Helper function to run async functions in Streamlit"""
    return asyncio.run(coroutine)

def is_valid_location(location: str, city: str) -> bool:
    """Check if a location seems valid and is in the specified city"""
    if not isinstance(location, str) or len(location) < 5:
        return False
    
    # Check if it contains the city name
    city_lower = city.lower()
    location_lower = location.lower()
    
    # Exclude generic locations
    generic_locations = [
        "multiple locations", "available online", "teleconsultation", 
        "consultation available", "multiple branches", "across india",
        "pan india", "all over india", "all major cities"
    ]
    
    for generic in generic_locations:
        if generic in location_lower:
            return False
    
    # Check if another major city is mentioned (and it's not the requested city)
    other_cities = ["delhi", "mumbai", "bangalore", "bengaluru", "chennai", "kolkata", 
                   "hyderabad", "pune", "ahmedabad", "jaipur", "lucknow"]
    
    for other_city in other_cities:
        if other_city != city_lower and other_city in location_lower:
            # Check if it's mentioning travel to the city
            travel_indicators = ["visit", "travels to", "also available in", "consultation in"]
            has_travel_indicator = any(indicator in location_lower for indicator in travel_indicators)
            if not has_travel_indicator:
                return False
    
    # If we reach here, the location is likely valid
    return True

def filter_doctor_data(doctors_data: List[Dict], city: str) -> List[Dict]:
    """Filter and clean doctor data to remove suspicious entries"""
    filtered_data = []
    
    for doctor in doctors_data:
        if not isinstance(doctor, dict):
            continue
            
        # Skip doctors with suspicious names
        name = doctor.get('name', '')
        if not name or any(x in name for x in ['XYZ', 'ABC', 'PQR']):
            continue
            
        # Clean up data fields
        clean_doctor = {
            'name': name,
            'rating': doctor.get('rating', 0),
            'reviews': doctor.get('reviews', 0),
            'specialization': doctor.get('specialization', ''),
            'city': doctor.get('city', '')
        }
        
        # Filter locations
        locations = doctor.get('locations', [])
        if isinstance(locations, list):
            clean_doctor['locations'] = [
                loc for loc in locations 
                if isinstance(loc, str) and is_valid_location(loc, city)
            ]
        else:
            clean_doctor['locations'] = []
            
        # Only include doctors with at least one valid location
        if clean_doctor['locations']:
            clean_doctor['contributing_sources'] = doctor.get('contributing_sources', [])
            filtered_data.append(clean_doctor)
    
    return filtered_data

def display_search_results(results: dict):
    """Display search results in a summary table format"""
    try:
        if not results:
            st.warning("No search results available.")
            return
            
        success = results.get('success', False)
        error = results.get('error', None)
        data = results.get('data', [])
        metadata = results.get('metadata', {})
        
        if not success:
            st.error(f"Search failed: {error}")
            return
        
        # Get city for location validation
        city = metadata.get('query', {}).get('city', '')
        
        # Clean and filter the data
        filtered_data = filter_doctor_data(data, city)
        
        # Log data for debugging
        logger.info(f"Displaying search results: original_count={len(data)}, filtered_count={len(filtered_data)}")
        
        if not filtered_data:
            st.warning("No qualified doctors found matching your search criteria.")
            return
        
        # Display metadata and search stats
        st.markdown(f"""
        <div class="results-count">
            Found {len(filtered_data)} verified doctors in {metadata.get('search_duration', 0):.2f} seconds
        </div>
        """, unsafe_allow_html=True)
        
        # Sorting options
        sort_option = st.selectbox(
            "Sort results by:",
            options=["Rating (High to Low)", "Reviews (High to Low)"]
        )
        
        # Sort data based on selection
        try:
            if sort_option == "Rating (High to Low)":
                sorted_data = sorted(
                    filtered_data, 
                    key=lambda x: (float(x.get('rating', 0)) if isinstance(x.get('rating'), (int, float, str)) else 0, 
                                   int(x.get('reviews', 0)) if isinstance(x.get('reviews'), (int, float, str)) else 0), 
                    reverse=True
                )
            else:  # Reviews (High to Low)
                sorted_data = sorted(
                    filtered_data, 
                    key=lambda x: (int(x.get('reviews', 0)) if isinstance(x.get('reviews'), (int, float, str)) else 0, 
                                   float(x.get('rating', 0)) if isinstance(x.get('rating'), (int, float, str)) else 0), 
                    reverse=True
                )
        except Exception as e:
            logger.error(f"Error sorting data: {type(e).__name__} - {str(e)}")
            sorted_data = filtered_data  # Use unsorted data if sorting fails
        
        # Create a summary DataFrame for display
        summary_data = []
        for doc in sorted_data:
            # Create a simplified summary for each doctor
            primary_location = doc.get('locations', ['Not Available'])[0] if doc.get('locations') else 'Not Available'
            secondary_location = doc.get('locations', ['', 'Not Available'])[1] if len(doc.get('locations', [])) > 1 else 'N/A'
            
            summary_data.append({
                'Name': doc.get('name', ''),
                'Rating': f"{float(doc.get('rating', 0)):.1f}" if isinstance(doc.get('rating'), (int, float, str)) else 'N/A',
                'Reviews': doc.get('reviews', 0),
                'Primary Location': primary_location,
                'Secondary Location': secondary_location,
                'Total Locations': len(doc.get('locations', []))
            })
        
        # Create DataFrame and display as table
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)
        
        # Create detailed dataframe for download
        try:
            # Full data with all details
            df = pd.DataFrame([
                {
                    'Name': d.get('name', ''),
                    'Rating': d.get('rating', 0),
                    'Reviews': d.get('reviews', 0),
                    'Locations': '; '.join(d.get('locations', [])) if isinstance(d.get('locations'), list) else '',
                    'Specialization': d.get('specialization', ''),
                    'City': d.get('city', ''),
                    'Contributing Sources': '; '.join(d.get('contributing_sources', [])) if isinstance(d.get('contributing_sources'), list) else ''
                } for d in sorted_data
            ])
            
            # Provide download options
            st.markdown('<div class="download-section">', unsafe_allow_html=True)
            st.markdown('<p class="download-title">Download Complete Results</p>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download as CSV",
                    data=csv,
                    file_name=f"doctors_{metadata.get('query', {}).get('city', 'city')}_{metadata.get('query', {}).get('specialization', 'specialty')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Preserve proper list structure in JSON
                json_data = json.dumps([{
                    'name': d.get('name', ''),
                    'rating': d.get('rating', 0),
                    'reviews': d.get('reviews', 0),
                    'locations': d.get('locations', []) if isinstance(d.get('locations'), list) else [],
                    'specialization': d.get('specialization', ''),
                    'city': d.get('city', ''),
                    'contributing_sources': d.get('contributing_sources', []) if isinstance(d.get('contributing_sources'), list) else []
                } for d in sorted_data], indent=2)
                
                st.download_button(
                    label="Download as JSON",
                    data=json_data,
                    file_name=f"doctors_{metadata.get('query', {}).get('city', 'city')}_{metadata.get('query', {}).get('specialization', 'specialty')}.json",
                    mime="application/json"
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            logger.error(f"Error creating download files: {type(e).__name__} - {str(e)}")
            st.error("Error preparing download files.")
    except Exception as e:
        logger.error(f"Error displaying search results: {type(e).__name__} - {str(e)}")
        st.error(f"Error displaying search results: {str(e)}")

def main():
    # Set page config
    st.set_page_config(
        page_title="Doctor Search | Find the Best Doctors",
        page_icon="🩺",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Apply custom CSS
    apply_custom_css()
    
    # Page title and intro
    st.markdown('<h1 class="title">🩺 Doctor Search</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Find the best doctors across multiple platforms</p>', unsafe_allow_html=True)
    
    # Create three columns layout for the search form
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # City input (with popular Indian cities as examples)
        city = st.text_input("City", placeholder="e.g., Mumbai, Delhi, Bangalore")
    
    with col2:
        # Specialization selection
        specialization = st.selectbox("Specialization", options=list(specializations.values()))
    
    with col3:
        # Search button that triggers the API call
        search_button = st.button("Search", use_container_width=True)
    
    # Initialize session state if not already done
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'is_searching' not in st.session_state:
        st.session_state.is_searching = False
    if 'error' not in st.session_state:
        st.session_state.error = None
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    
    # Add a debug toggle in the sidebar
    with st.sidebar:
        if 'debug_mode' not in st.session_state:
            st.session_state.debug_mode = False
        st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.debug_mode)
    
    # Handle search button click
    if search_button:
        # Validate inputs
        if not city or not specialization:
            st.error("Please enter both city and specialization")
        else:
            try:
                # Set searching state
                st.session_state.is_searching = True
                st.session_state.error = None
                
                # Show searching message
                with st.spinner(f"Searching for {specialization} in {city}..."):
                    # Call the search function
                    results = run_async(search_doctors(city, specialization))
                    
                    # Store results in session state
                    st.session_state.search_results = results
                    st.session_state.is_searching = False
                    
                    # Check if the API returned an error
                    if not results.get('success', False):
                        error_message = results.get('error', 'Unknown error')
                        error_detail = results.get('detail', '')
                        error_text = f"{error_message}"
                        if error_detail:
                            error_text += f"\nDetails: {error_detail}"
                        st.session_state.error = error_text
                        st.error(error_text)
                    
                    # Rerun the app to update the UI with the search results
                    st.rerun()
                    
            except Exception as e:
                st.session_state.is_searching = False
                error_message = f"Error: {type(e).__name__} - {str(e)}"
                st.session_state.error = error_message
                st.error(error_message)
                logger.error(f"Search error: {error_message}")
    
    # Display search results if available
    if st.session_state.search_results:
        display_search_results(st.session_state.search_results)
        
        # Display debug information if debug mode is enabled
        if st.session_state.debug_mode:
            st.markdown("### Debug Information")
            st.markdown('<div class="debug-info">', unsafe_allow_html=True)
            st.json(st.session_state.search_results)
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 