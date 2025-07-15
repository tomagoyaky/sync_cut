#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Error Handlers Module
Handles Flask application errors and exceptions
"""

import sys
from pathlib import Path
from flask import jsonify

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from plugins.config import MAX_CONTENT_LENGTH

def register_error_handlers(app):
    """
    注册Flask应用的错误处理器
    
    参数：
    - app: Flask应用实例
    
    功能：
    - 注册413错误（请求实体过大）处理器
    - 注册400错误（错误请求）处理器
    - 提供友好的错误响应
    """
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """
        处理413错误：请求实体过大
        
        功能：
        - 当上传文件超过MAX_CONTENT_LENGTH时触发
        - 返回友好的错误信息
        """
        max_size_gb = MAX_CONTENT_LENGTH / (1024*1024*1024)
        return jsonify({
            'success': False,
            'message': f'上传文件过大，最大允许 {max_size_gb:.1f}GB'
        }), 413

    @app.errorhandler(400)
    def bad_request(error):
        """
        处理400错误：错误请求
        
        功能：
        - 处理文件上传相关的错误请求
        - 返回详细的错误信息
        """
        return jsonify({
            'success': False,
            'message': '请求格式错误，请检查上传的文件'
        }), 400 