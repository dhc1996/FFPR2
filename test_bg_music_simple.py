# -*- coding: utf-8 -*-
"""
简化版背景音乐测试脚本
"""

import os
import sys

def test_background_music_simple():
    """简化的背景音乐测试"""
    print("=" * 50)
    print("Background Music Test")
    print("=" * 50)
    
    # 检查模块导入
    try:
        from background_music import BackgroundMusicProcessor
        from config import Config
        print("[OK] Modules imported successfully")
    except Exception as e:
        print("[Error] Module import failed: {}".format(str(e)))
        return
    
    # 创建处理器
    try:
        config = Config()
        processor = BackgroundMusicProcessor(config)
        print("[OK] Processor created successfully")
    except Exception as e:
        print("[Error] Processor creation failed: {}".format(str(e)))
        return
    
    # 测试简单方法
    try:
        # 测试一个不存在的文件（预期失败）
        result = processor.validate_files("nonexistent.mp4", "nonexistent.mp3")
        if not result[0]:
            print("[OK] File validation correctly rejected non-existent files")
        else:
            print("[Warning] File validation incorrectly accepted non-existent files")
    except Exception as e:
        print("[Error] File validation test failed: {}".format(str(e)))
    
    print("[Info] Basic functionality test completed")
    print("To test full functionality, run the main program: python cli.py")

if __name__ == "__main__":
    test_background_music_simple()
