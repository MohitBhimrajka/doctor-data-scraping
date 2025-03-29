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
    logo_path = pathlib.Path(__file__).parent / "logo.png"
    if not logo_path.exists():
        logo_path = assets_dir / "logo.png"
        if not logo_path.exists():
            logger.warning("Logo file not found. Please add 'logo.png' to the streamlit-frontend directory.")
            return None
    return Image.open(logo_path)

# Function to set favicon
def set_favicon():
    favicon_path = pathlib.Path(__file__).parent / "icon.png"
    if not favicon_path.exists():
        favicon_path = assets_dir / "icon.png"
        if not favicon_path.exists():
            logger.warning("Favicon file not found. Please add 'icon.png' to the streamlit-frontend directory.")
            return
    try:
        with open(favicon_path, "rb") as f:
            favicon_data = f.read()
        b64_favicon = base64.b64encode(favicon_data).decode("utf-8")
        favicon_html = f"""<link rel="shortcut icon" href="data:image/png;base64,{b64_favicon}">"""
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

# Custom CSS with centering and UI/UX enhancements
def apply_custom_css():
    st.markdown(f"""
    <style>
    /* Overall app styling */
    .stApp {{
        background-color: white;
    }}
    
    /* Main container centered */
    .main .block-container {{
        padding: 1rem 2rem 2rem 2rem;
        max-width: 1100px;
        margin: 0 auto;
    }}
    
    /* Center all key elements using full width containers */
    .logo-container, .search-button-container, .title, .subtitle, .search-container, .spec-section {{
        width: 100%;
        text-align: center;
    }}
    
    /* Logo container using inline-block for extra centering */
    .logo-container {{
        margin-bottom: 1rem;
    }}
    .logo-container img {{
        display: inline-block;
    }}
    
    /* Title styling */
    .title {{
        color: {COLORS['navy_blue']};
        font-weight: bold;
        font-size: 2.4rem;
        margin-bottom: 0.5rem;
        animation: fadeIn 0.8s ease-in-out;
    }}
    
    /* Subtitle styling */
    .subtitle {{
        color: {COLORS['dark_gray']};
        font-size: 1.1rem;
        margin-bottom: 2rem;
        animation: slideIn 0.8s ease-in-out;
    }}
    
    /* Search container styling */
    .search-container {{
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.07);
        padding: 2.5rem;
        margin-bottom: 2.5rem;
        border: 1px solid #e5e7eb;
        animation: fadeIn 0.8s ease-in-out;
    }}
    
    /* Search container title */
    .search-title {{
        color: {COLORS['navy_blue']};
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 2rem;
    }}
    
    /* Input fields styling and centering */
    .input-label {{
        font-weight: 600;
        color: {COLORS['navy_blue']};
        font-size: 1rem;
        margin-bottom: 0.6rem;
    }}
    .stTextInput {{
        margin-bottom: 1.5rem;
    }}
    .stTextInput > div > div > input {{
        border-radius: 8px;
        border: 1px solid #d1d5db;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.2s ease;
        text-align: center;
    }}
    .stTextInput > div > div > input:focus {{
        border-color: {COLORS['navy_blue']};
        box-shadow: 0 0 0 3px rgba(0, 11, 55, 0.1);
    }}
    
    /* Specialization section */
    .spec-section {{
        margin-top: 1.5rem;
        margin-bottom: 2rem;
    }}
    div[data-testid="stHorizontalBlock"] {{
         gap: 0.75rem;
    }}
    .stButton > button {{
        margin-bottom: 0.75rem;
    }}
    
    /* Default button styling */
    .stButton > button[data-baseweb="button"][kind="secondary"] {{
        background-color: #f9fafb;
        color: #374151;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.6rem 0.5rem;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        font-weight: 500;
    }}
    .stButton > button[data-baseweb="button"][kind="secondary"]:hover {{
        background-color: #f3f4f6;
        border-color: #d1d5db;
        transform: translateY(-1px);
    }}
    
    /* Primary button styling (selected specialization) */
    .stButton > button[data-baseweb="button"][kind="primary"] {{
        background-color: #ccd3e8 !important;
        color: {COLORS['navy_blue']} !important;
        border: 2px solid {COLORS['navy_blue']} !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        border-radius: 8px;
        padding: 0.6rem 0.5rem;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }}
    .stButton > button[data-baseweb="button"][kind="primary"]:hover {{
        background-color: #b3bfdc !important;
        border-color: {COLORS['navy_blue']} !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.15) !important;
    }}
    
    /* Custom "Other (Custom)" button styling */
    .stButton > button[data-key*="spec_"]:has-text("Other (Custom)") {{
        background-color: #f0f0f0 !important;
        color: #333333 !important;
        border: 2px dashed {COLORS['lime_green']} !important;
        font-weight: bold !important;
    }}
    .stButton > button[data-key*="spec_"]:has-text("Other (Custom)"):hover {{
        background-color: #e0e0e0 !important;
        border-color: {COLORS['lime_green']} !important;
    }}
    
    /* Custom specialization input container */
    .custom-spec-container {{
        margin-top: 1.5rem;
        padding: 1.5rem;
        background-color: #f9fafb;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        animation: fadeIn 0.5s ease-in-out;
    }}
    
    /* Centering the search button container */
    .search-button-container {{
        width: 100%;
        text-align: center;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }}
    .search-button-container button {{
        background-image: linear-gradient(to bottom, #001f70, #000b37) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 1rem 4rem !important;
        border-radius: 10px !important;
        border: none !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
        font-size: 1.3rem !important;
        cursor: pointer !important;
    }}
    .search-button-container button:hover {{
        background-image: linear-gradient(to bottom, #001a5e, #00082a) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
    }}
    .search-button-container button:active {{
        transform: translateY(0) !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.15) !important;
        background-image: linear-gradient(to bottom, #001a5e, #00082a) !important;
    }}
    .search-button-container button:disabled {{
        background-color: #d1d5db !important;
        background-image: none !important;
        color: #6b7280 !important;
        cursor: not-allowed !important;
    }}
    
    /* Results section */
    .results-section {{
        animation: fadeIn 0.8s ease-in-out;
        margin-top: 2.5rem;
    }}
    .results-count {{
        background-color: #eef2ff;
        border-left: 5px solid {COLORS['navy_blue']};
        color: {COLORS['navy_blue']};
        padding: 1rem 1.5rem;
        border-radius: 8px;
        font-size: 1rem;
        margin: 2rem 0;
        display: flex;
        align-items: baseline;
        flex-wrap: wrap;
        gap: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .results-count svg {{
        margin-right: 0.75rem;
        fill: {COLORS['navy_blue']};
        flex-shrink: 0;
    }}
    .results-count strong {{
        font-weight: 600;
    }}
    
    /* Sorting/Filtering controls */
    div[data-testid="stHorizontalBlock"] {{
        margin-bottom: 1.5rem;
    }}
    p:contains("Sort By"), p:contains("Minimum Rating") {{
         color: #000b37;
         font-weight: 600;
         margin-bottom: 0.5rem;
         font-size: 0.95rem;
    }}
    .stRadio > div {{
        gap: 0.8rem;
    }}
    .stSelectSlider {{
        margin-top: 1.8rem;
    }}
    
    /* DataFrame styling */
    .stDataFrame {{
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #e5e7eb;
    }}
    .dataframe {{
        border-collapse: separate;
        border-spacing: 0;
        width: 100%;
        border-radius: 8px;
        overflow: hidden;
    }}
    .dataframe thead th {{
        background-color: #f8f9fa;
        color: #495057;
        font-weight: 600;
        text-align: left;
        padding: 0.8rem 1rem;
        font-size: 0.9rem;
        border-bottom: 2px solid #dee2e6;
    }}
    .dataframe tbody td {{
        padding: 0.8rem 1rem;
        border-bottom: 1px solid #e5e7eb;
        font-size: 0.95rem;
        vertical-align: middle;
        line-height: 1.5;
    }}
    .dataframe tbody tr:last-child td {{
        border-bottom: none;
    }}
    .dataframe tbody tr:nth-child(even) {{
        background-color: #fcfcfd;
    }}
    .dataframe tbody tr:hover {{
        background-color: #f1f3f5;
    }}
    
    /* Download section */
    .download-section {{
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 2rem 0;
    }}
    .stDownloadButton > button {{
        background-color: {COLORS['navy_blue']} !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 8px !important;
        border: none !important;
        transition: all 0.2s ease !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-decoration: none !important;
        font-size: 0.95rem !important;
        cursor: pointer !important;
    }}
    .stDownloadButton > button:hover {{
        background-color: #000929 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }}
    
    /* Loading animations */
    .stSpinner > div {{
        border-top-color: {COLORS['navy_blue']} !important;
    }}
    .loading-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 3rem 1rem;
        text-align: center;
        animation: fadeIn 0.5s ease-in-out;
    }}
    .loading-text {{
        margin-top: 1.5rem;
        color: {COLORS['navy_blue']};
        font-weight: 500;
        font-size: 1.1rem;
    }}
    
    /* Sources pill */
    .source-pill {{
        display: inline-block;
        background-color: #e9ecef;
        color: #495057;
        font-size: 0.78rem;
        padding: 0.2rem 0.6rem;
        margin: 0.15rem 0.2rem;
        border-radius: 12px;
        border: 1px solid #dee2e6;
        white-space: nowrap;
    }}
    
    /* Animations */
    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}
    @keyframes slideIn {{
        from {{ transform: translateY(15px); opacity: 0; }}
        to {{ transform: translateY(0); opacity: 1; }}
    }}
    
    /* Hide default Streamlit menu */
    #MainMenu, footer, header {{
        visibility: hidden;
    }}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {{
        width: 10px;
        height: 10px;
    }}
    ::-webkit-scrollbar-track {{
        background: #f8f9fa;
        border-radius: 5px;
    }}
    ::-webkit-scrollbar-thumb {{
        background: #ced4da;
        border-radius: 5px;
        border: 2px solid #f8f9fa;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: #adb5bd;
    }}
    </style>
    """, unsafe_allow_html=True)

