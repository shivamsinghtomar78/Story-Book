import os
import requests
import time
import base64
import uuid
import json
import logging
from datetime import timedelta
from flask import Flask, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from PIL import Image
import io
from gtts import gTTS

# New Imports for Auth & DB
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
import bcrypt
import google.generativeai as genai

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, 
            static_folder=os.path.join(basedir, 'frontend/dist'),
            static_url_path='/')
CORS(app)  # Enable CORS for React frontend

# Configuration
load_dotenv()
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET_KEY', app.secret_key)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)

jwt = JWTManager(app)

# Database Setup
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    print("⚠️ WARNING: MONGO_URI not found in .env")
    client = None
    db = None
    users_collection = None
else:
    try:
        client = MongoClient(MONGO_URI)
        db = client['storybook_db']  # Database name
        users_collection = db['users']
        print("✅ Connected to MongoDB Atlas")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        client = None
        users_collection = None

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  
FREEPIK_API_KEY = os.getenv("FREEPIK_API_KEY")  

if not OPENROUTER_API_KEY:
    print("Warning: OPENROUTER_API_KEY missing in .env")
if not FREEPIK_API_KEY:
    print("Warning: FREEPIK_API_KEY missing in .env")

# Gemini Setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY missing in .env")

OPENROUTER_HEADERS = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
TEXT_MODEL = "google/gemini-2.0-flash-exp:free"

FREEPIK_HEADERS = {
    "x-freepik-api-key": FREEPIK_API_KEY,
    "Content-Type": "application/json"
}

# --- Auth Routes ---

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    if users_collection is None:
        return jsonify({"error": "Database not configured"}), 500
        
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
        
    if users_collection.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 400
        
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    user_id = users_collection.insert_one({
        "email": email,
        "password": hashed_password,
        "name": name,
        "created_at": time.time()
    }).inserted_id
    
    access_token = create_access_token(identity=str(user_id))
    
    return jsonify({
        "message": "User registered successfully",
        "token": access_token,
        "user": {"email": email, "name": name}
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    if users_collection is None:
        return jsonify({"error": "Database not configured"}), 500
        
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = users_collection.find_one({"email": email})
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        access_token = create_access_token(identity=str(user['_id']))
        return jsonify({
            "message": "Login successful",
            "token": access_token,
            "user": {"email": email, "name": user.get('name')}
        }), 200
        
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_user_profile():
    return jsonify({"message": "Valid token", "user_id": get_jwt_identity()})

# --- Story Routes ---


# List of models - Prioritize Gemini Flash
MODEL_LIST = [
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash", 
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "openchat/openchat-7:free"
]

def generate_story_pages(prompt, story_length="normal"):
    """Generate a children's story using Native Gemini or OpenRouter."""
    
    length_specs = {
        "short": {"pages": 3, "sentences": "1-2 sentences", "desc": "Toddler story"},
        "normal": {"pages": 5, "sentences": "2-3 sentences", "desc": "Standard story"},
        "long": {"pages": 8, "sentences": "3-4 sentences", "desc": "Detailed story"},
        "extended": {"pages": 10, "sentences": "4-5 sentences", "desc": "Chapter book style"}
    }
    
    spec = length_specs.get(story_length, length_specs["normal"])
    
    # ENHANCED PROMPT: Requests specific image prompts for each page
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
    
    for model in MODEL_LIST:
        print(f"🔄 Trying model: {model}")
        
        # Branch 1: Native Google Gemini
        if "gemini" in model and ":" not in model and GEMINI_API_KEY:
            try:
                g_model = genai.GenerativeModel(model)
                response = g_model.generate_content(
                    f"{system_message}\n\nSTORY TOPIC: {user_prompt}",
                    generation_config={"response_mime_type": "application/json"}
                )
                
                story_data = json.loads(response.text)
                print(f"✅ Gemini Native Success: {model}")
                return story_data
            except Exception as e:
                print(f"⚠️ Gemini Native Error: {e}")
                last_error = e
                continue

        # Branch 2: OpenRouter (Fallback)
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt},
                ]
            }
            
            resp = requests.post(url, headers=OPENROUTER_HEADERS, json=data, timeout=45)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                # Cleanup potential markdown
                content = content.replace("```json", "").replace("```", "").strip()
                story_data = json.loads(content)
                print(f"✅ OpenRouter Success: {model}")
                return story_data
            else:
                print(f"⚠️ API Error {resp.status_code}")
                time.sleep(1)
        except Exception as e:
            print(f"⚠️ Network error: {e}")
            last_error = e
            time.sleep(1)
            
    raise RuntimeError(f"All models failed. Last error: {last_error}")

 

