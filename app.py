import os
import requests
import time
import base64
import uuid
import json
from flask import Flask, render_template, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from PIL import Image
import io

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# ----------------------
# Load API Keys
# ----------------------

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

if not OPENROUTER_API_KEY:
    print("Warning: OPENROUTER_API_KEY missing in .env")
if not REPLICATE_API_TOKEN:
    print("Warning: REPLICATE_API_TOKEN missing in .env")
if not HUGGINGFACEHUB_API_TOKEN:
    print("Warning: HUGGINGFACEHUB_API_TOKEN missing in .env")

# ----------------------
# API Configuration
# ----------------------

OPENROUTER_HEADERS = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
TEXT_MODEL = "meta-llama/llama-4-maverick:free"
TTS_MODEL = "neversleep/night-tts"

REPLICATE_HEADERS = {"Authorization": f"Token {REPLICATE_API_TOKEN}"}
IMAGE_MODEL_VERSION = "black-forest-labs/flux-dev"

# Hugging Face configuration
HUGGINGFACE_HEADERS = {"Authorization": f"Bearer {HUGGINGFACEHUB_API_TOKEN}"}
HUGGINGFACE_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"

# ----------------------
# Story Generation Functions
# ----------------------

def generate_story_pages(prompt):
    """Generate a 5-page children's story based on the prompt"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    system_message = """You are a creative children's storybook writer. Create exactly 5 pages of a children's story.
    
    Format your response as JSON with this structure:
    {
        "title": "Story Title",
        "character_description": "Brief description of main character(s) for consistent image generation",
        "pages": [
            {"page": 1, "text": "Page 1 text content"},
            {"page": 2, "text": "Page 2 text content"},
            {"page": 3, "text": "Page 3 text content"},
            {"page": 4, "text": "Page 4 text content"},
            {"page": 5, "text": "Page 5 text content"}
        ]
    }
    
    Keep each page to 2-3 sentences. Make sure the story is appropriate for children aged 3-8."""
    
    data = {
        "model": TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Create a 5-page children's storybook about: {prompt}"},
        ]
    }
    
    resp = requests.post(url, headers=OPENROUTER_HEADERS, json=data)
    if resp.status_code == 200:
        try:
            content = resp.json()["choices"][0]["message"]["content"]
            # Try to extract JSON from the response if it's embedded in text
            if content.strip().startswith('{'):
                story_data = json.loads(content)
            else:
                # Look for JSON within the text
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    story_data = json.loads(json_match.group())
                else:
                    raise RuntimeError("No valid JSON found in response")
            return story_data
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse story JSON response: {e}\nContent: {content}")
    else:
        raise RuntimeError(f"Story generation failed: {resp.text}")

def generate_image_huggingface(prompt, filename="story.png"):
    """Generate image using Hugging Face Stable Diffusion XL"""
    print("\n🖼️ Image Generation via Hugging Face Stable Diffusion XL")
    
    url = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}"
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
            "width": 1024,
            "height": 768
        }
    }
    
    try:
        resp = requests.post(url, headers=HUGGINGFACE_HEADERS, json=payload)
        
        if resp.status_code == 200:
            # Save the image directly from response content
            with open(filename, "wb") as f:
                f.write(resp.content)
            print(f"✅ Hugging Face image saved as {filename}")
            return filename
        else:
            print(f"❌ Hugging Face image generation failed: {resp.status_code} - {resp.text}")
            return None
            
    except Exception as e:
        print(f"❌ Hugging Face image generation error: {e}")
        return None

def generate_image(story_text, filename="story.png"):
    """Generate image with Hugging Face primary and Replicate fallback"""
    
    # Create a focused prompt based on story content
    image_prompt = f"Children's storybook illustration: {story_text}. Whimsical, colorful, cartoon style, fairy tale atmosphere, beautiful lighting, suitable for children"
    
    # Try Hugging Face first (free and reliable)
    print("Trying Hugging Face Stable Diffusion XL...")
    hf_result = generate_image_huggingface(image_prompt, filename)
    if hf_result:
        return hf_result
    
    # Fallback to Replicate if Hugging Face fails
    print("Hugging Face failed, trying Replicate as fallback...")
    print("\n🖼️ Image Generation via Replicate (Fallback)")
    
    url = f"https://api.replicate.com/v1/models/{IMAGE_MODEL_VERSION}/predictions"
    payload = {
        "input": {
            "prompt": image_prompt,
            "width": 1024,
            "height": 768,
            "num_inference_steps": 28,
            "guidance_scale": 3.5
        }
    }
    
    resp = requests.post(url, headers=REPLICATE_HEADERS, json=payload)
    if resp.status_code in [200, 201]:
        prediction = resp.json()
        print(f"Started prediction: {prediction['id']}")
        
        # Poll until prediction is complete
        while prediction["status"] not in ["succeeded", "failed", "canceled"]:
            print(f"Status: {prediction['status']}...")
            time.sleep(3)
            check_url = f"https://api.replicate.com/v1/predictions/{prediction['id']}"
            prediction = requests.get(check_url, headers=REPLICATE_HEADERS).json()

        if prediction["status"] == "succeeded":
            image_url = prediction["output"][0] if isinstance(prediction["output"], list) else prediction["output"]
            image_data = requests.get(image_url).content
            with open(filename, "wb") as f:
                f.write(image_data)
            print(f"✅ Replicate image saved as {filename}")
            return filename
        else:
            print("❌ Replicate image generation failed:", prediction.get("error", prediction))
            return None
    else:
        print("❌ Failed to start Replicate image generation:", resp.text)
        return None

def generate_page_image(character_description, page_text, page_number, story_id):
    """Generate an image for a specific page using the working generate_image function"""
    print(f"\n🖼️ Generating image for page {page_number}")
    
    filename = f"page_{page_number}_{story_id}.png"
    filepath = os.path.join("uploads", filename)
    
    # Use the working generate_image function
    result = generate_image(page_text, filepath)
    
    if result:
        print(f"✅ Image saved as {filepath}")
        return filepath
    else:
        print(f"❌ Image generation failed for page {page_number}")
        return None

def try_fallback_tts(text, filename):
    """Try a simple fallback TTS method if the primary one fails"""
    print("Attempting fallback TTS solution...")
    try:
        # Try using gTTS (Google Text-to-Speech) as a fallback
        from gtts import gTTS
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(filename)
        print(f"✅ Fallback speech saved as {filename}")
        return filename
    except ImportError:
        print("❌ gTTS not installed. Install with: pip install gtts")
        return None
    except Exception as e:
        print(f"❌ Fallback TTS also failed: {e}")
        return None

def generate_speech_for_page(text, page_number, story_id):
    """Generate speech for a specific page with fallback support"""
    print(f"\n🔊 Generating TTS for page {page_number}")
    
    filename = f"page_{page_number}_{story_id}.wav"
    filepath = os.path.join("uploads", filename)
    
    # Try primary TTS method first (OpenRouter)
    url = "https://openrouter.ai/api/v1/audio/speech"
    data = {
        "model": TTS_MODEL,
        "input": text,
        "voice": "af_bella"
    }
    
    resp = requests.post(url, headers=OPENROUTER_HEADERS, json=data)
    if resp.status_code == 200:
        with open(filepath, "wb") as f:
            f.write(resp.content)
        print(f"✅ Primary TTS speech saved as {filepath}")
        return filepath
    else:
        print(f"❌ Primary TTS failed: {resp.text}")
        print("Trying fallback TTS method...")
        
        # Try fallback TTS (gTTS)
        # For gTTS, we need to use .mp3 extension
        fallback_filename = f"page_{page_number}_{story_id}.mp3"
        fallback_filepath = os.path.join("uploads", fallback_filename)
        
        result = try_fallback_tts(text, fallback_filepath)
        if result:
            return fallback_filepath
        else:
            print(f"❌ All TTS methods failed for page {page_number}")
            return None

def create_storybook_pdf(story_data, image_paths, story_id):
    """Create a PDF storybook combining text and images"""
    filename = f"storybook_{story_id}.pdf"
    filepath = os.path.join("uploads", filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # Center
        textColor=colors.darkblue
    )
    
    story_style = ParagraphStyle(
        'StoryText',
        parent=styles['Normal'],
        fontSize=14,
        spaceAfter=20,
        alignment=0,  # Left
        leftIndent=20,
        rightIndent=20
    )
    
    story = []
    
    # Title page
    story.append(Paragraph(story_data['title'], title_style))
    story.append(Spacer(1, 20))
    
    # Story pages
    for i, page in enumerate(story_data['pages']):
        page_num = page['page']
        
        # Add page title
        story.append(Paragraph(f"Page {page_num}", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        # Add image if available
        if i < len(image_paths) and image_paths[i] and os.path.exists(image_paths[i]):
            try:
                # Resize image to fit on page
                img = RLImage(image_paths[i], width=4*inch, height=3*inch)
                story.append(img)
                story.append(Spacer(1, 10))
            except Exception as e:
                print(f"Could not add image for page {page_num}: {e}")
        
        # Add text
        story.append(Paragraph(page['text'], story_style))
        story.append(Spacer(1, 30))
    
    doc.build(story)
    print(f"✅ PDF created: {filepath}")
    return filepath

# ----------------------
# Flask Routes
# ----------------------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/test-downloads')
def test_downloads():
    return render_template('test_downloads.html')

@app.route('/generate', methods=['POST'])
def generate_storybook():
    try:
        prompt = request.form.get('prompt')
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        story_id = str(uuid.uuid4())[:8]
        
        # Generate story text
        story_data = generate_story_pages(prompt)
        
        # Generate images for each page
        image_paths = []
        for page in story_data['pages']:
            image_path = generate_page_image(
                story_data['character_description'],
                page['text'],
                page['page'],
                story_id
            )
            image_paths.append(image_path)
        
        # Generate speech for each page (optional)
        audio_paths = []
        for page in story_data['pages']:
            audio_path = generate_speech_for_page(
                page['text'],
                page['page'],
                story_id
            )
            audio_paths.append(audio_path)
        
        # Create PDF
        pdf_path = create_storybook_pdf(story_data, image_paths, story_id)
        
        # Store story data for viewing
        story_file = os.path.join("uploads", f"story_data_{story_id}.json")
        with open(story_file, 'w') as f:
            json.dump({
                'story_data': story_data,
                'image_paths': image_paths,
                'audio_paths': audio_paths,
                'pdf_path': pdf_path
            }, f)
        
        return jsonify({
            'success': True,
            'story_id': story_id,
            'pdf_url': f'/download-pdf/{story_id}',
            'audiobook_url': f'/download-audiobook/{story_id}',
            'reader_url': f'/reader/{story_id}',
            'legacy_pdf_url': f'/download/{os.path.basename(pdf_path)}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        filepath = os.path.join("uploads", filename)
        if not os.path.exists(filepath):
            return "File not found", 404
        
        # Determine the appropriate mimetype
        if filename.lower().endswith('.pdf'):
            mimetype = 'application/pdf'
        elif filename.lower().endswith('.mp3'):
            mimetype = 'audio/mpeg'
        elif filename.lower().endswith('.wav'):
            mimetype = 'audio/wav'
        elif filename.lower().endswith('.zip'):
            mimetype = 'application/zip'
        else:
            mimetype = 'application/octet-stream'
            
        return send_file(filepath, as_attachment=True, mimetype=mimetype)
    except Exception as e:
        return f"Download error: {str(e)}", 500

@app.route('/download-pdf/<story_id>')
def download_pdf(story_id):
    try:
        pdf_filename = f"storybook_{story_id}.pdf"
        filepath = os.path.join("uploads", pdf_filename)
        if not os.path.exists(filepath):
            return "PDF not found", 404
        # Use download_name for better filename control
        try:
            return send_file(filepath, 
                            as_attachment=True, 
                            download_name=f"storybook_{story_id}.pdf",
                            mimetype='application/pdf')
        except TypeError:
            # Fallback for older Flask versions
            return send_file(filepath, 
                            as_attachment=True, 
                            attachment_filename=f"storybook_{story_id}.pdf",
                            mimetype='application/pdf')
    except Exception as e:
        return f"PDF download error: {str(e)}", 500

@app.route('/download-audiobook/<story_id>')
def download_audiobook(story_id):
    try:
        import zipfile
        import tempfile
        
        # Create a temporary zip file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
            # Add all audio files for this story
            for i in range(1, 6):  # Pages 1-5
                audio_file = f"page_{i}_{story_id}.mp3"
                audio_path = os.path.join("uploads", audio_file)
                if os.path.exists(audio_path):
                    zip_file.write(audio_path, f"Page_{i}.mp3")
        
        temp_zip.close()
        
        # Use attachment_filename for older Flask versions compatibility
        try:
            return send_file(temp_zip.name, 
                            as_attachment=True, 
                            download_name=f"audiobook_{story_id}.zip",
                            mimetype='application/zip')
        except TypeError:
            # Fallback for older Flask versions
            return send_file(temp_zip.name, 
                            as_attachment=True, 
                            attachment_filename=f"audiobook_{story_id}.zip",
                            mimetype='application/zip')
    except Exception as e:
        return f"Audiobook download error: {str(e)}", 500

@app.route('/reader/<story_id>')
def story_reader(story_id):
    try:
        story_file = os.path.join("uploads", f"story_data_{story_id}.json")
        with open(story_file, 'r') as f:
            story_info = json.load(f)
        
        return render_template('reader.html', 
                             story_data=story_info['story_data'],
                             image_paths=story_info['image_paths'],
                             audio_paths=story_info['audio_paths'],
                             story_id=story_id)
    except FileNotFoundError:
        return "Story not found", 404

@app.route('/audio/<filename>')
def serve_audio(filename):
    try:
        filepath = os.path.join("uploads", filename)
        # Determine MIME type based on file extension
        if filename.lower().endswith('.mp3'):
            mimetype = "audio/mpeg"
        else:
            mimetype = "audio/wav"
        return send_file(filepath, mimetype=mimetype)
    except FileNotFoundError:
        return "Audio file not found", 404

@app.route('/image/<filename>')
def serve_image(filename):
    try:
        return send_file(os.path.join("uploads", filename), mimetype="image/png")
    except FileNotFoundError:
        return "Image file not found", 404

@app.route('/debug/<story_id>')
def debug_story(story_id):
    """Debug route to check story files"""
    try:
        uploads_dir = "uploads"
        debug_info = {
            "story_id": story_id,
            "files": {},
            "urls": {}
        }
        
        # Check PDF
        pdf_file = f"storybook_{story_id}.pdf"
        pdf_path = os.path.join(uploads_dir, pdf_file)
        debug_info["files"]["pdf"] = {
            "filename": pdf_file,
            "exists": os.path.exists(pdf_path),
            "size": os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
        }
        
        # Check audio files
        debug_info["files"]["audio"] = {}
        for i in range(1, 6):
            audio_file = f"page_{i}_{story_id}.mp3"
            audio_path = os.path.join(uploads_dir, audio_file)
            debug_info["files"]["audio"][f"page_{i}"] = {
                "filename": audio_file,
                "exists": os.path.exists(audio_path),
                "size": os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
            }
        
        # Generate URLs
        debug_info["urls"] = {
            "pdf_download": f"/download-pdf/{story_id}",
            "audiobook_download": f"/download-audiobook/{story_id}",
            "reader": f"/reader/{story_id}"
        }
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Ensure uploads directory exists
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True, host='127.0.0.1', port=5000)
