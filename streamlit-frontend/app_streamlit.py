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

# Define popular specializations
POPULAR_SPECIALIZATIONS = [
    'Cardiologist',
    'Dermatologist',
    'Pediatrician',
    'Orthopedist',
    'Dentist',
    'General Physician',
    'Gynecologist',
    'ENT Specialist',
    'Ophthalmologist',
    'Psychiatrist',
    'Neurologist',
    'Other (Custom)'
]

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
    
    /* Main container - centered with max width */
    .main .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1000px;
        margin: 0 auto;
    }}
    
    /* Logo styling */
    .logo-container {{
        display: flex;
        justify-content: center;
        margin-bottom: 0.5rem;
        width: 100%;
    }}
    
    .logo-container img {{
        height: 12px;
        width: auto;
        transition: transform 0.3s ease;
    }}
    
    /* Title styling */
    .title {{
        color: {COLORS['navy_blue']};
        font-weight: bold;
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
        text-align: center;
        animation: fadeIn 0.8s ease-in-out;
    }}
    
    /* Subtitle styling */
    .subtitle {{
        color: {COLORS['dark_gray']};
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
        text-align: center;
        animation: slideIn 0.8s ease-in-out;
    }}
    
    /* Search container */
    .search-container {{
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        padding: 2rem;
        margin-bottom: 2rem;
        animation: fadeIn 0.8s ease-in-out;
        border: 1px solid #f0f0f0;
    }}
    
    /* Search container title */
    .search-title {{
        color: {COLORS['navy_blue']};
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        text-align: center;
    }}
    
    /* Input fields styling */
    .input-label {{
        font-weight: 600;
        color: {COLORS['navy_blue']};
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }}
    
    .stTextInput > div > div > input {{
        border-radius: 8px;
        border: 2px solid #e5e7eb;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        box-shadow: none;
        transition: all 0.2s ease;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: {COLORS['navy_blue']};
        box-shadow: 0 0 0 2px rgba(0, 11, 55, 0.1);
    }}
    
    /* Specialization tags grid */
    .spec-section {{
        margin: 1.5rem 0;
    }}
    
    /* Specialization tags styling */
    .spec-button {{
        background-color: #f9fafb;
        color: #374151;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.6rem 0.5rem;
        text-align: center;
        font-size: 0.9rem;
        margin-bottom: 0.75rem;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        display: block;
        width: 100%;
    }}
    
    .spec-button:hover {{
        background-color: #f3f4f6;
        border-color: #d1d5db;
        transform: translateY(-1px);
    }}
    
    /* Primary button styling - make selected state more obvious */
    .stButton > button[data-baseweb="button"][kind="primary"] {{
        background-color: #e6f0ff;
        color: #000b37;
        border: 2px solid #000b37;
        font-weight: 600;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    
    .stButton > button[data-baseweb="button"][kind="primary"]:hover {{
        background-color: #d1e3ff;
        border-color: #000b37;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
    }}
    
    /* Custom specialization button styling */
    .stButton > button[data-baseweb="button"][kind="secondary"]:has-text("Other (Custom)") {{
        background-color: #fef3c7;
        color: #92400e;
        border: 2px solid #92400e;
        font-weight: 600;
    }}
    
    .stButton > button[data-baseweb="button"][kind="secondary"]:has-text("Other (Custom)"):hover {{
        background-color: #fde68a;
        border-color: #92400e;
    }}
    
    /* Custom specialization input container */
    .custom-spec-container {{
        margin-top: 1rem;
        padding: 1.25rem;
        background-color: #fef3c7;
        border-radius: 8px;
        border: 2px solid #92400e;
        animation: fadeIn 0.5s ease-in-out;
    }}
    
    /* Custom specialization input styling */
    .custom-spec-container .stTextInput > div > div > input {{
        background-color: white;
        border: 1px solid #92400e;
        color: #92400e;
    }}
    
    .custom-spec-container .stTextInput > div > div > input:focus {{
        border-color: #92400e;
        box-shadow: 0 0 0 2px rgba(146, 64, 14, 0.1);
    }}
    
    /* Search button styling */
    .stButton > button {{
        background-color: {COLORS['navy_blue']};
        color: white;
        font-weight: 600;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        border: none;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        font-size: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
    }}
    
    .stButton > button:hover {{
        background-color: #000929;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
    }}
    
    .stButton > button:active {{
        transform: translateY(0);
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }}
    
    .stButton > button:disabled {{
        background-color: #d1d5db;
        color: #6b7280;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
    }}
    
    /* Results section styling */
    .results-section {{
        animation: fadeIn 0.8s ease-in-out;
    }}
    
    /* Results count box */
    .results-count {{
        background-color: #f9fafb;
        border-left: 4px solid {COLORS['navy_blue']};
        color: #374151;
        padding: 1rem 1.25rem;
        border-radius: 6px;
        font-size: 1.1rem;
        margin: 1.5rem 0;
        display: flex;
        align-items: center;
    }}
    
    .results-count svg {{
        margin-right: 0.5rem;
        fill: {COLORS['navy_blue']};
    }}
    
    /* Table styling */
    .stDataFrame {{
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }}
    
    .dataframe {{
        border-collapse: separate;
        border-spacing: 0;
        width: 100%;
        border-radius: 8px;
        overflow: hidden;
    }}
    
    .dataframe thead th {{
        background-color: {COLORS['navy_blue']};
        color: white;
        font-weight: 600;
        text-align: left;
        padding: 1rem;
        font-size: 0.9rem;
    }}
    
    .dataframe tbody td {{
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #e5e7eb;
        font-size: 0.9rem;
    }}
    
    .dataframe tbody tr:last-child td {{
        border-bottom: none;
    }}
    
    .dataframe tbody tr:nth-child(even) {{
        background-color: #f9fafb;
    }}
    
    .dataframe tbody tr:hover {{
        background-color: #f3f4f6;
    }}
    
    /* Download section */
    .download-section {{
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 1.5rem 0;
    }}
    
    .download-button {{
        background-color: {COLORS['navy_blue']};
        color: white;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        font-size: 0.95rem;
    }}
    
    .download-button svg {{
        margin-right: 0.5rem;
    }}
    
    .download-button:hover {{
        background-color: #000929;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    
    /* Loading state and animations */
    .stSpinner > div {{
        border-top-color: {COLORS['navy_blue']} !important;
    }}
    
    .loading-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        text-align: center;
        animation: fadeIn 0.5s ease-in-out;
    }}
    
    .loading-text {{
        margin-top: 1rem;
        color: {COLORS['navy_blue']};
        font-weight: 500;
    }}
    
    /* Sources pill */
    .source-pill {{
        display: inline-block;
        background-color: #f3f4f6;
        color: #374151;
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
        margin: 0.15rem;
        border-radius: 100px;
        border: 1px solid #e5e7eb;
    }}
    
    /* Animations */
    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}
    
    @keyframes slideIn {{
        from {{ transform: translateY(10px); opacity: 0; }}
        to {{ transform: translateY(0); opacity: 1; }}
    }}
    
    /* Hide Streamlit default elements */
    #MainMenu, footer, header {{
        visibility: hidden;
    }}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: #f1f1f1;
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {COLORS['navy_blue']};
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: #000929;
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

