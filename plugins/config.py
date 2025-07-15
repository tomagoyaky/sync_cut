"""
Configuration settings for Sync Cut application
"""

import os
import yaml
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
WORKSPACE_DIR = PROJECT_ROOT / 'workspace'
PLUGINS_DIR = PROJECT_ROOT / 'plugins'
TOOLS_DIR = PROJECT_ROOT / 'tools'

# Load configuration from YAML file
def load_config_file(config_path: Path = None):
    """Load configuration from YAML file"""
    if config_path is None:
        config_path = PROJECT_ROOT / 'config.yaml'
    
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    return {}

def save_config_file(config: dict, config_path: Path = None):
    """Save configuration to YAML file"""
    if config_path is None:
        config_path = PROJECT_ROOT / 'config.yaml'
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, ensure_ascii=False)

# Load configuration
_config = load_config_file()

# Application settings - from config.yaml or environment variables
APP_NAME = _config.get('app', {}).get('name', os.getenv('APP_NAME', 'Sync Cut'))
APP_VERSION = _config.get('app', {}).get('version', os.getenv('APP_VERSION', '1.0.0'))

# Web application settings - from config.yaml or environment variables
_web_config = _config.get('web_app', {})
DEBUG = _web_config.get('debug', os.getenv('DEBUG', 'False').lower() == 'true')
HOST = _web_config.get('host', os.getenv('HOST', '0.0.0.0'))
PORT = _web_config.get('port', int(os.getenv('PORT', 7000)))
MAX_CONTENT_LENGTH = _web_config.get('max_content_length', int(os.getenv('MAX_CONTENT_LENGTH', 10737418240)))

# File upload settings - from config.yaml
_file_upload_config = _config.get('file_upload', {})
ALLOWED_EXTENSIONS = set(_file_upload_config.get('allowed_extensions', [
    'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'mp3', 'wav', 'flac', 'aac'
]))

# MP4 to MP3 conversion settings - from config.yaml
_mp4_to_mp3_config = _config.get('mp4_to_mp3', {})
MP4_TO_MP3_CONFIG = {
    'audio_bitrate': _mp4_to_mp3_config.get('audio_bitrate', '64k'),
    'audio_codec': _mp4_to_mp3_config.get('audio_codec', 'mp3'),
    'audio_channels': _mp4_to_mp3_config.get('audio_channels', 1),
    'audio_sample_rate': _mp4_to_mp3_config.get('audio_sample_rate', 16000),
    'normalize_audio': _mp4_to_mp3_config.get('normalize_audio', True),
    'remove_silence': _mp4_to_mp3_config.get('remove_silence', True)
}

# MP3 to TXT conversion settings - from config.yaml
_mp3_to_txt_config = _config.get('mp3_to_txt', {})
MP3_TO_TXT_CONFIG = {
    'sample_rate': _mp3_to_txt_config.get('sample_rate', 16000),
    'format': _mp3_to_txt_config.get('format', 'pcm'),
    'enable_punctuation_prediction': _mp3_to_txt_config.get('enable_punctuation_prediction', True),
    'enable_inverse_text_normalization': _mp3_to_txt_config.get('enable_inverse_text_normalization', True),
    'enable_voice_detection': _mp3_to_txt_config.get('enable_voice_detection', True),
    'max_sentence_silence': _mp3_to_txt_config.get('max_sentence_silence', 800),
    'chunk_size': _mp3_to_txt_config.get('chunk_size', 8192),
    # Whisper specific settings
    'whisper_model_size': _mp3_to_txt_config.get('whisper_model_size', 'base'),
    'whisper_language': _mp3_to_txt_config.get('whisper_language', 'zh'),
    'whisper_device': _mp3_to_txt_config.get('whisper_device', 'cpu'),
    'whisper_verbose': _mp3_to_txt_config.get('whisper_verbose', False)
}

