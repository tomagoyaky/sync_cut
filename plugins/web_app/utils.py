#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility Functions Module
Contains shared utility functions and global variables
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from plugins.config import *

# Global variables for tracking conversions
active_conversions = {}
conversion_history = []

def is_allowed_file(filename):
    """
    检查文件是否为允许的格式
    
    参数：
    - filename: 文件名
    
    返回：
    - bool: 是否为允许的文件格式
    
    支持的格式：
    - 视频格式：.mp4, .avi, .mov, .mkv, .wmv, .flv
    - 音频格式：.mp3, .wav, .aac, .flac, .ogg, .m4a
    """
    if not filename:
        return False
    
    # 获取文件扩展名
    ext = Path(filename).suffix.lower()
    
    # 支持的视频格式
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'}
    
    # 支持的音频格式
    audio_extensions = {'.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'}
    
    # 返回是否为支持的格式
    return ext in video_extensions or ext in audio_extensions

def get_file_type(filename):
    """
    获取文件类型（视频或音频）
    
    参数：
    - filename: 文件名
    
    返回：
    - str: 'video', 'audio', 或 'unknown'
    """
    if not filename:
        return 'unknown'
    
    ext = Path(filename).suffix.lower()
    
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'}
    audio_extensions = {'.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'}
    
    if ext in video_extensions:
        return 'video'
    elif ext in audio_extensions:
        return 'audio'
    else:
        return 'unknown'

def validate_conversion_type(conversion_type, file_type):
    """
    验证转换类型是否与文件类型匹配
    
    参数：
    - conversion_type: 转换类型
    - file_type: 文件类型
    
    返回：
    - bool: 是否匹配
    - str: 错误信息（如果不匹配）
    """
    if conversion_type == 'mp4_to_mp3':
        if file_type != 'video':
            return False, "MP4转MP3需要视频文件"
    elif conversion_type == 'mp3_to_txt':
        if file_type != 'audio':
            return False, "MP3转文字需要音频文件"
    elif conversion_type == 'mp4_to_txt':
        if file_type != 'video':
            return False, "MP4转文字需要视频文件"
    else:
        return False, "不支持的转换类型"
    
    return True, ""

def format_file_size(size_bytes):
    """
    格式化文件大小显示
    
    参数：
    - size_bytes: 文件大小（字节）
    
    返回：
    - str: 格式化的文件大小字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def get_conversion_progress_message(conversion_type, progress):
    """
    根据转换类型和进度生成进度消息
    
    参数：
    - conversion_type: 转换类型
    - progress: 进度百分比
    
    返回：
    - str: 进度消息
    """
    if conversion_type == 'mp4_to_mp3':
        if progress < 20:
            return "正在分析视频文件..."
        elif progress < 60:
            return "正在提取音频..."
        elif progress < 90:
            return "正在压缩音频..."
        else:
            return "正在完成转换..."
    
    elif conversion_type == 'mp3_to_txt':
        if progress < 10:
            return "正在准备音频文件..."
        elif progress < 30:
            return "正在连接语音识别服务..."
        elif progress < 80:
            return "正在进行语音识别..."
        else:
            return "正在生成文字和字幕..."
    
    elif conversion_type == 'mp4_to_txt':
        if progress < 25:
            return "正在转换视频为音频..."
        elif progress < 50:
            return "正在准备语音识别..."
        elif progress < 90:
            return "正在进行语音识别..."
        else:
            return "正在生成最终结果..."
    
    return f"处理中... {progress}%" 