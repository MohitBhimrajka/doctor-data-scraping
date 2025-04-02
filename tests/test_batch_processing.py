import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the parent directory to sys.path to allow direct import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from doctor_search_enhanced import GeminiClient

async def test_batch_processing():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables")
        return False
    
    # Create client
    client = GeminiClient(api_key, "gemini-2.0-flash")
    
    # Create sample prompts
    prompts = [
        "Say hello",
        "What is 2+2?"
    ]
    
    print(f"Testing batch processing with {len(prompts)} prompts...")
    
    # Test generate_content_batch
    try:
        responses = await client.generate_content_batch(prompts)
        
        if len(responses) != len(prompts):
            print(f"Expected {len(prompts)} responses, got {len(responses)}")
            return False
            
        success = all(response is not None and len(response) > 0 for response in responses)
        if success:
            print("All batch prompts returned valid responses")
            return True
        else:
            print("Some prompts did not return valid responses")
            return False
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_batch_processing())
    exit(0 if result else 1)