# Alibaba NLS settings - from config.yaml or environment variables
_alibaba_nls_config = _config.get('alibaba_nls', {})
ALIBABA_NLS_CONFIG = {
    'app_key': _alibaba_nls_config.get('app_key', os.getenv('ALIBABA_NLS_APP_KEY', '')),
    'access_key_id': _alibaba_nls_config.get('access_key_id', os.getenv('ALIBABA_ACCESS_KEY_ID', '')),
    'access_key_secret': _alibaba_nls_config.get('access_key_secret', os.getenv('ALIBABA_ACCESS_KEY_SECRET', '')),
    'region': _alibaba_nls_config.get('region', os.getenv('ALIBABA_NLS_REGION', 'cn-shanghai')),
    'endpoint': _alibaba_nls_config.get('endpoint', 'wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1')
}

# Workspace subdirectories - from config.yaml or defaults
_paths_config = _config.get('paths', {})
WORKSPACE_DIR = PROJECT_ROOT / _paths_config.get('workspace', 'workspace')
PLUGINS_DIR = PROJECT_ROOT / _paths_config.get('plugins', 'plugins')
TOOLS_DIR = PROJECT_ROOT / _paths_config.get('tools', 'plugins/mp4_to_mp3/tools')
MODELS_DIR = PROJECT_ROOT / _paths_config.get('models', 'workspace/models')
LOGS_DIR = PROJECT_ROOT / _paths_config.get('logs', 'workspace/logs')
UPLOAD_DIR = PROJECT_ROOT / _paths_config.get('upload', 'workspace/upload')
TMP_DIR = PROJECT_ROOT / _paths_config.get('tmp', 'workspace/tmp')
STATUS_DIR = PROJECT_ROOT / _paths_config.get('status', 'workspace/status')

def is_allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_default_config():
    """Get default configuration"""
    return {
        'app': {
            'name': APP_NAME,
            'version': APP_VERSION
        },
        'web_app': {
            'host': HOST,
            'port': PORT,
            'debug': DEBUG,
            'max_content_length': MAX_CONTENT_LENGTH
        },
        'file_upload': {
            'allowed_extensions': list(ALLOWED_EXTENSIONS)
        },
        'mp4_to_mp3': MP4_TO_MP3_CONFIG,
        'mp3_to_txt': MP3_TO_TXT_CONFIG,
        'alibaba_nls': ALIBABA_NLS_CONFIG,
        'paths': {
            'workspace': str(WORKSPACE_DIR.relative_to(PROJECT_ROOT)),
            'plugins': str(PLUGINS_DIR.relative_to(PROJECT_ROOT)),
            'tools': str(TOOLS_DIR.relative_to(PROJECT_ROOT)),
            'models': str(MODELS_DIR.relative_to(PROJECT_ROOT)),
            'logs': str(LOGS_DIR.relative_to(PROJECT_ROOT)),
            'upload': str(UPLOAD_DIR.relative_to(PROJECT_ROOT)),
            'tmp': str(TMP_DIR.relative_to(PROJECT_ROOT)),
            'status': str(STATUS_DIR.relative_to(PROJECT_ROOT))
        }
    }

