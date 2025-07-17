# Sync Cut CLI Tools

Command Line Interface tools for the Sync Cut project, enabling MP4 to TXT/SRT conversion through various speech recognition engines.

## Overview

The CLI tools provide a complete pipeline for converting video files to text and subtitle files:

1. **MP4 → MP3**: Extract audio from video files with optimized settings
2. **MP3 → TXT/SRT**: Convert audio to text using Whisper or Alibaba NLS
3. **Complete Pipeline**: One-command conversion from MP4 to TXT/SRT

## Quick Start

### Windows Users (Recommended)

Use the simplified batch script:

```cmd
# Convert using Whisper engine (default)
start-cli.cmd demo.mp4

# Convert using Alibaba NLS engine  
start-cli.cmd demo.mp4 alibaba_nls

# Convert to specific output folder
start-cli.cmd demo.mp4 whisper output_folder
```

### Direct Python Usage

```bash
# Complete pipeline (MP4 → TXT/SRT)
python plugins/mp4_to_txt_cli.py input.mp4 output.txt output.srt --engine whisper

# MP4 to MP3 only
python plugins/mp4_to_mp3/mp4_to_mp3_cli.py input.mp4 output.mp3 --verbose

# MP3 to TXT only  
python plugins/mp3_to_txt/mp3_to_txt_cli.py input.mp3 output.txt --engine whisper
```

## CLI Tools

### 1. Complete Pipeline (`mp4_to_txt_cli.py`)

Converts MP4 videos directly to TXT and SRT files in one command.

**Usage:**
```bash
python plugins/mp4_to_txt_cli.py <input.mp4> <output.txt> [output.srt] [options]
```

**Options:**
- `--engine {whisper,alibaba_nls}` - Choose speech recognition engine
- `--config config.yaml` - Use custom configuration file
- `--keep-mp3` - Keep intermediate MP3 file after conversion
- `--temp-mp3 path` - Custom temporary MP3 file location
- `--verbose` - Detailed progress output
- `--quiet` - Suppress progress output
- `--bitrate 64k` - Audio bitrate for MP3 conversion
- `--model base` - Whisper model size (tiny/base/small/medium/large-v3)
- `--language zh` - Language code for recognition

**Examples:**
```bash
# Basic conversion with Whisper
python plugins/mp4_to_txt_cli.py demo.mp4 demo.txt demo.srt --engine whisper

# Keep intermediate MP3 file
python plugins/mp4_to_txt_cli.py demo.mp4 demo.txt --engine whisper --keep-mp3

# Use large model for better accuracy
python plugins/mp4_to_txt_cli.py demo.mp4 demo.txt --engine whisper --model large-v3

# Convert with Alibaba NLS
python plugins/mp4_to_txt_cli.py demo.mp4 demo.txt demo.srt --engine alibaba_nls
```

### 2. MP4 to MP3 Converter (`mp4_to_mp3_cli.py`)

Extracts audio from video files with optimized settings for speech recognition.

**Usage:**
```bash
python plugins/mp4_to_mp3/mp4_to_mp3_cli.py <input.mp4> <output.mp3> [options]
```

**Options:**
- `--bitrate 64k` - Audio bitrate (lower = smaller file)
- `--channels 1` - Audio channels (1=mono, 2=stereo)
- `--sample-rate 16000` - Audio sample rate in Hz
- `--normalize` - Normalize audio levels
- `--no-silence-removal` - Disable silence removal
- `--config config.yaml` - Use custom configuration
- `--verbose` - Detailed output
- `--quiet` - Suppress progress

**Examples:**
```bash
# Basic conversion
python plugins/mp4_to_mp3/mp4_to_mp3_cli.py demo.mp4 demo.mp3

# High quality stereo output
python plugins/mp4_to_mp3/mp4_to_mp3_cli.py demo.mp4 demo.mp3 --bitrate 192k --channels 2

# Optimized for speech recognition
python plugins/mp4_to_mp3/mp4_to_mp3_cli.py demo.mp4 demo.mp3 --bitrate 64k --channels 1 --normalize
```

### 3. MP3 to TXT Converter (`mp3_to_txt_cli.py`)

Converts audio files to text using Whisper or Alibaba NLS engines.

**Usage:**
```bash
python plugins/mp3_to_txt/mp3_to_txt_cli.py <input.mp3> <output.txt> [output.srt] [options]
```

**Options:**
- `--engine {whisper,alibaba_nls}` - Speech recognition engine
- `--model base` - Whisper model size
- `--language zh` - Language code (zh/en/ja/ko/auto)
- `--device cpu` - Computing device (cpu/cuda)
- `--config config.yaml` - Configuration file
- `--verbose` - Detailed output
- `--quiet` - Suppress progress

**Examples:**
```bash
# Convert with Whisper
python plugins/mp3_to_txt/mp3_to_txt_cli.py demo.mp3 demo.txt demo.srt --engine whisper

# Use large model for better accuracy
python plugins/mp3_to_txt/mp3_to_txt_cli.py demo.mp3 demo.txt --engine whisper --model large-v3

# Auto-detect language
python plugins/mp3_to_txt/mp3_to_txt_cli.py demo.mp3 demo.txt --engine whisper --language auto

# Use Alibaba NLS
python plugins/mp3_to_txt/mp3_to_txt_cli.py demo.mp3 demo.txt demo.srt --engine alibaba_nls
```

## Speech Recognition Engines

### Whisper (Recommended)

**Advantages:**
- Works offline (no internet required)
- Supports many languages
- Good accuracy for general use
- Free to use

**Requirements:**
- `faster-whisper` package
- `torch` and `torchaudio`
- Sufficient RAM (model dependent)

