#!/usr/bin/env python3
"""
Start the Sync Cut web application in test mode
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def start_app():
    """Start the web application"""
    try:
        print("Starting Sync Cut Web Application...")
        
        # Import required modules
        from plugins.web_app.app import create_app
        from plugins.config import load_config_file, get_default_config
        
        # Load configuration
        config = load_config_file()
        if not config:
            config = get_default_config()
        
        # Get web app configuration
        web_config = config.get('web_app', {})
        host = web_config.get('host', '0.0.0.0')
        port = web_config.get('port', 7000)
        debug = web_config.get('debug', False)
        
        print(f"Configuration loaded - Host: {host}, Port: {port}")
        
        # Create application instance
        app, socketio = create_app()
        
        print("Web application created successfully")
        print(f"Starting server on http://{host}:{port}")
        print("Note: Whisper functionality is not available without additional dependencies")
        print("Press Ctrl+C to stop the server")
        
        # Start the server
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=False,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(start_app())