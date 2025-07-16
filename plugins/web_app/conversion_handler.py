#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversion Handler Module
Handles background file conversion processing
"""

import sys
import logging
import threading
import time
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from plugins.config import *
from .utils import active_conversions, conversion_history

# Import converters with correct paths
from plugins.mp4_to_mp3.mp4_to_mp3 import MP4ToMP3Converter, save_conversion_log as save_mp4_log
from plugins.mp3_to_txt.mp3_to_txt import MP3ToTXTConverter, save_conversion_log as save_txt_log

# Try to import Whisper converter, but make it optional
try:
    from plugins.mp3_to_txt.whisper_convert import WhisperConverter, save_whisper_conversion_log
    WHISPER_AVAILABLE = True
except ImportError:
    WhisperConverter = None
    save_whisper_conversion_log = None
    WHISPER_AVAILABLE = False

# Import WebSocket handler
from . import websocket_handler

logger = logging.getLogger(__name__)

def process_conversion(conversion_id: str, input_path: str, conversion_type: str, original_filename: str, conversion_engine: str = 'alibaba_nls'):
    """
    后台转换处理函数
    
    功能：
    - 在后台线程中处理文件转换任务
    - 支持三种转换类型的具体实现
    - 实时更新转换进度和状态
    
    参数：
    - conversion_id: 转换任务唯一标识符
    - input_path: 输入文件路径
    - conversion_type: 转换类型 (mp4_to_mp3|mp3_to_txt|mp4_to_txt)
    - original_filename: 原始文件名
    
    转换类型说明：
    - mp4_to_mp3: 视频转音频，提取MP4中的音频保存为MP3
    - mp3_to_txt: 音频转文字，使用语音识别生成文字和字幕
    - mp4_to_txt: 完整流程，先转音频再转文字
    
    异常处理：
    - 转换失败时更新状态为failed
    - 记录详细错误信息
    - 清理临时文件
    """
    logger.info(f"开始处理转换任务 - ID: {conversion_id}, 类型: {conversion_type}, 文件: {original_filename}")
    logger.debug(f"输入文件路径: {input_path}")
    
    try:
        conversion = active_conversions[conversion_id]
        logger.debug(f"获取到转换任务对象: {conversion}")
        
        def update_progress(progress: int, message: str):
            """更新转换进度的回调函数"""
            logger.debug(f"进度更新 [{conversion_id}]: {progress}% - {message}")
            conversion['progress'] = progress
            conversion['message'] = message
            conversion['status'] = 'processing'
            
            # 通过WebSocket发送进度更新
            websocket_handler.emit_conversion_progress(conversion_id, progress, message, 'processing')
        
        # 加载配置
        logger.info(f"加载配置文件...")
        config = load_config_file()
        if not config:
            logger.warning("配置文件加载失败，使用默认配置")
            config = get_default_config()
        else:
            logger.debug(f"配置加载成功: {list(config.keys())}")
        
        input_file = Path(input_path)
        logger.info(f"输入文件信息 - 路径: {input_file}, 存在: {input_file.exists()}, 大小: {input_file.stat().st_size if input_file.exists() else 'N/A'} bytes")
        
        if conversion_type == 'mp4_to_mp3':
            logger.info("开始 MP4 转 MP3 转换")
            # MP4转MP3转换
            output_file = UPLOAD_DIR / f"{input_file.stem}.mp3"
            logger.debug(f"输出文件路径: {output_file}")
            
            logger.info("初始化 MP4ToMP3Converter")
            converter = MP4ToMP3Converter(config.get('mp4_to_mp3'))
            logger.debug(f"转换器配置: {config.get('mp4_to_mp3')}")
            
            logger.info("开始执行 MP4 到 MP3 转换")
            success, message, metadata = converter.convert(
                input_file, output_file, update_progress
            )
            
            logger.info(f"MP4 转 MP3 转换完成 - 成功: {success}, 消息: {message}")
            if metadata:
                logger.debug(f"转换元数据: {metadata}")
            
            if success:
                logger.info("保存转换日志")
                save_mp4_log(str(input_file), str(output_file), metadata)
                logger.debug(f"输出文件大小: {output_file.stat().st_size if output_file.exists() else 'N/A'} bytes")
            
        elif conversion_type == 'mp3_to_txt':
            logger.info(f"开始 MP3 转文字转换，使用引擎: {conversion_engine}")
            # MP3转文字转换
            output_txt_file = UPLOAD_DIR / f"{input_file.stem}.txt"
            output_srt_file = UPLOAD_DIR / f"{input_file.stem}.srt"
            logger.debug(f"输出文件路径 - TXT: {output_txt_file}, SRT: {output_srt_file}")
            
            # 根据引擎选择不同的转换器
            if conversion_engine == 'whisper':
                if not WHISPER_AVAILABLE:
                    raise ValueError("Whisper engine is not available. Please install openai-whisper or use 'alibaba_nls' engine.")
                logger.info("初始化 WhisperConverter")
                converter = WhisperConverter(config.get('mp3_to_txt'))
                logger.debug(f"Whisper转换器配置: {config.get('mp3_to_txt')}")
            else:
                logger.info("初始化 MP3ToTXTConverter (阿里云NLS)")
                converter = MP3ToTXTConverter(config.get('mp3_to_txt'))
                logger.debug(f"NLS转换器配置: {config.get('mp3_to_txt')}")
            
            logger.info("开始执行 MP3 到文字转换")
            success, message, metadata = converter.convert(
                input_file, output_txt_file, output_srt_file, update_progress
            )
            
            logger.info(f"MP3 转文字转换完成 - 成功: {success}, 消息: {message}")
            if metadata:
                logger.debug(f"转换元数据: {metadata}")
            
            if success:
                logger.info("保存转换日志")
                if conversion_engine == 'whisper':
                    save_whisper_conversion_log(str(input_file), str(output_txt_file), metadata)
                else:
                    save_txt_log(str(input_file), str(output_txt_file), metadata)
                output_file = output_txt_file
                logger.debug(f"输出文件大小: {output_file.stat().st_size if output_file.exists() else 'N/A'} bytes")
            
        elif conversion_type == 'mp4_to_txt':
            logger.info("开始 MP4 转文字完整转换流程")
            # 完整MP4转文字转换
            # 第一步：转换MP4为MP3
            temp_mp3_file = TMP_DIR / f"{input_file.stem}.mp3"
            logger.debug(f"临时 MP3 文件路径: {temp_mp3_file}")
            
            update_progress(0, "转换视频为音频...")
            logger.info("第一步：开始 MP4 转 MP3")
            mp4_converter = MP4ToMP3Converter(config.get('mp4_to_mp3'))
            success, message, metadata = mp4_converter.convert(
                input_file, temp_mp3_file, 
                lambda p, m: update_progress(p//2, f"视频转音频: {m}")
            )
            
            logger.info(f"MP4 转 MP3 完成 - 成功: {success}, 消息: {message}")
            if metadata:
                logger.debug(f"MP4 转 MP3 元数据: {metadata}")
            
            if not success:
                logger.error(f"视频转音频失败: {message}")
                raise Exception(f"视频转音频失败: {message}")
            
            logger.debug(f"临时 MP3 文件大小: {temp_mp3_file.stat().st_size if temp_mp3_file.exists() else 'N/A'} bytes")
            
            # 第二步：转换MP3为文字
            output_txt_file = UPLOAD_DIR / f"{input_file.stem}.txt"
            output_srt_file = UPLOAD_DIR / f"{input_file.stem}.srt"
            logger.debug(f"最终输出文件路径 - TXT: {output_txt_file}, SRT: {output_srt_file}")
            
            update_progress(50, "转换音频为文字...")
            logger.info(f"第二步：开始 MP3 转文字，使用引擎: {conversion_engine}")
            
            # 根据引擎选择不同的转换器
            if conversion_engine == 'whisper':
                if not WHISPER_AVAILABLE:
                    raise ValueError("Whisper engine is not available. Please install openai-whisper or use 'alibaba_nls' engine.")
                logger.info("初始化 WhisperConverter")
                txt_converter = WhisperConverter(config.get('mp3_to_txt'))
            else:
                logger.info("初始化 MP3ToTXTConverter (阿里云NLS)")
                txt_converter = MP3ToTXTConverter(config.get('mp3_to_txt'))
            
            success, message, metadata = txt_converter.convert(
                temp_mp3_file, output_txt_file, output_srt_file,
                lambda p, m: update_progress(50 + p//2, f"音频转文字: {m}")
            )
            
            logger.info(f"MP3 转文字完成 - 成功: {success}, 消息: {message}")
            if metadata:
                logger.debug(f"MP3 转文字元数据: {metadata}")
            
            # 清理临时文件
            logger.info("清理临时文件")
            if temp_mp3_file.exists():
                temp_mp3_file.unlink()
                logger.debug(f"已删除临时文件: {temp_mp3_file}")
            
            if success:
                logger.info("保存转换日志")
                if conversion_engine == 'whisper':
                    save_whisper_conversion_log(str(input_file), str(output_txt_file), metadata)
                else:
                    save_txt_log(str(input_file), str(output_txt_file), metadata)
                output_file = output_txt_file
                logger.debug(f"最终输出文件大小: {output_file.stat().st_size if output_file.exists() else 'N/A'} bytes")
        
        else:
            error_msg = f"不支持的转换类型: {conversion_type}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # 更新转换状态
        logger.info(f"更新转换状态 - 成功: {success}")
        conversion['completed'] = True
        conversion['success'] = success
        conversion['message'] = message
        conversion['progress'] = 100
        conversion['end_time'] = datetime.now().isoformat()
        
        if success:
            conversion['output_file'] = str(output_file)
            conversion['status'] = 'completed'
            logger.info(f"转换成功完成 - 输出文件: {output_file}")
        else:
            conversion['error'] = message
            conversion['status'] = 'failed'
            logger.error(f"转换失败 - 错误: {message}")
        
        # 通过WebSocket发送完成通知
        logger.debug("发送 WebSocket 完成通知")
        websocket_handler.emit_conversion_complete(conversion_id, conversion)
        
        # 添加到历史记录
        logger.info("添加到历史记录")
        history_entry = {
            'timestamp': conversion['end_time'],
            'input_file': original_filename,
            'output_file': Path(output_file).name if success else None,
            'type': conversion_type,
            'success': success,
            'message': message
        }
        conversion_history.append(history_entry)
        logger.debug(f"历史记录条目: {history_entry}")
        
        # 延迟清理输入文件
        def cleanup_input_file():
            """1小时后清理输入文件"""
            logger.info(f"开始延迟清理输入文件: {input_path}")
            time.sleep(3600)  # Wait 1 hour
            if Path(input_path).exists():
                Path(input_path).unlink()
                logger.info(f"已清理输入文件: {input_path}")
            else:
                logger.debug(f"输入文件已不存在，无需清理: {input_path}")
        
        cleanup_thread = threading.Thread(target=cleanup_input_file)
        cleanup_thread.daemon = True
        cleanup_thread.start()
        logger.debug("启动延迟清理线程")
        
        logger.info(f"转换任务 {conversion_id} 处理完成")
        
    except Exception as e:
        logger.error(f"转换任务 {conversion_id} 发生异常: {str(e)}", exc_info=True)
        conversion['completed'] = True
        conversion['success'] = False
        conversion['error'] = str(e)
        conversion['message'] = f"转换失败: {str(e)}"
        conversion['status'] = 'failed'
        conversion['end_time'] = datetime.now().isoformat()
        
        # 通过WebSocket发送错误通知
        logger.debug("发送 WebSocket 错误通知")
        websocket_handler.emit_error(conversion_id, str(e))
        
        logger.error(f"转换任务 {conversion_id} 最终状态: failed")

def start_conversion_task(conversion_id: str, input_path: str, conversion_type: str, original_filename: str, conversion_engine: str = 'alibaba_nls'):
    """
    启动转换任务
    
    功能：
    - 在后台线程中启动转换处理
    - 设置线程为守护线程
    
    参数：
    - conversion_id: 转换任务唯一标识符
    - input_path: 输入文件路径
    - conversion_type: 转换类型
    - original_filename: 原始文件名
    """
    thread = threading.Thread(
        target=process_conversion,
        args=(conversion_id, input_path, conversion_type, original_filename, conversion_engine)
    )
    thread.daemon = True
    thread.start()
    
    logger.info(f"Started conversion task {conversion_id} for {original_filename}")

def get_conversion_status(conversion_id: str):
    """
    获取转换状态
    
    参数：
    - conversion_id: 转换任务唯一标识符
    
    返回：
    - dict: 转换状态信息，如果不存在则返回None
    """
    return active_conversions.get(conversion_id)

def get_all_conversions():
    """
    获取所有转换任务
    
    返回：
    - dict: 包含活跃转换和历史记录的字典
    """
    return {
        'active_conversions': active_conversions,
        'history_count': len(conversion_history)
    }

def get_conversion_history(limit: int = 50):
    """
    获取转换历史记录
    
    参数：
    - limit: 返回记录数量限制
    
    返回：
    - dict: 包含历史记录和总数的字典
    """
    return {
        'history': conversion_history[-limit:],
        'total': len(conversion_history)
    } 