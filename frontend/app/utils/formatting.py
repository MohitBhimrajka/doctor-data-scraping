from typing import Dict, List
from datetime import datetime

def format_doctor_data(doctor: Dict) -> Dict:
    """Format doctor data for display.
    
    Args:
        doctor: Raw doctor data from API
        
    Returns:
        Formatted doctor data
    """
    return {
        "Name": doctor["name"],
        "Specialization": doctor["specialization"],
        "City": f"{doctor['city']} (T{doctor['city_tier']})" if doctor.get('city_tier') else doctor['city'],
        "Rating": f"{doctor['rating']:.1f} ⭐",
        "Reviews": f"{doctor['total_reviews']:,}",
        "Confidence": f"{doctor['confidence_score']*100:.1f}%",
        "Locations": ", ".join(doctor["locations"]) if doctor["locations"] else "N/A",
        "Sources": ", ".join(doctor["contributing_sources"]) if doctor["contributing_sources"] else "N/A",
        "Last Updated": doctor["timestamp"].strftime("%Y-%m-%d %H:%M") if isinstance(doctor["timestamp"], datetime) else "N/A"
    }

def format_excel_data(doctors: List[Dict]) -> List[Dict]:
    """Format doctor data for Excel export.
    
    Args:
        doctors: List of doctor data
        
    Returns:
        List of formatted doctor data for Excel
    """
    return [{
        "Name": doctor["name"],
        "Specialization": doctor["specialization"],
        "City": doctor["city"],
        "City Tier": doctor.get("city_tier", "N/A"),
        "Rating": doctor["rating"],
        "Reviews": doctor["total_reviews"],
        "Confidence Score": doctor["confidence_score"],
        "Locations": "; ".join(doctor["locations"]) if doctor["locations"] else "N/A",
        "Sources": "; ".join(doctor["contributing_sources"]) if doctor["contributing_sources"] else "N/A",
        "Profile URLs": "; ".join([f"{k}: {v}" for k, v in doctor["profile_urls"].items() if v]),
        "Last Updated": doctor["timestamp"].strftime("%Y-%m-%d %H:%M") if isinstance(doctor["timestamp"], datetime) else "N/A"
    } for doctor in doctors]

def format_stats(stats: Dict) -> Dict:
    """Format statistics for display.
    
    Args:
        stats: Raw statistics from API
        
    Returns:
        Formatted statistics
    """
    return {
        "Total Doctors": stats.get("total_doctors", 0),
        "Total Specializations": len(stats.get("specializations", [])),
        "Total Cities": len(stats.get("cities", [])),
        "Average Rating": f"{stats.get('average_rating', 0):.1f}",
        "Average Reviews": f"{stats.get('average_reviews', 0):.0f}",
        "Top Specializations": ", ".join(stats.get("top_specializations", [])[:5]),
        "Top Cities": ", ".join(stats.get("top_cities", [])[:5])
    }

