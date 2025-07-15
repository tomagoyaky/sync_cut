#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web App Package
Modular Flask web application for file conversion
"""

from .app import create_app

# 导出主要函数
__all__ = ['create_app', 'main']

def main():
    """
    主应用入口函数
    
    功能：
    - 初始化应用和目录结构
    - 启动Flask Web服务器
    - 配置多线程支持
    
    配置：
    - 从config.py读取HOST、PORT、DEBUG配置
    - 启用线程支持以处理并发请求
    """
    import sys
    import logging
    from pathlib import Path
    
    # Add the project root to Python path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from plugins.config import (
        APP_NAME, APP_VERSION, HOST, PORT, DEBUG,
        WORKSPACE_DIR, MODELS_DIR, LOGS_DIR, UPLOAD_DIR, TMP_DIR, STATUS_DIR
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}...")
    
    # 确保所有目录存在
    for directory in [WORKSPACE_DIR, MODELS_DIR, LOGS_DIR, UPLOAD_DIR, TMP_DIR, STATUS_DIR]:
        directory.mkdir(exist_ok=True, parents=True)
    
    # 创建Flask应用和SocketIO
    app, socketio = create_app()
    
    # 启动Flask应用
    logger.info(f"Starting web server on {HOST}:{PORT}")
    socketio.run(
        app,
        host=HOST,
        port=PORT,
        debug=DEBUG,
        allow_unsafe_werkzeug=True
    ) 