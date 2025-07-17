#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MP4 to MP3 Command Line Interface
Converts MP4 video files to MP3 audio files with configurable options
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
from plugins.mp4_to_mp3.mp4_to_mp3 import convert_mp4_to_mp3, get_default_config as get_mp4_config

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
        
        return config.get('mp4_to_mp3', get_mp4_config())
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        print("ℹ️  Using default configuration")
        return get_mp4_config()

def validate_input_file(input_path: Path) -> bool:
    """Validate input file"""
    if not input_path.exists():
        print(f"❌ Input file does not exist: {input_path}")
        return False
    
    if not input_path.is_file():
        print(f"❌ Input path is not a file: {input_path}")
        return False
    
    # Check file extension
    valid_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
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

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Convert MP4 video files to MP3 audio files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mp4_to_mp3_cli.py input.mp4 output.mp3
  python mp4_to_mp3_cli.py input.mp4 output.mp3 --verbose
  python mp4_to_mp3_cli.py input.mp4 output.mp3 --config config.yaml --quiet
  python mp4_to_mp3_cli.py input.mp4 output.mp3 --bitrate 128k --channels 2
        """
    )
    
    # Required arguments
    parser.add_argument(
        'input_file',
        type=str,
        help='Input MP4 video file path'
    )
    parser.add_argument(
        'output_file',
        type=str,
        help='Output MP3 audio file path'
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
    parser.add_argument(
        '--bitrate',
        type=str,
        help='Audio bitrate (e.g., 64k, 128k, 192k)'
    )
    parser.add_argument(
        '--channels',
        type=int,
        choices=[1, 2],
        help='Number of audio channels (1=mono, 2=stereo)'
    )
    parser.add_argument(
        '--sample-rate',
        type=int,
        help='Audio sample rate in Hz (e.g., 16000, 22050, 44100)'
    )
    parser.add_argument(
        '--normalize',
        action='store_true',
        help='Normalize audio levels'
    )
    parser.add_argument(
        '--no-silence-removal',
        action='store_true',
        help='Disable silence removal'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Validate arguments
    if args.verbose and args.quiet:
        print("❌ Error: --verbose and --quiet cannot be used together")
        sys.exit(1)
    
    # Convert paths
    input_path = Path(args.input_file).resolve()
    output_path = Path(args.output_file).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    
    # Validate input
    if not validate_input_file(input_path):
        sys.exit(1)
    
    # Ensure output directory exists
    if not ensure_output_directory(output_path):
        sys.exit(1)
    
    # Load configuration
    config = load_configuration(config_path)
    
    # Override configuration with command line arguments
    if args.bitrate:
        config['audio_bitrate'] = args.bitrate
    if args.channels:
        config['audio_channels'] = args.channels
    if args.sample_rate:
        config['audio_sample_rate'] = args.sample_rate
    if args.normalize:
        config['normalize_audio'] = True
    if args.no_silence_removal:
        config['remove_silence'] = False
    
    # Show configuration if verbose
    if args.verbose:
        print(f"📁 Input file: {input_path}")
        print(f"📁 Output file: {output_path}")
        print(f"⚙️  Configuration:")
        for key, value in config.items():
            print(f"   {key}: {value}")
        print()
    
    # Create progress callback
    progress_callback = create_progress_callback(args.verbose, args.quiet)
    
    # Perform conversion
    try:
        if not args.quiet:
            print(f"🔄 Converting {input_path.name} to {output_path.name}...")
        
        success, message, metadata = convert_mp4_to_mp3(
            str(input_path),
            str(output_path),
            config=config,
            progress_callback=progress_callback
        )
        
        if success:
            print(f"✅ {message}")
            
            if args.verbose and metadata:
                print(f"\n📊 Conversion Statistics:")
                print(f"   Original size: {metadata.get('original_size', 0):,} bytes")
                print(f"   Final size: {metadata.get('final_size', 0):,} bytes")
                print(f"   Compression ratio: {metadata.get('compression_ratio', 0):.3f}")
                print(f"   Processing time: {metadata.get('duration_seconds', 0):.2f} seconds")
                
                if 'video_info' in metadata:
                    video_info = metadata['video_info']
                    print(f"   Video duration: {video_info.get('duration', 0):.2f} seconds")
                    print(f"   Video resolution: {video_info.get('width', 0)}x{video_info.get('height', 0)}")
            
            if not args.quiet:
                file_size = output_path.stat().st_size
                print(f"📁 Output file: {output_path} ({file_size:,} bytes)")
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