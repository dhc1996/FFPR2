# -*- coding: utf-8 -*-
"""
简单的语音合成功能测试
"""
import sys
import os

def test_basic_tts():
    """基础TTS功能测试"""
    print(u"基础语音合成功能测试")
    print(u"=" * 40)
    
    try:
        from text_to_speech import TextToSpeechGenerator
        
        # 创建TTS生成器
        tts = TextToSpeechGenerator()
        print(u"✓ TTS生成器创建成功")
        
        # 检查可用引擎
        available = tts.check_tts_availability()
        print(u"可用引擎: {}".format(available))
        
        # 创建简单的测试字幕
        test_subtitles = [
            (0.0, 2.0, u"你好，这是语音测试。"),
            (2.0, 4.0, u"语音合成功能正常工作。")
        ]
        
        print(u"测试字幕:")
        for i, (start, end, text) in enumerate(test_subtitles):
            print(u"  {}. [{:.1f}s-{:.1f}s] {}".format(i+1, start, end, text))
        
        print(u"\n开始生成语音...")
        audio_info = tts.generate_speech_for_subtitles(
            test_subtitles, 
            voice='zh-CN-XiaoxiaoNeural',
            engine='auto'
        )
        
        print(u"✅ 语音生成成功！")
        print(u"生成信息:")
        print(u"  - 音频文件数: {}".format(len(audio_info.get('audio_files', []))))
        print(u"  - 合并音频: {}".format(audio_info.get('merged_audio', '无')))
        print(u"  - 使用引擎: {}".format(audio_info.get('engine_used', '未知')))
        print(u"  - 使用语音: {}".format(audio_info.get('voice_used', '未知')))
        
        return True
        
    except Exception as e:
        print(u"❌ 语音测试失败: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_basic_tts()
    if success:
        print(u"\n🎉 语音合成功能可以正常使用！")
        print(u"您现在可以在字幕工具中启用语音合成功能")
    else:
        print(u"\n💡 语音合成功能可能存在问题，但字幕功能仍可正常使用")
