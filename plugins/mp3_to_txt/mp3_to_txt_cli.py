#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MP3 to TXT Command Line Interface
Converts MP3 audio files to TXT and SRT subtitle files using Whisper or Alibaba NLS
"""

import os
import sys
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from plugins.config import load_config_file, get_default_config, PROJECT_ROOT
from plugins.mp3_to_txt.mp3_to_txt import convert_mp3_to_txt, get_default_config as get_mp3_config

def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s' if verbose else '%(message)s',
        datefmt='%H:%M:%S'
    )

def create_progress_callback(verbose: bool = False, quiet: bool = False):
    """Create progress callback function"""
    if quiet:
        return None
    
    def progress_callback(percent: int, message: str):
        if verbose:
            print(f"[{percent:3d}%] {message}")
        else:
            # Simple progress bar
            bar_length = 40
            filled_length = int(bar_length * percent // 100)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            print(f"\rProgress: |{bar}| {percent:3d}% {message}", end='', flush=True)
            if percent == 100:
                print()  # New line when complete
    
    return progress_callback

def load_configuration(config_file: Optional[Path] = None) -> Dict:
    """Load configuration from file or use defaults"""
    try:
        if config_file and config_file.exists():
            config = load_config_file(config_file)
            print(f"✅ Loaded configuration from: {config_file}")
        else:
            config = get_default_config()
            if config_file:
                print(f"⚠️  Configuration file not found: {config_file}, using defaults")
            else:
                print("ℹ️  Using default configuration")
        
        return config.get('mp3_to_txt', get_mp3_config())
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        print("ℹ️  Using default configuration")
        return get_mp3_config()

def validate_input_file(input_path: Path) -> bool:
    """Validate input file"""
    if not input_path.exists():
        print(f"❌ Input file does not exist: {input_path}")
        return False
    
    if not input_path.is_file():
        print(f"❌ Input path is not a file: {input_path}")
        return False
    
    # Check file extension
    valid_extensions = {'.mp3', '.wav', '.flac', '.aac', '.m4a'}
    if input_path.suffix.lower() not in valid_extensions:
        print(f"⚠️  Warning: Input file extension '{input_path.suffix}' may not be supported")
        print(f"   Supported extensions: {', '.join(valid_extensions)}")
    
    return True

def ensure_output_directory(output_path: Path) -> bool:
    """Ensure output directory exists"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"❌ Error creating output directory: {e}")
        return False

def validate_engine(engine: str) -> bool:
    """Validate conversion engine"""
    supported_engines = {'whisper', 'alibaba_nls'}
    if engine not in supported_engines:
        print(f"❌ Unsupported engine: {engine}")
        print(f"   Supported engines: {', '.join(supported_engines)}")
        return False
    return True

def check_engine_dependencies(engine: str) -> bool:
    """Check if engine dependencies are available"""
    if engine == 'whisper':
        try:
            import faster_whisper
            return True
        except ImportError:
            print(f"❌ Whisper engine not available: faster-whisper not installed")
            print("   Install with: pip install faster-whisper")
            return False
    elif engine == 'alibaba_nls':
        try:
            import websocket
            return True
        except ImportError:
            print(f"❌ Alibaba NLS engine not available: websocket-client not installed")
            print("   Install with: pip install websocket-client")
            return False
    return True

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Convert MP3 audio files to TXT and SRT subtitle files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mp3_to_txt_cli.py input.mp3 output.txt --engine whisper
  python mp3_to_txt_cli.py input.mp3 output.txt output.srt --engine alibaba_nls
  python mp3_to_txt_cli.py input.mp3 output.txt --engine whisper --verbose
  python mp3_to_txt_cli.py input.mp3 output.txt --config config.yaml --quiet

