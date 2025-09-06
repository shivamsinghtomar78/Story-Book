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
FREEPIK_API_KEY = os.getenv("FREEPIK_API_KEY")  # Added Freepik API key

# API key warnings
if not OPENROUTER_API_KEY:
    print("Warning: OPENROUTER_API_KEY missing in .env")
if not REPLICATE_API_TOKEN:
    print("Warning: REPLICATE_API_TOKEN missing in .env")
if not HUGGINGFACEHUB_API_TOKEN:
    print("Warning: HUGGINGFACEHUB_API_TOKEN missing in .env")
if not FREEPIK_API_KEY:
    print("Warning: FREEPIK_API_KEY missing in .env")

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

# Freepik API configuration
FREEPIK_HEADERS = {
    "x-freepik-api-key": FREEPIK_API_KEY,
    "Content-Type": "application/json"
}

# ----------------------
# Enhanced Story Generation Functions
# ----------------------

def generate_story_pages(prompt, story_length="normal"):
    """Generate a children's story with enhanced length options"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # Determine story specifications based on length
    length_specs = {
        "short": {"pages": 3, "sentences": "1-2 sentences per page", "description": "Very short story for toddlers"},
        "normal": {"pages": 5, "sentences": "2-3 sentences per page", "description": "Standard children's story"},
        "long": {"pages": 8, "sentences": "3-4 sentences per page", "description": "Longer story with more detail"},
        "extended": {"pages": 10, "sentences": "4-5 sentences per page", "description": "Extended story with rich detail"}
    }
    
    spec = length_specs.get(story_length, length_specs["normal"])
    
    system_message = f"""You are a creative children's storybook writer. Create exactly {spec['pages']} pages of a children's story.
    
    Story Requirements:
    - {spec['description']}
    - {spec['sentences']}
    - Rich, descriptive language that engages children
    - Include dialogue when appropriate
    - Build character development throughout the story
    - Create a satisfying story arc with beginning, middle, and end
    - Use vivid imagery that will translate well to illustrations
    - Make it educational and entertaining
    
    Format your response as JSON with this structure:
    {{
        "title": "Story Title",
        "character_description": "Detailed description of main character(s) including appearance, clothing, personality for consistent image generation",
        "setting": "Description of the main setting/world for consistent imagery",
        "pages": [
            {{"page": 1, "text": "Page 1 text content with rich detail"}},
            {{"page": 2, "text": "Page 2 text content with rich detail"}},
            ...continuing for all {spec['pages']} pages
        ],
        "moral": "The lesson or message of the story"
    }}
    
    Make sure the story is appropriate for children aged 3-8 and each page flows naturally to the next."""
    
    data = {
        "model": TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Create a {story_length} {spec['pages']}-page children's storybook about: {prompt}"},
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

# ----------------------
# Enhanced Image Generation Functions
# ----------------------

def generate_image_freepik(prompt, filename="story.png"):
    """Generate image using Freepik API - Primary method"""
    print("\n🎨 Image Generation via Freepik API")
    
    if not FREEPIK_API_KEY:
        print("❌ FREEPIK_API_KEY not found")
        return None
    
    url = "https://api.freepik.com/v1/ai/text-to-image"
    
    # Enhanced prompt for children's storybook
    enhanced_prompt = f"High-quality children's storybook illustration: {prompt}. Whimsical, colorful, cartoon style, bright vibrant colors, fairy tale atmosphere, professional digital art, detailed, beautiful lighting, suitable for children aged 3-8"
    
    payload = {
        "prompt": enhanced_prompt,
        "num_images": 1,
        "image": {
            "size": "landscape_4_3"  # Perfect for storybook pages
        }
    }
    
    try:
        print(f"📤 Sending request to Freepik API...")
        response = requests.post(url, headers=FREEPIK_HEADERS, json=payload, timeout=60)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if 'data' in result and result['data']:
                image_data = result['data'][0]
                
                # Handle base64 encoded image
                if 'base64' in image_data:
                    try:
                        base64_data = image_data['base64']
                        if base64_data.startswith('data:image'):
                            base64_data = base64_data.split(',', 1)[1]
                        
                        image_bytes = base64.b64decode(base64_data)
                        with open(filename, 'wb') as f:
                            f.write(image_bytes)
                        print(f"✅ Freepik image saved as {filename}")
                        return filename
                    except Exception as e:
                        print(f"❌ Failed to decode base64 image: {e}")
                        return None
                
                # Handle URL-based image
                elif 'url' in image_data:
                    try:
                        img_response = requests.get(image_data['url'], timeout=30)
                        if img_response.status_code == 200:
                            with open(filename, "wb") as f:
                                f.write(img_response.content)
                            print(f"✅ Freepik image downloaded as {filename}")
                            return filename
                        else:
                            print(f"❌ Failed to download image: {img_response.status_code}")
                            return None
                    except Exception as e:
                        print(f"❌ Error downloading image: {e}")
                        return None
                
                else:
                    print("❌ No recognizable image data in response")
                    return None
            else:
                print("❌ No image data in Freepik response")
                return None
                
        elif response.status_code == 401:
            print("❌ Freepik API: Authentication failed")
            return None
        elif response.status_code == 402:
            print("❌ Freepik API: Payment required - insufficient credits")
            return None
        elif response.status_code == 429:
            print("❌ Freepik API: Rate limit exceeded")
            return None
        else:
            print(f"❌ Freepik API failed: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Freepik API timeout")
        return None
    except Exception as e:
        print(f"❌ Freepik API error: {e}")
        return None

def generate_image_huggingface(prompt, filename="story.png"):
    """Generate image using Hugging Face Stable Diffusion XL"""
    print("\n🤗 Image Generation via Hugging Face")
    
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
            with open(filename, "wb") as f:
                f.write(resp.content)
            print(f"✅ Hugging Face image saved as {filename}")
            return filename
        else:
            print(f"❌ Hugging Face failed: {resp.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Hugging Face error: {e}")
        return None

def generate_image_replicate(prompt, filename="story.png"):
    """Generate image using Replicate as fallback"""
    print("\n🔄 Image Generation via Replicate")
    
    url = f"https://api.replicate.com/v1/models/{IMAGE_MODEL_VERSION}/predictions"
    payload = {
        "input": {
            "prompt": prompt,
            "width": 1024,
            "height": 768,
            "num_inference_steps": 28,
            "guidance_scale": 3.5
        }
    }
    
    try:
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
                print("❌ Replicate generation failed")
                return None
        else:
            print("❌ Failed to start Replicate generation")
            return None
    except Exception as e:
        print(f"❌ Replicate error: {e}")
        return None

def generate_image(story_text, character_desc="", setting_desc="", filename="story.png"):
    """Enhanced image generation with Freepik as primary, multiple fallbacks"""
    
    # Create enhanced prompt with character and setting consistency
    base_prompt = f"Children's storybook illustration: {story_text}"
    if character_desc:
        base_prompt += f" Character: {character_desc}"
    if setting_desc:
        base_prompt += f" Setting: {setting_desc}"
    
    image_prompt = f"{base_prompt}. Whimsical, colorful, cartoon style, fairy tale atmosphere, beautiful lighting, suitable for children"
    
    print(f"\n🎨 Starting image generation...")
    
    # Try Freepik first (best quality for storybooks)
    print("Trying Freepik API (Primary - High Quality)...")
    freepik_result = generate_image_freepik(image_prompt, filename)
    if freepik_result:
        return freepik_result
    
    # Fallback to Hugging Face
    print("Freepik failed, trying Hugging Face...")
    hf_result = generate_image_huggingface(image_prompt, filename)
    if hf_result:
        return hf_result
    
    # Final fallback to Replicate
    print("Hugging Face failed, trying Replicate...")
    replicate_result = generate_image_replicate(image_prompt, filename)
    if replicate_result:
        return replicate_result
    
    print("❌ All image generation methods failed")
    return None

def generate_page_image(character_description, page_text, page_number, story_id, setting_description=""):
    """Generate an image for a specific page with enhanced consistency"""
    print(f"\n🖼️ Generating image for page {page_number}")
    
    filename = f"page_{page_number}_{story_id}.png"
    filepath = os.path.join("uploads", filename)
    
    # Create a more focused prompt that maintains character consistency
    # Extract key action/scene from page text while keeping character context
    scene_keywords = extract_scene_keywords(page_text)
    
    # Build enhanced prompt with character consistency
    enhanced_prompt = f"Children's storybook illustration showing {character_description}"
    
    if scene_keywords:
        enhanced_prompt += f" in this scene: {scene_keywords}"
    else:
        # Fallback to first 100 characters of page text
        scene_desc = page_text[:100] + "..." if len(page_text) > 100 else page_text
        enhanced_prompt += f" in this scene: {scene_desc}"
    
    if setting_description:
        enhanced_prompt += f". Setting: {setting_description}"
    
    enhanced_prompt += ". Consistent character design, whimsical cartoon style, bright colors, child-friendly"
    
    print(f"📝 Enhanced prompt: {enhanced_prompt}")
    
    # Use enhanced generate_image function
    result = generate_image(enhanced_prompt, "", "", filepath)
    
    if result:
        print(f"✅ Image saved as {filepath}")
        return filepath
    else:
        print(f"❌ Image generation failed for page {page_number}")
        return None

def extract_scene_keywords(text):
    """Extract key scene elements while keeping it concise"""
    import re
    
    # Remove common story words that don't help with image generation
    stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
    
    # Extract action words and important nouns
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Keep important scene elements (actions, objects, emotions)
    important_words = []
    action_words = {'run', 'walk', 'jump', 'fly', 'swim', 'dance', 'sing', 'play', 'laugh', 'smile', 'cry', 'sleep', 'eat', 'drink', 'climb', 'fall', 'sit', 'stand', 'look', 'see', 'find', 'meet', 'help', 'save', 'fight', 'hide', 'explore', 'discover', 'build', 'create', 'magic', 'adventure'}
    object_words = {'tree', 'flower', 'house', 'castle', 'forest', 'mountain', 'river', 'ocean', 'garden', 'bridge', 'door', 'window', 'book', 'treasure', 'crown', 'sword', 'wand', 'star', 'moon', 'sun', 'cloud', 'rainbow'}
    
    for word in words:
        if word not in stop_words and len(word) > 2:
            if word in action_words or word in object_words or word.endswith('ing') or word.endswith('ed'):
                important_words.append(word)
    
    # Limit to most important words to keep prompt focused
    scene_desc = ' '.join(important_words[:8])
    
    return scene_desc if scene_desc else None

# ----------------------
# Enhanced TTS Functions
# ----------------------

def try_fallback_tts(text, filename):
    """Enhanced fallback TTS with multiple options"""
    print("Attempting fallback TTS solution...")
    try:
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
    """Generate speech for a specific page with enhanced voice options"""
    print(f"\n🔊 Generating TTS for page {page_number}")
    
    filename = f"page_{page_number}_{story_id}.wav"
    filepath = os.path.join("uploads", filename)
    
    # Try primary TTS method first (OpenRouter)
    url = "https://openrouter.ai/api/v1/audio/speech"
    data = {
        "model": TTS_MODEL,
        "input": text,
        "voice": "af_bella"  # Child-friendly voice
    }
    
    resp = requests.post(url, headers=OPENROUTER_HEADERS, json=data)
    if resp.status_code == 200:
        with open(filepath, "wb") as f:
            f.write(resp.content)
        print(f"✅ Primary TTS speech saved as {filepath}")
        return filepath
    else:
        print(f"❌ Primary TTS failed: {resp.text}")
        
        # Try fallback TTS (gTTS)
        fallback_filename = f"page_{page_number}_{story_id}.mp3"
        fallback_filepath = os.path.join("uploads", fallback_filename)
        
        result = try_fallback_tts(text, fallback_filepath)
        if result:
            return fallback_filepath
        else:
            print(f"❌ All TTS methods failed for page {page_number}")
            return None

# ----------------------
# Enhanced PDF Creation
# ----------------------

def create_storybook_pdf(story_data, image_paths, story_id):
    """Create enhanced PDF storybook with better formatting"""
    filename = f"storybook_{story_id}.pdf"
    filepath = os.path.join("uploads", filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    # Enhanced custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        spaceAfter=30,
        alignment=1,  # Center
        textColor=colors.darkblue,
        fontName='Helvetica-Bold'
    )
    
    story_style = ParagraphStyle(
        'StoryText',
        parent=styles['Normal'],
        fontSize=16,
        spaceAfter=20,
        alignment=0,  # Left
        leftIndent=30,
        rightIndent=30,
        leading=22
    )
    
    moral_style = ParagraphStyle(
        'MoralText',
        parent=styles['Normal'],
        fontSize=14,
        spaceAfter=15,
        alignment=1,  # Center
        leftIndent=40,
        rightIndent=40,
        textColor=colors.darkgreen,
        fontName='Helvetica-Oblique'
    )
    
    story = []
    
    # Title page
    story.append(Paragraph(story_data['title'], title_style))
    story.append(Spacer(1, 30))
    
    # Add moral/message if available
    if 'moral' in story_data and story_data['moral']:
        story.append(Paragraph(f"<i>Lesson: {story_data['moral']}</i>", moral_style))
        story.append(Spacer(1, 20))
    
    # Story pages with enhanced layout
    for i, page in enumerate(story_data['pages']):
        page_num = page['page']
        
        # Add page break between pages (except first)
        if i > 0:
            story.append(Spacer(1, 30))
        
        # Add page title
        story.append(Paragraph(f"Page {page_num}", styles['Heading2']))
        story.append(Spacer(1, 15))
        
        # Add image if available
        if i < len(image_paths) and image_paths[i] and os.path.exists(image_paths[i]):
            try:
                # Enhanced image sizing
                img = RLImage(image_paths[i], width=5*inch, height=3.75*inch)
                story.append(img)
                story.append(Spacer(1, 15))
            except Exception as e:
                print(f"Could not add image for page {page_num}: {e}")
        
        # Add text with better formatting
        story.append(Paragraph(page['text'], story_style))
        story.append(Spacer(1, 20))
    
    doc.build(story)
    print(f"✅ Enhanced PDF created: {filepath}")
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
        story_length = request.form.get('length', 'normal')  # New: story length option
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        story_id = str(uuid.uuid4())[:8]
        
        print(f"🚀 Generating {story_length} story: {prompt}")
        
        # Generate enhanced story text
        story_data = generate_story_pages(prompt, story_length)
        
        # Generate images for each page with enhanced consistency
        image_paths = []
        for page in story_data['pages']:
            image_path = generate_page_image(
                story_data['character_description'],
                page['text'],
                page['page'],
                story_id,
                story_data.get('setting', '')
            )
            image_paths.append(image_path)
        
        # Generate speech for each page
        audio_paths = []
        for page in story_data['pages']:
            audio_path = generate_speech_for_page(
                page['text'],
                page['page'],
                story_id
            )
            audio_paths.append(audio_path)
        
        # Create enhanced PDF
        pdf_path = create_storybook_pdf(story_data, image_paths, story_id)
        
        # Store story data for viewing
        story_file = os.path.join("uploads", f"story_data_{story_id}.json")
        with open(story_file, 'w') as f:
            json.dump({
                'story_data': story_data,
                'image_paths': image_paths,
                'audio_paths': audio_paths,
                'pdf_path': pdf_path,
                'story_length': story_length
            }, f)
        
        return jsonify({
            'success': True,
            'story_id': story_id,
            'pdf_url': f'/download-pdf/{story_id}',
            'audiobook_url': f'/download-audiobook/{story_id}',
            'reader_url': f'/reader/{story_id}',
            'story_data': story_data  # Include story data for immediate display
        })
        
    except Exception as e:
        print(f"❌ Error generating story: {e}")
        return jsonify({'error': str(e)}), 500

# Keep all existing download routes...
@app.route('/download/<filename>')
def download_file(filename):
    try:
        filepath = os.path.join("uploads", filename)
        if not os.path.exists(filepath):
            return "File not found", 404
        
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
        
        try:
            return send_file(filepath, 
                            as_attachment=True, 
                            download_name=f"storybook_{story_id}.pdf",
                            mimetype='application/pdf')
        except TypeError:
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
        
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
            # Check for both .wav and .mp3 files
            for i in range(1, 15):  # Support up to 15 pages
                for ext in ['.wav', '.mp3']:
                    audio_file = f"page_{i}_{story_id}{ext}"
                    audio_path = os.path.join("uploads", audio_file)
                    if os.path.exists(audio_path):
                        zip_file.write(audio_path, f"Page_{i}{ext}")
                        break  # Use first found format
        
        temp_zip.close()
        
        try:
            return send_file(temp_zip.name, 
                            as_attachment=True, 
                            download_name=f"audiobook_{story_id}.zip",
                            mimetype='application/zip')
        except TypeError:
            return send_file(temp_zip.name, 
                            as_attachment=True, 
                            attachment_filename=f"audiobook_{story_id}.zip",
                            mimetype='application/zip')
    except Exception as e:
        return f"Audiobook download error: {str(e)}", 500

@app.route('/reader/<story_id>')
def story_reader(story_id):
    """Enhanced story reader with improved functionality"""
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
    except Exception as e:
        print(f"Error loading story reader: {e}")
        return "Error loading story", 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    try:
        filepath = os.path.join("uploads", filename)
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

# New API endpoint for story data
@app.route('/api/story/<story_id>')
def get_story_data(story_id):
    """API endpoint to get story data as JSON"""
    try:
        story_file = os.path.join("uploads", f"story_data_{story_id}.json")
        with open(story_file, 'r') as f:
            story_info = json.load(f)
        return jsonify(story_info)
    except FileNotFoundError:
        return jsonify({'error': 'Story not found'}), 404

if __name__ == '__main__':
    # Ensure uploads directory exists
    os.makedirs('uploads', exist_ok=True)
    print("🚀 Enhanced Storybook App Starting...")
    print("Features:")
    print("✅ Freepik API Integration (Primary)")
    print("✅ Multiple story lengths")
    print("✅ Enhanced PDF generation")
    print("✅ Improved reader interface")
    print("✅ Better error handling")
    app.run(debug=True, host='127.0.0.1', port=5000)