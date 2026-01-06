"""Custom exceptions and error handlers."""
from flask import jsonify
import uuid


class StoryBookException(Exception):
    """Base exception for StoryBook application."""
    
    def __init__(self, message, code='UNKNOWN_ERROR', status_code=500, details=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class APIError(StoryBookException):
    """Exception for external API errors."""
    
    def __init__(self, message, service=None, details=None):
        super().__init__(
            message=message,
            code='API_ERROR',
            status_code=502,
            details=details or {}
        )
        if service:
            self.details['service'] = service


class RateLimitExceeded(StoryBookException):
    """Exception for rate limit violations."""
    
    def __init__(self, message='Rate limit exceeded', limit=None):
        super().__init__(
            message=message,
            code='RATE_LIMIT_EXCEEDED',
            status_code=429,
            details={'limit': limit} if limit else None
        )


class ValidationError(StoryBookException):
    """Exception for input validation errors."""
    
    def __init__(self, message, field=None):
        super().__init__(
            message=message,
            code='VALIDATION_ERROR',
            status_code=400,
            details={'field': field} if field else None
        )


class AuthenticationError(StoryBookException):
    """Exception for authentication failures."""
    
    def __init__(self, message='Authentication failed'):
        super().__init__(
            message=message,
            code='AUTHENTICATION_ERROR',
            status_code=401
        )


def format_error_response(error, request_id=None):
    """Format error into standardized JSON response.
    
    Args:
        error: Exception instance
        request_id: Optional request ID for tracking
    
    Returns:
        Tuple of (response_dict, status_code)
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    if isinstance(error, StoryBookException):
        response = {
            'error': {
                'code': error.code,
                'message': error.message,
                'request_id': request_id
            }
        }
        if error.details:
            response['error']['details'] = error.details
        
        return response, error.status_code
    
    # Handle unexpected errors
    response = {
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'An unexpected error occurred',
            'request_id': request_id
        }
    }
    
    return response, 500


def register_error_handlers(app):
    """Register error handlers with Flask app.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(StoryBookException)
    def handle_storybook_exception(error):
        response, status_code = format_error_response(error)
        return jsonify(response), status_code
    
    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Resource not found'
            }
        }), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        response, status_code = format_error_response(error)
        return jsonify(response), status_code
