#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MP4 to TXT Command Line Interface
Complete workflow: MP4 → MP3 → TXT/SRT conversion
Supports both Whisper and Alibaba NLS engines
"""

import os
import sys
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from plugins.config import load_config_file, get_default_config, PROJECT_ROOT, TMP_DIR
from plugins.mp4_to_mp3.mp4_to_mp3 import convert_mp4_to_mp3, get_default_config as get_mp4_config
from plugins.mp3_to_txt.mp3_to_txt import convert_mp3_to_txt, get_default_config as get_mp3_config

def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s' if verbose else '%(message)s',
        datefmt='%H:%M:%S'
    )

def create_progress_callback(verbose: bool = False, quiet: bool = False, stage: str = ""):
    """Create progress callback function"""
    if quiet:
        return None
    
    def progress_callback(percent: int, message: str):
        stage_prefix = f"[{stage}] " if stage else ""
        if verbose:
            print(f"{stage_prefix}[{percent:3d}%] {message}")
        else:
            # Simple progress bar
            bar_length = 30
            filled_length = int(bar_length * percent // 100)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            print(f"\r{stage_prefix}|{bar}| {percent:3d}% {message}", end='', flush=True)
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
        
        return config
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        print("ℹ️  Using default configuration")
        return get_default_config()

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

def generate_temp_mp3_path(input_path: Path, output_dir: Optional[Path] = None) -> Path:
    """Generate temporary MP3 file path"""
    if output_dir:
        temp_dir = output_dir
    else:
        temp_dir = TMP_DIR
    
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_filename = f"{input_path.stem}_temp.mp3"
    return temp_dir / temp_filename

def cleanup_temp_file(temp_path: Path, keep_temp: bool = False):
    """Clean up temporary file"""
    if not keep_temp and temp_path and temp_path.exists():
        try:
            temp_path.unlink()
        except Exception as e:
            print(f"⚠️  Warning: Could not delete temporary file {temp_path}: {e}")

def convert_mp4_to_txt_pipeline(
    input_path: Path,
    output_txt_path: Path,
    output_srt_path: Optional[Path],
    engine: str,
    config: Dict,
    keep_mp3: bool = False,
    temp_mp3_path: Optional[Path] = None,
    verbose: bool = False,
    quiet: bool = False
) -> Tuple[bool, str, Dict]:
    """Complete MP4 to TXT conversion pipeline"""
    
    # Generate temp MP3 path if not provided
    if not temp_mp3_path:
        if keep_mp3 and output_txt_path.parent != input_path.parent:
            # Place MP3 in same directory as output if keeping it
            temp_mp3_path = output_txt_path.parent / f"{input_path.stem}.mp3"
        else:
            temp_mp3_path = generate_temp_mp3_path(input_path)
    
    total_metadata = {}
    
    try:
        # Stage 1: MP4 to MP3 conversion
        if not quiet:
            print(f"🎬 Stage 1/2: Converting MP4 to MP3...")
        
        mp4_config = config.get('mp4_to_mp3', get_mp4_config())
        progress_cb_mp4 = create_progress_callback(verbose, quiet, "MP4→MP3")
        
        success, message, metadata = convert_mp4_to_mp3(
            str(input_path),
            str(temp_mp3_path),
            config=mp4_config,
            progress_callback=progress_cb_mp4
        )
        
        if not success:
            return False, f"MP4 to MP3 conversion failed: {message}", {}
        
        total_metadata['mp4_to_mp3'] = metadata
        
        if not quiet:
            print(f"✅ MP3 conversion completed: {temp_mp3_path.name}")
        
        # Stage 2: MP3 to TXT conversion
        if not quiet:
            print(f"🎤 Stage 2/2: Converting MP3 to TXT using {engine}...")
        
        mp3_config = config.get('mp3_to_txt', get_mp3_config())
        progress_cb_mp3 = create_progress_callback(verbose, quiet, "MP3→TXT")
        
        # Choose conversion function based on engine
        if engine == 'whisper':
            from plugins.mp3_to_txt.whisper_convert import convert_mp3_to_txt_whisper
            success, message, metadata = convert_mp3_to_txt_whisper(
                str(temp_mp3_path),
                str(output_txt_path),
                str(output_srt_path) if output_srt_path else None,
                config=mp3_config,
                progress_callback=progress_cb_mp3
            )
        else:  # alibaba_nls
            success, message, metadata = convert_mp3_to_txt(
                str(temp_mp3_path),
                str(output_txt_path),
                str(output_srt_path) if output_srt_path else None,
                config=mp3_config,
                progress_callback=progress_cb_mp3
            )
        
        if not success:
            cleanup_temp_file(temp_mp3_path, keep_mp3)
            return False, f"MP3 to TXT conversion failed: {message}", total_metadata
        
        total_metadata['mp3_to_txt'] = metadata
        
        # Clean up temporary MP3 file if not keeping it
        if not keep_mp3:
            cleanup_temp_file(temp_mp3_path, False)
        elif not quiet:
            mp3_size = temp_mp3_path.stat().st_size
            print(f"📁 MP3 file kept: {temp_mp3_path} ({mp3_size:,} bytes)")
        
        return True, "Complete conversion successful", total_metadata
        
    except Exception as e:
        cleanup_temp_file(temp_mp3_path, keep_mp3)
        raise e

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Convert MP4 video files to TXT and SRT subtitle files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mp4_to_txt_cli.py input.mp4 output.txt --engine whisper
  python mp4_to_txt_cli.py input.mp4 output.txt output.srt --engine alibaba_nls
  python mp4_to_txt_cli.py input.mp4 output.txt --engine whisper --keep-mp3
  python mp4_to_txt_cli.py input.mp4 output.txt --config config.yaml --verbose

Pipeline:
  1. Convert MP4 video to MP3 audio (optimized for speech recognition)
  2. Convert MP3 audio to TXT/SRT using selected engine
  3. Clean up temporary files (unless --keep-mp3 is specified)

Supported engines:
  whisper     - Uses Faster-Whisper for local speech recognition
  alibaba_nls - Uses Alibaba Cloud Natural Language Service
        """
    )
    
    # Required arguments
    parser.add_argument(
        'input_file',
        type=str,
        help='Input MP4 video file path'
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
    parser.add_argument(
        '--keep-mp3',
        action='store_true',
        help='Keep the intermediate MP3 file after conversion'
    )
    parser.add_argument(
        '--temp-mp3',
        type=str,
        help='Custom path for temporary MP3 file'
    )
    
    # Conversion options
    conv_group = parser.add_argument_group('Conversion options')
    conv_group.add_argument(
        '--bitrate',
        type=str,
        help='Audio bitrate for MP3 (e.g., 64k, 128k)'
    )
    conv_group.add_argument(
        '--model',
        type=str,
        choices=['tiny', 'base', 'small', 'medium', 'large-v1', 'large-v2', 'large-v3'],
        help='Whisper model size (default: base)'
    )
    conv_group.add_argument(
        '--language',
        type=str,
        help='Language code (e.g., zh, en, ja, ko, auto for auto-detection)'
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
    temp_mp3_path = Path(args.temp_mp3).resolve() if args.temp_mp3 else None
    
    # Validate input
    if not validate_input_file(input_path):
        sys.exit(1)
    
    # Ensure output directories exist
    if not ensure_output_directory(output_txt_path):
        sys.exit(1)
    if output_srt_path and not ensure_output_directory(output_srt_path):
        sys.exit(1)
    if temp_mp3_path and not ensure_output_directory(temp_mp3_path):
        sys.exit(1)
    
    # Load configuration
    config = load_configuration(config_path)
    
    # Override configuration with command line arguments
    if args.bitrate:
        if 'mp4_to_mp3' not in config:
            config['mp4_to_mp3'] = get_mp4_config()
        config['mp4_to_mp3']['audio_bitrate'] = args.bitrate
    
    if args.model:
        if 'mp3_to_txt' not in config:
            config['mp3_to_txt'] = get_mp3_config()
        config['mp3_to_txt']['whisper_model_size'] = args.model
    
    if args.language:
        if 'mp3_to_txt' not in config:
            config['mp3_to_txt'] = get_mp3_config()
        config['mp3_to_txt']['whisper_language'] = args.language
    
    # Show configuration if verbose
    if args.verbose:
        print(f"📁 Input file: {input_path}")
        print(f"📁 Output TXT file: {output_txt_path}")
        if output_srt_path:
            print(f"📁 Output SRT file: {output_srt_path}")
        if temp_mp3_path:
            print(f"📁 Temp MP3 file: {temp_mp3_path}")
        print(f"🤖 Engine: {args.engine}")
        print(f"🔄 Keep MP3: {args.keep_mp3}")
        print(f"⚙️  Configuration:")
        print(f"   MP4→MP3: {config.get('mp4_to_mp3', {})}")
        print(f"   MP3→TXT: {config.get('mp3_to_txt', {})}")
        print()
    
    # Perform complete conversion
    try:
        if not args.quiet:
            print(f"🚀 Starting complete MP4→TXT conversion...")
            print(f"   Input: {input_path.name}")
            print(f"   Engine: {args.engine}")
            print()
        
        success, message, metadata = convert_mp4_to_txt_pipeline(
            input_path=input_path,
            output_txt_path=output_txt_path,
            output_srt_path=output_srt_path,
            engine=args.engine,
            config=config,
            keep_mp3=args.keep_mp3,
            temp_mp3_path=temp_mp3_path,
            verbose=args.verbose,
            quiet=args.quiet
        )
        
        if success:
            print(f"✅ {message}")
            
            if args.verbose and metadata:
                print(f"\n📊 Complete Conversion Statistics:")
                
                # MP4 to MP3 stats
                mp4_meta = metadata.get('mp4_to_mp3', {})
                if mp4_meta:
                    print(f"   MP4→MP3:")
                    print(f"     Original size: {mp4_meta.get('original_size', 0):,} bytes")
                    print(f"     MP3 size: {mp4_meta.get('final_size', 0):,} bytes")
                    print(f"     Compression: {mp4_meta.get('compression_ratio', 0):.3f}")
                    print(f"     Duration: {mp4_meta.get('duration_seconds', 0):.2f}s")
                
                # MP3 to TXT stats
                mp3_meta = metadata.get('mp3_to_txt', {})
                if mp3_meta:
                    print(f"   MP3→TXT:")
                    print(f"     Processing time: {mp3_meta.get('duration_seconds', 0):.2f}s")
                    print(f"     Segments: {mp3_meta.get('segments_count', 0)}")
                    print(f"     Text length: {mp3_meta.get('txt_content_length', mp3_meta.get('total_text_length', 0))} chars")
                    if args.engine == 'whisper':
                        print(f"     Model: {mp3_meta.get('model_size', 'unknown')}")
                        print(f"     Language: {mp3_meta.get('language', 'unknown')}")
            
            if not args.quiet:
                print()
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