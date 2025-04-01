from typing import Dict, List

# City Tier Definitions
CITY_TIERS: Dict[int, str] = {
    1: "Metro",
    2: "Tier 2",
    3: "Tier 3"
}

# Source Types
SOURCE_TYPES: List[str] = [
    "practo",
    "google",
    "justdial",
    "hospital",
    "social"
]

# Hospital Chains
HOSPITAL_CHAINS: List[str] = [
    "apollo",
    "fortis",
    "manipal",
    "max",
    "medanta",
    "narayana",
    "aiims"
]

# Common Patterns
PATTERNS = {
    "doctor_title": r"^(?:Dr\.|Dr|Prof\.|Prof)\s+",
    "location_separators": [",", ";", "|", "•"],
    "generic_terms": [
        "multiple locations",
        "online",
        "consultation",
        "available at",
        "near",
        "opposite",
        "visit for",
        "clinic",
        "hospital",
        "centre",
        "various locations"
    ]
}

# Prompt Templates
PROMPT_TEMPLATES = {
    "discovery": {
        "practo": "site:practo.com {specialization} doctor practicing in {location}",
        "google": "site:google.com/maps {specialization} doctor clinics {location}",
        "justdial": "site:justdial.com {specialization} doctor in {location}",
        "hospital": "site:{hospital}.com {specialization} specialist {location} branch",
        "social": "site:linkedin.com/in {specialization} doctor {location}"
    },
    "verification": """
Objective: Accurately verify and aggregate ratings, review counts, primary practice locations, and profile URLs for a specific doctor in their primary city.

Doctor Details:
Name: "{name}"
Specialization: "{specialization}"
Primary City: "{city}"

Sources to Check (Prioritized):
1. Practo.com
2. Google (Search for Google Business Profile / Maps listing reviews)
3. Justdial.com
4. Major Hospital Websites (Check if affiliated with Apollo, Fortis, Manipal, Max, Medanta, Narayana, AIIMS, etc., in {city})
5. Other reputable sources like Healthgrades, Yelp (if applicable).

Task:
For the specified doctor ({name}, {specialization}) practicing primarily in {city}:
1. Search across the listed sources.
2. For EACH source where the exact doctor is found:
    - Extract the average user rating (on a 5-point scale, convert if necessary). Use 'null' if not found.
    - Extract the total number of user reviews associated with that rating. Use 0 if not found.
    - Extract the direct URL to the doctor's profile or listing on that source if available. Use 'null' if not available.
3. Consolidate the primary, specific clinic/hospital address(es) found for this doctor *within* {city}.

Output Format:
Provide the results STRICTLY in the following JSON format ONLY:
{{
  "verification_results": [
    {{"source": "Practo", "rating": 4.8, "reviews": 155, "url": "https://www.practo.com/..."}},
    {{"source": "Google", "rating": 4.6, "reviews": 210, "url": "https://www.google.com/maps/..."}},
    {{"source": "Justdial", "rating": 4.5, "reviews": 90, "url": "https://www.justdial.com/..."}},
    {{"source": "Apollo Hospital", "rating": null, "reviews": 0, "url": "https://www.apollohospitals.com/..."}},
    {{"source": "Healthgrades", "rating": 4.7, "reviews": 50, "url": null}}
  ],
  "verified_locations": [
    "Specific Clinic Address 1, Area, {city}, Pincode",
    "Hospital Name, Department, Address, {city}"
  ]
}}
"""
}

# Error Messages
ERROR_MESSAGES = {
    "api_error": "API request failed: {error}",
    "validation_error": "Data validation failed: {error}",
    "city_not_found": "City '{city}' not found in the database",
    "no_results": "No doctors found matching the criteria",
    "invalid_specialization": "Invalid specialization: {specialization}",
    "invalid_tiers": "Invalid city tiers specified: {tiers}"
}

# Success Messages
SUCCESS_MESSAGES = {
    "search_complete": "Search completed successfully. Found {count} doctors.",
    "verification_complete": "Verification completed for {count} doctors.",
    "data_saved": "Successfully saved {count} doctors to database."
} 