async def search_doctors(city: str, specialization: str) -> Dict[str, Any]:
    try:
        logger.info(f"Searching for {specialization} in {city}")
        payload = {"city": city, "specialization": specialization}
        logger.info(f"Sending request to {BACKEND_API_URL}/api/search with payload: {payload}")
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{BACKEND_API_URL}/api/search", json=payload, timeout=120.0)
            logger.info(f"Got response with status code: {response.status_code}")
            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.info(f"Search successful. Found {result.get('metadata', {}).get('total', 0)} doctors")
                    if 'data' not in result or result['data'] is None:
                        logger.warning(f"API returned success but no data field or empty data: {result}")
                        result['data'] = []
                    return result
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response: {response.text[:200]}")
                    return {"success": False, "error": "Failed to parse JSON response from backend", "data": [], "metadata": {"total": 0}}
            else:
                logger.error(f"API call failed with status code {response.status_code}: {response.text[:200]}")
                return {"success": False, "error": f"API call failed with status code {response.status_code}", "data": [], "metadata": {"total": 0}}
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        return {"success": False, "error": f"Failed to connect to the backend: {str(e)}", "data": [], "metadata": {"total": 0}}
    except Exception as e:
        logger.error(f"Unexpected error during API call: {type(e).__name__} - {str(e)}")
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}", "data": [], "metadata": {"total": 0}}

