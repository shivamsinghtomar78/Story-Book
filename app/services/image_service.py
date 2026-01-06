"""Image generation service using Freepik API."""
import os
import base64
import requests
import re
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename
from app.config import Config
from app.utils.logging_config import get_logger
from app.utils.error_handlers import APIError

logger = get_logger('image_service')


class ImageService:
    """Service for generating and managing story images."""
    
    def __init__(self):
        """Initialize image service."""
        self.api_key = Config.FREEPIK_API_KEY
        self.upload_folder = Config.UPLOAD_FOLDER
        os.makedirs(self.upload_folder, exist_ok=True)
        
        self.headers = {
            "x-freepik-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def generate_image(self, prompt, filename="story.png"):
        """Generate image using Freepik API.
        
        Args:
            prompt: Image generation prompt
            filename: Desired filename for the image
        
        Returns:
            str: Path to generated image or None if failed
        """
        logger.info(f"Generating image with Freepik API", extra={'prompt_length': len(prompt)})
        
        if not self.api_key:
            logger.warning("FREEPIK_API_KEY not configured")
            return self.create_placeholder_image(filename, 1, prompt)
        
        # Sanitize filename
        try:
            safe_filename = secure_filename(os.path.basename(filename))
            filepath = os.path.join(self.upload_folder, safe_filename)
        except Exception as e:
            logger.error(f"Error preparing file path: {e}")
            return None
        
        # Enhanced prompt for children's storybook
        prompt_text = f"High-quality children's storybook illustration: {prompt}. Whimsical, colorful, cartoon style, bright vibrant colors, fairy tale atmosphere, professional digital art, detailed, beautiful lighting, suitable for children aged 3-8"
        
        if len(prompt_text) > 500:  # Freepik's max prompt length
            prompt_text = prompt_text[:497] + "..."
        
        url = "https://api.freepik.com/v1/ai/text-to-image"
        payload = {
            "prompt": prompt_text,
            "num_images": 1,
            "image": {"size": "landscape_4_3"}
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                
                if not result.get('data'):
                    logger.warning("No image data in Freepik response")
                    return self.create_placeholder_image(filepath, 1, prompt)
                
                image_data = result['data'][0]
                
                # Handle base64 encoded image
                if 'base64' in image_data:
                    return self._save_base64_image(image_data['base64'], filepath)
                
                # Handle URL based image
                elif 'url' in image_data:
                    return self._download_image(image_data['url'], filepath)
                
                else:
                    logger.warning("No recognizable image data in response")
                    return self.create_placeholder_image(filepath, 1, prompt)
            
            elif response.status_code == 401:
                logger.error("Freepik API: Authentication failed")
                return self.create_placeholder_image(filepath, 1, prompt)
            
            elif response.status_code == 402:
                logger.error("Freepik API: Payment required - insufficient credits")
                return self.create_placeholder_image(filepath, 1, prompt)
            
            elif response.status_code == 429:
                logger.error("Freepik API: Rate limit exceeded")
                return self.create_placeholder_image(filepath, 1, prompt)
            
            else:
                logger.error(f"Freepik API failed with status {response.status_code}")
                return self.create_placeholder_image(filepath, 1, prompt)
        
        except requests.exceptions.Timeout:
            logger.error("Freepik API timeout")
            return self.create_placeholder_image(filepath, 1, prompt)
        
        except Exception as e:
            logger.error(f"Freepik API error: {str(e)}")
            return self.create_placeholder_image(filepath, 1, prompt)
    
    def _save_base64_image(self, base64_data, filepath):
        """Save base64 encoded image to file."""
        try:
            if base64_data.startswith('data:image'):
                base64_data = base64_data.split(',', 1)[1]
            
            image_bytes = base64.b64decode(base64_data)
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            
            logger.info(f"Image saved from base64: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
            return None
    
    def _download_image(self, url, filepath):
        """Download image from URL."""
        try:
            img_response = requests.get(url, timeout=30)
            if img_response.status_code == 200:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(img_response.content)
                logger.info(f"Image downloaded: {filepath}")
                return filepath
            else:
                logger.error(f"Failed to download image: {img_response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None
    
    def create_placeholder_image(self, filepath, page_number, page_text):
        """Create a placeholder image when AI generation fails.
        
        Args:
            filepath: Path to save the placeholder image
            page_number: Page number for the placeholder
            page_text: Text to display on placeholder
        
        Returns:
            str: Path to created placeholder image
        """
        try:
            # Create light blue background
            img = Image.new('RGB', (1024, 768), color=(240, 248, 255))
            draw = ImageDraw.Draw(img)
            
            # Try to load fonts
            try:
                font_large = ImageFont.truetype("arial.ttf", 48)
                font_small = ImageFont.truetype("arial.ttf", 24)
            except:
                font_large = None
                font_small = None
            
            # Draw page number
            if font_large:
                draw.text((50, 50), f"Page {page_number}", fill=(70, 130, 180), font=font_large)
            else:
                draw.text((50, 50), f"Page {page_number}", fill=(70, 130, 180))
            
            # Draw rectangle for illustration area
            draw.rectangle([200, 150, 824, 450], outline=(70, 130, 180), width=3)
            if font_small:
                draw.text((350, 280), "Story Illustration", fill=(70, 130, 180), font=font_small)
            else:
                draw.text((350, 280), "Story Illustration", fill=(70, 130, 180))
            
            # Add decorative circles
            for i in range(5):
                x = 100 + i * 150
                y = 500 + (i % 2) * 50
                draw.ellipse([x, y, x+30, y+30], fill=(255, 182, 193))
            
            # Save placeholder
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            img.save(filepath, 'PNG')
            logger.info(f"Placeholder image created: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Failed to create placeholder image: {e}")
            return None
    
    def generate_page_image(self, character_description, page_text, page_number, 
                           story_id, setting_description="", specific_image_prompt=None):
        """Generate an image for a specific story page.
        
        Args:
            character_description: Description of main character
            page_text: Text content of the page
            page_number: Page number
            story_id: Unique story identifier
            setting_description: Description of the setting
            specific_image_prompt: AI-generated image prompt (preferred)
        
        Returns:
            str: Path to generated image
        """
        logger.info(f"Generating image for page {page_number}")
        
        filename = f"page_{page_number}_{story_id}.png"
        filepath = os.path.join(self.upload_folder, filename)
        
        # Use AI-generated prompt if available
        if specific_image_prompt and len(specific_image_prompt) > 10:
            enhanced_prompt = f"Children's storybook illustration: {specific_image_prompt}. Style: Disney/Pixar-inspired cartoon, vibrant colors, soft lighting, 4k, detailed, masterpiece"
            logger.info(f"Using custom AI prompt for page {page_number}")
        else:
            # Fallback to keyword extraction
            scene_keywords = self._extract_scene_keywords(page_text)
            
            enhanced_prompt = f"""High-quality children's storybook illustration for the scene:
            
Characters: {character_description}
Setting: {setting_description}
Scene: {scene_keywords if scene_keywords else page_text[:100]}

Style requirements:
- Whimsical, Disney/Pixar-inspired cartoon style
- Rich, vibrant colors with proper lighting and shadows
- Child-friendly, engaging composition
- Professional digital art quality"""
        
        result = self.generate_image(enhanced_prompt, filepath)
        
        if result:
            return result
        else:
            logger.warning(f"Image generation failed for page {page_number}, creating placeholder")
            return self.create_placeholder_image(filepath, page_number, page_text)
    
    def _extract_scene_keywords(self, text):
        """Extract key scene elements from text.
        
        Args:
            text: Story text
        
        Returns:
            str: Extracted keywords describing the scene
        """
        # Simple keyword extraction
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
                     'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were'}
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return ' '.join(keywords[:10])  # Return top 10 keywords


# Singleton instance
_image_service = None


def get_image_service():
    """Get or create image service singleton.
    
    Returns:
        ImageService instance
    """
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service
