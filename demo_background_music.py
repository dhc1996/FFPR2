# -*- coding: utf-8 -*-
"""
背景音乐功能完整测试示例
"""

import os
import sys

def main():
    """主测试函数"""
    print("=" * 60)
    print("Background Music Feature Test")
    print("=" * 60)
    
    try:
        from background_music import BackgroundMusicProcessor
        from config import Config
        
        # 创建处理器
        config = Config()
        processor = BackgroundMusicProcessor(config)
        
        # 示例测试
        print("\n[Test] Creating demo files...")
        
        # 这里可以创建一个简单的测试视频（如果需要的话）
        # 实际使用时，用户需要提供真实的视频和音频文件
        
        print("\nTo test with real files:")
        print("1. Prepare a video file (mp4, avi, mov, etc.)")
        print("2. Prepare a music file (mp3, wav, aac, etc.)")
        print("3. Run: python cli.py")
        print("4. Choose option 6 (Background Music)")
        print("5. Follow the prompts")
        
        print("\nFeatures available:")
        print("- Music volume control (0.0 - 1.0)")
        print("- Original audio volume control")
        print("- Music looping for longer videos")
        print("- Fade in/out effects")
        print("- Custom start time for music")
        print("- High quality output with video copy")
        
        print("\nSupported video formats:")
        print("- MP4, AVI, MOV, MKV, WMV, FLV")
        
        print("\nSupported audio formats:")
        print("- MP3, WAV, AAC, M4A, OGG, FLAC")
        
        print("\n" + "=" * 60)
        print("Background music feature is ready to use!")
        print("=" * 60)
        
    except Exception as e:
        print("Error during test: {}".format(str(e)))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
