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
        margin-bottom: 1rem;
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
    .quality-score {{
        font-size: 1.2rem;
        font-weight: bold;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
    }}
    .quality-high {{
        background-color: #d4edda;
        color: #155724;
    }}
    .quality-medium {{
        background-color: #fff3cd;
        color: #856404;
    }}
    .quality-low {{
        background-color: #f8d7da;
        color: #721c24;
    }}
    .source-tag {{
        background-color: {COLORS['light_gray']};
        color: {COLORS['dark_gray']};
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }}
    .verified-badge {{
        background-color: {COLORS['lime_green']};
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
        margin-left: 0.5rem;
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
    """Display a single doctor's information in a card format"""
    with st.container():
        st.markdown('<div class="doctor-card">', unsafe_allow_html=True)
        
        # Header row with name, rating, and verified badge
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            header = f"### {doctor['name']}"
            if doctor.get('verified', False):
                header += ' <span class="verified-badge">✓ Verified</span>'
            st.markdown(header, unsafe_allow_html=True)
        
        with col2:
            st.metric("Rating", f"{doctor['rating']:.1f} ⭐")
        
        with col3:
            st.metric("Reviews", f"{doctor['reviews']} 👥")
        
        # Data quality score
        quality_score = doctor.get('data_quality_score', 0.0)
        quality_class = (
            'quality-high' if quality_score >= 0.7
            else 'quality-medium' if quality_score >= 0.4
            else 'quality-low'
        )
        st.markdown(
            f'<div class="quality-score {quality_class}">Data Quality: {quality_score:.2f}</div>',
            unsafe_allow_html=True
        )
        
        # Main information columns
        col1, col2 = st.columns(2)
        
        with col1:
            if doctor.get('experience'):
                st.markdown(f"**Experience:** {doctor['experience']}")
            if doctor.get('fees'):
                st.markdown(f"**Fees:** {doctor['fees']}")
            if doctor.get('qualifications'):
                st.markdown(f"**Qualifications:** {doctor['qualifications']}")
            if doctor.get('registration'):
                st.markdown(f"**Registration:** {doctor['registration']}")
            if doctor.get('languages'):
                st.markdown(f"**Languages:** {', '.join(doctor['languages'])}")
        
        with col2:
            if doctor.get('timings'):
                st.markdown(f"**Timings:** {doctor['timings']}")
            if doctor.get('locations'):
                st.markdown(f"**Locations:** {', '.join(doctor['locations'])}")
            if doctor.get('hospitals'):
                st.markdown(f"**Hospitals:** {', '.join(doctor['hospitals'])}")
            if doctor.get('subspecialties'):
                st.markdown(f"**Subspecialties:** {', '.join(doctor['subspecialties'])}")
        
        # Expandable sections
        if doctor.get('expertise') or doctor.get('services'):
            with st.expander("Expertise & Services"):
                if doctor.get('expertise'):
                    st.markdown(f"**Areas of Expertise:** {doctor['expertise']}")
                if doctor.get('services'):
                    st.markdown("**Services Offered:**")
                    for service in doctor['services']:
                        st.markdown(f"- {service}")
        
        if doctor.get('education') or doctor.get('awards_and_recognitions'):
            with st.expander("Education & Achievements"):
                if doctor.get('education'):
                    st.markdown("**Education:**")
                    for edu in doctor['education']:
                        st.markdown(f"- {edu}")
                if doctor.get('awards_and_recognitions'):
                    st.markdown("**Awards & Recognitions:**")
                    for award in doctor['awards_and_recognitions']:
                        st.markdown(f"- {award}")
        
        # Source information
        st.markdown("**Data Sources:**")
        sources_html = ' '.join([
            f'<span class="source-tag">{source}</span>'
            for source in doctor.get('contributing_sources', [doctor.get('source')])
        ])
        st.markdown(sources_html, unsafe_allow_html=True)
        
        # Last updated
        if doctor.get('last_updated'):
            st.markdown(
                f"<small>Last updated: {doctor['last_updated']}</small>",
                unsafe_allow_html=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_search_results(results: dict):
    """Display search results with enhanced visualization"""
    doctors = results.get("data", [])
    metadata = results.get("metadata", {})
    
    # Display search summary
    st.markdown("## Search Results")
    
    # Create metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Doctors", metadata.get("total", 0))
    with col2:
        avg_quality = metadata.get("data_quality", {}).get("average_score", 0)
        st.metric("Avg. Quality Score", f"{avg_quality:.2f}")
    with col3:
        verified = metadata.get("data_quality", {}).get("verified_profiles", 0)
        st.metric("Verified Profiles", verified)
    with col4:
        duration = metadata.get("search_duration", 0)
        st.metric("Search Time", f"{duration:.1f}s")
    
    # Display source information
    sources = metadata.get("sources_used", [])
    if sources:
        st.markdown("### Data Sources")
        source_cols = st.columns(len(sources))
        for idx, source in enumerate(sources):
            with source_cols[idx]:
                st.markdown(f"<span class='source-tag'>{source}</span>", unsafe_allow_html=True)
    
    # Sorting options
    sort_col1, sort_col2 = st.columns(2)
    with sort_col1:
        sort_by = st.selectbox(
            "Sort by",
            ["Rating", "Reviews", "Data Quality", "Experience"],
            key="sort_by"
        )
    with sort_col2:
        order = st.radio(
            "Order",
            ["Descending", "Ascending"],
            horizontal=True,
            key="sort_order"
        )
    
    # Sort doctors
    if doctors:
        if sort_by == "Rating":
            doctors.sort(key=lambda x: x["rating"], reverse=(order == "Descending"))
        elif sort_by == "Reviews":
            doctors.sort(key=lambda x: x["reviews"], reverse=(order == "Descending"))
        elif sort_by == "Data Quality":
            doctors.sort(key=lambda x: x.get("data_quality_score", 0), reverse=(order == "Descending"))
        elif sort_by == "Experience":
            # Extract years from experience string for sorting
            def extract_years(exp):
                if not exp:
                    return 0
                try:
                    return int(''.join(filter(str.isdigit, exp.split()[0])))
                except:
                    return 0
            doctors.sort(key=lambda x: extract_years(x.get("experience")), reverse=(order == "Descending"))
    
    # Display doctor cards
    for doctor in doctors:
        display_doctor_card(doctor)
    
    # Export options
    if doctors:
        st.markdown("### Export Data")
        col1, col2 = st.columns(2)
        
        with col1:
            # Prepare CSV
            df = pd.DataFrame(doctors)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name=f"doctor_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Prepare JSON
            json_str = json.dumps(doctors, indent=2, default=str)
            st.download_button(
                label="Download as JSON",
                data=json_str,
                file_name=f"doctor_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

def main():
    # Set page config
    st.set_page_config(
        page_title="Doctor Search | Supervity",
        page_icon="assets/Supervity_Icon.png",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom CSS
    apply_custom_css()
    
    # Initialize session state
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'search_error' not in st.session_state:
        st.session_state.search_error = None
    if 'is_searching' not in st.session_state:
        st.session_state.is_searching = False
    
    # Sidebar for filters and settings
    with st.sidebar:
        st.image("assets/Supervity_Black_Without_Background.png", width=200)
        st.markdown("### Search Filters")
        
        # Additional filters (to be implemented in backend)
        min_rating = st.slider("Minimum Rating", 0.0, 5.0, 0.0, 0.5)
        min_reviews = st.number_input("Minimum Reviews", 0, 1000, 0)
        verified_only = st.checkbox("Verified Doctors Only")
        
        st.markdown("### Data Sources")
        sources = {
            "practo": st.checkbox("Practo", value=True),
            "justdial": st.checkbox("JustDial", value=True),
            "hospitals": st.checkbox("Hospital Websites", value=True),
            "councils": st.checkbox("Medical Councils", value=True)
        }
    
    # Main content
    st.markdown("<h1 class='title'>Doctor Search</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='subtitle'>Find verified healthcare providers with comprehensive information</p>",
        unsafe_allow_html=True
    )
    
    # Search form
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
            
            with st.spinner("🔍 Searching for doctors across multiple sources..."):
                response = run_async(search_doctors(city, specialization_key))
                
                if response["success"]:
                    st.session_state.search_results = response
                else:
                    st.session_state.search_error = response["error"]
                
            st.session_state.is_searching = False
    
    # Display results or error
    if st.session_state.search_results:
        display_search_results(st.session_state.search_results)
    
    if st.session_state.search_error:
        st.error(f"Error: {st.session_state.search_error}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center'>"
        "<small>Powered by Supervity | Data aggregated from multiple verified sources</small>"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main() 