import os
import json
import time
import pandas as pd
import google.generativeai as genai
from google.generativeai import types
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set.")
    print("Please set the environment variable before running the script.")
    exit()

# Create a genai.Client to interact with the Gemini model
client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-2.5-pro-exp-03-25"

# Define available specializations
SPECIALIZATIONS = {
    "1": "Cardiologist",
    "2": "Dermatologist",
    "3": "Orthopedist",
    "4": "Pediatrician",
    "5": "Gynecologist",
    "6": "Ophthalmologist",
    "7": "ENT Specialist",
    "8": "Dentist",
    "9": "Psychiatrist",
    "10": "Neurologist",
    "11": "Gastroenterologist",
    "12": "Urologist",
    "13": "Pulmonologist",
    "14": "Endocrinologist",
    "15": "General Physician",
    "16": "All Specializations"
}

def get_user_input():
    """Get user input for location and specialization"""
    print("\n=== Doctor Search Configuration ===")
    
    # Get location
    location = input("\nEnter the city/area to search (e.g., Mumbai, Delhi, Bangalore): ").strip()
    
    # Show specialization options
    print("\nAvailable Specializations:")
    for key, value in SPECIALIZATIONS.items():
        print(f"{key}. {value}")
    
    # Get specialization choice
    while True:
        choice = input("\nEnter the number of specialization (1-16): ").strip()
        if choice in SPECIALIZATIONS:
            specialization = SPECIALIZATIONS[choice]
            break
        print("Invalid choice. Please enter a number between 1 and 16.")
    
    return location, specialization

def generate_structured_doctor_data(source_description, location, specialization):
    """
    Uses Gemini with Google Search grounding to find doctor information
    based on search results, optionally focusing on a specific source domain.
    """
    print(f"\nAttempting to find data about {specialization} doctors in {location}, focusing on '{source_description}' via Google Search...")

    # Construct the prompt based on the source description and specialization
    if source_description.lower() == "practo":
        prompt = f"""Use Google Search to find information about {specialization} doctors on Practo in {location}.
Search for: "site:practo.com {specialization} doctors in {location}"
For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Number of reviews (if mentioned)
- Rating or Score (e.g., 4.5 stars, 9/10 - provide the numerical value if possible)
- Location (specific clinic name, hospital, and area in {location})

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- reviews
- rating
- location

Include only doctors who are actively practicing in {location} and have at least a rating or reviews."""
    elif source_description.lower() == "justdial":
        prompt = f"""Use Google Search to find information about {specialization} doctors on JustDial in {location}.
Search for: "site:justdial.com {specialization} doctors in {location}"
For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Number of reviews (if mentioned)
- Rating or Score (e.g., 4.5 stars, 9/10 - provide the numerical value if possible)
- Location (specific clinic name, hospital, and area in {location})

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- reviews
- rating
- location

Include only doctors who are actively practicing in {location} and have at least a rating or reviews."""
    else:  # General Search
        prompt = f"""Use Google Search to find information about {specialization} doctors in {location}.
Use these search queries:
1. "{specialization} doctors in {location} reviews ratings"
2. "best {specialization} in {location} reviews"
3. "top rated {specialization} {location}"

For each doctor identified in the search results, please extract the following details if available:
- Name of the doctor (including title Dr.)
- Number of reviews (if mentioned)
- Rating or Score (e.g., 4.5 stars, 9/10 - provide the numerical value if possible)
- Location (specific clinic name, hospital, and area in {location})

Format the output strictly as a JSON list of dictionaries with these exact field names:
- name
- reviews
- rating
- location

Include only doctors who are actively practicing in {location} and have at least a rating or reviews.
Focus on verified and reliable sources like hospital websites, medical directories, and review platforms."""

    # Configure the Google Search tool and generation config
    tools = [types.Tool(google_search=types.GoogleSearch())]
    generate_content_config = types.GenerateContentConfig(
        tools=tools,
        response_mime_type="text/plain"
    )

    try:
        print(f"Sending request to Gemini for '{source_description}'...")
        
        # Prepare the content
        contents = [
            types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            )
        ]

        # Collect the streamed response
        full_response = ""
        for chunk in client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=contents,
            config=generate_content_config
        ):
            if chunk.text:
                full_response += chunk.text
                print(chunk.text, end="")

        print("\n----------------------------------------------------")

        # Parse the JSON response
        json_str = None
        if "```json" in full_response:
            parts = full_response.split("```json", 1)
            after_json_block = parts[1] if len(parts) > 1 else ""
            json_str = after_json_block.split("```", 1)[0].strip()
        elif full_response.strip().startswith('['):
            json_str = full_response.strip()
        else:
            start_index = full_response.find('[')
            end_index = full_response.rfind(']')
            if start_index != -1 and end_index > start_index:
                json_str = full_response[start_index:end_index + 1]

        if not json_str:
            print(f"Warning: Could not locate JSON list structure in the response for {source_description}.")
            return []

        data = json.loads(json_str)
        if isinstance(data, list):
            print(f"Successfully parsed {len(data)} records for {source_description}.")
            # Standardize field names and clean data
            standardized_data = []
            for item in data:
                if isinstance(item, dict):
                    # Clean and standardize the data
                    name = (item.get("name") or item.get("Full Name") or item.get("Name", "")).strip()
                    
                    # Handle reviews
                    reviews_str = str(item.get("reviews") or item.get("Number of reviews") or item.get("Number of Reviews", "0"))
                    try:
                        reviews = int(''.join(filter(str.isdigit, reviews_str)))
                    except:
                        reviews = 0
                    
                    # Handle rating
                    rating_str = str(item.get("rating") or item.get("Rating or Score") or item.get("Rating", "0"))
                    try:
                        # Handle percentage ratings (e.g., "97%")
                        if "%" in rating_str:
                            rating = float(rating_str.strip("%")) / 100
                        else:
                            # Handle decimal ratings (e.g., "4.5" or "0.97")
                            rating = float(rating_str.split()[0])
                    except:
                        rating = 0.0
                    
                    # Clean location
                    location = (item.get("location") or item.get("Location", "")).strip()
                    
                    standardized_item = {
                        "name": name,
                        "reviews": reviews,
                        "rating": rating,
                        "location": location,
                        "source": source_description
                    }
                    
                    # Only include items with at least a name and either rating or reviews
                    if standardized_item["name"] and (standardized_item["rating"] > 0 or standardized_item["reviews"] > 0):
                        standardized_data.append(standardized_item)
            return standardized_data
        else:
            print(f"Error: Parsed data is not a list for {source_description} (got type {type(data)}).")
            return []

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {source_description} data: {e}")
        return []
    except Exception as e:
        print(f"An error occurred during the API call or processing for {source_description}: {e}")
        return []

