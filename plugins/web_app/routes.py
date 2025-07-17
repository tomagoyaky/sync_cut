#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Web Routes Module
Contains all web page routes for the Flask application
"""

import sys
from pathlib import Path
from flask import Blueprint, render_template, current_app, jsonify, url_for

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

@main_bp.route('/workspace')
def workspace():
    """工作区页面"""
    return render_template('workspace.html')

@main_bp.route('/workspace/files')
def workspace_files():
    """获取工作区文件列表"""
    try:
        upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'workspace/upload'))
        files = {'videos': [], 'texts': [], 'subtitles': []}
        
        if upload_dir.exists():
            for file_path in upload_dir.iterdir():
                if file_path.is_file():
                    file_info = {
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': file_path.stat().st_size,
                        'modified': file_path.stat().st_mtime
                    }
                    
                    if file_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
                        files['videos'].append(file_info)
                    elif file_path.suffix.lower() == '.txt':
                        files['texts'].append(file_info)
                    elif file_path.suffix.lower() == '.srt':
                        files['subtitles'].append(file_info)
        
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/workspace/file/<filename>')
def get_workspace_file(filename):
    """获取工作区文件内容"""
    try:
        upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'workspace/upload'))
        file_path = upload_dir / filename
        
        if not file_path.exists():
            return jsonify({'error': '文件不存在'}), 404
        
        if file_path.suffix.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({'type': 'text', 'content': content})
        elif file_path.suffix.lower() == '.srt':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # 解析SRT内容
            subtitles = parse_srt_content(content)
            return jsonify({'type': 'srt', 'content': content, 'subtitles': subtitles})
        elif file_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
            # 返回视频文件URL
            video_url = url_for('main.serve_upload_file', filename=filename)
            return jsonify({'type': 'video', 'url': video_url})
        else:
            return jsonify({'error': '不支持的文件类型'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/uploads/thumbnails/<path:filename>')
def serve_thumbnail_file(filename):
    """提供缩略图文件服务"""
    try:
        upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'workspace/upload'))
        thumbnails_dir = upload_dir / 'thumbnails'
        file_path = thumbnails_dir / filename
        
        if file_path.exists() and file_path.is_file():
            from flask import send_file
            return send_file(file_path)
        else:
            return jsonify({'error': '缩略图文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def parse_srt_content(content):
    """解析SRT字幕内容"""
    subtitles = []
    lines = content.strip().split('\n')
    i = 0
    
    while i < len(lines):
        if lines[i].strip().isdigit():  # 字幕序号
            subtitle = {'index': int(lines[i].strip())}
            i += 1
            
            if i < len(lines) and '-->' in lines[i]:  # 时间轴
                time_line = lines[i].strip()
                start_time, end_time = time_line.split(' --> ')
                subtitle['start'] = srt_time_to_seconds(start_time)
                subtitle['end'] = srt_time_to_seconds(end_time)
                subtitle['start_display'] = start_time
                subtitle['end_display'] = end_time
                i += 1
                
                # 字幕文本
                text_lines = []
                while i < len(lines) and lines[i].strip():
                    text_lines.append(lines[i].strip())
                    i += 1
                subtitle['text'] = '\n'.join(text_lines)
                subtitles.append(subtitle)
        i += 1
    
    return subtitles

def srt_time_to_seconds(time_str):
    """将SRT时间格式转换为秒数"""
    try:
        time_part, ms_part = time_str.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)
        return h * 3600 + m * 60 + s + ms / 1000
    except:
        return 0 