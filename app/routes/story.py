"""Story generation routes."""
import os
import uuid
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.ai_service import get_ai_service
from app.services.image_service import get_image_service
from app.services.tts_service import get_tts_service
from app.services.pdf_service import get_pdf_service
from app.utils.logging_config import get_logger
from app.utils.error_handlers import ValidationError

logger = get_logger('story_routes')

story_bp = Blueprint('story', __name__, url_prefix='/api')


@story_bp.route('/generate', methods=['POST'])
def generate_storybook():
    """Generate a complete storybook with text, images, and audio.
    
    Request JSON:
        prompt: Story topic/prompt
        length: Story length (short, normal, long, extended)
    
    Returns:
        JSON with story data and file paths
    """
    try:
        # Get request data
        if request.is_json:
            data = request.get_json()
            prompt = data.get('prompt')
            story_length = data.get('length', 'normal')
        else:
            prompt = request.form.get('prompt')
            story_length = request.form.get('length', 'normal')
        
        if not prompt:
            raise ValidationError("Prompt is required", field='prompt')
        
        story_id = str(uuid.uuid4())[:8]
        
        logger.info(f"Generating {story_length} story", extra={
            'story_id': story_id,
            'prompt_length': len(prompt),
            'length': story_length
        })
        
        # Get services
        ai_service = get_ai_service()
        image_service = get_image_service()
        tts_service = get_tts_service()
        pdf_service = get_pdf_service()
        
        # 1. Generate story text
        logger.info(f"Step 1: Generating story text for {story_id}")
        story_data = ai_service.generate_story(prompt, story_length)
        
        # 2. Generate images for each page
        logger.info(f"Step 2: Generating images for {story_id}")
        image_paths = []
        successful_images = 0
        total_pages = len(story_data['pages'])
        
        for page in story_data['pages']:
            try:
                image_path = image_service.generate_page_image(
                    story_data.get('character_description', ''),
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
                    # Placeholder fallback
                    placeholder_path = image_service.create_placeholder_image(
                        os.path.join('uploads', f'page_{page["page"]}_{story_id}.png'),
                        page['page'],
                        page['text']
                    )
                    image_paths.append(placeholder_path)
            except Exception as e:
                logger.error(f"Error generating image for page {page['page']}: {e}")
                placeholder_path = image_service.create_placeholder_image(
                    os.path.join('uploads', f'page_{page["page"]}_{story_id}.png'),
                    page['page'],
                    page['text']
                )
                image_paths.append(placeholder_path)
        
        logger.info(f"Generated {successful_images}/{total_pages} images successfully")
        
        # 3. Generate audio for each page
        logger.info(f"Step 3: Generating audio for {story_id}")
        audio_paths = []
        successful_audio = 0
        
        for page in story_data['pages']:
            try:
                audio_path = tts_service.generate_speech(
                    page['text'],
                    page['page'],
                    story_id
                )
                audio_paths.append(audio_path)
                if audio_path:
                    successful_audio += 1
            except Exception as e:
                logger.error(f"Error generating audio for page {page['page']}: {e}")
                audio_paths.append(None)
        
        logger.info(f"Generated {successful_audio}/{total_pages} audio files successfully")
        
        # 4. Create PDF
        logger.info(f"Step 4: Creating PDF for {story_id}")
        try:
            pdf_path = pdf_service.create_storybook_pdf(story_data, image_paths, story_id)
            pdf_created = os.path.exists(pdf_path) if pdf_path else False
        except Exception as e:
            logger.error(f"Error creating PDF: {e}")
            pdf_path = None
            pdf_created = False
        
        # Extract filenames for response
        image_filenames = [os.path.basename(p) if p else None for p in image_paths]
        audio_filenames = [os.path.basename(p) if p else None for p in audio_paths]
        pdf_filename = os.path.basename(pdf_path) if pdf_path else None
        
        logger.info(f"Story generation completed for {story_id}")
        
        # Auto-save to library if user is authenticated
        saved_id = None
        try:
            from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
            
            # Check if user is authenticated (optional)
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            
            if user_id:
                from app.models.story import get_story_model
                from app.routes.library import stories_collection
                
                if stories_collection:
                    story_model = get_story_model(stories_collection)
                    
                    # Prepare data for saving
                    save_data = {
                        'story_id': story_id,
                        'title': story_data.get('title', 'Untitled Story'),
                        'prompt': prompt,
                        'story_length': story_length,
                        'story_mode': 'standard',
                        'story': story_data,
                        'image_files': image_filenames,
                        'audio_files': audio_filenames,
                        'pdf_file': pdf_filename
                    }
                    
                    saved_id = story_model.create(user_id, save_data)
                    logger.info(f"Story auto-saved to library: {saved_id}")
        except Exception as save_error:
            # Don't fail the entire request if save fails
            logger.warning(f"Auto-save failed: {save_error}")
        
        return jsonify({
            'success': True,
            'story_id': story_id,
            'saved_id': saved_id,
            'story': story_data,
            'image_files': image_filenames,
            'audio_files': audio_filenames,
            'pdf_file': pdf_filename,
            'pdf_created': pdf_created,
            'stats': {
                'successful_images': successful_images,
                'total_images': total_pages,
                'successful_audio': successful_audio,
                'total_audio': total_pages
            }
        }), 200
    
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Story generation failed: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@story_bp.route('/story/<story_id>', methods=['GET'])
def get_story(story_id):
    """Get story data by ID.
    
    Note: This is a simplified version. In production, you'd want to store
    story data in database.
    
    Returns:
        JSON with story data
    """
    # For now, just return a success message
    # In production, retrieve from database
    return jsonify({
        'success': True,
        'story_id': story_id,
        'message': 'Story retrieval not implemented yet'
    })


@story_bp.route('/download-pdf/<story_id>', methods=['GET'])
def download_pdf(story_id):
    """Download PDF storybook.
    
    Args:
        story_id: Story identifier
    
    Returns:
        PDF file download
    """
    try:
        pdf_filename = f"storybook_{story_id}.pdf"
        pdf_path = os.path.join('uploads', pdf_filename)
        
        if not os.path.exists(pdf_path):
            return jsonify({'error': 'PDF not found'}), 404
        
        logger.info(f"Download PDF requested: {story_id}")
        
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"storybook_{story_id}.pdf",
            mimetype='application/pdf'
        )
    
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        return jsonify({'error': str(e)}), 500