def reload_config():
    """Reload configuration from file"""
    global _config, APP_NAME, APP_VERSION, DEBUG, HOST, PORT, MAX_CONTENT_LENGTH
    global ALLOWED_EXTENSIONS, MP4_TO_MP3_CONFIG, MP3_TO_TXT_CONFIG, ALIBABA_NLS_CONFIG
    global WORKSPACE_DIR, PLUGINS_DIR, TOOLS_DIR, MODELS_DIR, LOGS_DIR, UPLOAD_DIR, TMP_DIR, STATUS_DIR
    
    _config = load_config_file()
    
    # Reload all configuration values
    APP_NAME = _config.get('app', {}).get('name', os.getenv('APP_NAME', 'Sync Cut'))
    APP_VERSION = _config.get('app', {}).get('version', os.getenv('APP_VERSION', '1.0.0'))
    
    _web_config = _config.get('web_app', {})
    DEBUG = _web_config.get('debug', os.getenv('DEBUG', 'False').lower() == 'true')
    HOST = _web_config.get('host', os.getenv('HOST', '0.0.0.0'))
    PORT = _web_config.get('port', int(os.getenv('PORT', 7000)))
    MAX_CONTENT_LENGTH = _web_config.get('max_content_length', int(os.getenv('MAX_CONTENT_LENGTH', 10737418240)))
    
    _file_upload_config = _config.get('file_upload', {})
    ALLOWED_EXTENSIONS = set(_file_upload_config.get('allowed_extensions', [
        'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'mp3', 'wav', 'flac', 'aac'
    ]))
    
    _mp4_to_mp3_config = _config.get('mp4_to_mp3', {})
    MP4_TO_MP3_CONFIG = {
        'audio_bitrate': _mp4_to_mp3_config.get('audio_bitrate', '64k'),
        'audio_codec': _mp4_to_mp3_config.get('audio_codec', 'mp3'),
        'audio_channels': _mp4_to_mp3_config.get('audio_channels', 1),
        'audio_sample_rate': _mp4_to_mp3_config.get('audio_sample_rate', 16000),
        'normalize_audio': _mp4_to_mp3_config.get('normalize_audio', True),
        'remove_silence': _mp4_to_mp3_config.get('remove_silence', True)
    }
    
    _mp3_to_txt_config = _config.get('mp3_to_txt', {})
    MP3_TO_TXT_CONFIG = {
        'sample_rate': _mp3_to_txt_config.get('sample_rate', 16000),
        'format': _mp3_to_txt_config.get('format', 'pcm'),
        'enable_punctuation_prediction': _mp3_to_txt_config.get('enable_punctuation_prediction', True),
        'enable_inverse_text_normalization': _mp3_to_txt_config.get('enable_inverse_text_normalization', True),
        'enable_voice_detection': _mp3_to_txt_config.get('enable_voice_detection', True),
        'max_sentence_silence': _mp3_to_txt_config.get('max_sentence_silence', 800),
        'chunk_size': _mp3_to_txt_config.get('chunk_size', 8192)
    }
    
    _alibaba_nls_config = _config.get('alibaba_nls', {})
    ALIBABA_NLS_CONFIG = {
        'app_key': _alibaba_nls_config.get('app_key', os.getenv('ALIBABA_NLS_APP_KEY', '')),
        'access_key_id': _alibaba_nls_config.get('access_key_id', os.getenv('ALIBABA_ACCESS_KEY_ID', '')),
        'access_key_secret': _alibaba_nls_config.get('access_key_secret', os.getenv('ALIBABA_ACCESS_KEY_SECRET', '')),
        'region': _alibaba_nls_config.get('region', os.getenv('ALIBABA_NLS_REGION', 'cn-shanghai')),
        'endpoint': _alibaba_nls_config.get('endpoint', 'wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1')
    }
    
    _paths_config = _config.get('paths', {})
    WORKSPACE_DIR = PROJECT_ROOT / _paths_config.get('workspace', 'workspace')
    PLUGINS_DIR = PROJECT_ROOT / _paths_config.get('plugins', 'plugins')
    TOOLS_DIR = PROJECT_ROOT / _paths_config.get('tools', 'plugins/mp4_to_mp3/tools')
    MODELS_DIR = PROJECT_ROOT / _paths_config.get('models', 'workspace/models')
    LOGS_DIR = PROJECT_ROOT / _paths_config.get('logs', 'workspace/logs')
    UPLOAD_DIR = PROJECT_ROOT / _paths_config.get('upload', 'workspace/upload')
    TMP_DIR = PROJECT_ROOT / _paths_config.get('tmp', 'workspace/tmp')
    STATUS_DIR = PROJECT_ROOT / _paths_config.get('status', 'workspace/status') 