def generate_image_freepik(prompt, filename="story.png"):
    """Generate image using Freepik API - Primary method"""
    print("\n Image Generation via Freepik API")
    
    if not FREEPIK_API_KEY:
        print(" FREEPIK_API_KEY not found")
        return None
    
    # Validate and sanitize filename
    try:
        safe_filename = secure_filename(os.path.basename(filename))
        filepath = os.path.join('uploads', safe_filename)
        os.makedirs('uploads', exist_ok=True)
    except Exception as e:
        print(f" Error preparing file path: {e}")
        return None
    
    url = "https://api.freepik.com/v1/ai/text-to-image"
    
    # Enhanced prompt for children's storybook with length limit
    prompt_text = f"High-quality children's storybook illustration: {prompt}. Whimsical, colorful, cartoon style, bright vibrant colors, fairy tale atmosphere, professional digital art, detailed, beautiful lighting, suitable for children aged 3-8"
    if len(prompt_text) > 500:  # Freepik's max prompt length
        prompt_text = prompt_text[:497] + "..."
    
    payload = {
        "prompt": prompt_text,
        "num_images": 1,
        "image": {
            "size": "landscape_4_3"
        }
    }
    
    try:
        print(" Sending request to Freepik API...")
        response = requests.post(url, headers=FREEPIK_HEADERS, json=payload, timeout=60)
        
        print(f" Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                print(f" Error parsing JSON response: {e}")
                return None
                
            if not result.get('data'):
                print(" No image data in response")
                return None
                
            image_data = result['data'][0]
            
            if 'base64' in image_data:
                try:
                    base64_data = image_data['base64']
                    if base64_data.startswith('data:image'):
                        base64_data = base64_data.split(',', 1)[1]
                    
                    image_bytes = base64.b64decode(base64_data)
                    
                    os.makedirs(os.path.dirname(filename), exist_ok=True)
                    with open(filename, 'wb') as f:
                        f.write(image_bytes)
                    print(f"✅ Freepik image saved as {filename}")
                    return filename
                except Exception as e:
                    print(f" Failed to decode base64 image: {e}")
                    return None
            
            # Handle URL-based image
            elif 'url' in image_data:
                try:
                    img_response = requests.get(image_data['url'], timeout=30)
                    if img_response.status_code == 200:
                        # Ensure directory exists before writing
                        os.makedirs(os.path.dirname(filename), exist_ok=True)
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
        print(f"❌ Freepik API error: {str(e)}")
        return None
        print(f" Freepik API error: {e}")
        return None

# def generate_image_huggingface(prompt, filename="story.png"):
#     """Generate image using Hugging Face Stable Diffusion XL"""
#     print("\n Image Generation via Hugging Face")
    
#     # Ensure uploads directory exists
#     os.makedirs('uploads', exist_ok=True)
    
#     url = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}"
    
#     payload = {
#         "inputs": prompt,
#         "parameters": {
#             "num_inference_steps": 30,
#             "guidance_scale": 7.5,
#             "width": 1024,
#             "height": 768
#         }
#     }
    
#     try:
#         resp = requests.post(url, headers=HUGGINGFACE_HEADERS, json=payload)
        
#         if resp.status_code == 200:
#             # Ensure directory exists before writing
#             os.makedirs(os.path.dirname(filename), exist_ok=True)
#             with open(filename, "wb") as f:
#                 f.write(resp.content)
#             print(f"✅ Hugging Face image saved as {filename}")
#             return filename
#         else:
#             print(f"❌ Hugging Face failed: {resp.status_code}")
#             return None
            
#     except Exception as e:
#         print(f"❌ Hugging Face error: {e}")
#         return None

# def generate_image_replicate(prompt, filename="story.png"):
#     """Generate image using Replicate as fallback"""
#     print("\n🔄 Image Generation via Replicate")
    
#     url = f"https://api.replicate.com/v1/models/{IMAGE_MODEL_VERSION}/predictions"
#     payload = {
#         "input": {
#             "prompt": prompt,
#             "width": 1024,
#             "height": 768,
#             "num_inference_steps": 28,
#             "guidance_scale": 3.5
#         }
#     }
    
#     try:
#         resp = requests.post(url, headers=REPLICATE_HEADERS, json=payload)
#         if resp.status_code in [200, 201]:
#             prediction = resp.json()
#             print(f"Started prediction: {prediction['id']}")
            
#             # Poll until prediction is complete
#             while prediction["status"] not in ["succeeded", "failed", "canceled"]:
#                 print(f"Status: {prediction['status']}...")
#                 time.sleep(3)
#                 check_url = f"https://api.replicate.com/v1/predictions/{prediction['id']}"
#                 prediction = requests.get(check_url, headers=REPLICATE_HEADERS).json()

#             if prediction["status"] == "succeeded":
#                 image_url = prediction["output"][0] if isinstance(prediction["output"], list) else prediction["output"]
#                 image_data = requests.get(image_url).content
#                 with open(filename, "wb") as f:
#                     f.write(image_data)
#                 print(f"✅ Replicate image saved as {filename}")
#                 return filename
#             else:
#                 print("❌ Replicate generation failed")
#                 return None
#         else:
#             print("❌ Failed to start Replicate generation")
#             return None
#     except Exception as e:
#         print(f"❌ Replicate error: {e}")
#         return None

def generate_image(story_text, character_desc="", setting_desc="", filename="story.png"):
    """Generate image using Freepik API"""
     
    base_prompt = f"Children's storybook illustration: {story_text}"
    if character_desc:
        base_prompt += f" Character: {character_desc}"
    if setting_desc:
        base_prompt += f" Setting: {setting_desc}"
    
    image_prompt = f"{base_prompt}. Whimsical, colorful, cartoon style, fairy tale atmosphere, beautiful lighting, suitable for children"
    
    print(f"\n Starting image generation...")
    print("Using Freepik API for image generation...")
    
    
    result = generate_image_freepik(image_prompt, filename)
    if result:
        return result
    
    print(" Image generation failed")
    return create_placeholder_image(filename, 1, story_text)

def create_placeholder_image(filepath, page_number, page_text):
    """Create a simple placeholder image when AI generation fails"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
         
        img = Image.new('RGB', (1024, 768), color=(240, 248, 255))  # Light blue
        draw = ImageDraw.Draw(img)
        
        
        try:
            font_large = ImageFont.truetype("arial.ttf", 48)
            font_small = ImageFont.truetype("arial.ttf", 24)
        except:
            try:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            except:
                font_large = None
                font_small = None
        
        
        if font_large:
            draw.text((50, 50), f"Page {page_number}", fill=(70, 130, 180), font=font_large)
        else:
            draw.text((50, 50), f"Page {page_number}", fill=(70, 130, 180))
        
        
        draw.rectangle([200, 150, 824, 450], outline=(70, 130, 180), width=3)
        if font_small:
            draw.text((350, 280), "Story Illustration", fill=(70, 130, 180), font=font_small)
        else:
            draw.text((350, 280), "Story Illustration", fill=(70, 130, 180))
        
         
        for i in range(5):
            x = 100 + i * 150
            y = 500 + (i % 2) * 50
            draw.ellipse([x, y, x+30, y+30], fill=(255, 182, 193))  # Light pink circles
        
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        img.save(filepath, 'PNG')
        print(f" Placeholder image created: {filepath}")
        return filepath
        
    except Exception as e:
        print(f" Failed to create placeholder image: {e}")
        return None

def generate_page_image(character_description, page_text, page_number, story_id, setting_description="", specific_image_prompt=None):
    """Generate an image for a specific page with enhanced consistency"""
    print(f"\n Generating image for page {page_number}")
    
    filename = f"page_{page_number}_{story_id}.png"
    filepath = os.path.join("uploads", filename)
    
    # Use the AI's specific prompt if available, otherwise fallback to keyword extraction
    if specific_image_prompt and len(specific_image_prompt) > 10:
        enhanced_prompt = f"Children's storybook illustration: {specific_image_prompt}. Style: Disney/Pixar-inspired cartoon, vibrant colors, soft lighting, 4k, detailed, masterpiece"
        print(f" This page has a custom AI prompt: {specific_image_prompt[:50]}...")
    else:
        scene_keywords = extract_scene_keywords(page_text)
        
        # Build enhanced prompt with character consistency
        enhanced_prompt = f"""High-quality children's storybook illustration for the scene:
        
        Characters: {character_description}
        Setting: {setting_description}
        Scene: {scene_keywords if scene_keywords else page_text[:100]}
    
    Style requirements:
    - Whimsical, Disney/Pixar-inspired cartoon style
    - Rich, vibrant colors with proper lighting and shadows
    - Clear, detailed character expressions and poses
    - Well-defined foreground and background elements
    - Child-friendly, engaging composition
    - Professional digital art quality
    - Consistent character design across pages
    - Clear focal point with good visual hierarchy
    - Soft, warm lighting for a cozy atmosphere"""
    
    print(f"📝 Enhanced prompt: {enhanced_prompt}")
    
    # Use enhanced generate_image function
    result = generate_image(enhanced_prompt, "", "", filepath)
    
    if result:
        print(f" Image saved as {filepath}")
        return filepath
    else:
        print(f" Image generation failed for page {page_number}, creating placeholder...")
        # Create a placeholder image as fallback
        return create_placeholder_image(filepath, page_number, page_text)

def extract_scene_keywords(text):
    """Extract key scene elements with enhanced context awareness"""
    import re
    
    # Expanded word sets for better scene understanding
    stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 
                 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had'}
    
    action_words = {
        'run', 'walk', 'jump', 'fly', 'swim', 'dance', 'sing', 'play', 'laugh', 'smile', 'cry', 'sleep',
        'eat', 'drink', 'climb', 'fall', 'sit', 'stand', 'look', 'see', 'find', 'meet', 'help', 'save',
        'fight', 'hide', 'explore', 'discover', 'build', 'create', 'magic', 'adventure', 'chase', 'search',
        'whisper', 'shout', 'giggle', 'dream', 'imagine', 'wonder', 'think', 'wish'
    }
    
    object_words = {
        'tree', 'flower', 'house', 'castle', 'forest', 'mountain', 'river', 'ocean', 'garden', 'bridge',
        'door', 'window', 'book', 'treasure', 'crown', 'sword', 'wand', 'star', 'moon', 'sun', 'cloud',
        'rainbow', 'path', 'road', 'street', 'shop', 'school', 'park', 'playground', 'beach', 'cave',
        'island', 'ship', 'boat', 'train', 'car', 'bicycle', 'balloon', 'kite', 'toy', 'pet'
    }
    
    emotion_words = {
        'happy', 'sad', 'excited', 'scared', 'brave', 'worried', 'curious', 'proud', 'friendly',
        'lonely', 'angry', 'peaceful', 'silly', 'surprised', 'confused', 'determined'
    }
    
    # Extract all words and keep their original order
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Process words with context awareness
    scene_elements = []
    for word in words:
        if word not in stop_words and len(word) > 2:
            # Prioritize words based on their category
            if word in emotion_words:
                scene_elements.insert(0, word)  # Emotions get high priority
            elif word in action_words or word.endswith('ing'):
                scene_elements.append(word)
            elif word in object_words:
                scene_elements.append(word)
            elif word.endswith('ly'):  # Adverbs for action description
                scene_elements.append(word)
    
    # Build scene description with context markers
    scene_desc = []
    emotions = [w for w in scene_elements if w in emotion_words]
    actions = [w for w in scene_elements if w in action_words or w.endswith('ing')]
    objects = [w for w in scene_elements if w in object_words]
    
    # Construct a more natural scene description
    if emotions:
        scene_desc.append(f"feeling {emotions[0]}")
    if actions:
        scene_desc.append(actions[0])
    if objects:
        scene_desc.extend(objects[:2])
    
    # Add remaining important words
    remaining_words = [w for w in scene_elements if w not in (emotions + actions + objects)]
    scene_desc.extend(remaining_words[:3])
    
    final_desc = ' '.join(scene_desc)
    
    # Add scene type hints
    if any(word in final_desc for word in ['run', 'jump', 'chase', 'dance']):
        final_desc += ", dynamic action scene"
    elif any(word in emotion_words for word in words):
        final_desc += ", emotional moment"
    elif any(word in ['forest', 'garden', 'beach', 'mountain'] for word in words):
        final_desc += ", nature scene"
    elif any(word in ['castle', 'house', 'shop', 'school'] for word in words):
        final_desc += ", architectural setting"
    
    return final_desc if final_desc else None

 

def try_fallback_tts(text, filename):
    """Enhanced fallback TTS with multiple options"""
    print("Attempting fallback TTS solution...")
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(filename)
        print(f" Fallback speech saved as {filename}")
        return filename
    except ImportError:
        print("gTTS not installed. Install with: pip install gtts")
        return None
    except Exception as e:
        print(f" Fallback TTS also failed: {e}")
        return None

def generate_speech_for_page(text, page_number, story_id):
    """Generate speech for a specific page using gTTS"""
    print(f"\n Generating TTS for page {page_number}")
    
    # Ensure uploads directory exists
    os.makedirs('uploads', exist_ok=True)
    
    filename = f"page_{page_number}_{story_id}.mp3"
    filepath = os.path.join("uploads", filename)
    
    try:
        # Generate speech using gTTS
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(filepath)
        print(f" TTS audio saved as {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ Error generating audio: {e}")
        return None

def create_storybook_pdf(story_data, image_paths, story_id):
    """Create a BEAUTIFUL, Premium Children's Book PDF"""
    os.makedirs('uploads', exist_ok=True)
    filename = f"storybook_{story_id}.pdf"
    filepath = os.path.join("uploads", filename)
    
    # Use A4 Landscape for a "storybook" feel (or keep Portrait if preferred, let's Stick to Portrait for now but cleaner)
    doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Custom Canvas for Borders
    def draw_page_border(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.gold)
        canvas.setLineWidth(4)
        canvas.rect(0.3*inch, 0.3*inch, A4[0]-0.6*inch, A4[1]-0.6*inch)
        canvas.restoreState()

    styles = getSampleStyleSheet()
    
    # --- Custom Styles ---
    title_style = ParagraphStyle(
        'MainTitle', parent=styles['Heading1'], fontSize=32, alignment=1, 
        textColor=colors.darkblue, spaceAfter=20, fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'StoryBody', parent=styles['Normal'], fontSize=18, alignment=1, 
        leading=24, spaceBefore=20, fontName='Helvetica'
    )
    
    page_num_style = ParagraphStyle(
        'PageNum', parent=styles['Normal'], fontSize=12, alignment=1, textColor=colors.gray
    )

    story = []
    
    # --- 1. COVER PAGE ---
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph(story_data['title'], title_style))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("A Story Generated by AI", styles['Heading3']))
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("🤖 ✨", title_style)) # Simple icon
    story.append(PageBreak())
    
    # --- 2. STORY PAGES ---
    for i, page in enumerate(story_data['pages']):
        page_num = page['page']
        
        # Image Center
        if i < len(image_paths) and image_paths[i] and os.path.exists(image_paths[i]):
            try:
                # Maximize image size while keeping aspect ratio
                img = RLImage(image_paths[i], width=6*inch, height=4.5*inch)
                story.append(img)
            except:
                pass
        
        story.append(Spacer(1, 20))
        
        # Text Center
        story.append(Paragraph(page['text'], body_style))
        story.append(Spacer(1, 30))
        
        # Page Number
        story.append(Paragraph(f"- {page_num} -", page_num_style))
        story.append(PageBreak())
    
    # --- 3. BACK COVER ---
    if 'moral' in story_data:
        story.append(Spacer(1, 3*inch))
        story.append(Paragraph("The End", title_style))
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"<b>Moral of the Story:</b><br/>{story_data['moral']}", body_style))
    
    # Build with Border
    doc.build(story, onFirstPage=draw_page_border, onLaterPages=draw_page_border)
    print(f"✅ Premium PDF created: {filepath}")
    return filepath

 

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    print(f"Serving frontend for path: {path}")
    static_file_path = os.path.join(app.static_folder, path)
    if path != "" and os.path.exists(static_file_path):
        return send_from_directory(app.static_folder, path)
    else:
        index_path = os.path.join(app.static_folder, 'index.html')
        print(f"Looking for index.html at: {index_path}")
        if os.path.exists(index_path):
            return send_from_directory(app.static_folder, 'index.html')
        else:
            print(f"❌ Error: index.html not found at {index_path}")
            return f"Frontend not found at {index_path}. Build might have failed or path is wrong.", 404

