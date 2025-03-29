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
from PIL import Image
import io
import base64
from streamlit_lottie import st_lottie
import requests
import time
from pandas.io.excel import ExcelWriter

# Create logs directory if it doesn't exist
log_dir = pathlib.Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

# Create assets directory if it doesn't exist
assets_dir = pathlib.Path(__file__).parent / 'assets'
assets_dir.mkdir(exist_ok=True)

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
    'general_physician': 'General Physician',
    'gynecologist': 'Gynecologist',
    'ent_specialist': 'ENT Specialist',
    'nephrologist': 'Nephrologist',
    'hematologist': 'Hematologist',
    'radiologist': 'Radiologist',
    'anesthesiologist': 'Anesthesiologist'
}

# Supervity brand colors
COLORS = {
    "navy_blue": "#000b37",  # Primary color
    "lime_green": "#85c20b",  # For buttons or accents
    "light_gray": "#f0f0f0",  # For background
    "dark_gray": "#333333",   # For text
}

# Function to load the Supervity logo
def load_logo():
    # Look for the logo file in the streamlit-frontend directory
    logo_path = pathlib.Path(__file__).parent / "logo.png"
    # Check if the logo file exists
    if not logo_path.exists():
        # If not, try looking in the assets directory
        logo_path = assets_dir / "logo.png"
        if not logo_path.exists():
            # If still not found, return None
            logger.warning("Logo file not found. Please add 'logo.png' to the streamlit-frontend directory.")
            return None
    return Image.open(logo_path)

