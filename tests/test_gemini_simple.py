import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the parent directory to sys.path to allow direct import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from doctor_search_enhanced import GeminiClient

async def test_simple_prompt():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables")
        return False
    
    # Create client
    client = GeminiClient(api_key, "gemini-2.0-flash")
    
    # Test generate_content
    try:
        print("Testing basic prompt...")
        response = await client.generate_content("Say hello")
        if response and len(response) > 0:
            print(f"Response received: {response[:50]}...")
            return True
        else:
            print("Empty response received")
            return False
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_simple_prompt())
    exit(0 if result else 1)
