#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Web Routes Module
Contains all web page routes for the Flask application
"""

import sys
from pathlib import Path
from flask import Blueprint, render_template

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from plugins.config import *

# Create blueprint for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    首页路由
    
    功能：
    - 显示应用主页
    - 展示系统基本信息和功能介绍
    
    返回：
    - 渲染的首页HTML模板
    - 包含应用版本和最大文件大小信息
    """
    return render_template('index.html', 
                         title="首页",
                         app_version=APP_VERSION,
                         max_file_size=MAX_CONTENT_LENGTH // (1024*1024*1024))

@main_bp.route('/upload')
def upload_page():
    """
    文件上传页面路由
    
    功能：
    - 显示文件上传界面
    - 提供文件选择和转换类型选择功能
    - 显示支持的文件格式和大小限制说明
    
    返回：
    - 渲染的上传页面HTML模板
    - 包含文件上传表单和转换选项
    """
    return render_template('upload.html', title="文件上传")

@main_bp.route('/config')
def config_page():
    """
    配置设置页面路由
    
    功能：
    - 显示系统配置界面
    - 允许用户修改MP4转MP3、MP3转文字、阿里云NLS等配置
    - 提供配置保存和重置功能
    
    返回：
    - 渲染的配置页面HTML模板
    - 包含当前配置信息和修改表单
    """
    # Load current configuration
    current_config = load_config_file()
    if not current_config:
        current_config = get_default_config()
    
    # Extract configuration sections
    mp4_config = current_config.get('mp4_to_mp3', {})
    mp3_config = current_config.get('mp3_to_txt', {})
    nls_config = current_config.get('alibaba_nls', {})
    
    return render_template('config.html', 
                         title="配置设置",
                         mp4_config=mp4_config,
                         mp3_config=mp3_config,
                         nls_config=nls_config)

@main_bp.route('/history')
def history_page():
    """
    转换历史页面路由
    
    功能：
    - 显示历史转换记录
    - 展示转换状态、时间、文件信息等
    - 提供转换记录的查看和管理功能
    
    返回：
    - 渲染的历史页面HTML模板
    - 包含转换历史记录列表
    """
    return render_template('history.html', title="转换历史")

@main_bp.route('/status')
def status_page():
    """
    系统状态页面路由
    
    功能：
    - 显示系统运行状态
    - 展示目录结构、配置信息等
    - 提供系统健康检查信息
    
    返回：
    - 渲染的状态页面HTML模板
    - 包含系统状态和配置信息
    """
    return render_template('status.html', title="系统状态") 