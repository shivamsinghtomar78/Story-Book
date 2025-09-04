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

if not OPENROUTER_API_KEY or not REPLICATE_API_TOKEN:
    print("Warning: API keys missing. Ensure OPENROUTER_API_KEY and REPLICATE_API_TOKEN are in .env")

# ----------------------
# API Configuration
# ----------------------

OPENROUTER_HEADERS = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
TEXT_MODEL = "meta-llama/llama-4-maverick:free"
TTS_MODEL = "neversleep/night-tts"

REPLICATE_HEADERS = {"Authorization": f"Token {REPLICATE_API_TOKEN}"}
IMAGE_MODEL_VERSION = "black-forest-labs/flux-dev"

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
        ],
        "response_format": {"type": "json_object"}
    }
    
    resp = requests.post(url, headers=OPENROUTER_HEADERS, json=data)
    if resp.status_code == 200:
        try:
            content = resp.json()["choices"][0]["message"]["content"]
            story_data = json.loads(content)
            return story_data
        except json.JSONDecodeError:
            raise RuntimeError("Failed to parse story JSON response")
    else:
        raise RuntimeError(f"Story generation failed: {resp.text}")

def generate_page_image(character_description, page_text, page_number, story_id):
    """Generate an image for a specific page with character consistency"""
    print(f"\n🖼️ Generating image for page {page_number}")
    
    # Create a focused image prompt based on the page text and character description
    image_prompt = f"Children's book illustration: {character_description} in a scene where {page_text}. Whimsical, colorful, cartoon style, suitable for children, consistent character design"
    
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
            
            filename = f"page_{page_number}_{story_id}.png"
            filepath = os.path.join("uploads", filename)
            
            with open(filepath, "wb") as f:
                f.write(image_data)
            print(f"✅ Image saved as {filepath}")
            return filepath
        else:
            print("❌ Image generation failed:", prediction.get("error", prediction))
            return None
    else:
        print("❌ Failed to start image generation:", resp.text)
        return None

def generate_speech_for_page(text, page_number, story_id):
    """Generate speech for a specific page"""
    print(f"\n🔊 Generating TTS for page {page_number}")
    
    url = "https://openrouter.ai/api/v1/audio/speech"
    data = {
        "model": TTS_MODEL,
        "input": text,
        "voice": "af_bella"
    }
    
    resp = requests.post(url, headers=OPENROUTER_HEADERS, json=data)
    if resp.status_code == 200:
        filename = f"page_{page_number}_{story_id}.wav"
        filepath = os.path.join("uploads", filename)
        
        with open(filepath, "wb") as f:
            f.write(resp.content)
        print(f"✅ Speech saved as {filepath}")
        return filepath
    else:
        print("❌ TTS generation failed:", resp.text)
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
            'pdf_url': f'/download/{os.path.basename(pdf_path)}',
            'reader_url': f'/reader/{story_id}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(os.path.join("uploads", filename), as_attachment=True)
    except FileNotFoundError:
        return "File not found", 404

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
        return send_file(os.path.join("uploads", filename), mimetype="audio/wav")
    except FileNotFoundError:
        return "Audio file not found", 404

@app.route('/image/<filename>')
def serve_image(filename):
    try:
        return send_file(os.path.join("uploads", filename), mimetype="image/png")
    except FileNotFoundError:
        return "Image file not found", 404

if __name__ == '__main__':
    # Ensure uploads directory exists
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True, host='127.0.0.1', port=5000)
