#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Whisper Model Management Script
管理Whisper模型的下载、删除和信息查看
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import whisper
from plugins.config import MODELS_DIR

def get_available_models() -> List[str]:
    """获取可用的Whisper模型列表"""
    return ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3']

def get_model_info() -> Dict[str, Dict]:
    """获取模型信息"""
    return {
        'tiny': {
            'size': '39 MB',
            'speed': '最快',
            'accuracy': '基础',
            'description': '适合快速测试和低资源环境'
        },
        'base': {
            'size': '74 MB', 
            'speed': '快',
            'accuracy': '良好',
            'description': '推荐用于一般使用，平衡速度和准确性'
        },
        'small': {
            'size': '244 MB',
            'speed': '中等',
            'accuracy': '更好',
            'description': '适合对准确性有一定要求的场景'
        },
        'medium': {
            'size': '769 MB',
            'speed': '慢',
            'accuracy': '高',
            'description': '高质量转录，适合专业使用'
        },
        'large': {
            'size': '1550 MB',
            'speed': '最慢',
            'accuracy': '最高',
            'description': '最佳质量，适合对准确性要求极高的场景'
        },
        'large-v2': {
            'size': '1550 MB',
            'speed': '最慢',
            'accuracy': '最高',
            'description': 'Large模型的改进版本，更好的多语言支持'
        },
        'large-v3': {
            'size': '1550 MB',
            'speed': '最慢',
            'accuracy': '最高',
            'description': '最新版本，性能和准确性进一步提升'
        }
    }

def list_models():
    """列出所有可用的模型"""
    print("可用的Whisper模型:")
    print("=" * 80)
    
    models_info = get_model_info()
    
    for model_name in get_available_models():
        info = models_info.get(model_name, {})
        # 检查模型是否已下载
        model_file = MODELS_DIR / f"{model_name}.pt"
        status = "✅ 已下载" if model_file.exists() else "❌ 未下载"
        
        print(f"模型: {model_name:<12} | 大小: {info.get('size', 'N/A'):<10} | "
              f"速度: {info.get('speed', 'N/A'):<6} | 准确性: {info.get('accuracy', 'N/A'):<6} | {status}")
        print(f"  描述: {info.get('description', 'N/A')}")
        print()

def download_model(model_name: str):
    """下载指定的模型"""
    if model_name not in get_available_models():
        print(f"❌ 错误: 不支持的模型 '{model_name}'")
        print(f"支持的模型: {', '.join(get_available_models())}")
        return False
    
    try:
        print(f"🔄 开始下载模型: {model_name}")
        print(f"📁 下载目录: {MODELS_DIR}")
        
        # 确保模型目录存在
        MODELS_DIR.mkdir(exist_ok=True)
        
        # 下载模型
        model = whisper.load_model(model_name, download_root=str(MODELS_DIR))
        
        print(f"✅ 模型 '{model_name}' 下载完成!")
        return True
        
    except Exception as e:
        print(f"❌ 下载失败: {str(e)}")
        return False

def delete_model(model_name: str):
    """删除指定的模型"""
    if model_name not in get_available_models():
        print(f"❌ 错误: 不支持的模型 '{model_name}'")
        return False
    
    model_file = MODELS_DIR / f"{model_name}.pt"
    
    if not model_file.exists():
        print(f"❌ 模型 '{model_name}' 未找到")
        return False
    
    try:
        model_file.unlink()
        print(f"✅ 模型 '{model_name}' 已删除")
        return True
        
    except Exception as e:
        print(f"❌ 删除失败: {str(e)}")
        return False

def check_model_status(model_name: str = None):
    """检查模型状态"""
    if model_name:
        if model_name not in get_available_models():
            print(f"❌ 错误: 不支持的模型 '{model_name}'")
            return
        
        model_file = MODELS_DIR / f"{model_name}.pt"
        if model_file.exists():
            size = model_file.stat().st_size / (1024 * 1024)  # MB
            print(f"✅ 模型 '{model_name}' 已下载 (大小: {size:.1f} MB)")
        else:
            print(f"❌ 模型 '{model_name}' 未下载")
    else:
        print("已下载的模型:")
        downloaded_models = []
        for model_name in get_available_models():
            model_file = MODELS_DIR / f"{model_name}.pt"
            if model_file.exists():
                size = model_file.stat().st_size / (1024 * 1024)  # MB
                downloaded_models.append(f"{model_name} ({size:.1f} MB)")
        
        if downloaded_models:
            for model in downloaded_models:
                print(f"  ✅ {model}")
        else:
            print("  ❌ 没有已下载的模型")

def clean_models():
    """清理所有模型"""
    print("🧹 开始清理所有模型...")
    
    deleted_count = 0
    for model_name in get_available_models():
        model_file = MODELS_DIR / f"{model_name}.pt"
        if model_file.exists():
            try:
                model_file.unlink()
                print(f"  ✅ 删除 {model_name}")
                deleted_count += 1
            except Exception as e:
                print(f"  ❌ 删除 {model_name} 失败: {str(e)}")
    
    print(f"🎉 清理完成，删除了 {deleted_count} 个模型")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Whisper模型管理工具")
    parser.add_argument('action', choices=['list', 'download', 'delete', 'status', 'clean'], 
                       help='操作类型')
    parser.add_argument('model', nargs='?', help='模型名称')
    
    args = parser.parse_args()
    
    print("🎤 Whisper模型管理工具")
    print("=" * 50)
    
    if args.action == 'list':
        list_models()
    elif args.action == 'download':
        if not args.model:
            print("❌ 错误: 请指定要下载的模型名称")
            print("示例: python manage_models.py download base")
            return
        download_model(args.model)
    elif args.action == 'delete':
        if not args.model:
            print("❌ 错误: 请指定要删除的模型名称")
            print("示例: python manage_models.py delete base")
            return
        delete_model(args.model)
    elif args.action == 'status':
        check_model_status(args.model)
    elif args.action == 'clean':
        confirm = input("⚠️  确定要删除所有模型吗？(y/N): ")
        if confirm.lower() == 'y':
            clean_models()
        else:
            print("❌ 操作已取消")

if __name__ == "__main__":
    main() 