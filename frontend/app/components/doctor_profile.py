import streamlit as st
from typing import Dict, List, Optional
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd

def create_doctor_radar_chart(doctor: Dict) -> None:
    """Create a radar chart for doctor metrics."""
    categories = ['Rating', 'Reviews', 'Confidence', 'Experience', 'Verification']
    
    # Calculate normalized values
    values = [
        doctor['rating'] / 5.0,  # Rating (0-5)
        min(doctor['total_reviews'] / 1000.0, 1.0),  # Reviews (normalized to 1000)
        doctor['confidence_score'],  # Confidence (0-1)
        0.8,  # Experience (placeholder)
        len(doctor['contributing_sources']) / 4.0  # Verification (normalized to 4 sources)
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name=doctor['name']
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=True,
        title="Doctor Metrics"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_doctor_profile(doctor: Dict) -> None:
    """Render detailed doctor profile.
    
    Args:
        doctor: Doctor dictionary
    """
    st.subheader(f"👨‍⚕️ {doctor['name']}")
    
    # Basic Information
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        **Specialization:** {doctor['specialization']}
        
        **Location:** {doctor['city']} (Tier {doctor['city_tier']})
        """)
    
    with col2:
        st.markdown(f"""
        **Rating:** {doctor['rating']} ⭐
        
        **Reviews:** {doctor['reviews']}
        """)
    
    with col3:
        st.markdown(f"""
        **Confidence:** {doctor['confidence_score']*100:.1f}%
        
        **Last Updated:** {doctor['timestamp']}
        """)
    
    # Practice Locations
    st.markdown("### Practice Locations")
    for location in doctor['locations']:
        st.markdown(f"- {location}")
    
    # Source Verification
    st.markdown("### Verified Sources")
    for source in doctor['contributing_sources']:
        st.markdown(f"- {source}")
    
    # Profile URLs
    st.markdown("### Profile Links")
    if doctor.get('profile_urls'):
        for source, url in doctor['profile_urls'].items():
            st.markdown(f"- [{source}]({url})")
    else:
        st.markdown("No profile links available")
    
    # Metrics Visualization
    st.markdown("### Performance Metrics")
    create_doctor_radar_chart(doctor)

def render_doctor_comparison(doctors: List[Dict]) -> None:
    """Render doctor comparison view.
    
    Args:
        doctors: List of doctor dictionaries
    """
    if len(doctors) < 2:
        st.warning("Select at least 2 doctors to compare")
        return
    
    st.subheader("Doctor Comparison")
    
    # Create comparison table
    comparison_data = []
    for doctor in doctors:
        comparison_data.append({
            "Name": doctor['name'],
            "Specialization": doctor['specialization'],
            "Location": f"{doctor['city']} (Tier {doctor['city_tier']})",
            "Rating": doctor['rating'],
            "Reviews": doctor['total_reviews'],
            "Confidence": f"{doctor['confidence_score']*100:.1f}%",
            "Sources": len(doctor['contributing_sources'])
        })
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True)
    
    # Create comparison charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Rating comparison
        fig1 = go.Figure()
        for doctor in doctors:
            fig1.add_trace(go.Bar(
                name=doctor['name'],
                x=['Rating', 'Reviews', 'Confidence'],
                y=[
                    doctor['rating'],
                    doctor['total_reviews'] / 100,  # Normalize for better visualization
                    doctor['confidence_score'] * 100
                ]
            ))
        
        fig1.update_layout(
            title="Doctor Metrics Comparison",
            barmode='group'
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Source verification comparison
        fig2 = go.Figure()
        for doctor in doctors:
            fig2.add_trace(go.Bar(
                name=doctor['name'],
                x=list(doctor['contributing_sources']),
                y=[1] * len(doctor['contributing_sources'])
            ))
        
        fig2.update_layout(
            title="Source Verification Comparison",
            showlegend=True
        )
        st.plotly_chart(fig2, use_container_width=True) 