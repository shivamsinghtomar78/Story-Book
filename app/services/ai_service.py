"""AI service for story generation using LLMs."""
import json
import time
import requests
import google.generativeai as genai
from app.config import Config
from app.utils.logging_config import get_logger
from app.utils.error_handlers import APIError

logger = get_logger('ai_service')


class AIService:
    """Service for AI-powered story generation."""
    
    def __init__(self):
        """Initialize AI service with API keys and models."""
        self.openrouter_key = Config.OPENROUTER_API_KEY
        self.gemini_key = Config.GEMINI_API_KEY
        self.model_list = Config.MODEL_LIST
        self.text_model = Config.TEXT_MODEL
        
        # Configure Gemini
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
        
        self.openrouter_headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }
    
    def generate_story(self, prompt, story_length="normal"):
        """Generate a children's story using AI models.
        
        Args:
            prompt: Story topic/prompt
            story_length: Length of story (short, normal, long, extended)
        
        Returns:
            dict: Story data with title, pages, character description, etc.
        
        Raises:
            APIError: If all AI models fail
        """
        logger.info(f"Generating story with prompt: {prompt[:50]}...", extra={
            'prompt_length': len(prompt),
            'story_length': story_length
        })
        
        length_specs = {
            "short": {"pages": 3, "sentences": "1-2 sentences", "desc": "Toddler story"},
            "normal": {"pages": 5, "sentences": "2-3 sentences", "desc": "Standard story"},
            "long": {"pages": 8, "sentences": "3-4 sentences", "desc": "Detailed story"},
            "extended": {"pages": 10, "sentences": "4-5 sentences", "desc": "Chapter book style"}
        }
        
        spec = length_specs.get(story_length, length_specs["normal"])
        
        system_message = f"""You are a professional children's book author. Write a {spec['pages']}-page story.
        
CRITICAL REQUIREMENT: For EVERY page, you must write a specific "image_prompt" that describes exactly what should be drawn.

Target Audience: Children 3-8 years old.
Style: {spec['desc']}, {spec['sentences']} per page.

JSON Output Format:
{{
    "title": "Title",
    "story_cover_prompt": "A beautiful cover illustration description...",
    "character_description": "Main character visual details...",
    "setting": "World details...",
    "moral": "The lesson",
    "pages": [
        {{
            "page": 1, 
            "text": "The story text...", 
            "image_prompt": "A cute cartoon illustration of [character] doing [action] in [setting], soft lighting, 4k"
        }},
        ...
    ]
}}
"""
        
        user_prompt = f"Write a children's story about: {prompt}"
        
        last_error = None
        
        # Try each model in sequence
        for model in self.model_list:
            try:
                logger.info(f"Trying model: {model}")
                
                # Branch 1: Native Google Gemini
                if "gemini" in model and ":" not in model and self.gemini_key:
                    story_data = self._generate_with_gemini(model, system_message, user_prompt)
                    if story_data:
                        logger.info(f"Successfully generated story with Gemini: {model}")
                        return story_data
                
                # Branch 2: OpenRouter
                story_data = self._generate_with_openrouter(model, system_message, user_prompt)
                if story_data:
                    logger.info(f"Successfully generated story with OpenRouter: {model}")
                    return story_data
                    
            except Exception as e:
                logger.warning(f"Model {model} failed: {str(e)}", extra={'model': model})
                last_error = e
                time.sleep(1)  # Brief delay before trying next model
        
        # All models failed
        error_msg = f"All AI models failed to generate story. Last error: {str(last_error)}"
        logger.error(error_msg)
        raise APIError(error_msg, service='AI Models', details={'last_error': str(last_error)})
    
    def _generate_with_gemini(self, model, system_message, user_prompt):
        """Generate story using native Gemini API.
        
        Args:
            model: Model name
            system_message: System prompt
            user_prompt: User prompt
        
        Returns:
            dict: Story data or None if failed
        """
        try:
            g_model = genai.GenerativeModel(model)
            response = g_model.generate_content(
                f"{system_message}\n\nSTORY TOPIC: {user_prompt}",
                generation_config={"response_mime_type": "application/json"}
            )
            
            story_data = json.loads(response.text)
            return story_data
            
        except Exception as e:
            logger.warning(f"Gemini generation failed: {str(e)}")
            return None
    
    def _generate_with_openrouter(self, model, system_message, user_prompt):
        """Generate story using OpenRouter API.
        
        Args:
            model: Model name
            system_message: System prompt
            user_prompt: User prompt
        
        Returns:
            dict: Story data or None if failed
        """
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt},
                ]
            }
            
            resp = requests.post(url, headers=self.openrouter_headers, json=data, timeout=45)
            
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                # Cleanup potential markdown
                content = content.replace("```json", "").replace("```", "").strip()
                story_data = json.loads(content)
                return story_data
            else:
                logger.warning(f"OpenRouter API returned status {resp.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"OpenRouter generation failed: {str(e)}")
            return None


# Singleton instance
_ai_service = None


def get_ai_service():
    """Get or create AI service singleton.
    
    Returns:
        AIService instance
    """
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
