#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Faster-Whisper MP3 to TXT Conversion Module
Converts MP3 audio files to TXT and SRT subtitle files using Faster-Whisper
High-performance implementation of Fast Whisper with CUDA support
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

from faster_whisper import WhisperModel
from pydub import AudioSegment

from plugins.config import MP3_TO_TXT_CONFIG, TMP_DIR, LOGS_DIR, MODELS_DIR

logger = logging.getLogger(__name__)

class WhisperConverter:
    """Faster-Whisper音频转文字转换器"""
    
    def __init__(self, config: Dict = None):
        """初始化Faster-Whisper转换器"""
        self.config = config or MP3_TO_TXT_CONFIG.copy()
        self.tmp_dir = TMP_DIR
        self.models_dir = MODELS_DIR
        self.tmp_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)
        
        # Faster-Whisper模型配置
        self.whisper_config = {
            'model_size': self.config.get('whisper_model_size', 'base'),
            'language': self.config.get('whisper_language', 'zh'),
            'device': self.config.get('whisper_device', 'cpu'),
            'compute_type': self.config.get('whisper_compute_type', 'int8'),
            'download_root': str(self.models_dir),
            'verbose': self.config.get('whisper_verbose', False)
        }
        
        self.model = None
        
    def _load_model(self, progress_callback=None):
        """加载Faster-Whisper模型"""
        try:
            if progress_callback:
                progress_callback(5, "加载Faster-Whisper模型...")
            
            logger.info(f"🤖 正在加载Faster-Whisper模型...")
            logger.info(f"📦 模型大小: {self.whisper_config['model_size']}")
            logger.info(f"💻 计算设备: {self.whisper_config['device']}")
            logger.info(f"⚙️ 计算类型: {self.whisper_config['compute_type']}")
            logger.info(f"📁 模型存储路径: {self.whisper_config['download_root']}")
            
            if progress_callback:
                progress_callback(10, f"初始化Faster-Whisper模型...")
            
            logger.info(f"⏰ 开始初始化模型... {datetime.now().strftime('%H:%M:%S')}")
            start_load_time = time.time()
            
            # 创建Faster-Whisper模型
            self.model = WhisperModel(
                model_size_or_path=self.whisper_config['model_size'],
                device=self.whisper_config['device'],
                compute_type=self.whisper_config['compute_type'],
                download_root=self.whisper_config['download_root']
            )
            
            load_duration = time.time() - start_load_time
            logger.info(f"✅ 模型加载完成! 耗时: {load_duration:.2f}秒")
            
            if progress_callback:
                progress_callback(20, "模型加载完成")
            
            logger.info("Faster-Whisper模型加载成功")
            return True
            
        except Exception as e:
            error_msg = f"加载Faster-Whisper模型失败: {str(e)}"
            logger.info(f"❌ 模型加载失败: {error_msg}")
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
        """使用Faster-Whisper进行音频转录"""
        try:
            if progress_callback:
                progress_callback(40, "开始语音识别...")
            
            logger.info(f"开始Faster-Whisper转录: {audio_path}")
            
            # 设置语言参数，如果是'auto'则不指定语言让模型自动检测
            language = self.whisper_config['language'] if self.whisper_config['language'] != 'auto' else None
            
            if progress_callback:
                progress_callback(45, f"使用模型: {self.whisper_config['model_size']}")
            
            logger.info(f"🔄 正在使用Faster-Whisper进行语音识别...")
            logger.info(f"📁 音频文件: {audio_path.name}")
            logger.info(f"🤖 模型大小: {self.whisper_config['model_size']}")
            logger.info(f"🌍 语言设置: {self.whisper_config['language']}")
            logger.info(f"💻 计算设备: {self.whisper_config['device']}")
            logger.info(f"⚙️ 计算类型: {self.whisper_config['compute_type']}")
            
            # 执行转录 - Faster-Whisper返回的是生成器
            if progress_callback:
                progress_callback(50, "正在执行语音识别...")
            
            logger.info(f"⏰ 开始转录... {datetime.now().strftime('%H:%M:%S')}")
            start_transcribe_time = time.time()
            
            segments, info = self.model.transcribe(
                str(audio_path),
                language=language,
                word_timestamps=True,  # 启用词级时间戳
                vad_filter=True,      # 启用语音活动检测
                vad_parameters=dict(min_silence_duration_ms=500)  # VAD参数
            )
            
            if progress_callback:
                progress_callback(60, "正在处理转录片段...")
            
            # 将生成器转换为列表并构建结果
            logger.info(f"📝 正在处理转录片段...")
            segments_list = []
            segment_count = 0
            
            for segment in segments:
                segments_list.append(segment)
                segment_count += 1
                
                # 每10个片段打印一次进度
                if segment_count % 10 == 0:
                    logger.info(f"  ✅ 已处理 {segment_count} 个片段...")
                    if progress_callback:
                        progress_callback(60 + min(15, segment_count // 10), f"已处理 {segment_count} 个片段")
            
            transcribe_duration = time.time() - start_transcribe_time
            logger.info(f"⏰ 转录完成! 耗时: {transcribe_duration:.2f}秒")
            logger.info(f"📊 总片段数: {len(segments_list)}")
            
            # 构建与原Fast Whisper兼容的结果格式
            if progress_callback:
                progress_callback(75, "构建转录结果...")
            
            result = {
                'text': ' '.join([segment.text for segment in segments_list]),
                'segments': [],
                'language': info.language,
                'language_probability': info.language_probability,
                'duration': info.duration,
                'duration_after_vad': info.duration_after_vad
            }
            
            logger.info(f"🌍 检测到语言: {info.language} (置信度: {info.language_probability:.2f})")
            logger.info(f"⏱️ 音频总时长: {info.duration:.2f}秒")
            logger.info(f"🎤 有效语音时长: {info.duration_after_vad:.2f}秒")
            
            # 转换segments格式
            logger.info(f"🔄 正在转换片段格式...")
            for i, segment in enumerate(segments_list):
                result['segments'].append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text,
                    'avg_logprob': segment.avg_logprob,
                    'no_speech_prob': segment.no_speech_prob,
                    'words': [
                        {
                            'start': word.start,
                            'end': word.end,
                            'word': word.word,
                            'probability': word.probability
                        } for word in segment.words
                    ] if segment.words else []
                })
                
                # 每20个片段打印一次进度
                if (i + 1) % 20 == 0:
                    logger.info(f"  🔄 已转换 {i + 1}/{len(segments_list)} 个片段")
            
            if progress_callback:
                progress_callback(80, "语音识别完成")
            
            logger.info(f"✅ Faster-Whisper转录完成!")
            logger.info(f"📝 识别到的文本总长度: {len(result['text'])} 字符")
            
            logger.info(f"Faster-Whisper转录完成，识别到 {len(result['segments'])} 个片段")
            logger.info(f"检测到语言: {info.language} (置信度: {info.language_probability:.2f})")
            return result
            
        except Exception as e:
            error_msg = f"Faster-Whisper转录失败: {str(e)}"
            logger.info(f"❌ 转录失败: {error_msg}")
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _process_results(self, whisper_result: Dict) -> Tuple[str, List[Dict]]:
        """处理Whisper转录结果，优先生成SRT格式"""
        try:
            logger.info(f"🔄 正在处理转录结果...")
            
            # 处理分段结果
            segments = []
            total_segments = len(whisper_result.get('segments', []))
            logger.info(f"📊 需要处理 {total_segments} 个分段")
            
            for i, segment in enumerate(whisper_result.get('segments', [])):
                segment_data = {
                    'text': segment.get('text', '').strip(),
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0),
                    'confidence': segment.get('avg_logprob', 0),  # Whisper使用avg_logprob作为置信度
                    'timestamp': datetime.now().isoformat()
                }
                segments.append(segment_data)
                
                # 每50个分段打印一次进度
                if (i + 1) % 50 == 0 or (i + 1) == total_segments:
                    logger.info(f"  ✅ 已处理分段: {i + 1}/{total_segments}")
            
            logger.info(f"📝 开始生成SRT字幕文件...")
            # 基于segments生成SRT内容
            srt_content = self._generate_srt(segments)
            
            logger.info(f"✅ 结果处理完成!")
            logger.info(f"📊 分段数量: {len(segments)}")
            logger.info(f"📝 SRT内容长度: {len(srt_content)} 字符")
            
            logger.info(f"处理结果: 分段数量 {len(segments)}")
            return srt_content, segments
            
        except Exception as e:
            error_msg = f"处理转录结果失败: {str(e)}"
            logger.info(f"❌ 处理结果失败: {error_msg}")
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
                    
                    # srt_content += f"{i}\n"
                    srt_content += f"{self._format_srt_time(start_td)} --> {self._format_srt_time(end_td)}\n"
                    srt_content += f"{text}\n"
            
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
    
    def _srt_to_txt(self, srt_content: str) -> str:
        """从SRT内容提取纯文本，去掉时间轴"""
        try:
            lines = srt_content.strip().split('\n')
            text_lines = []
            
            for line in lines:
                line = line.strip()
                # 跳过序号行
                if line.isdigit():
                    continue
                # 跳过时间轴行
                if '-->' in line:
                    continue
                # 跳过空行
                if not line:
                    continue
                # 这是字幕文本行
                text_lines.append(line)
            
            # 将所有文本连接起来
            full_text = '\n'.join(text_lines)
            logger.info(f"从SRT提取文本，长度: {len(full_text)}")
            return full_text
            
        except Exception as e:
            error_msg = f"从SRT提取文本失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
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
            logger.info(f"开始Faster-Whisper音频转文字: {input_path.name}")
            start_time = datetime.now()
            
            if progress_callback:
                progress_callback(0, "初始化Faster-Whisper转换器...")
            
            # 加载模型
            if not self._load_model(progress_callback):
                return False, "Faster-Whisper模型加载失败", {}
            
            # 准备音频文件
            prepared_audio_path = self._prepare_audio(input_path, progress_callback)
            
            # 执行转录
            whisper_result = self._transcribe_audio(prepared_audio_path, progress_callback)
            
            if progress_callback:
                progress_callback(85, "处理转录结果...")
            
            # 处理结果，优先生成SRT
            srt_content, segments = self._process_results(whisper_result)
            
            if progress_callback:
                progress_callback(90, "保存结果文件...")
            
            logger.info(f"💾 正在保存结果文件...")
            
            # 保存SRT文件（优先生成）
            if output_srt_path:
                logger.info(f"📝 保存SRT字幕文件: {output_srt_path.name}")
                with open(output_srt_path, 'w', encoding='utf-8') as f:
                    f.write(srt_content)
                logger.info(f"✅ SRT文件保存成功: {len(srt_content)} 字符")
                logger.info(f"SRT字幕文件已保存: {output_srt_path}")
            
            # 基于SRT生成TXT文件（去掉时间轴）
            logger.info(f"📄 从SRT提取纯文本...")
            full_text = self._srt_to_txt(srt_content)
            logger.info(f"📝 保存TXT文本文件: {output_txt_path.name}")
            with open(output_txt_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            logger.info(f"✅ TXT文件保存成功: {len(full_text)} 字符")
            logger.info(f"TXT文本文件已保存: {output_txt_path}")
            
            # 清理临时文件
            if prepared_audio_path != input_path and prepared_audio_path.exists():
                prepared_audio_path.unlink()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            metadata = {
                'converter': 'faster-whisper',
                'model_size': self.whisper_config['model_size'],
                'language': whisper_result.get('language', self.whisper_config['language']),
                'language_probability': whisper_result.get('language_probability', 0),
                'compute_type': self.whisper_config['compute_type'],
                'duration_seconds': duration,
                'audio_duration': whisper_result.get('duration', 0),
                'audio_duration_after_vad': whisper_result.get('duration_after_vad', 0),
                'segments_count': len(segments),
                'srt_content_length': len(srt_content),
                'txt_content_length': len(full_text),
                'config_used': self.config.copy(),
                'timestamp': end_time.isoformat()
            }
            
            if progress_callback:
                progress_callback(100, "转换完成！")
            
            logger.info(f"🎉 Faster-Whisper转换全部完成!")
            logger.info(f"⏰ 总耗时: {duration:.2f}秒")
            logger.info(f"📊 处理统计:")
            logger.info(f"  - 识别片段: {len(segments)} 个")
            logger.info(f"  - SRT字幕: {len(srt_content)} 字符")
            logger.info(f"  - TXT文本: {len(full_text)} 字符")
            logger.info(f"  - 使用模型: {self.whisper_config['model_size']}")
            logger.info(f"  - 检测语言: {metadata.get('language', 'unknown')}")
            
            logger.info(f"Faster-Whisper转换完成: {output_txt_path.name}")
            logger.info(f"处理了 {len(segments)} 个片段")
            logger.info(f"SRT字幕长度: {len(srt_content)}, TXT文本长度: {len(full_text)}")
            
            return True, "转换完成", metadata
            
        except Exception as e:
            error_msg = f"Faster-Whisper转换失败: {str(e)}"
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
        if 'whisper_compute_type' in new_config:
            self.whisper_config['compute_type'] = new_config['whisper_compute_type']
        
        # 重新加载模型（如果关键参数改变）
        self.model = None
        logger.info(f"配置已更新: {new_config}")

def convert_mp3_to_txt_whisper(input_path: str, output_txt_path: str, 
                              output_srt_path: str = None, config: Dict = None, 
                              progress_callback=None) -> Tuple[bool, str, Dict]:
    """
    使用Faster-Whisper将音频转换为文字的便捷函数
    
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
    """获取可用的Faster-Whisper模型列表"""
    return ['tiny', 'tiny.en', 'base', 'base.en', 'small', 'small.en', 'medium', 'medium.en', 'large-v1', 'large-v2', 'large-v3']

def get_whisper_languages() -> List[str]:
    """获取支持的语言列表"""
    return ['zh', 'en', 'ja', 'ko', 'auto']

def get_whisper_compute_types() -> List[str]:
    """获取支持的计算类型列表"""
    return ['int8', 'int8_float16', 'int16', 'float16', 'float32']

def get_whisper_default_config() -> Dict:
    """获取Faster-Whisper默认配置"""
    return {
        'whisper_model_size': 'base',
        'whisper_language': 'zh',
        'whisper_device': 'cpu',
        'whisper_compute_type': 'int8',
        'whisper_verbose': False
    }

def save_whisper_conversion_log(input_file: str, output_file: str, metadata: Dict):
    """保存Faster-Whisper转换日志"""
    try:
        log_file = LOGS_DIR / "faster_whisper_conversions.json"
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'input_file': input_file,
            'output_file': output_file,
            'metadata': metadata,
            'converter': 'faster-whisper'
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
            
        logger.info(f"Faster-Whisper转换日志已保存: {log_file}")
        
    except Exception as e:
        logger.error(f"保存Faster-Whisper转换日志失败: {str(e)}")

if __name__ == "__main__":
    # 测试Faster-Whisper转换器
    import sys
    
    if len(sys.argv) < 3:
        logger.info("用法: python whisper_convert.py <input.mp3> <output.txt> [output.srt]")
        logger.info("使用Faster-Whisper进行音频转文字")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_txt_file = sys.argv[2]
    output_srt_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    def progress_callback(percent, message):
        logger.info(f"进度: {percent}% - {message}")
    
    success, message, metadata = convert_mp3_to_txt_whisper(
        input_file, output_txt_file, output_srt_file, 
        progress_callback=progress_callback
    )
    
    if success:
        logger.info(f"✅ {message}")
        logger.info(f"元数据: {json.dumps(metadata, indent=2, ensure_ascii=False)}")
    else:
        logger.info(f"❌ {message}")
        sys.exit(1) 