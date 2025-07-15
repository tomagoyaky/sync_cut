#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FFmpeg Utilities
Provides FFmpeg-based video and audio processing tools
"""

import os
import subprocess
import logging
import platform
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import json
import shlex

logger = logging.getLogger(__name__)

class FFmpegTools:
    """FFmpeg tools wrapper"""
    
    def __init__(self):
        """Initialize FFmpeg tools"""
        self.system = platform.system().lower()
        
        if self.system == "windows":
            # Windows: Use bundled FFmpeg tools
            project_root = Path(__file__).parent.parent
            self.tools_dir = project_root / "tools"
            self.ffmpeg_path = self.tools_dir / "ffmpeg.exe"
            self.ffprobe_path = self.tools_dir / "ffprobe.exe"
            
            # Check if tools exist
            if not self.ffmpeg_path.exists():
                raise FileNotFoundError(f"FFmpeg not found at {self.ffmpeg_path}")
            if not self.ffprobe_path.exists():
                raise FileNotFoundError(f"FFprobe not found at {self.ffprobe_path}")
                
        elif self.system == "darwin":
            # macOS: Use system PATH
            self.ffmpeg_path = self._find_system_executable("ffmpeg")
            self.ffprobe_path = self._find_system_executable("ffprobe")
            
            if not self.ffmpeg_path:
                raise FileNotFoundError("FFmpeg not found in system PATH. Please install with: brew install ffmpeg")
            if not self.ffprobe_path:
                raise FileNotFoundError("FFprobe not found in system PATH. Please install with: brew install ffmpeg")
                
        else:
            # Linux and other systems: Use system PATH
            self.ffmpeg_path = self._find_system_executable("ffmpeg")
            self.ffprobe_path = self._find_system_executable("ffprobe")
            
            if not self.ffmpeg_path:
                raise FileNotFoundError("FFmpeg not found in system PATH. Please install FFmpeg.")
            if not self.ffprobe_path:
                raise FileNotFoundError("FFprobe not found in system PATH. Please install FFmpeg.")
    
    def _find_system_executable(self, name: str) -> Optional[str]:
        """Find executable in system PATH"""
        try:
            result = subprocess.run(
                ["which", name] if self.system != "windows" else ["where", name],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip().split('\n')[0]
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def get_video_info(self, video_path: Path) -> Dict:
        """
        Get video file information using ffprobe
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary containing video information
        """
        try:
            cmd = [
                str(self.ffprobe_path),
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(video_path)
            ]
            
            # Print the command before execution
            logger.info(f"执行 FFprobe 命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            probe_data = json.loads(result.stdout)
            
            # Extract video and audio stream info
            video_stream = None
            audio_stream = None
            
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'video' and video_stream is None:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and audio_stream is None:
                    audio_stream = stream
            
            format_info = probe_data.get('format', {})
            
            info = {
                'duration': float(format_info.get('duration', 0)),
                'size': int(format_info.get('size', 0)),
                'bitrate': int(format_info.get('bit_rate', 0)),
                'format_name': format_info.get('format_name', ''),
                'filename': video_path.name,
                'has_video': video_stream is not None,
                'has_audio': audio_stream is not None
            }
            
            if video_stream:
                info.update({
                    'video_codec': video_stream.get('codec_name', ''),
                    'video_width': int(video_stream.get('width', 0)),
                    'video_height': int(video_stream.get('height', 0)),
                    'video_fps': self._parse_fps(video_stream.get('r_frame_rate', '0/1')),
                    'video_bitrate': int(video_stream.get('bit_rate', 0)) if video_stream.get('bit_rate') else 0
                })
            
            if audio_stream:
                info.update({
                    'audio_codec': audio_stream.get('codec_name', ''),
                    'audio_sample_rate': int(audio_stream.get('sample_rate', 0)),
                    'audio_channels': int(audio_stream.get('channels', 0)),
                    'audio_bitrate': int(audio_stream.get('bit_rate', 0)) if audio_stream.get('bit_rate') else 0
                })
            
            logger.info(f"Video info retrieved: {video_path.name}")
            return info
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe failed: {e.stderr}")
            return {}
        except Exception as e:
            logger.error(f"Failed to get video info: {str(e)}")
            return {}
    
    def extract_audio(self, video_path: Path, output_path: Path, 
                     audio_config: Dict, progress_callback=None) -> Tuple[bool, str]:
        """
        Extract audio from video using FFmpeg
        
        Args:
            video_path: Path to input video file
            output_path: Path to output audio file
            audio_config: Audio configuration parameters
            progress_callback: Optional progress callback function
            
        Returns:
            Tuple of (success, message)
        """
        try:
            logger.info(f"Extracting audio from: {video_path.name}")
            
            if progress_callback:
                progress_callback(0, "Preparing audio extraction...")
            
            # Build FFmpeg command
            cmd = [
                str(self.ffmpeg_path),
                "-i", str(video_path),
                "-vn",  # No video
                "-acodec", "libmp3lame",  # MP3 codec
                "-ab", audio_config.get('audio_bitrate', '8k'),
                "-ac", str(audio_config.get('audio_channels', 1)),
                "-ar", str(audio_config.get('audio_sample_rate', 8000)),
                "-y",  # Overwrite output file
                str(output_path)
            ]
            
            # Add additional parameters if configured
            if audio_config.get('normalize_audio', False):
                # Add audio normalization filter
                cmd.insert(-2, "-af")
                cmd.insert(-2, "loudnorm")
            
            if progress_callback:
                progress_callback(20, "Starting audio extraction...")
            
            # Get video duration for progress calculation
            video_info = self.get_video_info(video_path)
            total_duration = video_info.get('duration', 0)
            
            # Print the command before execution
            logger.info(f"执行 FFmpeg 命令: {' '.join(cmd)}")
            
            # Run FFmpeg with progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            
            # Monitor progress
            progress = 20
            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                
                if output and progress_callback:
                    # Parse time progress from FFmpeg output
                    if 'time=' in output:
                        try:
                            time_str = output.split('time=')[1].split()[0]
                            current_time = self._parse_time(time_str)
                            if total_duration > 0:
                                progress = min(20 + int((current_time / total_duration) * 60), 80)
                                progress_callback(progress, f"Extracting audio... {current_time:.1f}s/{total_duration:.1f}s")
                        except:
                            pass
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code == 0:
                if progress_callback:
                    progress_callback(100, "Audio extraction completed!")
                
                logger.info(f"Audio extracted successfully: {output_path.name}")
                return True, "Audio extraction completed successfully"
            else:
                error_output = process.stderr.read()
                error_msg = f"FFmpeg failed with return code {return_code}: {error_output}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Audio extraction failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def validate_video_file(self, video_path: Path) -> Tuple[bool, str]:
        """
        Validate video file using FFprobe
        
        Args:
            video_path: Path to video file
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if not video_path.exists():
                return False, "Video file does not exist"
            
            if video_path.stat().st_size == 0:
                return False, "Video file is empty"
            
            info = self.get_video_info(video_path)
            
            if not info:
                return False, "Unable to read video file information"
            
            if info.get('duration', 0) <= 0:
                return False, "Video has no duration"
            
            if not info.get('has_audio', False):
                return False, "Video has no audio track"
            
            return True, "Video file is valid"
            
        except Exception as e:
            return False, f"Video validation failed: {str(e)}"
    
    def _parse_fps(self, fps_str: str) -> float:
        """Parse FPS from fraction string"""
        try:
            if '/' in fps_str:
                num, den = fps_str.split('/')
                return float(num) / float(den)
            else:
                return float(fps_str)
        except:
            return 0.0
    
    def _parse_time(self, time_str: str) -> float:
        """Parse time string to seconds"""
        try:
            # Format: HH:MM:SS.mmm
            parts = time_str.split(':')
            if len(parts) == 3:
                hours = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            return 0.0
        except:
            return 0.0

# Convenience functions
def get_video_info(video_path: str) -> Dict:
    """
    Convenience function to get video information
    
    Args:
        video_path: Path to video file
        
    Returns:
        Dictionary containing video information
    """
    tools = FFmpegTools()
    return tools.get_video_info(Path(video_path))

def extract_audio(video_path: str, output_path: str, audio_config: Dict, 
                 progress_callback=None) -> Tuple[bool, str]:
    """
    Convenience function to extract audio from video
    
    Args:
        video_path: Path to input video file
        output_path: Path to output audio file
        audio_config: Audio configuration parameters
        progress_callback: Optional progress callback function
        
    Returns:
        Tuple of (success, message)
    """
    tools = FFmpegTools()
    return tools.extract_audio(
        Path(video_path), Path(output_path), audio_config, progress_callback
    )

def validate_video_file(video_path: str) -> Tuple[bool, str]:
    """
    Convenience function to validate video file
    
    Args:
        video_path: Path to video file
        
    Returns:
        Tuple of (is_valid, message)
    """
    tools = FFmpegTools()
    return tools.validate_video_file(Path(video_path)) 