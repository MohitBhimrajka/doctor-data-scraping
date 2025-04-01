import json
import logging
from typing import Any, Dict, List, Optional, Union
import google.generativeai as genai
from ..config import GOOGLE_API_KEY

logger = logging.getLogger(__name__)

class GeminiClient:
    """Client for interacting with Google's Gemini API."""

    def __init__(self, model_name: str):
        """Initialize the client."""
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(model_name)

    async def generate(self, prompt: str, timeout: Optional[int] = None) -> str:
        """
        Generate text response from Gemini.

        Args:
            prompt: Input prompt
            timeout: Optional timeout in seconds

        Returns:
            Generated text response
        """
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return ""

    async def generate_structured(
        self,
        prompt: str,
        timeout: Optional[int] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generate structured response from Gemini.

        Args:
            prompt: Input prompt
            timeout: Optional timeout in seconds

        Returns:
            Structured response as dictionary or list of dictionaries
        """
        try:
            response = await self.model.generate_content_async(prompt)
            return self.parse_response(response.text)

        except Exception as e:
            logger.error(f"Error generating structured response: {str(e)}")
            return []

    def parse_response(self, response: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Parse response text into structured data.

        Args:
            response: Response text to parse

        Returns:
            Parsed data as dictionary or list of dictionaries
        """
        try:
            # Try to parse as JSON directly
            try:
                data = json.loads(response)
                return data
            except json.JSONDecodeError:
                pass

            # Try to extract JSON from the response
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                try:
                    data = json.loads(json_str)
                    return data
                except json.JSONDecodeError:
                    pass

            # Try to parse as key-value pairs
            data = {}
            for line in response.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    data[key] = value

            return data

        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return {} 