@story_bp.route('/download-audiobook/<story_id>', methods=['GET'])
def download_audiobook(story_id):
    """Download audiobook as ZIP.
    
    Args:
        story_id: Story identifier
    
    Returns:
        ZIP file with all audio files
    """
    try:
        import zipfile
        import io
        
        # Find all audio files for this story
        audio_files = []
        for filename in os.listdir('uploads'):
            if filename.endswith('.mp3') and story_id in filename:
                audio_files.append(filename)
        
        if not audio_files:
            return jsonify({'error': 'Audio files not found'}), 404
        
        # Create ZIP in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for audio_file in audio_files:
                audio_path = os.path.join('uploads', audio_file)
                zipf.write(audio_path, arcname=audio_file)
        
        memory_file.seek(0)
        
        logger.info(f"Download audiobook requested: {story_id}")
        
        return send_file(
            memory_file,
            as_attachment=True,
            download_name=f"audiobook_{story_id}.zip",
            mimetype='application/zip'
        )
    
    except Exception as e:
        logger.error(f"Error downloading audiobook: {e}")
        return jsonify({'error': str(e)}), 500


@story_bp.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download any file from uploads folder.
    
    Args:
        filename: Name of the file to download
    
    Returns:
        File from uploads folder
    """
    try:
        from app.config import Config
        from flask import send_from_directory
        
        # Security check: ensure filename doesn't contain path traversal
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': 'Invalid filename'}), 400
            
        return send_from_directory(
            os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), Config.UPLOAD_FOLDER),
            filename
        )
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {e}")
        return jsonify({'error': str(e)}), 500
