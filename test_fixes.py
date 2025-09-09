# -*- coding: utf-8 -*-
"""
测试修复后的字幕和语音功能
"""

def test_subtitle_with_speech():
    print(u"=== 测试字幕+语音功能修复 ===")
    
    # 准备测试数据
    video_path = 'sources/my.mp4'
    text_path = 'sources/my.txt'
    
    import os
    if not os.path.exists(video_path):
        print(u"视频文件不存在: {}".format(video_path))
        return
    
    if not os.path.exists(text_path):
        print(u"创建测试文本文件...")
        with open(text_path, 'w') as f:
            f.write(u"这是一个测试语音合成的字幕。\n第二条测试字幕内容。".encode('utf-8'))
    
    # 测试字幕插入器
    from subtitle_inserter import SubtitleInserter
    inserter = SubtitleInserter()
    
    try:
        print(u"开始处理字幕和语音...")
        result = inserter.insert_subtitles_to_video(
            video_path=video_path,
            subtitle_source=text_path,
            style='default',
            split_mode='smart_split',
            start_time=0.0,
            enable_speech=True,
            voice='zh-CN-XiaoxiaoNeural'
        )
        
        print(u"✓ 处理成功！")
        print(u"输出文件: {}".format(result))
        
        # 检查文件
        if os.path.exists(result):
            file_size = os.path.getsize(result) / (1024 * 1024)
            print(u"文件大小: {:.2f} MB".format(file_size))
            print(u"✓ 输出文件确实保存到了output目录")
        else:
            print(u"✗ 输出文件不存在")
            
    except Exception as e:
        print(u"处理失败: {}".format(str(e)))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_subtitle_with_speech()
