#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket Handler Module
Handles real-time WebSocket connections for progress updates
"""

import sys
import logging
from pathlib import Path
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .utils import active_conversions, conversion_history

logger = logging.getLogger(__name__)

# Global SocketIO instance
socketio = None

def init_socketio(app):
    """
    初始化SocketIO实例
    
    参数：
    - app: Flask应用实例
    
    返回：
    - SocketIO实例
    """
    global socketio
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=False,
        engineio_logger=False
    )
    
    # 注册事件处理器
    register_handlers()
    
    logger.info("SocketIO initialized successfully")
    return socketio

def register_handlers():
    """
    注册WebSocket事件处理器
    """
    
    @socketio.on('connect')
    def handle_connect():
        """
        处理客户端连接事件
        """
        client_id = request.sid
        logger.info(f"Client {client_id} connected")
        
        # 发送连接成功消息
        emit('connection_status', {
            'status': 'connected',
            'message': '已连接到服务器',
            'client_id': client_id
        })
        
        # 发送当前活跃的转换状态
        emit('active_conversions', {
            'conversions': active_conversions,
            'history_count': len(conversion_history)
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """
        处理客户端断开连接事件
        """
        client_id = request.sid
        logger.info(f"Client {client_id} disconnected")
    
    @socketio.on('join_conversion')
    def handle_join_conversion(data):
        """
        处理加入转换房间事件
        
        参数：
        - data: 包含conversion_id的字典
        """
        conversion_id = data.get('conversion_id')
        if conversion_id:
            join_room(conversion_id)
            logger.info(f"Client {request.sid} joined conversion room {conversion_id}")
            
            # 如果转换存在，发送当前状态
            if conversion_id in active_conversions:
                emit('conversion_status', active_conversions[conversion_id])
        else:
            emit('error', {'message': '无效的转换ID'})
    
    @socketio.on('leave_conversion')
    def handle_leave_conversion(data):
        """
        处理离开转换房间事件
        
        参数：
        - data: 包含conversion_id的字典
        """
        conversion_id = data.get('conversion_id')
        if conversion_id:
            leave_room(conversion_id)
            logger.info(f"Client {request.sid} left conversion room {conversion_id}")
    
    @socketio.on('get_conversion_status')
    def handle_get_conversion_status(data):
        """
        处理获取转换状态请求
        
        参数：
        - data: 包含conversion_id的字典
        """
        conversion_id = data.get('conversion_id')
        if conversion_id and conversion_id in active_conversions:
            emit('conversion_status', active_conversions[conversion_id])
        else:
            emit('error', {'message': '转换不存在'})
    
    @socketio.on('get_all_conversions')
    def handle_get_all_conversions():
        """
        处理获取所有转换状态请求
        """
        emit('all_conversions', {
            'active_conversions': active_conversions,
            'history_count': len(conversion_history)
        })

def emit_upload_progress(conversion_id, loaded, total, speed=None, eta=None):
    """
    发送上传进度更新
    
    参数：
    - conversion_id: 转换ID
    - loaded: 已上传字节数
    - total: 总字节数
    - speed: 上传速度（可选）
    - eta: 预计剩余时间（可选）
    """
    if not socketio:
        return
    
    percentage = int((loaded / total) * 100) if total > 0 else 0
    
    progress_data = {
        'type': 'upload_progress',
        'conversion_id': conversion_id,
        'loaded': loaded,
        'total': total,
        'percentage': percentage,
        'speed': speed,
        'eta': eta
    }
    
    # 发送到特定转换房间
    socketio.emit('upload_progress', progress_data, room=conversion_id)
    logger.debug(f"Sent upload progress for {conversion_id}: {percentage}%")

def emit_conversion_progress(conversion_id, progress, message, status='processing'):
    """
    发送转换进度更新
    
    参数：
    - conversion_id: 转换ID
    - progress: 进度百分比
    - message: 进度消息
    - status: 转换状态
    """
    if not socketio:
        return
    
    progress_data = {
        'type': 'conversion_progress',
        'conversion_id': conversion_id,
        'progress': progress,
        'message': message,
        'status': status
    }
    
    # 发送到特定转换房间
    socketio.emit('conversion_progress', progress_data, room=conversion_id)
    logger.debug(f"Sent conversion progress for {conversion_id}: {progress}% - {message}")

def emit_conversion_status(conversion_id, status_data):
    """
    发送转换状态更新
    
    参数：
    - conversion_id: 转换ID
    - status_data: 完整的状态数据
    """
    if not socketio:
        return
    
    # 发送到特定转换房间
    socketio.emit('conversion_status', status_data, room=conversion_id)
    
    # 同时发送到所有连接的客户端（用于更新活跃转换列表）
    socketio.emit('conversion_update', {
        'conversion_id': conversion_id,
        'status': status_data
    })
    
    logger.info(f"Sent conversion status for {conversion_id}: {status_data.get('status', 'unknown')}")

def emit_conversion_complete(conversion_id, result_data):
    """
    发送转换完成通知
    
    参数：
    - conversion_id: 转换ID
    - result_data: 完整的结果数据
    """
    if not socketio:
        return
    
    complete_data = {
        'type': 'conversion_complete',
        'conversion_id': conversion_id,
        'success': result_data.get('success', False),
        'message': result_data.get('message', ''),
        'output_file': result_data.get('output_file'),
        'error': result_data.get('error'),
        'end_time': result_data.get('end_time')
    }
    
    # 发送到特定转换房间
    socketio.emit('conversion_complete', complete_data, room=conversion_id)
    
    # 发送到所有连接的客户端（用于更新活跃转换列表）
    socketio.emit('conversion_finished', {
        'conversion_id': conversion_id,
        'success': result_data.get('success', False)
    })
    
    logger.info(f"Sent conversion complete for {conversion_id}: {'success' if result_data.get('success') else 'failed'}")

def emit_error(conversion_id, error_message):
    """
    发送错误消息
    
    参数：
    - conversion_id: 转换ID（可选）
    - error_message: 错误消息
    """
    if not socketio:
        return
    
    error_data = {
        'type': 'error',
        'conversion_id': conversion_id,
        'message': error_message
    }
    
    if conversion_id:
        # 发送到特定转换房间
        socketio.emit('error', error_data, room=conversion_id)
    else:
        # 发送到所有连接的客户端
        socketio.emit('error', error_data)
    
    logger.error(f"Sent error for {conversion_id}: {error_message}")

def broadcast_system_status(status_data):
    """
    广播系统状态更新
    
    参数：
    - status_data: 系统状态数据
    """
    if not socketio:
        return
    
    socketio.emit('system_status', status_data)
    logger.info("Broadcasted system status update")

def get_socketio():
    """
    获取SocketIO实例
    
    返回：
    - SocketIO实例
    """
    return socketio 