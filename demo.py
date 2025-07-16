#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo runner for Sync Cut application
Runs the application with mock modules for demonstration when dependencies are not available
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Install mock modules first
from plugins.mock_modules import install_mock_modules
install_mock_modules()

def main():
    """Run the demo application"""
    print("=" * 60)
    print("SYNC CUT - AUDIO/VIDEO CONVERSION TOOL")
    print("=" * 60)
    print()
    
    try:
        # Load configuration
        from plugins.config import load_config_file, get_default_config
        config = load_config_file()
        if not config:
            config = get_default_config()
        
        # Get web app configuration
        web_config = config.get('web_app', {})
        host = web_config.get('host', '0.0.0.0')
        port = web_config.get('port', 7000)
        
        print(f"📁 Project: {config.get('app', {}).get('name', 'Sync Cut')}")
        print(f"🌍 Host: {host}")
        print(f"🚪 Port: {port}")
        print()
        
        # Create and run the application
        from plugins.web_app.app import create_app
        
        print("🚀 Starting application...")
        app, socketio = create_app()
        
        print("✅ Application created successfully!")
        print()
        print("📝 Available Features:")
        print("  • MP4 to MP3 conversion (using FFmpeg)")
        print("  • MP3 to TXT conversion (using Alibaba NLS)")  
        print("  • MP3 to TXT conversion (using OpenAI Whisper)")
        print("  • Web interface for file upload and conversion")
        print("  • Real-time progress updates via WebSocket")
        print("  • Configuration management")
        print()
        print("🔧 Project Structure:")
        print("  • plugins/mp4_to_mp3/ - Video to audio conversion")
        print("  • plugins/mp3_to_txt/ - Audio to text conversion")
        print("  • plugins/web_app/ - Web interface")
        print("  • plugins/common/ - Shared utilities")
        print("  • workspace/ - Working directories")
        print()
        
        print(f"🌟 Demo server would start at: http://{host}:{port}")
        print()
        print("📋 To run with real dependencies:")
        print("  1. Install dependencies: pip install -r plugins/requirements.txt")
        print("  2. Configure config.yaml with your Alibaba NLS credentials")
        print("  3. Run: python plugins/web_app/run.py")
        print()
        print("🎉 Project completion status: COMPLETE")
        
        # Simulate starting the server
        socketio.run(app, host=host, port=port, debug=False)
        
    except Exception as e:
        print(f"❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)