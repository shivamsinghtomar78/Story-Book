"""Authentication routes."""
import time
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
import bcrypt
from app.config import Config
from app.utils.logging_config import get_logger
from app.utils.error_handlers import AuthenticationError, ValidationError

logger = get_logger('auth_routes')

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Database connection
mongo_client = None
users_collection = None

def initialize_db():
    """Initialize database connection."""
    global mongo_client, users_collection
    
    if not Config.MONGO_URI:
        logger.warning("MONGO_URI not configured")
        return
    
    try:
        mongo_client = MongoClient(Config.MONGO_URI)
        db = mongo_client['storybook_db']
        users_collection = db['users']
        logger.info("Connected to MongoDB Atlas")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Register a new user.
    
    Request JSON:
        email: User email
        password: User password
        name: User name (optional)
    
    Returns:
        JSON with token and user info
    """
    if users_collection is None:
        raise ValidationError("Database not configured")
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    if not email or not password:
        raise ValidationError("Email and password required")
    
    # Check if user exists
    if users_collection.find_one({"email": email}):
        raise ValidationError("User already exists", field='email')
    
    # Hash password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    user_id = users_collection.insert_one({
        "email": email,
        "password": hashed_password,
        "name": name,
        "created_at": time.time()
    }).inserted_id
    
    # Generate token
    access_token = create_access_token(identity=str(user_id))
    
    logger.info(f"New user registered: {email}")
    
    return jsonify({
        "message": "User registered successfully",
        "token": access_token,
        "user": {"email": email, "name": name}
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user.
    
    Request JSON:
        email: User email
        password: User password
    
    Returns:
        JSON with token and user info
    """
    if users_collection is None:
        raise ValidationError("Database not configured")
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        raise ValidationError("Email and password required")
    
    # Find user
    user = users_collection.find_one({"email": email})
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        access_token = create_access_token(identity=str(user['_id']))
        
        logger.info(f"User logged in: {email}")
        
        return jsonify({
            "message": "Login successful",
            "token": access_token,
            "user": {"email": email, "name": user.get('name')}
        }), 200
    
    raise AuthenticationError("Invalid credentials")


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Get current user profile.
    
    Returns:
        JSON with user info
    """
    user_id = get_jwt_identity()
    
    return jsonify({
        "message": "Valid token",
        "user_id": user_id
    })
