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
    .doctor-card {{
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }}
    .doctor-name {{
        color: {COLORS['navy_blue']};
        font-weight: bold;
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }}
    .metric-label {{
        color: {COLORS['navy_blue']};
        font-weight: bold;
        font-size: 0.9rem;
    }}
    .metric-value {{
        color: {COLORS['dark_gray']};
        font-size: 1.1rem;
    }}
    .location-item {{
        background-color: #f8f9fa;
        padding: 0.3rem 0.6rem;
        border-radius: 5px;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        display: inline-block;
        font-size: 0.9rem;
    }}
    .phone-item {{
        background-color: #e8f4fc;
        padding: 0.3rem 0.6rem;
        border-radius: 5px;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        display: inline-block;
        font-size: 0.9rem;
    }}
    .source-item {{
        background-color: #e9f7ef;
        padding: 0.3rem 0.6rem;
        border-radius: 5px;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        display: inline-block;
        font-size: 0.9rem;
    }}
    .icon {{
        margin-right: 0.3rem;
    }}
    .search-status {{
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
        margin: 1rem 0;
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

def display_doctor_card(doctor: dict):
    """Display a single doctor's information focusing on the core fields"""
    with st.container():
        st.markdown('<div class="doctor-card">', unsafe_allow_html=True)
        
        # Doctor name
        st.markdown(f'<div class="doctor-name">{doctor["name"]}</div>', unsafe_allow_html=True)
        
        # Rating and reviews in columns
        col1, col2 = st.columns(2)
        with col1:
            stars = "⭐" * int(doctor['rating']) + ("⭐" if doctor['rating'] % 1 >= 0.5 else "")
            st.markdown(f"**Rating:** {doctor['rating']:.1f} {stars}")
        with col2:
            st.markdown(f"**Reviews:** {doctor['reviews']} 👥")
        
        # Location(s)
        if doctor.get('locations'):
            st.markdown("**📍 Locations:**")
            locations_html = ""
            for location in doctor['locations']:
                locations_html += f'<span class="location-item">{location}</span>'
            st.markdown(locations_html, unsafe_allow_html=True)
        else:
            st.markdown("**📍 Locations:** <span style='color: #888;'>Not Available</span>", unsafe_allow_html=True)
        
        # Phone Number(s)
        if doctor.get('phone_numbers'):
            st.markdown("**📞 Phone Numbers:**")
            phones_html = ""
            for phone in doctor['phone_numbers']:
                # Make phone numbers clickable with tel: links
                phones_html += f'<span class="phone-item"><a href="tel:{phone}">{phone}</a></span>'
            st.markdown(phones_html, unsafe_allow_html=True)
        else:
            st.markdown("**📞 Phone Numbers:** <span style='color: #888;'>Not Available</span>", unsafe_allow_html=True)
        
        # Source URL(s)
        if doctor.get('source_urls'):
            st.markdown("**🔗 Source URLs:**")
            sources_html = ""
            for i, url in enumerate(doctor['source_urls']):
                # Extract domain name for display
                try:
                    # Get domain from URL
                    if '//' in url:
                        domain = url.split('//')[1].split('/')[0]
                    else:
                        domain = url.split('/')[0]
                    
                    # Remove www. if present
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    
                    # Use domain as link text
                    sources_html += f'<span class="source-item"><a href="{url}" target="_blank">{domain}</a></span>'
                except:
                    # Fallback to numbered source if domain extraction fails
                    sources_html += f'<span class="source-item"><a href="{url}" target="_blank">Source {i+1}</a></span>'
            st.markdown(sources_html, unsafe_allow_html=True)
        else:
            st.markdown("**🔗 Source URLs:** <span style='color: #888;'>Not Available</span>", unsafe_allow_html=True)
        
        # Add a bit more space between cards
        st.markdown('<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def display_search_results(results: dict):
    """Display search results with a focus on core fields"""
    if not results.get('success', False):
        error_message = results.get('error', 'Unknown error')
        st.error(f"Search failed: {error_message}")
        return
    
    data = results.get('data', [])
    metadata = results.get('metadata', {})
    
    if not data:
        st.warning("No doctors found matching your search criteria.")
        return
    
    # Display metadata and search stats
    st.markdown(f"""
    <div class="results-count">
        Found {len(data)} doctors in {metadata.get('search_duration', 0):.2f} seconds
    </div>
    """, unsafe_allow_html=True)
    
    # Sorting options
    sort_option = st.selectbox(
        "Sort results by:",
        options=["Rating (High to Low)", "Reviews (High to Low)"]
    )
    
    # Sort data based on selection
    if sort_option == "Rating (High to Low)":
        sorted_data = sorted(data, key=lambda x: (x.get('rating', 0), x.get('reviews', 0)), reverse=True)
    else:  # Reviews (High to Low)
        sorted_data = sorted(data, key=lambda x: (x.get('reviews', 0), x.get('rating', 0)), reverse=True)
    
    # Display all doctors
    for doctor in sorted_data:
        display_doctor_card(doctor)
    
    # Create dataframe for download - improved CSV formatting
    df = pd.DataFrame([
        {
            'Name': d.get('name', ''),
            'Rating': d.get('rating', 0),
            'Reviews': d.get('reviews', 0),
            'Locations': '; '.join(d.get('locations', [])),
            'Phone Numbers': '; '.join(d.get('phone_numbers', [])),
            'Source URLs': '; '.join(d.get('source_urls', [])),
            'Specialization': d.get('specialization', ''),
            'City': d.get('city', ''),
            'Contributing Sources': '; '.join(d.get('contributing_sources', []))
        } for d in sorted_data
    ])
    
    # Provide download options
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
            'locations': d.get('locations', []),
            'phone_numbers': d.get('phone_numbers', []),
            'source_urls': d.get('source_urls', []),
            'specialization': d.get('specialization', ''),
            'city': d.get('city', ''),
            'contributing_sources': d.get('contributing_sources', [])
        } for d in sorted_data], indent=2)
        
        st.download_button(
            label="Download as JSON",
            data=json_data,
            file_name=f"doctors_{metadata.get('query', {}).get('city', 'city')}_{metadata.get('query', {}).get('specialization', 'specialty')}.json",
            mime="application/json"
        )

