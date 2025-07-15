#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Whisper MP3 to TXT Conversion Module
Converts MP3 audio files to TXT and SRT subtitle files using OpenAI Whisper
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import whisper
from pydub import AudioSegment

from plugins.config import MP3_TO_TXT_CONFIG, TMP_DIR, LOGS_DIR, MODELS_DIR

logger = logging.getLogger(__name__)

class WhisperConverter:
    """OpenAI Whisper音频转文字转换器"""
    
    def __init__(self, config: Dict = None):
        """初始化Whisper转换器"""
        self.config = config or MP3_TO_TXT_CONFIG.copy()
        self.tmp_dir = TMP_DIR
        self.models_dir = MODELS_DIR
        self.tmp_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)
        
        # Whisper模型配置
        self.whisper_config = {
            'model_size': self.config.get('whisper_model_size', 'base'),
            'language': self.config.get('whisper_language', 'zh'),
            'device': self.config.get('whisper_device', 'cpu'),
            'download_root': str(self.models_dir),
            'verbose': self.config.get('whisper_verbose', False)
        }
        
        self.model = None
        
    def _load_model(self, progress_callback=None):
        """加载Whisper模型"""
        try:
            if progress_callback:
                progress_callback(5, "加载Whisper模型...")
            
            logger.info(f"加载Whisper模型: {self.whisper_config['model_size']}")
            logger.info(f"模型存储路径: {self.whisper_config['download_root']}")
            
            # 检查模型文件是否存在
            model_name = self.whisper_config['model_size']
            model_file = self.models_dir / f"{model_name}.pt"
            
            if not model_file.exists():
                if progress_callback:
                    progress_callback(10, f"下载Whisper模型 {model_name}...")
                logger.info(f"模型文件不存在，将下载: {model_file}")
            else:
                logger.info(f"使用已存在的模型文件: {model_file}")
            
            # 加载模型
            self.model = whisper.load_model(
                name=self.whisper_config['model_size'],
                device=self.whisper_config['device'],
                download_root=self.whisper_config['download_root']
            )
            
            if progress_callback:
                progress_callback(20, "模型加载完成")
            
            logger.info("Whisper模型加载成功")
            return True
            
        except Exception as e:
            error_msg = f"加载Whisper模型失败: {str(e)}"
            logger.error(error_msg)
            if progress_callback:
                progress_callback(0, error_msg)
            return False
    
    def _prepare_audio(self, input_path: Path, progress_callback=None) -> Path:
        """准备音频文件供Whisper处理"""
        try:
            if progress_callback:
                progress_callback(25, "准备音频文件...")
            
            # 检查是否需要转换格式
            if input_path.suffix.lower() in ['.mp3', '.wav', '.flac', '.m4a']:
                # 直接使用原文件
                logger.info(f"音频文件格式支持，直接使用: {input_path}")
                return input_path
            
            # 需要转换为WAV格式
            logger.info(f"转换音频格式: {input_path.suffix} -> .wav")
            
            # 加载音频文件
            audio = AudioSegment.from_file(str(input_path))
            
            # 转换为WAV格式（Whisper推荐）
            output_path = self.tmp_dir / f"{input_path.stem}_whisper.wav"
            audio.export(str(output_path), format="wav")
            
            if progress_callback:
                progress_callback(30, "音频格式转换完成")
            
            logger.info(f"音频格式转换完成: {output_path}")
            return output_path
            
        except Exception as e:
            error_msg = f"音频格式转换失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _transcribe_audio(self, audio_path: Path, progress_callback=None) -> Dict:
        """使用Whisper进行音频转录"""
        try:
            if progress_callback:
                progress_callback(40, "开始语音识别...")
            
            logger.info(f"开始Whisper转录: {audio_path}")
            
            # 执行转录
            result = self.model.transcribe(
                str(audio_path),
                language=self.whisper_config['language'],
                verbose=self.whisper_config['verbose']
            )
            
            if progress_callback:
                progress_callback(80, "语音识别完成")
            
            logger.info(f"Whisper转录完成，识别到 {len(result.get('segments', []))} 个片段")
            return result
            
        except Exception as e:
            error_msg = f"Whisper转录失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _process_results(self, whisper_result: Dict) -> Tuple[str, List[Dict]]:
        """处理Whisper转录结果"""
        try:
            # 提取完整文本
            full_text = whisper_result.get('text', '').strip()
            
            # 处理分段结果
            segments = []
            for segment in whisper_result.get('segments', []):
                segment_data = {
                    'text': segment.get('text', '').strip(),
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0),
                    'confidence': segment.get('avg_logprob', 0),  # Whisper使用avg_logprob作为置信度
                    'timestamp': datetime.now().isoformat()
                }
                segments.append(segment_data)
            
            logger.info(f"处理结果: 完整文本长度 {len(full_text)}, 分段数量 {len(segments)}")
            return full_text, segments
            
        except Exception as e:
            error_msg = f"处理转录结果失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _generate_srt(self, segments: List[Dict]) -> str:
        """生成SRT字幕格式"""
        try:
            srt_content = ""
            
            for i, segment in enumerate(segments, 1):
                text = segment.get('text', '').strip()
                if text:
                    start_time = segment.get('start', 0)
                    end_time = segment.get('end', 0)
                    
                    # 转换为timedelta
                    start_td = timedelta(seconds=start_time)
                    end_td = timedelta(seconds=end_time)
                    
                    srt_content += f"{i}\n"
                    srt_content += f"{self._format_srt_time(start_td)} --> {self._format_srt_time(end_td)}\n"
                    srt_content += f"{text}\n\n"
            
            return srt_content
            
        except Exception as e:
            error_msg = f"生成SRT字幕失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _format_srt_time(self, td: timedelta) -> str:
        """格式化SRT时间格式"""
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        milliseconds = int((td.total_seconds() % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def convert(self, input_path: Path, output_txt_path: Path, 
                output_srt_path: Path = None, progress_callback=None) -> Tuple[bool, str, Dict]:
        """
        转换音频为文字
        
        Args:
            input_path: 输入音频文件路径
            output_txt_path: 输出文本文件路径
            output_srt_path: 输出字幕文件路径（可选）
            progress_callback: 进度回调函数
            
        Returns:
            Tuple of (success, message, metadata)
        """
        try:
            logger.info(f"开始Whisper音频转文字: {input_path.name}")
            start_time = datetime.now()
            
            if progress_callback:
                progress_callback(0, "初始化转换器...")
            
            # 加载模型
            if not self._load_model(progress_callback):
                return False, "模型加载失败", {}
            
            # 准备音频文件
            prepared_audio_path = self._prepare_audio(input_path, progress_callback)
            
            # 执行转录
            whisper_result = self._transcribe_audio(prepared_audio_path, progress_callback)
            
            if progress_callback:
                progress_callback(85, "处理转录结果...")
            
            # 处理结果
            full_text, segments = self._process_results(whisper_result)
            
            if progress_callback:
                progress_callback(90, "保存结果文件...")
            
            # 保存TXT文件
            with open(output_txt_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            # 保存SRT文件（如果需要）
            if output_srt_path:
                srt_content = self._generate_srt(segments)
                with open(output_srt_path, 'w', encoding='utf-8') as f:
                    f.write(srt_content)
            
            # 清理临时文件
            if prepared_audio_path != input_path and prepared_audio_path.exists():
                prepared_audio_path.unlink()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            metadata = {
                'converter': 'whisper',
                'model_size': self.whisper_config['model_size'],
                'language': self.whisper_config['language'],
                'duration_seconds': duration,
                'segments_count': len(segments),
                'total_text_length': len(full_text),
                'config_used': self.config.copy(),
                'timestamp': end_time.isoformat()
            }
            
            if progress_callback:
                progress_callback(100, "转换完成！")
            
            logger.info(f"Whisper转换完成: {output_txt_path.name}")
            logger.info(f"处理了 {len(segments)} 个片段，总文本长度: {len(full_text)}")
            
            return True, "转换完成", metadata
            
        except Exception as e:
            error_msg = f"Whisper转换失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}
    
    def update_config(self, new_config: Dict):
        """更新转换器配置"""
        self.config.update(new_config)
        if 'whisper_model_size' in new_config:
            self.whisper_config['model_size'] = new_config['whisper_model_size']
        if 'whisper_language' in new_config:
            self.whisper_config['language'] = new_config['whisper_language']
        if 'whisper_device' in new_config:
            self.whisper_config['device'] = new_config['whisper_device']
        
        # 重新加载模型（如果模型大小改变）
        self.model = None
        logger.info(f"配置已更新: {new_config}")

def convert_mp3_to_txt_whisper(input_path: str, output_txt_path: str, 
                              output_srt_path: str = None, config: Dict = None, 
                              progress_callback=None) -> Tuple[bool, str, Dict]:
    """
    使用Whisper将音频转换为文字的便捷函数
    
    Args:
        input_path: 输入音频文件路径
        output_txt_path: 输出文本文件路径
        output_srt_path: 输出字幕文件路径（可选）
        config: 配置字典（可选）
        progress_callback: 进度回调函数
        
    Returns:
        Tuple of (success, message, metadata)
    """
    converter = WhisperConverter(config)
    return converter.convert(
        Path(input_path), 
        Path(output_txt_path), 
        Path(output_srt_path) if output_srt_path else None,
        progress_callback
    )

def get_whisper_models() -> List[str]:
    """获取可用的Whisper模型列表"""
    return ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3']

def get_whisper_languages() -> List[str]:
    """获取支持的语言列表"""
    return ['zh', 'en', 'ja', 'ko', 'auto']

def get_whisper_default_config() -> Dict:
    """获取Whisper默认配置"""
    return {
        'whisper_model_size': 'base',
        'whisper_language': 'zh',
        'whisper_device': 'cpu',
        'whisper_verbose': False
    }

def save_whisper_conversion_log(input_file: str, output_file: str, metadata: Dict):
    """保存Whisper转换日志"""
    try:
        log_file = LOGS_DIR / "whisper_conversions.json"
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'input_file': input_file,
            'output_file': output_file,
            'metadata': metadata,
            'converter': 'whisper'
        }
        
        # 加载现有日志
        logs = []
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        
        # 添加新日志条目
        logs.append(log_entry)
        
        # 保存更新后的日志
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Whisper转换日志已保存: {log_file}")
        
    except Exception as e:
        logger.error(f"保存Whisper转换日志失败: {str(e)}")

if __name__ == "__main__":
    # 测试转换器
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python whisper_convert.py <input.mp3> <output.txt> [output.srt]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_txt_file = sys.argv[2]
    output_srt_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    def progress_callback(percent, message):
        print(f"进度: {percent}% - {message}")
    
    success, message, metadata = convert_mp3_to_txt_whisper(
        input_file, output_txt_file, output_srt_file, 
        progress_callback=progress_callback
    )
    
    if success:
        print(f"✅ {message}")
        print(f"元数据: {json.dumps(metadata, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ {message}")
        sys.exit(1) 