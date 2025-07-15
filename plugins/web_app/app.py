#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Application Factory
Creates and configures Flask application
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask

# Import configuration
from plugins.config import *

# Import WebSocket handler
from plugins.web_app import websocket_handler

# Configure logging to output to workspace/logs directory
log_dir = project_root / "workspace" / "logs"
log_dir.mkdir(exist_ok=True, parents=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'web_app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    """
    Create and configure Flask application
    
    功能：
    - 创建Flask应用实例
    - 配置应用参数（文件上传限制、密钥等）
    - 确保必要目录存在
    - 注册蓝图和错误处理器
    
    返回：
    - Flask应用实例
    """
    app = Flask(__name__, template_folder='templates')
    app.secret_key = os.urandom(24)
    
    # 配置文件上传限制
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    app.config['UPLOAD_FOLDER'] = str(UPLOAD_DIR)
    
    # 记录配置信息
    logger.info(f"Flask app configured with MAX_CONTENT_LENGTH: {MAX_CONTENT_LENGTH} bytes ({MAX_CONTENT_LENGTH / (1024*1024*1024):.2f} GB)")
    
    # 确保目录存在
    for directory in [UPLOAD_DIR, TMP_DIR, LOGS_DIR, STATUS_DIR]:
        directory.mkdir(exist_ok=True, parents=True)
    
    # 注册错误处理器
    from . import error_handlers
    error_handlers.register_error_handlers(app)
    
    # 注册路由蓝图
    from . import routes
    from . import api_routes
    
    app.register_blueprint(routes.main_bp)
    app.register_blueprint(api_routes.api_bp, url_prefix='/api')
    
    # 初始化SocketIO
    socketio = websocket_handler.init_socketio(app)
    
    return app, socketio 