"""Sentry configuration for error monitoring."""
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from app.config import Config
from app.utils.logging_config import get_logger

logger = get_logger('sentry')


def initialize_sentry(app):
    """Initialize Sentry SDK for error tracking.
    
    Args:
        app: Flask application instance
    """
    if not Config.SENTRY_DSN:
        logger.info("Sentry DSN not configured, skipping initialization")
        return
    
    try:
        sentry_sdk.init(
            dsn=Config.SENTRY_DSN,
            integrations=[
                FlaskIntegration(),
            ],
            traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
            profiles_sample_rate=0.1,  # 10% of transactions for profiling
            environment=app.config.get('ENV', 'production'),
            send_default_pii=False,  # Don't send personally identifiable information
        )
        
        logger.info("Sentry initialized successfully")
    
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