def to_excel(df: pd.DataFrame) -> bytes:
    """Create a well-formatted Excel file with proper styling"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write the dataframe to Excel
        df.to_excel(writer, sheet_name='Doctors', index=False)
        
        # Get the workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Doctors']
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': COLORS['navy_blue'],
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'font_size': 11
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap': True,
            'font_size': 10
        })
        
        # Set column widths
        worksheet.set_column('A:A', 30)  # Name
        worksheet.set_column('B:B', 15)  # Rating
        worksheet.set_column('C:C', 15)  # Reviews
        worksheet.set_column('D:D', 40)  # Primary Location
        worksheet.set_column('E:E', 40)  # Secondary Location
        worksheet.set_column('F:F', 30)  # Sources
        worksheet.set_column('G:G', 15)  # Total Locations
        
        # Apply formats to header row
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Apply formats to data rows
        for row_num in range(len(df)):
            for col_num in range(len(df.columns)):
                worksheet.write(row_num + 1, col_num, df.iloc[row_num, col_num], cell_format)
        
        # Add a title
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': COLORS['navy_blue']
        })
        
        # Add metadata
        metadata_format = workbook.add_format({
            'font_size': 10,
            'align': 'left',
            'valign': 'vcenter',
            'font_color': '#666666'
        })
        
        # Add title and metadata
        worksheet.insert_image('A1', 'logo.png', {'x_scale': 0.5, 'y_scale': 0.5})
        worksheet.write('A2', 'Doctor Search Results', title_format)
        worksheet.write('A3', f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', metadata_format)
        
        # Add a footer
        footer_format = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': '#666666'
        })
        
        last_row = len(df) + 5
        worksheet.write(last_row, 0, '© 2024 Supervity. All rights reserved.', footer_format)
        
        # Freeze panes
        worksheet.freeze_panes(5, 0)  # Freeze the header row and first column
    
    output.seek(0)
    return output.getvalue()

def display_search_results(results: dict):
    """Display search results in a clean, modern format with improved visual styling"""
    try:
        if not results:
            st.warning("No search results available.")
            return
            
        success = results.get('success', False)
        error = results.get('error', None)
        data = results.get('data', [])
        metadata = results.get('metadata', {})
        
        if not success:
            # Display error with animation
            error_lottie = load_lottie_url("https://lottie.host/ae48c1bc-3e83-4e09-89fc-71dfc6fdc51d/rckD4EXxQR.json")
            if error_lottie:
                st.markdown('<div style="display: flex; justify-content: center; margin: 1rem 0;">', unsafe_allow_html=True)
                st_lottie(error_lottie, height=120, key="error")
                st.markdown('</div>', unsafe_allow_html=True)
            
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
                st.markdown('<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 2rem 0;">', unsafe_allow_html=True)
                st_lottie(no_results_lottie, height=180, key="no_results")
                st.markdown('<h3 style="color:#374151; margin-top:1rem; text-align:center;">No qualified doctors found</h3>', unsafe_allow_html=True)
                st.markdown('<p style="color:#6b7280; text-align:center;">Try a different city or specialization</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Display results count with nicely formatted icon
        st.markdown(f"""
        <div class="results-count">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
            Found <strong>{len(filtered_data)}</strong> verified doctors in <strong>{metadata.get('search_duration', 0):.2f}</strong> seconds
        </div>
        """, unsafe_allow_html=True)
        
        # Create download section
        try:
            # Create a detailed dataframe for download
            df = pd.DataFrame([
                {
                    'Name': d.get('name', ''),
                    'Rating': d.get('rating', 0),
                    'Reviews': d.get('reviews', 0),
                    'Locations': '; '.join(d.get('locations', [])) if isinstance(d.get('locations'), list) else '',
                    'Specialization': d.get('specialization', ''),
                    'City': d.get('city', ''),
                    'Sources': '; '.join(d.get('contributing_sources', [])) if isinstance(d.get('contributing_sources'), list) else ''
                } for d in filtered_data
            ])
            
            # Generate Excel file
            excel_data = to_excel(df)
            
            # Create download button
            st.markdown('<div class="download-section">', unsafe_allow_html=True)
            download_label = f"doctors_{metadata.get('query', {}).get('city', 'city')}_{metadata.get('query', {}).get('specialization', 'specialty')}.xlsx"
            
            st.download_button(
                label="📥 Download as Excel",
                data=excel_data,
                file_name=download_label,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel",
                help="Download the complete results as an Excel file"
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            logger.error(f"Error creating Excel file: {type(e).__name__} - {str(e)}")
            st.error("Error preparing download file.")
        
        # Sorting and filter controls
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("<p style='color:#000b37; font-weight:600; margin-bottom:0.5rem;'>Sort By</p>", unsafe_allow_html=True)
            sort_option = st.radio(
                "Sort By",  # Use a proper label
                options=["Rating (High to Low)", "Reviews (High to Low)"],
                horizontal=True,
                label_visibility="collapsed"  # Hide the label since we're using our custom styled label
            )
        
        with col2:
            min_rating = st.select_slider(
                "Minimum Rating",
                options=[0, 3, 3.5, 4, 4.5],
                value=0
            )
        
        # Sort and filter data
        try:
            # Filter by rating
            if min_rating > 0:
                filtered_data = [
                    doc for doc in filtered_data 
                    if isinstance(doc.get('rating'), (int, float, str)) and float(doc.get('rating', 0)) >= min_rating
                ]
            
            # Sort based on selection
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
                
            # Show count after filtering
            if min_rating > 0 and len(filtered_data) != len(data):
                st.markdown(f"<p style='color:#6b7280; font-size:0.9rem; margin-top:0.5rem;'>Showing {len(filtered_data)} doctors with {min_rating}+ rating</p>", unsafe_allow_html=True)
                
        except Exception as e:
            logger.error(f"Error sorting data: {type(e).__name__} - {str(e)}")
            sorted_data = filtered_data  # Use unsorted data if sorting fails
        
        if not filtered_data:
            st.warning(f"No doctors found with rating {min_rating}+. Try lowering the minimum rating.")
            return
        
        # Create a summary DataFrame for display
        summary_data = []
        for doc in sorted_data:
            # Get primary location
            primary_location = doc.get('locations', ['Not Available'])[0] if doc.get('locations') else 'Not Available'
            
            # Get additional locations count
            additional_locations = len(doc.get('locations', [])) - 1 if len(doc.get('locations', [])) > 1 else 0
            location_text = primary_location
            if additional_locations > 0:
                location_text = f"{primary_location} (+{additional_locations} more)"
            
            # Get sources and format them as HTML
            sources = doc.get('contributing_sources', [])
            if isinstance(sources, list):
                sources_html = "".join([f'<span class="source-pill">{src.lower()}</span>' for src in sorted(set(sources))])
            else:
                sources_html = "N/A"
            
            # Format rating with stars
            rating = float(doc.get('rating', 0)) if isinstance(doc.get('rating'), (int, float, str)) else 0
            rating_str = f"{rating:.1f} ⭐" if rating > 0 else "N/A"
            
            # Add formatted row to summary data
            summary_data.append({
                'Name': doc.get('name', ''),
                'Rating': rating_str,
                'Reviews': f"{doc.get('reviews', 0):,}" if doc.get('reviews', 0) else "N/A",
                'Location': location_text,
                'Sources': sources_html
            })
        
        # Create DataFrame and display as table with improved styling
        summary_df = pd.DataFrame(summary_data)
        
        # Configure column display with HTML rendering for Sources
        st.dataframe(
            summary_df,
            use_container_width=True,
            column_config={
                'Name': st.column_config.TextColumn(
                    'Doctor Name',
                    width='large'
                ),
                'Rating': st.column_config.TextColumn(
                    'Rating',
                    width='small'
                ),
                'Reviews': st.column_config.TextColumn(
                    'Reviews',
                    width='small'
                ),
                'Location': st.column_config.TextColumn(
                    'Location',
                    width='large'
                ),
                'Sources': st.column_config.HTMLColumn(
                    'Contributing Sources',
                    width='medium'
                )
            },
            hide_index=True
        )
        
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
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        st.image(logo, use_container_width=False)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        st.markdown(f'<h3 style="color:{COLORS["navy_blue"]};">Supervity</h3>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Page title and intro with animations
    st.markdown('<h1 class="title">Find the Best Doctors</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Search across multiple platforms to discover qualified doctors in your city</p>', unsafe_allow_html=True)
    
    # Main search container with vertical flow
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="search-title">Start Your Search</h2>', unsafe_allow_html=True)
    
    # City input section - full width
    st.markdown('<p class="input-label">Enter City</p>', unsafe_allow_html=True)
    city = st.text_input(
        "City",  # Use a proper label 
        placeholder="e.g., Mumbai, Delhi, Bangalore",
        help="Enter the city where you want to find doctors",
        label_visibility="collapsed"  # Hide the label since we're using our custom styled label
    )
    
    # Specialization section
    st.markdown('<div class="spec-section">', unsafe_allow_html=True)
    st.markdown('<p class="input-label">Select Specialization</p>', unsafe_allow_html=True)
    
    # Initialize session state for specialization if not exists
    if 'selected_specialization' not in st.session_state:
        st.session_state.selected_specialization = None
    if 'custom_spec_input' not in st.session_state:
        st.session_state.custom_spec_input = ""
    
    # Create a grid of specialization buttons (4 columns)
    cols = st.columns(4)
    for idx, spec in enumerate(POPULAR_SPECIALIZATIONS):
        with cols[idx % 4]:
            # Create clickable buttons with appropriate styling
            button_type = "primary" if st.session_state.selected_specialization == spec else "secondary"
            if spec == "Other (Custom)":
                button_type = "secondary"  # Always use secondary for custom button
            if st.button(
                spec,
                key=f"spec_{idx}",
                use_container_width=True,
                type=button_type
            ):
                st.session_state.selected_specialization = spec
                if spec != "Other (Custom)":
                    st.session_state.custom_spec_input = ""
                st.rerun()
    
    # Show custom input if "Other (Custom)" is selected
    if st.session_state.selected_specialization == "Other (Custom)":
        st.markdown('<div class="custom-spec-container">', unsafe_allow_html=True)
        custom_spec = st.text_input(
            "Enter Custom Specialization",
            value=st.session_state.custom_spec_input,
            placeholder="e.g., Sports Medicine, Pain Management",
            help="Type a specific medical specialization"
        )
        if custom_spec:
            st.session_state.custom_spec_input = custom_spec
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close spec-section
    
    # Determine if search can be performed
    can_search = bool(city and (
        (st.session_state.selected_specialization and st.session_state.selected_specialization != "Other (Custom)") or
        (st.session_state.selected_specialization == "Other (Custom)" and st.session_state.custom_spec_input)
    )) and not st.session_state.get('is_searching', False)
    
    # Search button - centered
    search_button = st.button(
        "Search Doctors 🔍",
        disabled=not can_search,
        use_container_width=False
    )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close search-container
    
    # Initialize session state if not already done
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'is_searching' not in st.session_state:
        st.session_state.is_searching = False
    if 'error' not in st.session_state:
        st.session_state.error = None
    
    # Handle search button click
    if search_button:
        # Validate inputs
        if not city or not st.session_state.selected_specialization:
            st.error("Please enter both city and specialization")
        else:
            try:
                # Set searching state
                st.session_state.is_searching = True
                st.session_state.error = None
                
                # Determine the final specialization query
                final_specialization = (
                    st.session_state.custom_spec_input
                    if st.session_state.selected_specialization == "Other (Custom)"
                    else st.session_state.selected_specialization
                )
                
                # Show searching animation and message
                searching_lottie = load_lottie_url("https://lottie.host/6dbcad90-b4ca-45f4-b8a1-4eb34c634d87/jkoWAGLSQT.json")
                if searching_lottie:
                    st.markdown('<div class="loading-container">', unsafe_allow_html=True)
                    st_lottie(searching_lottie, height=150, key="searching")
                    st.markdown(f'<p class="loading-text">Searching for {final_specialization} in {city}...</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Call the search function
                with st.spinner():
                    # Add a slight delay for visual effect
                    time.sleep(0.5)
                    
                    # Make the API call
                    results = run_async(search_doctors(city, final_specialization))
                    
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
        st.markdown('<div class="results-section">', unsafe_allow_html=True)
        display_search_results(st.session_state.search_results)
        st.markdown('</div>', unsafe_allow_html=True)
    elif not st.session_state.is_searching:
        # Show welcome animation when no search has been performed yet
        welcome_lottie = load_lottie_url("https://lottie.host/c9cc25ba-fe8a-422a-b735-1611399e3b3b/zNvxQpVgN3.json")
        if welcome_lottie:
            st.markdown('<div style="display: flex; justify-content: center; margin: 2rem 0;">', unsafe_allow_html=True)
            st_lottie(welcome_lottie, height=250, key="welcome")
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 