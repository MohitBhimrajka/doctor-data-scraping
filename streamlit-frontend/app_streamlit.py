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

# Create logs directory if it doesn't exist
log_dir = pathlib.Path(__file__).parent.parent / 'logs'
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
    }}
    .stButton > button {{
        background-color: {COLORS['lime_green']};
        color: white;
    }}
    .stButton > button:hover {{
        background-color: {COLORS['navy_blue']};
        color: white;
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
        
        # Make the API call
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_API_URL}/api/search",
                json=payload,
                timeout=60.0  # Longer timeout as search can take time
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Search successful. Found {result.get('metadata', {}).get('total', 0)} doctors")
                return result
            else:
                logger.error(f"API call failed with status code {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "error": f"API call failed with status code {response.status_code}",
                    "data": None,
                    "metadata": {"total": 0}
                }
                
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to connect to the backend: {str(e)}",
            "data": None,
            "metadata": {"total": 0}
        }
    except Exception as e:
        logger.error(f"Unexpected error during API call: {str(e)}")
        return {
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}",
            "data": None,
            "metadata": {"total": 0}
        }

def run_async(coroutine):
    """Helper function to run async functions in Streamlit"""
    return asyncio.run(coroutine)

def main():
    # Set page config
    st.set_page_config(
        page_title="Doctor Search | Supervity",
        page_icon="assets/Supervity_Icon.png",
        layout="wide"
    )
    
    # Apply custom CSS
    apply_custom_css()
    
    # Initialize session state for storing search results
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'search_error' not in st.session_state:
        st.session_state.search_error = None
    if 'is_searching' not in st.session_state:
        st.session_state.is_searching = False
    
    # Display logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("assets/Supervity_Black_Without_Background.png", width=300)
    
    # Header
    st.markdown("<h1 class='title'>Doctor Search</h1>", unsafe_allow_html=True)
    st.markdown("Find healthcare providers in your area with our advanced search tool.")
    
    # Create a form for inputs to prevent automatic resubmission
    with st.form(key="search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            city = st.text_input("City", placeholder="Enter city name", key="city")
        
        with col2:
            specialization_key = st.selectbox(
                "Specialization",
                options=list(specializations.keys()),
                format_func=lambda key: specializations[key],
                key="specialization"
            )
        
        # Search button
        submitted = st.form_submit_button("Search Doctors", type="primary")
    
    # Process form submission
    if submitted:
        if not city.strip():
            st.error("Please enter a city name")
        else:
            st.session_state.is_searching = True
            st.session_state.search_results = None
            st.session_state.search_error = None
            
            with st.spinner("Searching for doctors... Please wait."):
                response = run_async(search_doctors(city, specialization_key))
                
                if response["success"]:
                    st.session_state.search_results = response
                else:
                    st.session_state.search_error = response["error"]
                
            st.session_state.is_searching = False
    
    # Display search results
    if st.session_state.search_results:
        results = st.session_state.search_results
        doctors = results.get("data", [])
        total = results.get("metadata", {}).get("total", 0)
        
        st.success(f"Found {total} doctors")
        
        if doctors:
            # Process the data for display
            display_data = []
            for doctor in doctors:
                display_data.append({
                    "Name": doctor["name"],
                    "Rating": f"{doctor['rating']:.1f}",
                    "Reviews": doctor["reviews"],
                    "Location": ", ".join(doctor["locations"]),
                    "Source": doctor["source"],
                    "Specialization": doctor["specialization"]
                })
            
            # Convert to DataFrame
            df = pd.DataFrame(display_data)
            
            # Display as a table
            st.dataframe(df, use_container_width=True)
            
            # Download button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name=f"doctor_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No doctors found matching your search criteria.")
    
    # Display error message
    if st.session_state.search_error:
        st.error(f"Error: {st.session_state.search_error}")
    
    # Display backend connection status
    with st.expander("API Connection Status"):
        st.info(f"Connected to backend API at: {BACKEND_API_URL}")

if __name__ == "__main__":
    main() 