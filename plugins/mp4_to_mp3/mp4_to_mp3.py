"""
MP4 to MP3 Conversion Module
Converts MP4 video files to MP3 audio files with optimized settings for minimal file size
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pydub import AudioSegment
from pydub.silence import split_on_silence

from plugins.config import MP4_TO_MP3_CONFIG, TMP_DIR, LOGS_DIR
from plugins.common.ffmpeg_utils import FFmpegTools, get_video_info, extract_audio, validate_video_file

logger = logging.getLogger(__name__)

class MP4ToMP3Converter:
    """MP4 to MP3 converter with configurable parameters"""
    
    def __init__(self, config: Dict = None):
        """Initialize converter with configuration"""
        self.config = config or MP4_TO_MP3_CONFIG.copy()
        self.tmp_dir = TMP_DIR
        self.tmp_dir.mkdir(exist_ok=True)
        self.ffmpeg_tools = FFmpegTools()
        
    def convert(self, input_path: Path, output_path: Path, 
                progress_callback=None) -> Tuple[bool, str, Dict]:
        """
        Convert MP4 to MP3
        
        Args:
            input_path: Path to input MP4 file
            output_path: Path to output MP3 file
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (success, message, metadata)
        """
        try:
            logger.info(f"Starting MP4 to MP3 conversion: {input_path.name}")
            
            # Get file info
            original_size = input_path.stat().st_size
            start_time = datetime.now()
            
            if progress_callback:
                progress_callback(0, "Validating video file...")
            
            # Validate video file using FFmpeg tools
            is_valid, validation_msg = self.ffmpeg_tools.validate_video_file(input_path)
            if not is_valid:
                return False, f"Video validation failed: {validation_msg}", {}
            
            if progress_callback:
                progress_callback(10, "Getting video information...")
            
            # Get video info using FFmpeg
            video_info = self.ffmpeg_tools.get_video_info(input_path)
            
            # Create temporary audio file
            temp_audio_path = self.tmp_dir / f"temp_{input_path.stem}.mp3"
            
            if progress_callback:
                progress_callback(20, "Extracting audio with FFmpeg...")
            
            # Extract audio using FFmpeg tools
            success, extract_msg = self.ffmpeg_tools.extract_audio(
                input_path, temp_audio_path, self.config,
                lambda p, m: progress_callback(20 + p//3, m) if progress_callback else None
            )
            
            if not success:
                return False, f"Audio extraction failed: {extract_msg}", {}
            
            if progress_callback:
                progress_callback(60, "Post-processing audio...")
            
            # Load audio with pydub for additional processing
            audio_segment = AudioSegment.from_mp3(str(temp_audio_path))
            
            # Apply additional audio processing if configured
            processed_audio = self._process_audio(audio_segment, progress_callback)
            
            if progress_callback:
                progress_callback(80, "Saving final MP3 file...")
            
            # Export final MP3 with optimized settings
            processed_audio.export(
                str(output_path),
                format="mp3",
                bitrate=self.config['audio_bitrate'],
                parameters=[
                    "-ac", str(self.config['audio_channels']),
                    "-ar", str(self.config['audio_sample_rate'])
                ]
            )
            
            # Clean up temporary file
            if temp_audio_path.exists():
                temp_audio_path.unlink()
            
            # Get final file info
            final_size = output_path.stat().st_size
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            metadata = {
                'original_size': original_size,
                'final_size': final_size,
                'compression_ratio': round(final_size / original_size, 3),
                'duration_seconds': duration,
                'video_info': video_info,
                'config_used': self.config.copy(),
                'timestamp': end_time.isoformat()
            }
            
            if progress_callback:
                progress_callback(100, "Conversion completed!")
            
            logger.info(f"Conversion completed: {output_path.name}")
            logger.info(f"Size reduction: {original_size} -> {final_size} bytes "
                       f"({round((1 - final_size/original_size) * 100, 1)}% reduction)")
            
            return True, "Conversion completed successfully", metadata
            
        except Exception as e:
            error_msg = f"Conversion failed: {str(e)}"
            logger.error(error_msg)
            
            # Clean up on error
            if 'temp_audio_path' in locals() and temp_audio_path.exists():
                temp_audio_path.unlink()
            
            return False, error_msg, {}
    
    def _process_audio(self, audio: AudioSegment, progress_callback=None) -> AudioSegment:
        """Process audio according to configuration"""
        processed = audio
        
        # Convert to mono if configured
        if self.config['audio_channels'] == 1:
            processed = processed.set_channels(1)
        
        # Set sample rate
        processed = processed.set_frame_rate(self.config['audio_sample_rate'])
        
        # Normalize audio if configured
        if self.config.get('normalize_audio', False):
            if progress_callback:
                progress_callback(65, "Normalizing audio...")
            processed = processed.normalize()
        
        # Remove silence if configured
        if self.config.get('remove_silence', False):
            if progress_callback:
                progress_callback(70, "Removing silence...")
            processed = self._remove_silence(processed)
        
        return processed
    
    def _remove_silence(self, audio: AudioSegment) -> AudioSegment:
        """Remove silence from audio to reduce file size"""
        try:
            # Split audio on silence
            chunks = split_on_silence(
                audio,
                min_silence_len=1000,  # 1 second of silence
                silence_thresh=audio.dBFS - 16,  # 16dB below average
                keep_silence=200  # Keep 200ms of silence
            )
            
            # Concatenate chunks
            if chunks:
                return sum(chunks)
            else:
                return audio
                
        except Exception as e:
            logger.warning(f"Failed to remove silence: {str(e)}")
            return audio
    
    def get_video_info(self, video_path: Path) -> Dict:
        """Get video file information"""
        try:
            return self.ffmpeg_tools.get_video_info(video_path)
        except Exception as e:
            logger.error(f"Failed to get video info: {str(e)}")
            return {}
    
    def update_config(self, new_config: Dict):
        """Update converter configuration"""
        self.config.update(new_config)
        logger.info(f"Configuration updated: {new_config}")

def convert_mp4_to_mp3(input_path: str, output_path: str, 
                      config: Dict = None, progress_callback=None) -> Tuple[bool, str, Dict]:
    """
    Convenience function to convert MP4 to MP3
    
    Args:
        input_path: Path to input MP4 file
        output_path: Path to output MP3 file
        config: Optional configuration dictionary
        progress_callback: Optional progress callback function
        
    Returns:
        Tuple of (success, message, metadata)
    """
    converter = MP4ToMP3Converter(config)
    return converter.convert(Path(input_path), Path(output_path), progress_callback)

def get_default_config() -> Dict:
    """Get default MP4 to MP3 configuration"""
    return MP4_TO_MP3_CONFIG.copy()

def save_conversion_log(input_file: str, output_file: str, metadata: Dict):
    """Save conversion log to file"""
    try:
        log_file = LOGS_DIR / "mp4_to_mp3_conversions.json"
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'input_file': input_file,
            'output_file': output_file,
            'metadata': metadata
        }
        
        # Load existing logs
        logs = []
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        
        # Add new log entry
        logs.append(log_entry)
        
        # Save updated logs
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Conversion log saved: {log_file}")
        
    except Exception as e:
        logger.error(f"Failed to save conversion log: {str(e)}")

if __name__ == "__main__":
    # Test the converter
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python mp4_to_mp3.py <input.mp4> <output.mp3>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    def progress_callback(percent, message):
        print(f"Progress: {percent}% - {message}")
    
    success, message, metadata = convert_mp4_to_mp3(
        input_file, output_file, progress_callback=progress_callback
    )
    
    if success:
        print(f"✅ {message}")
        print(f"Metadata: {json.dumps(metadata, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ {message}")
        sys.exit(1) 