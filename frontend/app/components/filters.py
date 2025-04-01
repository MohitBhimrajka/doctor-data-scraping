import streamlit as st
from typing import Dict, List
from datetime import datetime, timedelta

def render_filters():
    """Render filters and sorting options in the sidebar."""
    
    # Sorting Options
    st.subheader("Sort Results")
    sort_options = [
        "Rating (High to Low)",
        "Reviews (High to Low)",
        "Confidence (High to Low)",
        "City Tier (Ascending)",
        "Name (A-Z)",
        "Last Updated (Newest)"
    ]
    
    sort_by = st.radio(
        "Sort by",
        sort_options,
        key="sort_by",
        help="Choose how to sort the results"
    )
    
    # Rating Filter
    st.subheader("Rating Filter")
    min_rating = st.slider(
        "Minimum Rating",
        min_value=0.0,
        max_value=5.0,
        value=0.0,
        step=0.5,
        help="Filter doctors by minimum rating"
    )
    
    # Reviews Filter
    min_reviews = st.number_input(
        "Minimum Reviews",
        min_value=0,
        value=0,
        help="Filter doctors by minimum number of reviews"
    )
    
    # Confidence Filter
    st.subheader("Confidence Filter")
    min_confidence = st.slider(
        "Minimum Confidence",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=5.0,
        help="Filter doctors by minimum confidence score"
    )
    
    # Date Range Filter
    st.subheader("Date Range")
    col1, col2 = st.columns(2)
    
    with col1:
        days_ago = st.number_input(
            "Updated within",
            min_value=0,
            value=30,
            help="Show only doctors updated within this many days"
        )
    
    with col2:
        min_date = datetime.now() - timedelta(days=days_ago)
        st.info(f"Showing updates from {min_date.strftime('%Y-%m-%d')}")
    
    # Source Verification Filter
    st.subheader("Source Verification")
    sources = ["practo", "google", "justdial", "lybrate"]
    selected_sources = st.multiselect(
        "Verified Sources",
        options=sources,
        default=sources,
        help="Filter doctors by verification sources"
    )
    
    # Store filters in session state
    st.session_state.filters = {
        "sort_by": sort_by,
        "min_rating": min_rating,
        "min_reviews": min_reviews,
        "min_confidence": min_confidence / 100.0,  # Convert to decimal
        "min_date": min_date,
        "selected_sources": selected_sources
    }
    
    # Pagination Controls
    st.subheader("Pagination")
    col1, col2 = st.columns(2)
    
    with col1:
        page_size = st.select_slider(
            "Results per page",
            options=[10, 25, 50, 100],
            value=10,
            help="Number of results to display per page"
        )
    
    with col2:
        current_page = st.number_input(
            "Page",
            min_value=1,
            value=1,
            help="Current page number"
        )
    
    # Store pagination in session state
    st.session_state.pagination = {
        "page_size": page_size,
        "current_page": current_page
    }

def apply_filters(doctors: List[Dict]) -> List[Dict]:
    """Apply filters to the list of doctors.
    
    Args:
        doctors: List of doctor dictionaries
        
    Returns:
        Filtered and sorted list of doctors
    """
    if not doctors:
        return []
    
    # Get current filters from session state
    filters = st.session_state.get("filters", {})
    
    # Apply rating filter
    if filters.get("min_rating", 0) > 0:
        doctors = [d for d in doctors if d["rating"] >= filters["min_rating"]]
    
    # Apply reviews filter
    if filters.get("min_reviews", 0) > 0:
        doctors = [d for d in doctors if d["reviews"] >= filters["min_reviews"]]
    
    # Apply confidence filter
    if filters.get("min_confidence", 0) > 0:
        doctors = [d for d in doctors if d["confidence_score"] >= filters["min_confidence"]]
    
    # Apply date filter
    if filters.get("min_date"):
        min_date = filters["min_date"]
        doctors = [
            d for d in doctors 
            if datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")) >= min_date
        ]
    
    # Apply source verification filter
    if filters.get("selected_sources"):
        selected_sources = filters["selected_sources"]
        doctors = [
            d for d in doctors 
            if any(source in d["contributing_sources"] for source in selected_sources)
        ]
    
    # Apply sorting
    sort_by = filters.get("sort_by", "Rating (High to Low)")
    
    if sort_by == "Rating (High to Low)":
        doctors.sort(key=lambda x: x["rating"], reverse=True)
    elif sort_by == "Reviews (High to Low)":
        doctors.sort(key=lambda x: x["reviews"], reverse=True)
    elif sort_by == "Confidence (High to Low)":
        doctors.sort(key=lambda x: x["confidence_score"], reverse=True)
    elif sort_by == "City Tier (Ascending)":
        doctors.sort(key=lambda x: x.get("city_tier", 999))
    elif sort_by == "Name (A-Z)":
        doctors.sort(key=lambda x: x["name"])
    elif sort_by == "Last Updated (Newest)":
        doctors.sort(
            key=lambda x: datetime.fromisoformat(x["timestamp"].replace("Z", "+00:00")),
            reverse=True
        )
    
    return doctors

