# -*- coding: utf-8 -*-
"""
快速字幕工具 - 简化版
解决CLI输入验证问题的直接调用版本
"""

import os
import sys
from subtitle_inserter import SubtitleInserter

def main():
    print("=" * 60)
    print("      快速视频字幕添加工具")
    print("=" * 60)
    
    # 设置默认文件路径
    video_file = "sources/my.mp4"
    text_file = "sources/my.txt"
    
    # 检查文件是否存在
    if not os.path.exists(video_file):
        print(u"视频文件不存在: {}".format(video_file))
        return
    
    if not os.path.exists(text_file):
        print(u"文本文件不存在: {}".format(text_file))
        return
    
    print(u"视频文件: {}".format(video_file))
    print(u"文本文件: {}".format(text_file))
    print()
    
    # 创建字幕插入器
    inserter = SubtitleInserter()
    
    try:
        print(u"开始处理...")
        
        # 执行字幕和语音合成
        output_path = inserter.insert_subtitles_to_video(
            video_path=video_file,
            subtitle_source=text_file,
            style='default',
            split_mode='smart_split',
            enable_speech=True,
            voice='zh-CN-XiaoxiaoNeural'
        )
        
        print()
        print("=" * 60)
        print(u"处理完成！")
        print(u"输出文件: {}".format(output_path))
        print("=" * 60)
        
    except Exception as e:
        print(u"处理失败: {}".format(str(e)))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
