import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import json
import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from backend.utils.gemini_client import GeminiClient
from backend.config import GEMINI_API_KEY

@pytest.mark.asyncio
async def test_doctor_search():
    """Test doctor search with Gemini API to understand response format."""
    if not GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY not found in environment")
        
    client = GeminiClient(model_name="gemini-1.5-pro")
    
    # Test prompts for different sources
    prompts = [
        # Practo-style prompt
        """
        Search for Cardiologists in Mumbai on Practo and provide the results in JSON format with the following structure:
        [
            {
                "name": "Doctor name with proper title (Dr.)",
                "specialization": "Exact specialization",
                "city": "Mumbai",
                "rating": "Rating out of 5.0",
                "reviews": "Number of reviews",
                "locations": ["Primary clinic/hospital", "Other locations if any"],
                "profile_url": "Profile URL if available"
            }
        ]

        Please provide real, accurate information for at least 3 top cardiologists.
        """,
        
        # Google-style prompt
        """
        Search for Cardiologists in Mumbai on Google Maps and provide the results in JSON format with the following structure:
        [
            {
                "name": "Doctor name with proper title (Dr.)",
                "specialization": "Exact specialization",
                "city": "Mumbai",
                "rating": "Rating out of 5.0",
                "reviews": "Number of reviews",
                "locations": ["Primary clinic/hospital", "Other locations if any"],
                "profile_url": "Google Maps URL if available"
            }
        ]

        Please provide real, accurate information for at least 3 top cardiologists.
        """
    ]
    
    results = []
    
    for i, prompt in enumerate(prompts):
        print(f"\nTesting prompt {i+1}:")
        print("-" * 50)
        try:
            response = await client.generate(prompt)
            print("Raw response:")
            print(response)
            
            # Try to parse as JSON
            try:
                data = json.loads(response)
                print("\nParsed JSON:")
                print(json.dumps(data, indent=2))
                results.append(data)
            except json.JSONDecodeError:
                print("\nCould not parse as JSON")
                # Try to extract JSON from the response
                try:
                    start = response.find('[')
                    end = response.rfind(']') + 1
                    if start >= 0 and end > start:
                        json_str = response[start:end]
                        data = json.loads(json_str)
                        print("\nExtracted and parsed JSON:")
                        print(json.dumps(data, indent=2))
                        results.append(data)
                except Exception as e:
                    print(f"Could not extract JSON: {str(e)}")
                
        except Exception as e:
            print(f"Error: {str(e)}")
    
    # Analyze results
    if results:
        print("\nAnalysis of results:")
        print("-" * 50)
        for i, result in enumerate(results):
            source = "Practo" if i == 0 else "Google"
            print(f"\n{source} Results:")
            if isinstance(result, list):
                print(f"Number of doctors: {len(result)}")
                for doc in result:
                    print(f"\nDoctor: {doc.get('name', 'N/A')}")
                    print(f"Fields present: {list(doc.keys())}")
                    print(f"Fields missing: {set(['name', 'specialization', 'city', 'rating', 'reviews', 'locations', 'profile_url']) - set(doc.keys())}")
            else:
                print("Result is not a list of doctors")

if __name__ == "__main__":
    asyncio.run(test_doctor_search()) 