**Models:**
- `tiny` - Fastest, lowest accuracy (~39 MB)
- `base` - Good balance (~74 MB) 
- `small` - Better accuracy (~244 MB)
- `medium` - High accuracy (~769 MB)
- `large-v3` - Best accuracy (~1550 MB)

### Alibaba NLS

**Advantages:**
- Cloud-based processing
- Optimized for Chinese
- Professional quality
- Real-time processing

**Requirements:**
- Internet connection
- Valid Alibaba Cloud account
- NLS service activated
- Configuration in `config.yaml`

**Setup:**
1. Get credentials from [Alibaba Cloud Console](https://ram.console.aliyun.com/manage/ak)
2. Create NLS app at [NLS Portal](https://nls-portal.console.aliyun.com/applist) 
3. Configure in `config.yaml`:
```yaml
alibaba_nls:
  access_key_id: "YOUR_ACCESS_KEY_ID"
  access_key_secret: "YOUR_ACCESS_KEY_SECRET"
  app_key: "YOUR_APP_KEY"
```

## Configuration

### Default Configuration

The tools use sensible defaults, but you can customize via `config.yaml`:

```yaml
mp4_to_mp3:
  audio_bitrate: "64k"
  audio_channels: 1
  audio_sample_rate: 16000
  normalize_audio: true
  remove_silence: true

mp3_to_txt:
  whisper_model_size: "base"
  whisper_language: "zh"
  whisper_device: "cpu"
  sample_rate: 16000
  enable_punctuation_prediction: true

alibaba_nls:
  access_key_id: "YOUR_ACCESS_KEY_ID"
  access_key_secret: "YOUR_ACCESS_KEY_SECRET"
  app_key: "YOUR_APP_KEY"
```

### Command Line Overrides

All configuration options can be overridden via command line arguments:

```bash
# Override MP3 settings
python plugins/mp4_to_txt_cli.py demo.mp4 demo.txt --bitrate 128k

# Override Whisper settings  
python plugins/mp4_to_txt_cli.py demo.mp4 demo.txt --model large-v3 --language en
```

## Installation & Dependencies

### Automatic Installation (Windows)

The `start-cli.cmd` script automatically handles dependencies:

```cmd
start-cli.cmd demo.mp4
```

### Manual Installation

```bash
# Basic dependencies
pip install pyyaml requests

# For Whisper engine
pip install faster-whisper torch torchaudio

# For Alibaba NLS engine  
pip install websocket-client

# Optional: All dependencies
pip install -r plugins/requirements.txt
```

### Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate.bat  # Windows

pip install -r plugins/requirements.txt
```

## Troubleshooting

### Common Issues

**1. "Module not found" errors**
```bash
# Install missing dependencies
pip install faster-whisper websocket-client pyyaml
```

**2. Whisper model download fails**
```bash
# Check internet connection and disk space
# Models are downloaded to workspace/models/
```

**3. Alibaba NLS authentication fails**
```bash
# Check credentials in config.yaml
# Verify NLS service is activated
# Check network connectivity
```

**4. Out of memory errors**
```bash
# Use smaller Whisper model: --model tiny
# Close other applications
# Use CPU instead of GPU: --device cpu
```

### Verbose Output

For detailed debugging, use `--verbose`:

```bash
python plugins/mp4_to_txt_cli.py demo.mp4 demo.txt --verbose --engine whisper
```

### File Permissions

Ensure write permissions for output directories:

```bash
chmod 755 output_directory/  # Linux/Mac
```

## Performance Tips

### For Speed
- Use `--model tiny` or `--model base` for Whisper
- Use `--bitrate 64k` for smaller intermediate files
- Enable `--quiet` to reduce output overhead

### For Accuracy  
- Use `--model large-v3` for Whisper
- Use `--bitrate 128k` or higher for better audio quality
- Use `--normalize` to improve audio levels
- Specify correct `--language` instead of auto-detection

### For Batch Processing
- Use `--quiet` to suppress interactive output
- Keep intermediate MP3 files with `--keep-mp3` if processing multiple outputs
- Use configuration files to avoid repeating parameters

## File Formats

### Supported Input Formats
- **Video**: MP4, AVI, MOV, MKV, FLV, WMV
- **Audio**: MP3, WAV, FLAC, AAC, M4A

### Output Formats
- **TXT**: Plain text transcription
- **SRT**: SubRip subtitle format with timestamps

### Example Output

**TXT file:**
```
你好，欢迎使用 Sync Cut 工具。这是一个演示视频，展示了如何将视频转换为文字。
```

**SRT file:**
```
1
00:00:00,000 --> 00:00:03,500
你好，欢迎使用 Sync Cut 工具。

2
00:00:03,500 --> 00:00:07,200
这是一个演示视频，展示了如何将视频转换为文字。
```

## Integration

### Batch Scripts

Process multiple files:

```bash
#!/bin/bash
for file in *.mp4; do
    python plugins/mp4_to_txt_cli.py "$file" "${file%.mp4}.txt" --engine whisper --quiet
done
```

### Python Integration

Use in your own scripts:

```python
import subprocess

result = subprocess.run([
    'python', 'plugins/mp4_to_txt_cli.py',
    'input.mp4', 'output.txt', 
    '--engine', 'whisper', '--quiet'
], capture_output=True, text=True)

if result.returncode == 0:
    print("Conversion successful")
else:
    print(f"Error: {result.stderr}")
```

## License & Credits

Part of the Sync Cut project. See main repository for license information.

### Dependencies
- **Faster-Whisper**: High-performance Whisper implementation
- **PyDub**: Audio processing library
- **FFmpeg**: Audio/video processing backend
- **Alibaba Cloud SDK**: Cloud speech recognition services