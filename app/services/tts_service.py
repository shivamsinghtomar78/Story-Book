"""Text-to-speech service using gTTS."""
import os
from gtts import gTTS
from app.config import Config
from app.utils.logging_config import get_logger

logger = get_logger('tts_service')


class TTSService:
    """Service for text-to-speech generation."""
    
    def __init__(self):
        """Initialize TTS service."""
        self.upload_folder = Config.UPLOAD_FOLDER
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def generate_speech(self, text, page_number, story_id):
        """Generate speech audio for a story page.
        
        Args:
            text: Text to convert to speech
            page_number: Page number for filename
            story_id: Unique story identifier
        
        Returns:
            str: Path to generated audio file or None if failed
        """
        logger.info(f"Generating TTS for page {page_number}", extra={
            'page_number': page_number,
            'story_id': story_id,
            'text_length': len(text)
        })
        
        filename = f"page_{page_number}_{story_id}.mp3"
        filepath = os.path.join(self.upload_folder, filename)
        
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(filepath)
            logger.info(f"TTS audio saved: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error generating audio for page {page_number}: {e}")
            return None


# Singleton instance
_tts_service = None


def get_tts_service():
    """Get or create TTS service singleton.
    
    Returns:
        TTSService instance
    """
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