Supported engines:
  whisper     - Uses Faster-Whisper for local speech recognition
  alibaba_nls - Uses Alibaba Cloud Natural Language Service
        """
    )
    
    # Required arguments
    parser.add_argument(
        'input_file',
        type=str,
        help='Input MP3 audio file path'
    )
    parser.add_argument(
        'output_txt_file',
        type=str,
        help='Output TXT text file path'
    )
    parser.add_argument(
        'output_srt_file',
        type=str,
        nargs='?',
        help='Output SRT subtitle file path (optional)'
    )
    
    # Engine selection
    parser.add_argument(
        '--engine',
        type=str,
        choices=['whisper', 'alibaba_nls'],
        default='whisper',
        help='Speech recognition engine to use (default: whisper)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--config',
        type=str,
        help='Configuration file path (YAML format)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress output'
    )
    
    # Whisper-specific options
    whisper_group = parser.add_argument_group('Whisper options')
    whisper_group.add_argument(
        '--model',
        type=str,
        choices=['tiny', 'base', 'small', 'medium', 'large-v1', 'large-v2', 'large-v3'],
        help='Whisper model size (default: base)'
    )
    whisper_group.add_argument(
        '--language',
        type=str,
        help='Language code (e.g., zh, en, ja, ko, auto for auto-detection)'
    )
    whisper_group.add_argument(
        '--device',
        type=str,
        choices=['cpu', 'cuda'],
        help='Computing device (default: cpu)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Validate arguments
    if args.verbose and args.quiet:
        print("❌ Error: --verbose and --quiet cannot be used together")
        sys.exit(1)
    
    # Validate engine
    if not validate_engine(args.engine):
        sys.exit(1)
    
    # Check engine dependencies
    if not check_engine_dependencies(args.engine):
        sys.exit(1)
    
    # Convert paths
    input_path = Path(args.input_file).resolve()
    output_txt_path = Path(args.output_txt_file).resolve()
    output_srt_path = Path(args.output_srt_file).resolve() if args.output_srt_file else None
    config_path = Path(args.config).resolve() if args.config else None
    
    # Validate input
    if not validate_input_file(input_path):
        sys.exit(1)
    
    # Ensure output directories exist
    if not ensure_output_directory(output_txt_path):
        sys.exit(1)
    if output_srt_path and not ensure_output_directory(output_srt_path):
        sys.exit(1)
    
    # Load configuration
    config = load_configuration(config_path)
    
    # Override configuration with command line arguments
    if args.model:
        config['whisper_model_size'] = args.model
    if args.language:
        config['whisper_language'] = args.language
    if args.device:
        config['whisper_device'] = args.device
    
    # Show configuration if verbose
    if args.verbose:
        print(f"📁 Input file: {input_path}")
        print(f"📁 Output TXT file: {output_txt_path}")
        if output_srt_path:
            print(f"📁 Output SRT file: {output_srt_path}")
        print(f"🤖 Engine: {args.engine}")
        print(f"⚙️  Configuration:")
        for key, value in config.items():
            if args.engine == 'whisper' and key.startswith('whisper_'):
                print(f"   {key}: {value}")
            elif args.engine == 'alibaba_nls' and not key.startswith('whisper_'):
                print(f"   {key}: {value}")
        print()
    
    # Create progress callback
    progress_callback = create_progress_callback(args.verbose, args.quiet)
    
    # Perform conversion
    try:
        if not args.quiet:
            print(f"🔄 Converting {input_path.name} to text using {args.engine}...")
        
        # Choose conversion function based on engine
        if args.engine == 'whisper':
            from plugins.mp3_to_txt.whisper_convert import convert_mp3_to_txt_whisper
            success, message, metadata = convert_mp3_to_txt_whisper(
                str(input_path),
                str(output_txt_path),
                str(output_srt_path) if output_srt_path else None,
                config=config,
                progress_callback=progress_callback
            )
        else:  # alibaba_nls
            success, message, metadata = convert_mp3_to_txt(
                str(input_path),
                str(output_txt_path),
                str(output_srt_path) if output_srt_path else None,
                config=config,
                progress_callback=progress_callback
            )
        
        if success:
            print(f"✅ {message}")
            
            if args.verbose and metadata:
                print(f"\n📊 Conversion Statistics:")
                print(f"   Processing time: {metadata.get('duration_seconds', 0):.2f} seconds")
                print(f"   Segments count: {metadata.get('segments_count', 0)}")
                print(f"   Text length: {metadata.get('txt_content_length', metadata.get('total_text_length', 0))} characters")
                
                if args.engine == 'whisper':
                    print(f"   Model used: {metadata.get('model_size', 'unknown')}")
                    print(f"   Language detected: {metadata.get('language', 'unknown')}")
                    print(f"   Audio duration: {metadata.get('audio_duration', 0):.2f} seconds")
            
            if not args.quiet:
                txt_size = output_txt_path.stat().st_size
                print(f"📁 TXT file: {output_txt_path} ({txt_size:,} bytes)")
                if output_srt_path and output_srt_path.exists():
                    srt_size = output_srt_path.stat().st_size
                    print(f"📁 SRT file: {output_srt_path} ({srt_size:,} bytes)")
        else:
            print(f"❌ {message}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Conversion interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()