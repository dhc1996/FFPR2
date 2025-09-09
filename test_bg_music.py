# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def safe_print(text):
    """安全的中文输出"""
    try:
        print(text.encode('gbk'))
    except:
        try:
            print(text.encode('utf-8'))
        except:
            print(repr(text))

from background_music import BackgroundMusicProcessor

# 测试代码
processor = BackgroundMusicProcessor()

video_path = r"D:\FF\FFPR\output\output_ad_20250806_174957_with_ad.mp4"
audio_path = r"D:\FF\FFPR\sources\music.mp3"  # 使用英文名称的音频文件

safe_print(u"测试视频信息获取...")
video_info = processor.get_video_info(video_path)
safe_print(u"视频信息: {}".format(video_info))

safe_print(u"测试音频信息获取...")
audio_info = processor.get_audio_info(audio_path)
safe_print(u"音频信息: {}".format(audio_info))
