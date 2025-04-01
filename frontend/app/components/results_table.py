import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List
from ..utils.formatting import format_doctor_data
from .doctor_profile import render_doctor_profile, render_doctor_comparison

def create_rating_distribution(doctors: List[Dict]) -> None:
    """Create rating distribution chart."""
    if not doctors:
        return
        
    df = pd.DataFrame([format_doctor_data(d) for d in doctors])
    
    fig = px.histogram(
        df,
        x="Rating",
        nbins=10,
        title="Rating Distribution",
        labels={"Rating": "Rating", "count": "Number of Doctors"}
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_city_tier_distribution(doctors: List[Dict]) -> None:
    """Create city tier distribution chart."""
    if not doctors:
        return
        
    df = pd.DataFrame([format_doctor_data(d) for d in doctors])
    
    fig = px.pie(
        df,
        names="City Tier",
        title="City Tier Distribution",
        hole=0.4
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_specialization_breakdown(doctors: List[Dict]) -> None:
    """Create specialization breakdown chart."""
    if not doctors:
        return
        
    df = pd.DataFrame([format_doctor_data(d) for d in doctors])
    
    fig = px.bar(
        df.groupby("Specialization").size().reset_index(name="count"),
        x="Specialization",
        y="count",
        title="Specialization Breakdown",
        labels={"count": "Number of Doctors"}
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_confidence_vs_rating(doctors: List[Dict]) -> None:
    """Create confidence vs rating scatter plot."""
    if not doctors:
        return
        
    df = pd.DataFrame([format_doctor_data(d) for d in doctors])
    
    fig = px.scatter(
        df,
        x="Rating",
        y="Confidence",
        title="Confidence vs Rating",
        labels={"Rating": "Rating", "Confidence": "Confidence Score (%)"}
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_results_table(doctors: List[Dict]):
    """Render the results table with doctor information and visualizations.
    
    Args:
        doctors: List of doctor dictionaries
    """
    if not doctors:
        st.info("No doctors found matching your search criteria.")
        return
    
    # Format doctor data for display
    formatted_doctors = [format_doctor_data(doctor) for doctor in doctors]
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(formatted_doctors)
    
    # Display results count
    st.write(f"Found {len(doctors)} doctors")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["List View", "Analytics", "Comparison"])
    
    with tab1:
        # Create expandable sections for each doctor
        for idx, doctor in enumerate(formatted_doctors):
            with st.expander(f"{doctor['Name']} - {doctor['Specialization']}", expanded=idx < 3):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"""
                    **Location:** {doctor['City']} ({doctor['City Tier']})
                    
                    **Rating:** {doctor['Rating']} ⭐ ({doctor['Reviews']} reviews)
                    
                    **Confidence Score:** {doctor['Confidence']}%
                    
                    **Last Updated:** {doctor['Last Updated']}
                    """)
                
                with col2:
                    # Display profile URLs
                    st.markdown("**Profile URLs:**")
                    for source, url in doctor['Profile URLs'].items():
                        st.markdown(f"- [{source}]({url})")
                
                # Add view profile button
                if st.button("View Detailed Profile", key=f"profile_{idx}"):
                    render_doctor_profile(doctors[idx])
    
    with tab2:
        # Create visualizations
        st.subheader("Data Insights")
        
        # Rating distribution
        create_rating_distribution(doctors)
        
        # City tier distribution
        create_city_tier_distribution(doctors)
        
        # Specialization breakdown
        create_specialization_breakdown(doctors)
        
        # Confidence vs Rating
        create_confidence_vs_rating(doctors)
    
    with tab3:
        # Doctor comparison
        st.subheader("Compare Doctors")
        
        # Multi-select for doctors to compare
        selected_indices = st.multiselect(
            "Select doctors to compare",
            options=range(len(doctors)),
            format_func=lambda x: f"{doctors[x]['name']} - {doctors[x]['specialization']}"
        )
        
        if selected_indices:
            selected_doctors = [doctors[i] for i in selected_indices]
            render_doctor_comparison(selected_doctors)
    
    # Add export options
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Export to Excel"):
            # Format data for Excel export
            excel_data = [format_doctor_data(doctor, for_excel=True) for doctor in doctors]
            df_excel = pd.DataFrame(excel_data)
            
            # Create Excel file
            excel_file = df_excel.to_excel(index=False)
            st.download_button(
                label="Download Excel",
                data=excel_file,
                file_name="doctor_search_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        if st.button("Export to CSV"):
            # Format data for CSV export
            csv_data = [format_doctor_data(doctor, for_excel=True) for doctor in doctors]
            df_csv = pd.DataFrame(csv_data)
            
            # Create CSV file
            csv_file = df_csv.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_file,
                file_name="doctor_search_results.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("Export to JSON"):
            # Format data for JSON export
            json_data = [format_doctor_data(doctor, for_excel=True) for doctor in doctors]
            
            # Create JSON file
            json_file = pd.DataFrame(json_data).to_json(orient='records')
            st.download_button(
                label="Download JSON",
                data=json_file,
                file_name="doctor_search_results.json",
                mime="application/json"
            )

