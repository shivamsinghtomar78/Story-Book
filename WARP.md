# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development Commands

### Environment Setup
```powershell
# Install Python dependencies
pip install -r requirements.txt

# Create environment file from example
cp .env.example .env
# Then edit .env with your API keys:
# OPENROUTER_API_KEY=your_openrouter_api_key_here
# REPLICATE_API_TOKEN=your_replicate_api_token_here
```

### Running the Application
```powershell
# Start development server
python app.py

# The app runs on http://127.0.0.1:5000
```

### Testing and Validation
```powershell
# Test API keys are working
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('OpenRouter:', bool(os.getenv('OPENROUTER_API_KEY'))); print('Replicate:', bool(os.getenv('REPLICATE_API_TOKEN')))"

# Check dependencies
pip list | findstr -i "flask requests pillow reportlab"

# Validate uploads directory exists
python -c "import os; print('Uploads dir exists:', os.path.exists('uploads'))"
```

## Architecture Overview

### Application Structure
This is a **Flask-based AI storybook generator** that orchestrates multiple AI APIs to create children's storybooks:

- **Frontend**: Bootstrap 5 + custom JavaScript for interactive UI
- **Backend**: Flask web server with API integration layer
- **AI Pipeline**: Sequential AI service calls (text → images → audio → PDF)
- **File Management**: Local uploads directory for generated content

### Core Workflow
1. **Story Generation**: OpenRouter API (meta-llama/llama-4-maverick) creates 5-page JSON story structure
2. **Image Generation**: Replicate API (black-forest-labs/flux-dev) creates consistent character illustrations
3. **Audio Generation**: OpenRouter TTS API (neversleep/night-tts) creates narration
4. **PDF Assembly**: ReportLab combines text, images into downloadable storybook
5. **Interactive Reader**: Web-based reader with audio playback and navigation

### API Integration Patterns
- **OpenRouter Integration**: Handles both text generation and text-to-speech using different models
- **Replicate Integration**: Implements polling pattern for image generation completion
- **Error Handling**: Comprehensive try-catch with user-friendly error messages
- **Rate Limiting**: Built-in delays between API calls to respect service limits

### Key Components

#### Main Flask App (`app.py`)
- Route handlers for generation, downloads, and reader
- API orchestration functions for each generation step
- File serving for images, audio, and PDFs
- Session management for story data persistence

#### Frontend Templates
- **`base.html`**: Bootstrap layout with custom fonts (Fredoka)
- **`index.html`**: Story prompt form with progress tracking
- **`reader.html`**: Interactive storybook reader with audio controls

#### Static Assets
- **`script.js`**: Utility library with notification system, storage helpers, and UI animations
- **`style.css`**: Custom styling and gradients for children's book aesthetic

### Data Flow
1. User submits story prompt via form
2. Backend generates story JSON with character descriptions
3. Images generated sequentially using character consistency prompts
4. Audio files generated for each page text
5. PDF assembled with embedded images and styled text
6. Story data saved as JSON for reader access
7. User gets download link and reader URL

### File Organization
- **`uploads/`**: Generated content (images, audio, PDFs, story JSON)
- **`templates/`**: Jinja2 HTML templates
- **`static/`**: CSS, JavaScript, and client-side assets
- **`.env`**: API keys (not committed to repo)

### Configuration Points
- **Text Model**: `meta-llama/llama-4-maverick:free` (OpenRouter)
- **Image Model**: `black-forest-labs/flux-dev` (Replicate)  
- **TTS Model**: `neversleep/night-tts` (OpenRouter)
- **Image Specs**: 1024x768 resolution, cartoon/whimsical style
- **Audio**: WAV format with af_bella voice
- **PDF**: A4 format with custom styling

## Important Implementation Details

### API Response Handling
- Story generation expects structured JSON response with title, character_description, and 5 pages
- Image generation uses polling pattern - check status until "succeeded", "failed", or "canceled"
- TTS returns binary audio data directly
- All API calls include comprehensive error handling

### Character Consistency Strategy
The app maintains visual consistency across pages by:
1. Generating detailed character description in story JSON
2. Using same character description in all image generation prompts
3. Adding contextual scene information from each page's text

### Performance Considerations
- Sequential API calls (not parallel) to manage rate limits
- Local file caching prevents regeneration
- Progress indicators keep users engaged during long generation times
- Graceful degradation if individual services fail

### Security Notes
- API keys stored in environment variables only
- File uploads validated and secured in uploads directory  
- No user data persistence beyond session
- Temporary story files include unique IDs to prevent conflicts
