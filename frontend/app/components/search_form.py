import streamlit as st
from typing import Dict, Optional, List
from ..utils.validation import validate_search_inputs

def render_search_form() -> Optional[Dict]:
    """Render the search form and handle user input.
    
    Returns:
        Optional[Dict]: Search parameters if form is submitted and valid,
                       None otherwise
    """
    # Create a container for the form
    with st.container():
        st.subheader("Search Parameters")
        
        # Search Mode Selection
        mode = st.radio(
            "Search Mode",
            ["Single City", "Country-Wide"],
            horizontal=True,
            help="Choose between searching in a specific city or across multiple cities"
        )
        
        # Store mode in session state
        st.session_state.search_mode = mode
        
        # Initialize search parameters
        search_params = {}
        
        # Specialization Input (common to both modes)
        specialization = st.text_input(
            "Specialization",
            placeholder="e.g., Cardiologist, Orthopedist",
            help="Enter the doctor's specialization"
        )
        
        # Mode-specific inputs
        if mode == "Single City":
            # City Input
            city = st.text_input(
                "City",
                placeholder="e.g., Mumbai, Delhi",
                help="Enter the city name"
            )
            
            # Validate inputs for single city mode
            if specialization and city:
                try:
                    search_params = validate_search_inputs(
                        specialization=specialization,
                        city=city
                    )
                except ValueError as e:
                    st.error(str(e))
                    return None
                    
        else:  # Country-Wide mode
            # Tier Selection
            st.markdown("### Select City Tiers")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                tier1 = st.checkbox(
                    "Tier 1",
                    value=True,
                    help="Major metropolitan cities (e.g., Mumbai, Delhi)"
                )
            with col2:
                tier2 = st.checkbox(
                    "Tier 2",
                    value=True,
                    help="Large cities (e.g., Pune, Ahmedabad)"
                )
            with col3:
                tier3 = st.checkbox(
                    "Tier 3",
                    value=False,
                    help="Smaller cities and towns"
                )
            
            # Get selected tiers
            selected_tiers = []
            if tier1: selected_tiers.append(1)
            if tier2: selected_tiers.append(2)
            if tier3: selected_tiers.append(3)
            
            # Store selected tiers in session state
            st.session_state.selected_tiers = selected_tiers
            
            # Validate inputs for country-wide mode
            if specialization and selected_tiers:
                try:
                    search_params = validate_search_inputs(
                        specialization=specialization,
                        country="India",
                        tiers=selected_tiers
                    )
                except ValueError as e:
                    st.error(str(e))
                    return None
        
        # Search Button
        search_button = st.button(
            "Search Doctors",
            disabled=not specialization or (mode == "Single City" and not city) or (mode == "Country-Wide" and not selected_tiers),
            help="Click to search for doctors based on the specified criteria"
        )
        
        # Handle search button click
        if search_button and search_params:
            # Store search parameters in session state
            st.session_state.search_params = search_params
            return search_params
        
        return None