def run_async(coroutine):
    return asyncio.run(coroutine)

def is_valid_location(location: str, city: str) -> bool:
    if not isinstance(location, str) or len(location) < 5:
        return False
    city_lower = city.lower()
    location_lower = location.lower()
    generic_locations = [
        "multiple locations", "available online", "teleconsultation", 
        "consultation available", "multiple branches", "across india",
        "pan india", "all over india", "all major cities"
    ]
    for generic in generic_locations:
        if generic in location_lower:
            return False
    other_cities = ["delhi", "mumbai", "bangalore", "bengaluru", "chennai", "kolkata", "hyderabad", "pune", "ahmedabad", "jaipur", "lucknow"]
    for other_city in other_cities:
        if other_city != city_lower and other_city in location_lower:
            travel_indicators = ["visit", "travels to", "also available in", "consultation in"]
            if not any(indicator in location_lower for indicator in travel_indicators):
                return False
    return True

def filter_doctor_data(doctors_data: List[Dict], city: str) -> List[Dict]:
    filtered_data = []
    for doctor in doctors_data:
        if not isinstance(doctor, dict):
            continue
        name = doctor.get('name', '')
        if not name or any(x in name for x in ['XYZ', 'ABC', 'PQR']):
            continue
        clean_doctor = {
            'name': name,
            'rating': doctor.get('rating', 0),
            'reviews': doctor.get('reviews', 0),
            'specialization': doctor.get('specialization', ''),
            'city': doctor.get('city', '')
        }
        locations = doctor.get('locations', [])
        if isinstance(locations, list):
            clean_doctor['locations'] = [loc for loc in locations if isinstance(loc, str) and is_valid_location(loc, city)]
        else:
            clean_doctor['locations'] = []
        if clean_doctor['locations']:
            clean_doctor['contributing_sources'] = doctor.get('contributing_sources', [])
            filtered_data.append(clean_doctor)
    return filtered_data