def filter_low_quality_data(df):
    """Filter out records with too many nulls and low quality data"""
    # Calculate completeness score for each row
    df['completeness'] = df.notna().sum(axis=1) / len(df.columns)
    
    # Filter out rows with low completeness (less than 60% complete)
    df = df[df['completeness'] >= 0.6]
    
    # Sort by completeness and then by number of reviews
    df = df.sort_values(['completeness', 'reviews'], ascending=[False, False])
    
    # Drop the completeness column
    df = df.drop('completeness', axis=1)
    
    return df

def main():
    """
    Main function to fetch data from multiple sources, deduplicate the results,
    and save them to a CSV file.
    """
    print("=== Doctor Information Search Tool ===")
    print(f"Using model: {MODEL_NAME}")
    
    # Get user input
    location, specialization = get_user_input()
    
    # List of sources to query
    sources = ["Practo", "JustDial", "General Search"]
    all_data = []

    for source in sources:
        source_data = generate_structured_doctor_data(source, location, specialization)
        if source_data:
            all_data.extend(source_data)
        time.sleep(2)  # Pause between API calls

    if not all_data:
        print("\nNo data was successfully retrieved or parsed from any source.")
        return

    print(f"\nTotal records collected across all sources: {len(all_data)}")

    # --- Data Deduplication ---
    print("Deduplicating data based on Name...")
    unique_data = []
    seen_names = set()
    duplicates_found = 0

    for item in all_data:
        if not isinstance(item, dict) or not item.get('name'):
            duplicates_found += 1
            continue

        name = item.get('name', '').strip().lower()
        if name not in seen_names:
            unique_data.append(item)
            seen_names.add(name)
        else:
            duplicates_found += 1

    print(f"Found and removed {duplicates_found} duplicate or invalid entries.")
    print(f"Total unique records: {len(unique_data)}")

    # --- Save Data to CSV ---
    if unique_data:
        print("\nPreparing data for CSV export...")
        df = pd.DataFrame(unique_data)
        
        # Reorder columns for better readability
        columns_order = ["name", "reviews", "rating", "location", "source"]
        
        # Add missing columns
        for col in columns_order:
            if col not in df.columns:
                df[col] = None
        
        # Reorder columns
        df = df[columns_order]
        
        # Filter out low quality data
        df = filter_low_quality_data(df)
        
        # Clean up column names
        df.columns = [col.replace('_', ' ').title() for col in df.columns]
        
        # Generate filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_filename = f"doctors_data_{location.lower().replace(' ', '_')}_{timestamp}.csv"
        
        try:
            df.to_csv(output_filename, index=False, encoding='utf-8')
            print(f"\nData successfully saved to: {output_filename}")
            print(f"Total records saved: {len(df)}")
            print("\nData Quality Summary:")
            print(f"- Records with ratings: {df['Rating'].notna().sum()}")
            print(f"- Records with reviews: {df['Reviews'].notna().sum()}")
            print(f"- Average rating: {df['Rating'].mean():.2f}")
            print(f"- Average reviews: {df['Reviews'].mean():.1f}")
        except Exception as e:
            print(f"\nError saving data to CSV file '{output_filename}': {e}")
    else:
        print("\nNo unique data found to save to CSV.")

if __name__ == "__main__":
    main()
