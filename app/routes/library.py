"""Story library routes for managing saved stories."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient
from app.config import Config
from app.models.story import get_story_model
from app.utils.logging_config import get_logger
from app.utils.error_handlers import ValidationError

logger = get_logger('library_routes')

library_bp = Blueprint('library', __name__, url_prefix='/api')

# MongoDB connection for stories
mongo_client = None
stories_collection = None
story_model = None


def initialize_library_db():
    """Initialize MongoDB connection for library."""
    global mongo_client, stories_collection, story_model
    
    if not Config.MONGO_URI:
        logger.warning("MONGO_URI not configured")
        return
    
    try:
        if mongo_client is None:
            mongo_client = MongoClient(Config.MONGO_URI)
            db = mongo_client['storybook_db']
            stories_collection = db['stories']
            story_model = get_story_model(stories_collection)
            logger.info("Library database initialized")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB for library: {e}")


@library_bp.route('/story/save', methods=['POST'])
@jwt_required()
def save_story():
    """Save a generated story to user's library.
    
    Request JSON:
        story_id: Unique story identifier
        title: Story title
        prompt: Original prompt
        story_length: Story length
        story: Story data (pages, character, etc.)
        image_files: List of image filenames
        audio_files: List of audio filenames
        pdf_file: PDF filename
    
    Returns:
        JSON with saved story ID
    """
    if story_model is None:
        raise ValidationError("Library not available - database not configured")
    
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        raise ValidationError("No story data provided")
    
    try:
        # Create story in database
        saved_id = story_model.create(user_id, data)
        
        logger.info(f"Story saved to library", extra={
            "user_id": user_id,
            "saved_id": saved_id
        })
        
        return jsonify({
            "success": True,
            "message": "Story saved to library",
            "saved_id": saved_id
        }), 201
    
    except Exception as e:
        logger.error(f"Error saving story: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@library_bp.route('/stories', methods=['GET'])
@jwt_required()
def get_stories():
    """Get user's story library with pagination and filtering.
    
    Query Parameters:
        page: Page number (default: 1)
        limit: Items per page (default: 20, max: 100)
        sort_by: Field to sort by (default: created_at)
        sort_order: asc or desc (default: desc)
        favorites: true to show only favorites
    
    Returns:
        JSON with stories array and pagination info
    """
    if story_model is None:
        raise ValidationError("Library not available - database not configured")
    
    user_id = get_jwt_identity()
    
    # Parse query parameters
    page = max(1, int(request.args.get('page', 1)))
    limit = min(100, max(1, int(request.args.get('limit', 20))))
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order_str = request.args.get('sort_order', 'desc')
    favorites_only = request.args.get('favorites', '').lower() == 'true'
    
    # Convert sort order
    sort_order = -1 if sort_order_str == 'desc' else 1
    
    # Calculate skip
    skip = (page - 1) * limit
    
    try:
        stories, total = story_model.find_by_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            favorites_only=favorites_only
        )
        
        total_pages = (total + limit - 1) // limit  # Ceiling division
        
        return jsonify({
            "success": True,
            "stories": stories,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching stories: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@library_bp.route('/story/<story_id>', methods=['GET'])
@jwt_required()
def get_story(story_id):
    """Get a single story by ID.
    
    Args:
        story_id: MongoDB document ID
    
    Returns:
        JSON with story details
    """
    if story_model is None:
        raise ValidationError("Library not available - database not configured")
    
    user_id = get_jwt_identity()
    
    try:
        story = story_model.find_by_id(story_id, user_id)
        
        if not story:
            return jsonify({
                "success": False,
                "error": "Story not found"
            }), 404
        
        return jsonify({
            "success": True,
            "story": story
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching story: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@library_bp.route('/story/<story_id>', methods=['DELETE'])
@jwt_required()
def delete_story(story_id):
    """Delete a story from library.
    
    Args:
        story_id: MongoDB document ID
    
    Returns:
        JSON with success status
    """
    if story_model is None:
        raise ValidationError("Library not available - database not configured")
    
    user_id = get_jwt_identity()
    
    try:
        deleted = story_model.delete(story_id, user_id)
        
        if not deleted:
            return jsonify({
                "success": False,
                "error": "Story not found or already deleted"
            }), 404
        
        return jsonify({
            "success": True,
            "message": "Story deleted successfully"
        }), 200
    
    except Exception as e:
        logger.error(f"Error deleting story: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@library_bp.route('/story/<story_id>/favorite', methods=['PATCH'])
@jwt_required()
def toggle_favorite(story_id):
    """Toggle favorite status of a story.
    
    Args:
        story_id: MongoDB document ID
    
    Returns:
        JSON with new favorite status
    """
    if story_model is None:
        raise ValidationError("Library not available - database not configured")
    
    user_id = get_jwt_identity()
    
    try:
        new_status = story_model.toggle_favorite(story_id, user_id)
        
        if new_status is None:
            return jsonify({
                "success": False,
                "error": "Story not found"
            }), 404
        
        return jsonify({
            "success": True,
            "is_favorite": new_status,
            "message": f"Story {'added to' if new_status else 'removed from'} favorites"
        }), 200
    
    except Exception as e:
        logger.error(f"Error toggling favorite: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@library_bp.route('/stories/search', methods=['GET'])
@jwt_required()
def search_stories():
    """Search stories by text.
    
    Query Parameters:
        q: Search query (required)
        page: Page number (default: 1)
        limit: Items per page (default: 20)
    
    Returns:
        JSON with search results
    """
    if story_model is None:
        raise ValidationError("Library not available - database not configured")
    
    user_id = get_jwt_identity()
    query = request.args.get('q', '').strip()
    
    if not query:
        raise ValidationError("Search query required", field='q')
    
    page = max(1, int(request.args.get('page', 1)))
    limit = min(100, max(1, int(request.args.get('limit', 20))))
    skip = (page - 1) * limit
    
    try:
        stories, total = story_model.search(
            user_id=user_id,
            query=query,
            skip=skip,
            limit=limit
        )
        
        total_pages = (total + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "query": query,
            "stories": stories,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error searching stories: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@library_bp.route('/stories/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get user's story statistics.
    
    Returns:
        JSON with statistics
    """
    if story_model is None:
        raise ValidationError("Library not available - database not configured")
    
    user_id = get_jwt_identity()
    
    try:
        stats = story_model.get_user_stats(user_id)
        
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
