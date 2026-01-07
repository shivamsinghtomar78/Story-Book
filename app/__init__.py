"""Flask application factory."""
import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta

from app.config import Config
from app.utils.logging_config import setup_logging
from app.utils.error_handlers import register_error_handlers
from app.utils.request_id import add_request_id_middleware
from app.utils.sentry_config import initialize_sentry
from app.routes.auth import auth_bp, initialize_db as init_auth_db
from app.routes.story import story_bp
from app.routes.library import library_bp, initialize_library_db


def create_app(config_name='default'):
    """Create and configure Flask application.
    
    Args:
        config_name: Configuration name (development, production, etc.)
    
    Returns:
        Configured Flask application
    """
    # Determine base directory
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    static_folder = os.path.join(basedir, 'frontend', 'dist')
    
    # Create Flask app
    app = Flask(
        __name__,
        static_folder=static_folder,
        static_url_path='/'
    )
    
    # Load configuration
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)
    
    # Validate environment
    try:
        Config.validate()
    except ValueError as e:
        app.logger.warning(f"Configuration warning: {e}")
    
    # Setup logging
    logger = setup_logging('storybook')
    app.logger.handlers = logger.handlers
    app.logger.setLevel(logger.level)
    
    # Initialize extensions
    CORS(app)
    jwt = JWTManager(app)
    
    # Add middleware
    add_request_id_middleware(app)
    
    # Initialize Sentry
    initialize_sentry(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Initialize database for auth
    init_auth_db()
    
    # Initialize database for library
    initialize_library_db()
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(story_bp)
    app.register_blueprint(library_bp)
    
    # Create upload folder
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    # Health check and utility routes
    @app.route('/api/health')
    def health_check():
        """Health check endpoint."""
        return {
            'status': 'healthy',
            'uploads_dir_exists': os.path.exists(Config.UPLOAD_FOLDER),
            'api_keys_configured': {
                'openrouter': bool(Config.OPENROUTER_API_KEY),
                'freepik': bool(Config.FREEPIK_API_KEY),
                'gemini': bool(Config.GEMINI_API_KEY)
            }
        }
    
    @app.route('/api/welcome')
    def welcome():
        """Welcome endpoint."""
        return {
            'message': 'Welcome to the StoryBook AI API',
            'status': 'online',
            'version': '2.0.0'
        }
    
    @app.route('/api/debug-static')
    def debug_static():
        """Debug endpoint to list static files."""
        files = []
        if os.path.exists(app.static_folder):
            for root, dirs, filenames in os.walk(app.static_folder):
                for f in filenames:
                    files.append(os.path.relpath(os.path.join(root, f), app.static_folder))
        return {
            'static_folder': app.static_folder,
            'exists': os.path.exists(app.static_folder),
            'files': files
        }
    
    # Serve frontend
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        """Serve React frontend."""
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
    
    app.logger.info(f"Application initialized with config: {config_name}")
    
    return app