def main():
    # Set page config
    st.set_page_config(
        page_title="Doctor Search | Supervity",
        page_icon="🩺",
        layout="wide"
    )
    
    # Apply custom CSS
    apply_custom_css()
    
    # Title and description
    st.markdown('<div class="title">Doctor Search</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Find doctors by specialization and location</div>', unsafe_allow_html=True)
    
    # Search form in columns
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        city = st.text_input("City", placeholder="Enter city name")
    
    with col2:
        specialization = st.selectbox(
            "Specialization",
            options=list(specializations.values())
        )
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        search_button = st.button("Search", use_container_width=True)
    
    # Handle search
    if search_button:
        if not city or not specialization:
            st.warning("Please enter both city and specialization.")
            return
            
        with st.spinner("Searching for doctors, please wait..."):
            st.markdown(f"""
            <div class="search-status" style="background-color: #e8f4fd;">
                Searching for {specialization} doctors in {city}...
            </div>
            """, unsafe_allow_html=True)
            
            try:
                # Call backend API
                results = run_async(search_doctors(city, specialization))
                
                # Check for specific connection errors
                if not results.get('success', False) and "Failed to connect to the backend" in results.get('error', ''):
                    st.error("Cannot connect to the backend server. Please check if the server is running and try again.")
                    st.info("Technical details: " + results.get('error', ''))
                    return
                    
                # Display results
                display_search_results(results)
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
                logger.error(f"Frontend error: {str(e)}")
    
    # Show instructions if no search has been performed
    if 'results' not in locals():
        st.info("""
        ### How to use:
        1. Enter a city name
        2. Select a medical specialization
        3. Click the Search button
        
        You'll get a list of doctors with their ratings, reviews, locations, phone numbers, and source links.
        """)

if __name__ == "__main__":
    main() 