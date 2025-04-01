import streamlit as st
from typing import Optional, Dict, Any
import time

def add_loading_animation(container: st.container, message: str = "Loading...") -> None:
    """Add a loading animation to a container."""
    with container:
        spinner = st.spinner(message)
        time.sleep(0.1)  # Small delay for smooth animation
        return spinner

def add_tooltip(text: str, help_text: str) -> str:
    """Add a tooltip to text using HTML."""
    return f'<span title="{help_text}">{text}</span>'

def add_aria_label(element: str, label: str) -> str:
    """Add ARIA label to an element."""
    return f'<div role="region" aria-label="{label}">{element}</div>'

def get_theme_colors(is_dark: bool) -> Dict[str, str]:
    """Get theme colors based on dark/light mode."""
    if is_dark:
        return {
            "background": "#1E1E1E",
            "text": "#FFFFFF",
            "primary": "#FF4B4B",
            "secondary": "#0E86D4",
            "accent": "#05A8AA",
            "error": "#FF6B6B",
            "success": "#4CAF50",
            "warning": "#FFC107"
        }
    return {
        "background": "#FFFFFF",
        "text": "#000000",
        "primary": "#FF4B4B",
        "secondary": "#0E86D4",
        "accent": "#05A8AA",
        "error": "#FF6B6B",
        "success": "#4CAF50",
        "warning": "#FFC107"
    }

def apply_theme(container: st.container, is_dark: bool) -> None:
    """Apply theme to a container."""
    colors = get_theme_colors(is_dark)
    container.markdown(f"""
        <style>
        .stApp {{
            background-color: {colors['background']};
            color: {colors['text']};
        }}
        .stButton>button {{
            background-color: {colors['primary']};
            color: {colors['text']};
        }}
        .stTextInput>div>div>input {{
            background-color: {colors['background']};
            color: {colors['text']};
        }}
        .stSelectbox>div>div>select {{
            background-color: {colors['background']};
            color: {colors['text']};
        }}
        </style>
    """, unsafe_allow_html=True)

def add_transition(element: str, transition_type: str = "fade") -> str:
    """Add CSS transition to an element."""
    transitions = {
        "fade": "opacity 0.3s ease-in-out",
        "slide": "transform 0.3s ease-in-out",
        "scale": "transform 0.3s ease-in-out"
    }
    return f'<div style="transition: {transitions.get(transition_type, transitions["fade"])}">{element}</div>'

def add_high_contrast_mode(container: st.container) -> None:
    """Add high contrast mode styles."""
    container.markdown("""
        <style>
        .high-contrast {
            background-color: #000000 !important;
            color: #FFFFFF !important;
        }
        .high-contrast * {
            background-color: #000000 !important;
            color: #FFFFFF !important;
            border-color: #FFFFFF !important;
        }
        .high-contrast button {
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }
        </style>
    """, unsafe_allow_html=True)

def add_error_message(message: str, error_type: str = "error") -> str:
    """Add styled error message."""
    colors = {
        "error": "#FF6B6B",
        "warning": "#FFC107",
        "info": "#0E86D4"
    }
    return f'<div style="color: {colors.get(error_type, colors["error"])}; padding: 10px; border-radius: 5px; background-color: rgba(255, 107, 107, 0.1);">{message}</div>'

def add_help_text(text: str, help_text: str) -> str:
    """Add help text with info icon."""
    return f'<div style="display: flex; align-items: center; gap: 5px;">{text} <span title="{help_text}" style="cursor: help;">ℹ️</span></div>' 