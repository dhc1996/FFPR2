# -*- coding: utf-8 -*-
"""
测试完整的语音合成和清理功能
"""

def test_complete_workflow():
    print(u"=== 完整语音合成工作流程测试 ===")
    
    # 1. 准备测试数据
    from subtitle_generator import SubtitleGenerator
    generator = SubtitleGenerator()
    
    test_texts = [
        u'这是第一条测试字幕',
        u'这是第二条测试字幕', 
        u'这是第三条测试字幕',
        u'这是最后一条测试字幕'
    ]
    
    subtitles = generator._process_normal_lines_by_seconds(test_texts, 0.0)
    print(u"✓ 生成了{}条字幕数据".format(len(subtitles)))
    
    # 2. 语音合成
    from text_to_speech import TextToSpeechGenerator
    tts = TextToSpeechGenerator()
    
    print(u"\n开始语音合成...")
    try:
        result = tts.generate_speech_for_subtitles(
            subtitles, 
            voice='zh-CN-XiaoxiaoNeural', 
            engine='pyttsx3'
        )
        
        print(u"✓ 语音合成成功")
        print(u"  - 处理片段数: {}".format(result['segments_count']))
        print(u"  - 总时长: {:.1f}秒".format(result['total_duration']))
        print(u"  - 使用引擎: {}".format(result['engine_used']))
        print(u"  - 最终文件: {}".format(result['merged_audio']))
        
        # 3. 验证文件状态
        import os
        audio_dir = os.path.join(os.path.dirname(__file__), 'audio')
        audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
        print(u"\n当前音频目录文件:")
        for f in audio_files:
            print(u"  - {}".format(f))
        
        # 统计文件数量
        merged_files = [f for f in audio_files if f.startswith('merged_speech_')]
        temp_files = [f for f in audio_files if f.startswith('speech_') and 'part' in f]
        
        print(u"\n文件统计:")
        print(u"  - 最终合并文件: {}个".format(len(merged_files)))
        print(u"  - 临时片段文件: {}个".format(len(temp_files)))
        
        if len(temp_files) == 0:
            print(u"✓ 临时文件清理成功！")
        else:
            print(u"⚠ 仍有{}个临时文件未清理".format(len(temp_files)))
            
    except Exception as e:
        print(u"✗ 语音合成失败: {}".format(str(e)))
        import traceback
        traceback.print_exc()
    
    print(u"\n=== 测试完成 ===")

if __name__ == "__main__":
    test_complete_workflow()
