#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web App Runner
专门用于启动Flask应用的脚本
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    """启动Web应用"""
    try:
        # 导入应用创建函数
        from plugins.web_app.app import create_app
        from plugins.web_app import websocket_handler
        from plugins.config import load_config_file, get_default_config
        
        # 加载配置
        config = load_config_file()
        if not config:
            config = get_default_config()
        
        # 获取web应用配置
        web_config = config.get('web_app', {})
        host = web_config.get('host', '0.0.0.0')
        port = web_config.get('port', 7000)
        debug = web_config.get('debug', False)
        
        # 创建应用实例
        app, socketio = create_app()
        
        # 启动应用
        print("Starting Sync Cut Web Application...")
        print(f"Server will run on http://{host}:{port}")
        
        # 使用SocketIO运行应用
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=False,
            allow_unsafe_werkzeug=True
        )
        
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 