def to_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Doctors', index=False, startrow=0)
        workbook = writer.book
        worksheet = writer.sheets['Doctors']
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
            'valign': 'top', 
            'text_wrap': True,
            'font_size': 10
        })
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        for row_num in range(len(df)):
            worksheet.set_row(row_num + 1, None, cell_format)
            for col_num in range(len(df.columns)):
                cell_value = df.iloc[row_num, col_num]
                if pd.isna(cell_value):
                    worksheet.write_blank(row_num + 1, col_num, None, cell_format)
                else:
                    worksheet.write_string(row_num + 1, col_num, str(cell_value), cell_format)
        worksheet.set_column('A:A', 35)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:C', 12)
        worksheet.set_column('D:D', 45)
        worksheet.set_column('E:E', 25)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 45)
    output.seek(0)
    return output.getvalue()

def display_search_results(results: dict):
    try:
        if not results:
            st.warning("No search results available.")
            return
        success = results.get('success', False)
        error = results.get('error', None)
        data = results.get('data', [])
        metadata = results.get('metadata', {})
        if not success:
            error_lottie = load_lottie_url("https://lottie.host/ae48c1bc-3e83-4e09-89fc-71dfc6fdc51d/rckD4EXxQR.json")
            if error_lottie:
                st.markdown('<div style="display: flex; justify-content: center; margin: 1rem 0;">', unsafe_allow_html=True)
                st_lottie(error_lottie, height=120, key="error")
                st.markdown('</div>', unsafe_allow_html=True)
            st.error(f"Search failed: {error}")
            return
        city = metadata.get('query', {}).get('city', '')
        filtered_data = filter_doctor_data(data, city)
        logger.info(f"Displaying search results: original_count={len(data)}, filtered_count={len(filtered_data)}")
        if not filtered_data:
            no_results_lottie = load_lottie_url("https://lottie.host/be2fa43c-1084-4583-8be6-0d1cd6c41f21/gTzFHlwqak.json")
            if no_results_lottie:
                st.markdown('<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 2rem 0;">', unsafe_allow_html=True)
                st_lottie(no_results_lottie, height=180, key="no_results")
                st.markdown('<h3 style="color:#374151; margin-top:1rem; text-align:center;">No qualified doctors found</h3>', unsafe_allow_html=True)
                st.markdown('<p style="color:#6b7280; text-align:center;">Try a different city or specialization</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            return
        st.markdown(f"""
        <div class="results-count">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
            Found <strong>{len(filtered_data)}</strong> verified doctors in <strong>{metadata.get('search_duration', 0):.2f}</strong> seconds
        </div>
        """, unsafe_allow_html=True)
        try:
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
            excel_data = to_excel(df)
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
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("<p style='color:#000b37; font-weight:600; margin-bottom:0.5rem;'>Sort By</p>", unsafe_allow_html=True)
            sort_option = st.radio(
                "Sort By",
                options=["Rating (High to Low)", "Reviews (High to Low)"],
                horizontal=True,
                label_visibility="collapsed"
            )
        with col2:
            min_rating = st.select_slider("Minimum Rating", options=[0, 3, 3.5, 4, 4.5], value=0)
        try:
            if min_rating > 0:
                filtered_data = [doc for doc in filtered_data if isinstance(doc.get('rating'), (int, float, str)) and float(doc.get('rating', 0)) >= min_rating]
            if sort_option == "Rating (High to Low)":
                sorted_data = sorted(filtered_data, key=lambda x: (float(x.get('rating', 0)) if isinstance(x.get('rating'), (int, float, str)) else 0, int(x.get('reviews', 0)) if isinstance(x.get('reviews'), (int, float, str)) else 0), reverse=True)
            else:
                sorted_data = sorted(filtered_data, key=lambda x: (int(x.get('reviews', 0)) if isinstance(x.get('reviews'), (int, float, str)) else 0, float(x.get('rating', 0)) if isinstance(x.get('rating'), (int, float, str)) else 0), reverse=True)
            if min_rating > 0 and len(filtered_data) != len(data):
                st.markdown(f"<p style='color:#6b7280; font-size:0.9rem; margin-top:0.5rem;'>Showing {len(filtered_data)} doctors with {min_rating}+ rating</p>", unsafe_allow_html=True)
        except Exception as e:
            logger.error(f"Error sorting data: {type(e).__name__} - {str(e)}")
            sorted_data = filtered_data
        if not filtered_data:
            st.warning(f"No doctors found with rating {min_rating}+. Try lowering the minimum rating.")
            return
        summary_data = []
        for doc in sorted_data:
            primary_location = doc.get('locations', ['Not Available'])[0] if doc.get('locations') else 'Not Available'
            additional_locations = len(doc.get('locations', [])) - 1 if len(doc.get('locations', [])) > 1 else 0
            location_text = primary_location if additional_locations == 0 else f"{primary_location} (+{additional_locations} more)"
            sources = doc.get('contributing_sources', [])
            sources_text = ", ".join(sorted(list(set(src.lower() for src in sources)))) if isinstance(sources, list) else "N/A"
            rating = float(doc.get('rating', 0)) if isinstance(doc.get('rating'), (int, float, str)) else 0
            rating_str = f"{rating:.1f} ⭐" if rating > 0 else "N/A"
            summary_data.append({
                'Name': doc.get('name', ''),
                'Rating': rating_str,
                'Reviews': f"{doc.get('reviews', 0):,}" if doc.get('reviews', 0) else "N/A",
                'Location': location_text,
                'Sources': sources_text
            })
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(
            summary_df,
            use_container_width=True,
            column_config={
                'Name': st.column_config.TextColumn('Doctor Name', width='large'),
                'Rating': st.column_config.TextColumn('Rating', width='small'),
                'Reviews': st.column_config.TextColumn('Reviews', width='small'),
                'Location': st.column_config.TextColumn('Location', width='large'),
                'Sources': st.column_config.TextColumn('Contributing Sources', width='medium')
            },
            hide_index=True
        )
    except Exception as e:
        logger.error(f"Error displaying search results: {type(e).__name__} - {str(e)}")
        st.error(f"Error displaying search results: {str(e)}")

def main():
    st.set_page_config(
        page_title="Find the Best Doctors | Supervity",
        page_icon="🩺",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    set_favicon()
    apply_custom_css()
    logo = load_logo()
    if logo:
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        st.image(logo, width=180)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        st.markdown(f'<h3 style="color:{COLORS["navy_blue"]};">Supervity</h3>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="title">Find the Best Doctors</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Search across multiple platforms to discover qualified doctors in your city</p>', unsafe_allow_html=True)
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="search-title">Start Your Search</h2>', unsafe_allow_html=True)
    st.markdown('<p class="input-label">Enter City</p>', unsafe_allow_html=True)
    city = st.text_input("City", placeholder="e.g., Mumbai, Delhi, Bangalore", help="Enter the city where you want to find doctors", label_visibility="collapsed")
    st.markdown('<div class="spec-section">', unsafe_allow_html=True)
    st.markdown('<p class="input-label">Select Specialization</p>', unsafe_allow_html=True)
    if 'selected_specialization' not in st.session_state:
        st.session_state.selected_specialization = None
    if 'custom_spec_input' not in st.session_state:
        st.session_state.custom_spec_input = ""
    cols = st.columns(4)
    for idx, spec in enumerate(POPULAR_SPECIALIZATIONS):
        with cols[idx % 4]:
            button_type = "primary" if st.session_state.selected_specialization == spec else "secondary"
            if spec == "Other (Custom)":
                button_type = "secondary"
            if st.button(spec, key=f"spec_{idx}", use_container_width=True, type=button_type):
                st.session_state.selected_specialization = spec
                if spec != "Other (Custom)":
                    st.session_state.custom_spec_input = ""
                st.rerun()
    if st.session_state.selected_specialization == "Other (Custom)":
        st.markdown('<div class="custom-spec-container">', unsafe_allow_html=True)
        custom_spec = st.text_input("Enter Custom Specialization", value=st.session_state.custom_spec_input, placeholder="e.g., Sports Medicine, Pain Management", help="Type a specific medical specialization")
        if custom_spec:
            st.session_state.custom_spec_input = custom_spec
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    can_search = bool(city and ((st.session_state.selected_specialization and st.session_state.selected_specialization != "Other (Custom)") or (st.session_state.selected_specialization == "Other (Custom)" and st.session_state.custom_spec_input))) and not st.session_state.get('is_searching', False)
    st.markdown('<div class="search-button-container">', unsafe_allow_html=True)
    search_button = st.button("Search Doctors 🔍", disabled=not can_search, use_container_width=False)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'is_searching' not in st.session_state:
        st.session_state.is_searching = False
    if 'error' not in st.session_state:
        st.session_state.error = None
    if search_button:
        if not city or not st.session_state.selected_specialization:
            st.error("Please enter both city and specialization")
        else:
            try:
                st.session_state.is_searching = True
                st.session_state.error = None
                final_specialization = st.session_state.custom_spec_input if st.session_state.selected_specialization == "Other (Custom)" else st.session_state.selected_specialization
                searching_lottie = load_lottie_url("https://lottie.host/6dbcad90-b4ca-45f4-b8a1-4eb34c634d87/jkoWAGLSQT.json")
                if searching_lottie:
                    st.markdown('<div class="loading-container">', unsafe_allow_html=True)
                    st_lottie(searching_lottie, height=150, key="searching")
                    st.markdown(f'<p class="loading-text">Searching for {final_specialization} in {city}...</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                with st.spinner():
                    time.sleep(0.5)
                    results = run_async(search_doctors(city, final_specialization))
                    st.session_state.search_results = results
                    st.session_state.is_searching = False
                    if not results.get('success', False):
                        error_message = results.get('error', 'Unknown error')
                        error_detail = results.get('detail', '')
                        error_text = f"{error_message}"
                        if error_detail:
                            error_text += f"\nDetails: {error_detail}"
                        st.session_state.error = error_text
                        st.error(error_text)
                    st.rerun()
            except Exception as e:
                st.session_state.is_searching = False
                error_message = f"Error: {type(e).__name__} - {str(e)}"
                st.session_state.error = error_message
                st.error(error_message)
                logger.error(f"Search error: {error_message}")
    if st.session_state.search_results:
        st.markdown('<div class="results-section">', unsafe_allow_html=True)
        display_search_results(st.session_state.search_results)
        st.markdown('</div>', unsafe_allow_html=True)
    elif not st.session_state.is_searching:
        welcome_lottie = load_lottie_url("https://lottie.host/c9cc25ba-fe8a-422a-b735-1611399e3b3b/zNvxQpVgN3.json")
        if welcome_lottie:
            st.markdown('<div style="width:100%; text-align:center; margin:2rem 0;">', unsafe_allow_html=True)
            st_lottie(welcome_lottie, height=250, key="welcome")
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
