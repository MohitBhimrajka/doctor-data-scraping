import os
from typing import Optional, Dict, Any
import json
import google.generativeai as genai
from ..config import GEMINI_API_KEY

class GeminiClient:
    def __init__(self, model_name: str):
        """
        Initialize Gemini client.
        
        Args:
            model_name: Name of the Gemini model to use
        """
        # Configure API
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Get model
        self.model = genai.GenerativeModel(model_name)
        
        # Configure generation settings
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        # Configure safety settings
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]

    async def generate(
        self,
        prompt: str,
        generation_config: Optional[Dict[str, Any]] = None,
        safety_settings: Optional[list] = None
    ) -> str:
        """
        Generate text using the Gemini model.
        
        Args:
            prompt: Input prompt
            generation_config: Optional generation configuration
            safety_settings: Optional safety settings
            
        Returns:
            Generated text
        """
        try:
            # Use provided config or default
            config = generation_config or self.generation_config
            safety = safety_settings or self.safety_settings
            
            # Generate response
            response = await self.model.generate_content_async(
                prompt,
                generation_config=config,
                safety_settings=safety
            )
            
            # Extract text
            if response.text:
                return response.text
            else:
                raise ValueError("Empty response from model")
                
        except Exception as e:
            raise Exception(f"Error generating content: {str(e)}")

    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        generation_config: Optional[Dict[str, Any]] = None,
        safety_settings: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Generate structured data using the Gemini model.
        
        Args:
            prompt: Input prompt
            schema: Expected response schema
            generation_config: Optional generation configuration
            safety_settings: Optional safety settings
            
        Returns:
            Structured data matching the schema
        """
        try:
            # Add schema to prompt
            schema_prompt = f"""
            {prompt}
            
            Please provide the response in the following JSON schema:
            {json.dumps(schema, indent=2)}
            
            Important:
            1. The response MUST be valid JSON
            2. The response MUST match the provided schema exactly
            3. Do not include any explanatory text before or after the JSON
            4. All string values should be properly escaped
            """
            
            # Generate response
            response = await self.generate(
                schema_prompt,
                generation_config,
                safety_settings
            )
            
            # Try to parse as JSON directly
            try:
                data = json.loads(response)
                return data
            except json.JSONDecodeError:
                # Try to extract JSON from the response
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    try:
                        json_str = response[start:end]
                        data = json.loads(json_str)
                        return data
                    except json.JSONDecodeError:
                        pass
                        
                # Try array format
                start = response.find('[')
                end = response.rfind(']') + 1
                if start >= 0 and end > start:
                    try:
                        json_str = response[start:end]
                        data = json.loads(json_str)
                        return data
                    except json.JSONDecodeError:
                        pass
                
                raise ValueError("Could not parse response as JSON")
            
        except Exception as e:
            raise Exception(f"Error generating structured content: {str(e)}") 