"""
Robust Gemini API client with key rotation and retry logic.
"""
import time
import json
from typing import Optional, Dict, Any
import google.generativeai as genai
from requests.exceptions import RequestException
from core.observability import logger
from config import Config

class GeminiClient:
    def __init__(self, system_instruction: str):
        self.system_instruction = system_instruction
        self.max_retries = len(Config.GEMINI_API_KEYS) or 1
        self.retry_delay = 1  # seconds
        
    def generate_response(
        self, 
        prompt: str, 
        json_mode: bool = False
    ) -> Optional[str]:
        """
        Generate response with key rotation and retry logic.
        Returns None if all retries fail.
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                key = Config.rotate_gemini_key()
                logger.log("GeminiClient", f"Using API key {attempt + 1}/{self.max_retries}")
                
                genai.configure(api_key=key)
                
                generation_config = {
                    "temperature": Config.TEMPERATURE,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": Config.MAX_OUTPUT_TOKENS,
                    "response_mime_type": "application/json" if json_mode else "text/plain",
                }
                
                model = genai.GenerativeModel(
                    model_name=Config.MODEL_NAME,
                    generation_config=generation_config,
                    system_instruction=self.system_instruction
                )
                
                chat_session = model.start_chat(history=[])
                response = chat_session.send_message(prompt)
                
                # Validate response
                if not response or not response.text:
                    raise ValueError("Empty response from Gemini")
                    
                return response.text.strip()
                
            except RequestException as e:
                logger.log("GeminiClient", f"Network error (attempt {attempt + 1}): {e}")
                last_exception = e
                time.sleep(self.retry_delay)
            except Exception as e:
                logger.log("GeminiClient", f"API error (attempt {attempt + 1}): {e}")
                last_exception = e
                time.sleep(self.retry_delay)
        
        logger.log("GeminiClient", f"All retries failed. Last error: {last_exception}")
        return None
    
    def generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Generate and parse JSON response"""
        response_text = self.generate_response(prompt, json_mode=True)
        if not response_text:
            return None
            
        try:
            # Clean response
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
                
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.log("GeminiClient", f"JSON parsing error: {e}")
            return None