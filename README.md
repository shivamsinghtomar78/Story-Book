# 📚 AI-Generated Storybook Creator

A Flask web application that creates beautiful 5-page children's storybooks with AI-generated text, illustrations, and narration. Perfect for creating personalized bedtime stories!

## ✨ Features

- **🎨 AI Story Generation**: Creates engaging 5-page children's stories based on your prompt
- **🖼️ Consistent Illustrations**: Generates beautiful artwork with consistent character design across all pages
- **🔊 Audio Narration**: Natural human voice narration for each page using text-to-speech
- **📖 PDF Export**: Download your complete storybook as a professional PDF
- **📱 Interactive Reader**: Web-based book reader with audio playback and navigation
- **💾 Auto-save**: Saves your prompts locally for convenience

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- API keys for OpenRouter and Replicate (see setup instructions below)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd storybook-creator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys:**
   Create a `.env` file in the root directory:
   ```bash
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   REPLICATE_API_TOKEN=your_replicate_api_token_here
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Open your browser:**
   Navigate to `http://127.0.0.1:5000`

## 🔑 API Keys Setup

### OpenRouter API Key
1. Visit [OpenRouter](https://openrouter.ai/)
2. Sign up for an account
3. Go to the API Keys section
4. Create a new API key
5. Add it to your `.env` file

### Replicate API Token
1. Visit [Replicate](https://replicate.com/)
2. Sign up for an account
3. Go to your account settings
4. Generate an API token
5. Add it to your `.env` file

## 📖 How to Use

1. **Enter your story idea**: Describe the characters, setting, and adventure you want
2. **Generate your storybook**: The AI creates a 5-page story with illustrations
3. **Download PDF**: Get a beautifully formatted PDF storybook
4. **Use the reader**: Listen to narration and navigate through pages

### Example Prompts
- "A brave little mouse who goes on an adventure to find the magical cheese kingdom"
- "A young dragon who learns to fly with the help of friendly clouds"
- "A curious cat who discovers a secret garden filled with talking flowers"

## 🏗️ Project Structure

```
storybook-creator/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create this)
├── templates/         # HTML templates
│   ├── base.html      # Base template
│   ├── index.html     # Home page
│   └── reader.html    # Book reader
├── static/           # Static files
│   ├── style.css     # Custom CSS
│   └── script.js     # JavaScript utilities
└── uploads/          # Generated files (created automatically)
```

## 🎯 API Models Used

- **Text Generation**: `meta-llama/llama-4-maverick:free` (OpenRouter)
- **Image Generation**: `black-forest-labs/flux-dev` (Replicate)
- **Text-to-Speech**: `neversleep/night-tts` (OpenRouter)

## 🔧 Configuration

You can modify the API models and settings in `app.py`:

```python
TEXT_MODEL = "meta-llama/llama-4-maverick:free"
TTS_MODEL = "neversleep/night-tts"
IMAGE_MODEL_VERSION = "black-forest-labs/flux-dev"
```

## 📱 Features Overview

### Story Generation
- Creates exactly 5 pages of content
- Appropriate for children aged 3-8
- Consistent character descriptions for image generation
- JSON-structured output for easy processing

### Image Generation
- 1024x768 resolution images
- Consistent character design across pages
- Cartoon/whimsical art style
- Optimized for children's books

### Audio Narration
- Natural human voice (af_bella)
- WAV format for compatibility
- Auto-advance to next page option
- Playback controls

### PDF Export
- Professional A4 format
- Embedded images and text
- Custom styling and fonts
- Ready for printing

### Interactive Reader
- Page navigation (Previous/Next)
- Quick page jumping
- Progress tracking
- Keyboard navigation support
- Mobile-responsive design

## 🛠️ Technical Details

### Backend (Flask)
- **Routes**: Home, Generate, Download, Reader, Static file serving
- **File handling**: Automatic cleanup and organization
- **Error handling**: Comprehensive error reporting
- **Session management**: Story data persistence

### Frontend
- **Bootstrap 5**: Responsive design framework
- **Custom CSS**: Beautiful gradients and animations
- **JavaScript**: Interactive functionality and utilities
- **Progressive enhancement**: Works without JavaScript

### APIs Integration
- **OpenRouter**: Text generation and TTS with error handling
- **Replicate**: Image generation with polling for completion
- **Rate limiting**: Built-in delays to respect API limits

## 🐛 Troubleshooting

### Production Deployment Issues (Fixed)

The following issues have been resolved in the latest version:

1. **"No such file or directory" errors** ✅ FIXED
   - App now automatically creates the `uploads` directory
   - Enhanced file path handling with proper directory creation
   - Graceful fallbacks when file operations fail

2. **Image generation failures** ✅ FIXED
   - Added multiple image generation providers (Freepik → Hugging Face → Replicate)
   - Placeholder images created when all AI services fail
   - PDF generation continues even without images

3. **Missing gTTS dependency** ✅ FIXED
   - Added `gtts==2.5.1` to requirements.txt
   - Fallback TTS system for when primary TTS fails

4. **Port binding issues on Render** ✅ FIXED
   - App now uses PORT environment variable
   - Proper host binding for production deployment

### Common Issues

1. **API Keys not working**
   - Verify your `.env` file is in the root directory
   - Check that API keys are valid and have sufficient credits
   - Ensure no extra spaces in the `.env` file

2. **Images not generating**
   - The app now has multiple fallbacks and will create placeholder images
   - Check API credits for Freepik, Hugging Face, or Replicate
   - Verify internet connection

3. **Audio not playing**
   - App now falls back to gTTS if primary TTS fails
   - Check OpenRouter TTS credits
   - Verify browser audio permissions

4. **PDF not downloading**
   - PDF generation now works even without images (uses placeholders)
   - Check file permissions in uploads directory
   - Verify all dependencies are installed

### Health Check Endpoints

- `/health` - Check app status and API configuration
- `/test-story` - Test basic functionality without external APIs

## 📈 Performance Tips

- **Batch processing**: Generate multiple stories efficiently
- **Caching**: Stories are cached locally for quick access
- **Optimization**: Images are optimized for web and PDF
- **Error recovery**: Graceful handling of API failures

## 🔐 Security Notes

- API keys are stored in environment variables
- No sensitive data is logged
- File uploads are validated and secured
- Session data is temporary

 

 
