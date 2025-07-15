#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MP3 to TXT Conversion Module
Converts MP3 audio files to TXT and SRT subtitle files using Alibaba Cloud Intelligent Speech Interaction
Based on: https://help.aliyun.com/zh/isi/getting-started/start-here
"""

import os
import sys
import json
import logging
import time
import wave
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import base64
import hashlib

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
import hmac
import urllib.parse
import ssl

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import websocket
import requests

from pydub import AudioSegment

from plugins.config import MP3_TO_TXT_CONFIG, ALIBABA_NLS_CONFIG, TMP_DIR, LOGS_DIR

logger = logging.getLogger(__name__)

class AlibabaNLSRealTimeClient:
    """Alibaba Cloud NLS (Natural Language Service) Real-time Speech Recognition Client"""
    
    def __init__(self, config: Dict = None):
        """Initialize NLS client with configuration"""
        self.config = config or ALIBABA_NLS_CONFIG.copy()
        self.recognition_config = MP3_TO_TXT_CONFIG.copy()
        self.ws = None
        self.results = []
        self.sentence_results = []
        self.is_connected = False
        self.recognition_completed = False
        self.error_message = None
        self.task_id = None
        self.lock = threading.Lock()
        
        # Validate configuration
        if not self.config.get('access_key_id') or not self.config.get('access_key_secret'):
            raise ValueError("Alibaba Cloud access key ID and secret are required")
        if not self.config.get('app_key'):
            raise ValueError("Alibaba NLS app key is required")
    
    def _get_token(self) -> str:
        """Get access token from Alibaba Cloud STS"""
        try:
            # Use STS to get token
            url = "https://nls-meta.cn-shanghai.aliyuncs.com/pop/2018-05-18/tokens"
            
            # Build headers
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Build request data
            data = {
                'AccessKeyId': self.config['access_key_id'],
                'Action': 'CreateToken',
                'Version': '2019-02-28',
                'RegionId': 'cn-shanghai',
                'Format': 'JSON'
            }
            
            # Make request
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                token = result.get('Token', {}).get('Id')
                if token:
                    logger.info("Successfully obtained access token")
                    return token
                else:
                    logger.error(f"Failed to get token from response: {result}")
                    return None
            else:
                logger.error(f"Failed to get token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting token: {str(e)}")
            return None
    
    def _build_auth_url(self) -> str:
        """Build WebSocket URL with authentication"""
        # Get token
        token = self._get_token()
        if not token:
            # Fallback to direct access key authentication
            token = self.config['access_key_id']
        
        # Build WebSocket URL
        url = f"wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1"
        params = {
            'token': token,
            'appkey': self.config['app_key']
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{url}?{query_string}"
    
    def _on_message(self, ws, message):
        """Handle WebSocket messages"""
        try:
            data = json.loads(message)
            header = data.get('header', {})
            payload = data.get('payload', {})
            
            message_name = header.get('name', '')
            status = header.get('status', 0)
            
            if message_name == 'TranscriptionStarted':
                # Recognition started
                self.task_id = header.get('task_id')
                logger.info(f"Recognition started, task_id: {self.task_id}")
                
            elif message_name == 'SentenceBegin':
                # Sentence recognition started
                logger.debug("Sentence recognition started")
                
            elif message_name == 'TranscriptionResultChanged':
                # Intermediate result
                result = payload.get('result', '')
                if result:
                    logger.debug(f"Intermediate result: {result}")
                    
            elif message_name == 'SentenceEnd':
                # Final sentence result
                result = payload.get('result', '')
                if result:
                    with self.lock:
                        sentence_data = {
                            'text': result,
                            'confidence': payload.get('confidence', 0),
                            'begin_time': payload.get('begin_time', 0),
                            'end_time': payload.get('end_time', 0),
                            'timestamp': datetime.now().isoformat()
                        }
                        self.sentence_results.append(sentence_data)
                        logger.info(f"Sentence result: {result}")
                
            elif message_name == 'TranscriptionCompleted':
                # Recognition completed
                logger.info("Recognition completed")
                self.recognition_completed = True
                
            elif message_name == 'TaskFailed':
                # Error occurred
                error_code = status
                error_message = payload.get('message', 'Unknown error')
                self.error_message = f"Recognition failed (code: {error_code}): {error_message}"
                logger.error(self.error_message)
                self.recognition_completed = True
                
            elif status != 20000000:  # Success status code
                # Other error
                error_message = payload.get('message', f'Unknown error with status: {status}')
                self.error_message = f"Recognition error: {error_message}"
                logger.error(self.error_message)
                self.recognition_completed = True
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            self.error_message = f"Message processing error: {str(e)}"
            self.recognition_completed = True
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")
        self.error_message = f"WebSocket error: {str(error)}"
        self.recognition_completed = True
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        self.is_connected = False
        if not self.recognition_completed:
            self.recognition_completed = True
    
    def _on_open(self, ws):
        """Handle WebSocket open"""
        logger.info("WebSocket connection opened")
        self.is_connected = True
        
        # Send start recognition message
        start_message = {
            "header": {
                "message_id": str(int(time.time() * 1000)),
                "name": "StartTranscription",
                "namespace": "SpeechTranscriber"
            },
            "payload": {
                "format": self.recognition_config['format'],
                "sample_rate": self.recognition_config['sample_rate'],
                "enable_punctuation_prediction": self.recognition_config['enable_punctuation_prediction'],
                "enable_inverse_text_normalization": self.recognition_config['enable_inverse_text_normalization'],
                "enable_voice_detection": self.recognition_config['enable_voice_detection'],
                "max_sentence_silence": self.recognition_config['max_sentence_silence'],
                "enable_words": False,
                "enable_sample_rate_adaptive": True
            }
        }
        
        try:
            ws.send(json.dumps(start_message))
            logger.info("Start recognition message sent")
        except Exception as e:
            logger.error(f"Failed to send start message: {str(e)}")
            self.error_message = f"Failed to send start message: {str(e)}"
            self.recognition_completed = True
    
    def recognize_audio(self, audio_data: bytes, progress_callback=None) -> Tuple[bool, str, List[Dict]]:
        """
        Recognize speech from audio data
        
        Args:
            audio_data: PCM audio data
            progress_callback: Optional progress callback function
            
        Returns:
            Tuple of (success, message, results)
        """
        try:
            logger.info("Starting real-time speech recognition")
            
            # Reset state
            self.results = []
            self.sentence_results = []
            self.recognition_completed = False
            self.error_message = None
            self.task_id = None
            
            if progress_callback:
                progress_callback(0, "Connecting to Alibaba NLS service...")
            
            # Build WebSocket URL
            url = self._build_auth_url()
            
            # Create WebSocket connection
            self.ws = websocket.WebSocketApp(
                url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # Start WebSocket in a separate thread
            ws_thread = threading.Thread(
                target=self.ws.run_forever,
                kwargs={'sslopt': {"cert_reqs": ssl.CERT_NONE}}
            )
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for connection
            connection_timeout = 15
            start_time = time.time()
            while not self.is_connected and time.time() - start_time < connection_timeout:
                if self.error_message:
                    return False, self.error_message, []
                time.sleep(0.1)
            
            if not self.is_connected:
                return False, "Failed to connect to Alibaba NLS service", []
            
            if progress_callback:
                progress_callback(20, "Sending audio data...")
            
            # Send audio data in chunks
            chunk_size = self.recognition_config['chunk_size']
            total_chunks = len(audio_data) // chunk_size + 1
            
            for i in range(0, len(audio_data), chunk_size):
                if self.error_message:
                    break
                    
                chunk = audio_data[i:i + chunk_size]
                
                # Send audio chunk
                audio_message = {
                    "header": {
                        "message_id": str(int(time.time() * 1000)),
                        "name": "RunTranscription",
                        "namespace": "SpeechTranscriber"
                    },
                    "payload": {
                        "audio": base64.b64encode(chunk).decode('utf-8')
                    }
                }
                
                try:
                    self.ws.send(json.dumps(audio_message))
                    
                    # Update progress
                    if progress_callback:
                        progress = 20 + (i // chunk_size) * 60 // total_chunks
                        progress_callback(progress, f"Processing audio chunk {i//chunk_size + 1}/{total_chunks}")
                    
                    # Small delay to avoid overwhelming the service
                    time.sleep(0.05)
                    
                except Exception as e:
                    logger.error(f"Failed to send audio chunk: {str(e)}")
                    self.error_message = f"Failed to send audio data: {str(e)}"
                    break
            
            if progress_callback:
                progress_callback(80, "Finalizing recognition...")
            
            # Send stop message
            stop_message = {
                "header": {
                    "message_id": str(int(time.time() * 1000)),
                    "name": "StopTranscription",
                    "namespace": "SpeechTranscriber"
                }
            }
            
            try:
                self.ws.send(json.dumps(stop_message))
                logger.info("Stop recognition message sent")
            except Exception as e:
                logger.error(f"Failed to send stop message: {str(e)}")
            
            # Wait for completion
            completion_timeout = 30
            start_time = time.time()
            while not self.recognition_completed and time.time() - start_time < completion_timeout:
                time.sleep(0.1)
            
            if progress_callback:
                progress_callback(100, "Recognition completed!")
            
            # Close connection
            try:
                self.ws.close()
            except:
                pass
            
            if self.error_message:
                return False, self.error_message, []
            
            if not self.sentence_results:
                return False, "No recognition results received", []
            
            return True, "Recognition completed successfully", self.sentence_results
            
        except Exception as e:
            error_msg = f"Recognition failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, []
        finally:
            # Ensure WebSocket is closed
            if self.ws:
                try:
                    self.ws.close()
                except:
                    pass

class MP3ToTXTConverter:
    """MP3 to TXT converter using Alibaba Cloud NLS"""
    
    def __init__(self, config: Dict = None):
        """Initialize converter with configuration"""
        self.config = config or MP3_TO_TXT_CONFIG.copy()
        self.nls_client = AlibabaNLSRealTimeClient()
        self.tmp_dir = TMP_DIR
        self.tmp_dir.mkdir(exist_ok=True)
    
    def convert(self, input_path: Path, output_txt_path: Path, 
                output_srt_path: Path = None, progress_callback=None) -> Tuple[bool, str, Dict]:
        """
        Convert MP3 to TXT and optionally SRT
        
        Args:
            input_path: Path to input MP3 file
            output_txt_path: Path to output TXT file
            output_srt_path: Optional path to output SRT file
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (success, message, metadata)
        """
        try:
            logger.info(f"Starting MP3 to TXT conversion: {input_path.name}")
            
            start_time = datetime.now()
            
            if progress_callback:
                progress_callback(0, "Loading audio file...")
            
            # Load and prepare audio
            audio_data = self._prepare_audio(input_path, progress_callback)
            
            if progress_callback:
                progress_callback(30, "Starting speech recognition...")
            
            # Perform speech recognition
            success, message, results = self.nls_client.recognize_audio(
                audio_data, 
                lambda p, m: progress_callback(30 + p * 0.6, m) if progress_callback else None
            )
            
            if not success:
                return False, message, {}
            
            if progress_callback:
                progress_callback(90, "Saving results...")
            
            # Process results
            full_text = self._process_results(results)
            
            # Save TXT file
            with open(output_txt_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            # Save SRT file if requested
            if output_srt_path:
                srt_content = self._generate_srt(results)
                with open(output_srt_path, 'w', encoding='utf-8') as f:
                    f.write(srt_content)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            metadata = {
                'duration_seconds': duration,
                'results_count': len(results),
                'total_text_length': len(full_text),
                'sentences_count': len(results),
                'config_used': self.config.copy(),
                'timestamp': end_time.isoformat()
            }
            
            if progress_callback:
                progress_callback(100, "Conversion completed!")
            
            logger.info(f"Conversion completed: {output_txt_path.name}")
            logger.info(f"Processed {len(results)} sentences, total text length: {len(full_text)}")
            
            return True, "Conversion completed successfully", metadata
            
        except Exception as e:
            error_msg = f"Conversion failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}
    
    def _prepare_audio(self, input_path: Path, progress_callback=None) -> bytes:
        """Prepare audio for recognition"""
        if progress_callback:
            progress_callback(10, "Converting audio format...")
        
        # Load audio file
        audio = AudioSegment.from_mp3(str(input_path))
        
        # Convert to required format for NLS
        audio = audio.set_frame_rate(self.config['sample_rate'])
        audio = audio.set_channels(1)  # Mono
        audio = audio.set_sample_width(2)  # 16-bit
        
        if progress_callback:
            progress_callback(20, "Extracting audio data...")
        
        # Export to PCM format
        return audio.raw_data
    
    def _process_results(self, results: List[Dict]) -> str:
        """Process recognition results into full text"""
        full_text = ""
        
        # Sort results by begin_time if available
        sorted_results = sorted(results, key=lambda x: x.get('begin_time', 0))
        
        for result in sorted_results:
            text = result.get('text', '').strip()
            if text:
                full_text += text + " "
        
        return full_text.strip()
    
    def _generate_srt(self, results: List[Dict]) -> str:
        """Generate SRT subtitle format"""
        srt_content = ""
        
        # Sort results by begin_time
        sorted_results = sorted(results, key=lambda x: x.get('begin_time', 0))
        
        for i, result in enumerate(sorted_results, 1):
            text = result.get('text', '').strip()
            if text:
                # Use actual timestamps from NLS if available
                begin_time = result.get('begin_time', (i-1) * 5000)  # milliseconds
                end_time = result.get('end_time', i * 5000)  # milliseconds
                
                # Convert to timedelta
                start_td = timedelta(milliseconds=begin_time)
                end_td = timedelta(milliseconds=end_time)
                
                srt_content += f"{i}\n"
                srt_content += f"{self._format_srt_time(start_td)} --> {self._format_srt_time(end_td)}\n"
                srt_content += f"{text}\n\n"
        
        return srt_content
    
    def _format_srt_time(self, td: timedelta) -> str:
        """Format timedelta for SRT format"""
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        milliseconds = int((td.total_seconds() % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def update_config(self, new_config: Dict):
        """Update converter configuration"""
        self.config.update(new_config)
        logger.info(f"Configuration updated: {new_config}")

def convert_mp3_to_txt(input_path: str, output_txt_path: str, 
                      output_srt_path: str = None, config: Dict = None, 
                      progress_callback=None) -> Tuple[bool, str, Dict]:
    """
    Convenience function to convert MP3 to TXT
    
    Args:
        input_path: Path to input MP3 file
        output_txt_path: Path to output TXT file
        output_srt_path: Optional path to output SRT file
        config: Optional configuration dictionary
        progress_callback: Optional progress callback function
        
    Returns:
        Tuple of (success, message, metadata)
    """
    converter = MP3ToTXTConverter(config)
    return converter.convert(
        Path(input_path), 
        Path(output_txt_path), 
        Path(output_srt_path) if output_srt_path else None,
        progress_callback
    )

def get_default_config() -> Dict:
    """Get default MP3 to TXT configuration"""
    return MP3_TO_TXT_CONFIG.copy()

def save_conversion_log(input_file: str, output_file: str, metadata: Dict):
    """Save conversion log to file"""
    try:
        log_file = LOGS_DIR / "mp3_to_txt_conversions.json"
        
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
        print("Usage: python mp3_to_txt.py <input.mp3> <output.txt> [output.srt]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_txt_file = sys.argv[2]
    output_srt_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    def progress_callback(percent, message):
        print(f"Progress: {percent}% - {message}")
    
    success, message, metadata = convert_mp3_to_txt(
        input_file, output_txt_file, output_srt_file, 
        progress_callback=progress_callback
    )
    
    if success:
        print(f"✅ {message}")
        print(f"Metadata: {json.dumps(metadata, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ {message}")
        sys.exit(1) 