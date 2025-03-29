import os
import sys
import asyncio
import json
from dotenv import load_dotenv

# Add the parent directory to sys.path to allow direct import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from doctor_search_enhanced import GeminiClient, PromptManager, DataProcessor

async def test_doctor_prompt():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables")
        return False
    
    # Create client
    client = GeminiClient(api_key, "gemini-2.0-flash")
    
    # Create a simple search prompt
    prompt = PromptManager._add_json_instruction(
        "site:practo.com Dermatologist doctor primarily practicing in Mumbai clinic address rating reviews"
    )
    
    print(f"Testing doctor search prompt...")
    
    # Test generate_content with the prompt
    try:
        response = await client.generate_content(prompt)
        print("Response received!")
        
        # Try to extract JSON data
        extracted_data = DataProcessor.extract_json_from_response(response)
        if extracted_data:
            print(f"Successfully extracted {len(extracted_data)} doctors")
            return True
        else:
            print("Could not extract JSON data from response")
            print("Raw response sample:", response[:200])
            return False
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_doctor_prompt())
    exit(0 if result else 1)