@app.route('/api/welcome')
def welcome():
    return jsonify({
        "message": "Welcome to the StoryBook AI API",
        "status": "online",
        "version": "2.0.0"
    })

@app.route('/api/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'uploads_dir_exists': os.path.exists('uploads'),
        'api_keys_configured': {
            'openrouter': bool(OPENROUTER_API_KEY),
            'freepik': bool(FREEPIK_API_KEY)
        }
    })

@app.route('/api/test-story')
def test_story():
    """Simple test endpoint to verify basic functionality"""
    try:
        # Ensure uploads directory exists
        os.makedirs('uploads', exist_ok=True)
        
        # Test basic story generation without external APIs
        test_story_data = {
            'title': 'Test Story',
            'character_description': 'A friendly test character',
            'setting': 'A test environment',
            'pages': [
                {'page': 1, 'text': 'This is a test story to verify the app is working.'},
                {'page': 2, 'text': 'If you can see this, the basic functionality is operational.'}
            ],
            'moral': 'Testing is important!'
        }
        
        story_id = 'test123'
        
        # Create a simple test PDF
        pdf_path = create_storybook_pdf(test_story_data, [], story_id)
        
        return jsonify({
            'success': True,
            'message': 'Test story created successfully',
            'story_id': story_id,
            'pdf_created': os.path.exists(pdf_path) if pdf_path else False
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate', methods=['POST'])
def generate_storybook():
    try:
        # Ensure uploads directory exists at the start
        os.makedirs('uploads', exist_ok=True)
        
        # Accept both form data and JSON
        if request.is_json:
            data = request.get_json()
            prompt = data.get('prompt')
            story_length = data.get('length', 'normal')
        else:
            prompt = request.form.get('prompt')
            story_length = request.form.get('length', 'normal')
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        story_id = str(uuid.uuid4())[:8]
        
        print(f" Generating {story_length} story: {prompt}")
        
        # Generate enhanced story text
        story_data = generate_story_pages(prompt, story_length)
        
        # Generate images for each page with enhanced consistency
        image_paths = []
        successful_images = 0
        total_pages = len(story_data['pages'])
        
        for page in story_data['pages']:
            try:
                image_path = generate_page_image(
                    story_data['character_description'],
                    page['text'],
                    page['page'],
                    story_id,
                    story_data.get('setting', ''),
                    page.get('image_prompt')
                )
                if image_path:
                    image_paths.append(image_path)
                    successful_images += 1
                else:
                    # Create placeholder image if generation fails
                    placeholder_path = create_placeholder_image(
                        os.path.join('uploads', f'page_{page["page"]}_{story_id}.png'),
                        page['page'],
                        page['text']
                    )
                    image_paths.append(placeholder_path)
            except Exception as e:
                print(f"❌ Error generating image for page {page['page']}: {e}")
                # Create placeholder image on error
                placeholder_path = create_placeholder_image(
                    os.path.join('uploads', f'page_{page["page"]}_{story_id}.png'),
                    page['page'],
                    page['text']
                )
                image_paths.append(placeholder_path)
        
        print(f"✅ Generated {successful_images}/{total_pages} images successfully")
        
        # Generate speech for each page
        audio_paths = []
        successful_audio = 0
        for page in story_data['pages']:
            try:
                audio_path = generate_speech_for_page(
                    page['text'],
                    page['page'],
                    story_id
                )
                audio_paths.append(audio_path)
                if audio_path:
                    successful_audio += 1
            except Exception as e:
                print(f" Error generating audio for page {page['page']}: {e}")
                audio_paths.append(None)
        
        print(f" Generated {successful_audio}/{len(story_data['pages'])} audio files successfully")
        
        # Create enhanced PDF (this should work even without images)
        try:
            pdf_path = create_storybook_pdf(story_data, image_paths, story_id)
        except Exception as e:
            print(f" Error creating PDF: {e}")
            pdf_path = None
        
        # Store story data for viewing
        story_file = os.path.join("uploads", f"story_data_{story_id}.json")
        try:
            with open(story_file, 'w') as f:
                json.dump({
                    'story_data': story_data,
                    'image_paths': image_paths,
                    'audio_paths': audio_paths,
                    'pdf_path': pdf_path,
                    'story_length': story_length
                }, f)
        except Exception as e:
            print(f" Error saving story data: {e}")
        
        # Return success even if some components failed
        response_data = {
            'success': True,
            'story_id': story_id,
            'story_data': story_data,
            'stats': {
                'images_generated': successful_images,
                'audio_generated': successful_audio,
                'total_pages': len(story_data['pages'])
            }
        }
        
        if pdf_path:
            response_data['pdf_url'] = f'/api/download-pdf/{story_id}'
        
        if successful_audio > 0:
            response_data['audiobook_url'] = f'/api/download-audiobook/{story_id}'
        
        response_data['reader_url'] = f'/reader/{story_id}'
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f" Error generating story: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Story generation failed: {str(e)}'}), 500

# Keep all existing download routes...
@app.route('/api/download/<filename>')
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

@app.route('/api/download-pdf/<story_id>')
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

@app.route('/api/download-audiobook/<story_id>')
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

def check_environment():
    """Check all required environment variables and configurations"""
    required_vars = {
        'OPENROUTER_API_KEY': 'Story generation',
        'FREEPIK_API_KEY': 'Image generation',
        'SECRET_KEY': 'Application security'
    }
    
    missing_vars = []
    for var, purpose in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} ({purpose})")
    
    if missing_vars:
        print("⚠️ WARNING: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these variables in your .env file")
        return False
    return True

if __name__ == '__main__':
    # Check environment variables
    env_check = check_environment()
    
    # Ensure uploads directory exists
    try:
        os.makedirs('uploads', exist_ok=True)
        print("\n🚀 Enhanced Storybook App Starting...")
        print("Features:")
        print("✅ Freepik API Integration")
        print("✅ Multiple story lengths")
        print("✅ Enhanced PDF generation")
        print("✅ Improved reader interface")
        print("✅ Better error handling")
        print("✅ gTTS audio generation")
        
        if not env_check:
            print("\n⚠️ Starting with limited functionality due to missing environment variables")
        
        port = int(os.environ.get('PORT', 5000))
        host = '0.0.0.0'
        debug = os.environ.get('FLASK_ENV') != 'production'
        
        print(f"\n🌐 Starting server on {host}:{port}")
        print(f"🔧 Debug mode: {'on' if debug else 'off'}")
        
        app.run(debug=debug, host=host, port=port)
    except Exception as e:
        print(f"\n❌ Failed to start application: {e}")
        raise