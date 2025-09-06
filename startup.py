#!/usr/bin/env python3
"""
Startup script for the Storybook app
Ensures all necessary directories and configurations are in place
"""

import os
import sys

def setup_directories():
    """Create necessary directories"""
    directories = ['uploads', 'static', 'templates']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📁 Directory exists: {directory}")

def check_environment():
    """Check environment variables"""
    required_vars = [
        'OPENROUTER_API_KEY',
        'FREEPIK_API_KEY', 
        'HUGGINGFACEHUB_API_TOKEN',
        'REPLICATE_API_TOKEN'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   The app will still run but some features may not work")
    else:
        print("✅ All environment variables are configured")

def main():
    print("🚀 Starting Storybook App Setup...")
    
    setup_directories()
    check_environment()
    
    print("✅ Setup complete!")
    
    # Import and run the main app
    from app import app
    
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print(f"🌐 Starting server on {host}:{port}")
    app.run(debug=debug, host=host, port=port)

if __name__ == '__main__':
    main()