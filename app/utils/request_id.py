"""Request ID middleware for tracking."""
import uuid
from flask import request, g


def generate_request_id():
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def add_request_id_middleware(app):
    """Add request ID middleware to Flask app.
    
    Args:
        app: Flask application instance
    """
    
    @app.before_request
    def before_request():
        """Generate request ID before each request."""
        g.request_id = request.headers.get('X-Request-ID', generate_request_id())
    
    @app.after_request
    def after_request(response):
        """Add request ID to response headers."""
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        return response
