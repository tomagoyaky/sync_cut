#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Routes Module
Contains all API endpoints for the Flask application
"""

import sys
import json
import logging
import uuid
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from plugins.config import *
from .utils import active_conversions, conversion_history, is_allowed_file, get_file_type, validate_conversion_type
from .conversion_handler import start_conversion_task, get_conversion_status, get_all_conversions, get_conversion_history

logger = logging.getLogger(__name__)

# Create blueprint for API routes
api_bp = Blueprint('api', __name__)

@api_bp.route('/convert', methods=['POST'])
def api_convert():
    """
    文件转换API接口
    
    功能：
    - 处理文件上传和转换请求
    - 支持三种转换类型：mp4_to_mp3、mp3_to_txt、mp4_to_txt
    - 异步处理转换任务，立即返回转换ID
    
    请求参数：
    - file: 上传的文件对象 (multipart/form-data)
    - conversion_type: 转换类型 (mp4_to_mp3|mp3_to_txt|mp4_to_txt)
    
    返回：
    - 成功: {'success': True, 'conversion_id': str, 'message': str}
    - 失败: {'success': False, 'message': str}
    
    异常处理：
    - 文件格式验证
    - 文件大小检查
    - 转换类型验证
    """
    try:
        # 验证文件是否存在
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        file = request.files['file']
        conversion_type = request.form.get('conversion_type')
        conversion_engine = request.form.get('conversion_engine', 'alibaba_nls')  # 默认使用阿里云NLS
        
        # 验证文件名
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        # 验证转换类型
        if not conversion_type:
            return jsonify({'success': False, 'message': '请选择转换类型'})
        
        # 验证文件格式
        if not is_allowed_file(file.filename):
            return jsonify({'success': False, 'message': '不支持的文件格式'})
        
        # 验证转换类型与文件类型的匹配
        file_type = get_file_type(file.filename)
        is_valid, error_message = validate_conversion_type(conversion_type, file_type)
        if not is_valid:
            return jsonify({'success': False, 'message': error_message})
        
        # 记录文件信息用于调试
        logger.info(f"Processing file: {file.filename}, Content-Type: {file.content_type}")
        logger.info(f"Max content length configured: {MAX_CONTENT_LENGTH} bytes ({MAX_CONTENT_LENGTH / (1024*1024*1024):.2f} GB)")
        
        # 检查文件大小（如果可以获取的话）
        try:
            # 尝试获取文件大小
            file.seek(0, 2)  # 移动到文件末尾
            file_size = file.tell()
            file.seek(0)  # 重置文件指针
            
            logger.info(f"File size: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
            
            if file_size > MAX_CONTENT_LENGTH:
                return jsonify({
                    'success': False, 
                    'message': f'文件大小 ({file_size / (1024*1024*1024):.2f} GB) 超过限制 ({MAX_CONTENT_LENGTH / (1024*1024*1024):.2f} GB)'
                })
        except Exception as size_check_error:
            logger.warning(f"Could not check file size: {size_check_error}")
            # 继续处理，让Flask的内置检查处理大小限制
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        input_path = UPLOAD_DIR / unique_filename
        file.save(str(input_path))
        
        # 生成转换ID
        conversion_id = str(uuid.uuid4())
        
        # 初始化转换跟踪信息
        active_conversions[conversion_id] = {
            'id': conversion_id,
            'filename': filename,
            'input_path': str(input_path),
            'type': conversion_type,
            'status': 'starting',
            'progress': 0,
            'message': '准备中...',
            'start_time': datetime.now().isoformat(),
            'completed': False,
            'success': False,
            'output_file': None,
            'error': None
        }
        
        # 在后台线程中开始转换
        start_conversion_task(conversion_id, str(input_path), conversion_type, filename, conversion_engine)
        
        return jsonify({
            'success': True,
            'conversion_id': conversion_id,
            'message': '转换已开始'
        })
        
    except Exception as e:
        logger.error(f"Conversion API error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@api_bp.route('/conversion/<conversion_id>')
def api_conversion_status(conversion_id):
    """
    获取转换状态API接口
    
    功能：
    - 查询指定转换任务的实时状态
    - 返回转换进度、状态信息和结果
    
    URL参数：
    - conversion_id: 转换任务的唯一标识符
    
    返回：
    - 成功: 转换状态对象 {
        'id': str,
        'filename': str,
        'type': str,
        'status': str,
        'progress': int,
        'message': str,
        'completed': bool,
        'success': bool,
        'output_file': str,
        'error': str
      }
    - 失败: {'error': 'Conversion not found'} (404)
    """
    conversion = get_conversion_status(conversion_id)
    if conversion:
        return jsonify(conversion)
    else:
        return jsonify({'error': 'Conversion not found'}), 404

@api_bp.route('/conversions')
def api_conversions():
    """
    获取所有转换任务API接口
    
    功能：
    - 返回所有活跃的转换任务状态
    - 提供转换历史记录数量统计
    
    返回：
    - {
        'active_conversions': dict,  # 活跃转换任务字典
        'history_count': int         # 历史记录总数
      }
    """
    return jsonify(get_all_conversions())

@api_bp.route('/config', methods=['GET', 'POST'])
def api_config():
    """
    配置管理API接口
    
    功能：
    - GET: 获取当前系统配置
    - POST: 更新系统配置
    
    GET请求：
    - 返回: 完整的配置对象
    
    POST请求：
    - 请求体: JSON格式的配置对象
    - 返回: {'success': bool, 'message': str}
    
    异常处理：
    - 配置文件读写错误
    - JSON格式验证
    """
    if request.method == 'GET':
        # 获取当前配置
        config = load_config_file()
        if not config:
            config = get_default_config()
        return jsonify(config)
    
    elif request.method == 'POST':
        # 更新配置
        try:
            new_config = request.get_json()
            save_config_file(new_config)
            return jsonify({'success': True, 'message': '配置保存成功'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

@api_bp.route('/config/reset', methods=['POST'])
def api_config_reset():
    """
    重置配置API接口
    
    功能：
    - 将系统配置重置为默认值
    - 清除所有用户自定义配置
    
    请求方法：POST
    
    返回：
    - 成功: {'success': True, 'message': '配置已重置为默认值'}
    - 失败: {'success': False, 'message': str}
    
    异常处理：
    - 配置文件写入错误
    """
    try:
        default_config = get_default_config()
        save_config_file(default_config)
        return jsonify({'success': True, 'message': '配置已重置为默认值'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@api_bp.route('/history')
def api_history():
    """
    获取转换历史API接口
    
    功能：
    - 返回最近的转换历史记录
    - 提供历史记录的分页和统计信息
    
    返回：
    - {
        'history': list,  # 最近50条转换记录
        'total': int      # 历史记录总数
      }
    
    历史记录格式：
    - {
        'timestamp': str,      # 转换完成时间
        'input_file': str,     # 输入文件名
        'output_file': str,    # 输出文件名
        'type': str,           # 转换类型
        'success': bool,       # 转换是否成功
        'message': str         # 转换结果消息
      }
    """
    return jsonify(get_conversion_history())

@api_bp.route('/status')
def api_status():
    """
    获取系统状态API接口
    
    功能：
    - 返回系统运行状态信息
    - 提供应用版本、目录结构等信息
    
    返回：
    - {
        'status': str,           # 系统状态 (running)
        'app_name': str,         # 应用名称
        'version': str,          # 应用版本
        'workspace': str,        # 工作空间目录
        'plugins': str,          # 插件目录
        'tools': str,            # 工具目录
        'directories': {         # 各子目录路径
          'models': str,
          'logs': str,
          'upload': str,
          'tmp': str,
          'status': str
        }
      }
    """
    return jsonify({
        'status': 'running',
        'app_name': APP_NAME,
        'version': APP_VERSION,
        'max_content_length': MAX_CONTENT_LENGTH,
        'max_content_length_gb': round(MAX_CONTENT_LENGTH / (1024*1024*1024), 2),
        'workspace': str(WORKSPACE_DIR),
        'plugins': str(PLUGINS_DIR),
        'tools': str(TOOLS_DIR),
        'directories': {
            'models': str(MODELS_DIR),
            'logs': str(LOGS_DIR),
            'upload': str(UPLOAD_DIR),
            'tmp': str(TMP_DIR),
            'status': str(STATUS_DIR)
        }
    })

@api_bp.route('/download/<conversion_id>')
def api_download(conversion_id):
    """
    文件下载API接口
    
    功能：
    - 下载指定转换任务的输出文件
    - 支持浏览器直接下载
    
    URL参数：
    - conversion_id: 转换任务的唯一标识符
    
    返回：
    - 成功: 文件流 (application/octet-stream)
    - 失败: {'error': 'File not found'} (404)
    
    验证：
    - 转换任务是否存在
    - 转换是否已完成且成功
    - 输出文件是否存在
    """
    conversion = get_conversion_status(conversion_id)
    if conversion and conversion['completed'] and conversion['success']:
        output_file = conversion['output_file']
        if output_file and Path(output_file).exists():
            return send_file(output_file, as_attachment=True)
    
    return jsonify({'error': 'File not found'}), 404

@api_bp.route('/debug/config')
def api_debug_config():
    """
    调试配置API接口
    
    功能：
    - 返回详细的配置信息用于调试
    - 包括Flask配置和系统配置
    
    返回：
    - 详细的配置信息对象
    """
    from flask import current_app
    
    return jsonify({
        'config_from_file': load_config_file(),
        'max_content_length': MAX_CONTENT_LENGTH,
        'max_content_length_gb': MAX_CONTENT_LENGTH / (1024*1024*1024),
        'flask_config': {
            'MAX_CONTENT_LENGTH': current_app.config.get('MAX_CONTENT_LENGTH'),
            'UPLOAD_FOLDER': current_app.config.get('UPLOAD_FOLDER')
        },
        'directories': {
            'upload': str(UPLOAD_DIR),
            'tmp': str(TMP_DIR),
            'logs': str(LOGS_DIR)
        }
    }) 