# Function to set favicon
def set_favicon():
    # Look for the favicon file in the streamlit-frontend directory
    favicon_path = pathlib.Path(__file__).parent / "icon.png"
    # Check if the favicon file exists
    if not favicon_path.exists():
        # If not, try looking in the assets directory
        favicon_path = assets_dir / "icon.png"
        if not favicon_path.exists():
            # If still not found, log a warning
            logger.warning("Favicon file not found. Please add 'icon.png' to the streamlit-frontend directory.")
            return
    
    # Read the favicon file
    try:
        with open(favicon_path, "rb") as f:
            favicon_data = f.read()
        
        # Convert the image to base64
        b64_favicon = base64.b64encode(favicon_data).decode("utf-8")
        
        # Create the HTML for setting the favicon
        favicon_html = f"""
        <link rel="shortcut icon" href="data:image/png;base64,{b64_favicon}">
        """
        
        # Apply the favicon
        st.markdown(favicon_html, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error setting favicon: {e}")

# Function to load a Lottie animation from URL
def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception as e:
        logger.error(f"Error loading Lottie animation: {e}")
        return None

# Custom CSS with animations
def apply_custom_css():
    st.markdown(f"""
    <style>
    /* Overall app styling */
    .stApp {{
        background-color: white;
    }}
    
    /* Main container */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    
    /* Logo styling */
    .logo-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 1.5rem;
        width: 100%;
    }}
    
    .logo-container img {{
        max-width: 250px;
        margin: 0 auto;
    }}
    
    /* Title styling */
    .title {{
        color: {COLORS['navy_blue']};
        font-weight: bold;
        font-size: 2.5rem;
        margin-bottom: 1rem;
        text-align: center;
        animation: fadeIn 0.8s ease-in-out;
    }}
    
    /* Subtitle styling */
    .subtitle {{
        color: {COLORS['dark_gray']};
        font-size: 1.2rem;
        margin-bottom: 2rem;
        text-align: center;
        animation: slideIn 1s ease-in-out;
    }}
    
    /* Buttons */
    .stButton > button {{
        background-color: {COLORS['navy_blue']};
        color: white;
        font-weight: bold;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    }}
    .stButton > button:hover {{
        background-color: {COLORS['lime_green']};
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    }}
    
    /* Search form styling */
    .search-form {{
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 11, 55, 0.1);
        margin-bottom: 2rem;
        animation: fadeIn 0.8s ease-in-out;
    }}
    
    /* Results count box */
    .results-count {{
        font-size: 1.2rem;
        color: white;
        margin: 1rem 0;
        padding: 0.8rem;
        background-color: {COLORS['navy_blue']};
        border-radius: 5px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        animation: pulse 2s infinite;
    }}
    
    /* Table styling */
    .dataframe {{
        border-radius: 5px;
        overflow: hidden;
        animation: fadeIn 1s ease-in-out;
    }}
    
    /* Download section */
    .download-section {{
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        margin: 2rem auto;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 12px rgba(0, 11, 55, 0.1);
        animation: fadeIn 1s ease-in-out;
        max-width: 800px;
        text-align: center;
    }}
    
    /* Download title */
    .download-title {{
        font-weight: bold;
        font-size: 1.3rem;
        margin-bottom: 1.5rem;
        color: {COLORS['navy_blue']};
        text-align: center;
    }}
    
    /* Download button */
    .download-button {{
        background-color: {COLORS['navy_blue']};
        color: white;
        padding: 1rem 2rem;
        border-radius: 5px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        cursor: pointer;
        text-align: center;
        max-width: 400px;
        margin: 0 auto;
        font-size: 1.1rem;
    }}
    
    .download-button:hover {{
        background-color: {COLORS['lime_green']};
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    }}
    
    /* Custom specialization box */
    .custom-specialization {{
        margin-top: 0.5rem;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 5px;
        border: 1px solid #e0e0e0;
        animation: fadeIn 0.8s ease-in-out;
    }}
    
    /* Sources pills */
    .sources-pill {{
        display: inline-block;
        padding: 4px 12px;
        margin: 3px;
        border-radius: 20px;
        background-color: {COLORS['navy_blue']};
        color: white;
        font-size: 0.85rem;
        box-shadow: 0 2px 3px rgba(0, 0, 0, 0.1);
    }}
    
    /* Sidebar styling */
    .css-1r6slb0 {{
        background-color: {COLORS['navy_blue']};
        color: white;
    }}
    .css-1r6slb0 .css-vsklj7 {{
        color: white;
    }}
    
    /* Loading spinner */
    .stSpinner > div {{
        border-top-color: {COLORS['navy_blue']} !important;
    }}
    
    /* Debug info */
    .debug-info {{
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        margin-top: 2rem;
        font-family: monospace;
        font-size: 0.8rem;
        animation: fadeIn 1s ease-in-out;
    }}
    
    /* Animations */
    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}
    
    @keyframes slideIn {{
        from {{ transform: translateY(20px); opacity: 0; }}
        to {{ transform: translateY(0); opacity: 1; }}
    }}
    
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(0, 11, 55, 0.4); }}
        70% {{ box-shadow: 0 0 0 10px rgba(0, 11, 55, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(0, 11, 55, 0); }}
    }}
    
    /* Radio buttons styling */
    .stRadio > div {{
        display: flex;
        gap: 10px;
    }}
    
    .stRadio > div > label {{
        background-color: #f0f0f0;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        transition: all 0.3s ease;
    }}
    
    .stRadio > div > label:hover {{
        background-color: #e0e0e0;
    }}
    
    .stRadio > div > label > div {{
        display: flex;
        align-items: center;
    }}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: #f1f1f1;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {COLORS['navy_blue']};
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {COLORS['lime_green']};
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

# Function to convert DataFrame to Excel
def to_excel(df):
    output = io.BytesIO()
    with ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Doctors', index=False)
        # Get the xlsxwriter workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Doctors']
        
        # Add a header format
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': COLORS['navy_blue'],
            'font_color': 'white',
            'border': 1
        })
        
        # Write the column headers with the defined format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Set column widths
        worksheet.set_column('A:A', 30)  # Name
        worksheet.set_column('B:B', 10)  # Rating
        worksheet.set_column('C:C', 10)  # Reviews
        worksheet.set_column('D:D', 50)  # Locations
        worksheet.set_column('E:E', 20)  # Specialization
        worksheet.set_column('F:F', 15)  # City
        worksheet.set_column('G:G', 20)  # Contributing Sources
        
        # Add zebra striping
        for row_num in range(1, len(df) + 1):
            if row_num % 2 == 0:
                worksheet.set_row(row_num, None, workbook.add_format({'bg_color': '#f0f0f0'}))
    
    processed_data = output.getvalue()
    return processed_data

def display_search_results(results: dict):
    """Display search results in a summary table format with improved UI"""
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
            # Use Lottie animation for no results
            no_results_lottie = load_lottie_url("https://lottie.host/be2fa43c-1084-4583-8be6-0d1cd6c41f21/gTzFHlwqak.json")
            if no_results_lottie:
                st_lottie(no_results_lottie, height=200, key="no_results")
            
            st.warning("No qualified doctors found matching your search criteria.")
            return
        
        # Display metadata and search stats with animation
        st.markdown(f"""
        <div class="results-count">
            ✨ Found {len(filtered_data)} verified doctors in {metadata.get('search_duration', 0):.2f} seconds
        </div>
        """, unsafe_allow_html=True)
        
        # Create download section immediately after results count
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
                } for d in filtered_data
            ])
            
            # Generate Excel file
            excel_data = to_excel(df)
            
            # Provide download button prominently
            st.markdown('<div class="download-section">', unsafe_allow_html=True)
            st.markdown('<p class="download-title">📥 Download Doctor Information</p>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="Download as Excel",
                    data=excel_data,
                    file_name=f"doctors_{metadata.get('query', {}).get('city', 'city')}_{metadata.get('query', {}).get('specialization', 'specialty')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel",
                    help="Click to download the complete results as an Excel file",
                    use_container_width=True
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            logger.error(f"Error creating Excel file: {type(e).__name__} - {str(e)}")
            st.error("Error preparing download file.")
        
        # Sorting options with improved styling
        st.markdown("<h3 style='color:#000b37;'>Explore Results</h3>", unsafe_allow_html=True)
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
            
            # Get sources and format them
            sources = doc.get('contributing_sources', [])
            if isinstance(sources, list):
                sources_str = ", ".join(sorted(set(src.lower() for src in sources)))
            else:
                sources_str = "N/A"
            
            summary_data.append({
                'Name': doc.get('name', ''),
                'Rating': f"{float(doc.get('rating', 0)):.1f}" if isinstance(doc.get('rating'), (int, float, str)) else 'N/A',
                'Reviews': doc.get('reviews', 0),
                'Primary Location': primary_location,
                'Secondary Location': secondary_location,
                'Sources': sources_str,
                'Total Locations': len(doc.get('locations', []))
            })
        
        # Create DataFrame and display as table with improved styling
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error displaying search results: {type(e).__name__} - {str(e)}")
        st.error(f"Error displaying search results: {str(e)}")

def main():
    # Set page config with custom title and favicon
    st.set_page_config(
        page_title="Find the Best Doctors | Supervity",
        page_icon="🩺",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Set favicon
    set_favicon()
    
    # Apply custom CSS
    apply_custom_css()
    
    # Display Supervity logo
    logo = load_logo()
    if logo:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo, width=50, use_container_width=True)
    else:
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        st.markdown(f'<h2 style="color:{COLORS["navy_blue"]}; text-align:center;">Supervity</h2>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Page title and intro with animations
    st.markdown('<h1 class="title">Find the Best Doctors</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Search across multiple platforms to discover qualified doctors in your city</p>', unsafe_allow_html=True)
    
    # Wrap search form in a container with styling
    st.markdown('<div class="search-form">', unsafe_allow_html=True)
    
    # Create columns layout for the search form
    col1, col2 = st.columns(2)
    
    with col1:
        # City input with placeholder and help text
        city = st.text_input(
            "City", 
            placeholder="e.g., Mumbai, Delhi, Bangalore",
            help="Enter the city where you want to find doctors"
        )
    
    with col2:
        # Add option to use predefined or custom specialization
        specialization_type = st.radio(
            "Specialization Type",
            options=["Choose from list", "Enter custom"],
            horizontal=True
        )
        
        if specialization_type == "Choose from list":
            # Specialization selection from predefined list
            specialization = st.selectbox(
                "Specialization", 
                options=list(specializations.values()),
                help="Select the type of doctor you're looking for"
            )
        else:
            # Custom specialization input
            specialization = st.text_input(
                "Enter Custom Specialization", 
                placeholder="e.g., Sports Medicine, Pain Management",
                help="Type a specific medical specialization"
            )
    
    # Search button in a centered column with animation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        search_button = st.button("Search Doctors", use_container_width=True)
        
        # Add note about custom specializations
        if specialization_type == "Enter custom":
            st.markdown(
                "<div class='custom-specialization'>Note: Custom specializations may return fewer or less accurate results "
                "than our predefined list, as they depend on how commonly they appear in our data sources.</div>", 
                unsafe_allow_html=True
            )
    
    # Close the search form container
    st.markdown('</div>', unsafe_allow_html=True)
    
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
        st.markdown('<div style="display:flex; justify-content:center; margin-bottom:20px;">', unsafe_allow_html=True)
        if logo:
            st.image(logo, width=60)
        else:
            st.markdown(f'<h3 style="color:white; text-align:center;">Supervity</h3>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown(f"<h3 style='color:white;'>Search Tips</h3>", unsafe_allow_html=True)
        st.markdown(
            "<div style='color:white;'>"
            "- For more results, try different cities nearby your location<br>"
            "- Some specializations may have more doctors in certain cities<br>"
            "- Results are filtered to ensure only doctors with verified locations are shown<br>"
            "- Use custom specialization for specific needs"
            "</div>",
            unsafe_allow_html=True
        )
        
        # Add collapsible about section
        with st.expander("About Supervity", expanded=False):
            st.markdown(
                "<div style='color:white;'>"
                "Supervity helps you find verified doctors across multiple platforms. "
                "Our advanced search algorithms ensure you get the most relevant results "
                "specific to your city and medical needs."
                "</div>",
                unsafe_allow_html=True
            )
        
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
                
                # Show searching message with a nice animation
                with st.spinner(f"Searching for {specialization} in {city}..."):
                    # Add a slight delay for visual effect
                    time.sleep(0.5)
                    
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
    else:
        # Show welcome animation when no search has been performed yet
        welcome_lottie = load_lottie_url("https://lottie.host/c9cc25ba-fe8a-422a-b735-1611399e3b3b/zNvxQpVgN3.json")
        if welcome_lottie:
            st.markdown('<div style="display: flex; justify-content: center; margin: 2rem 0;">', unsafe_allow_html=True)
            st_lottie(welcome_lottie, height=300, key="welcome")
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 