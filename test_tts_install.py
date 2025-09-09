# -*- coding: utf-8 -*-
"""
TTS依赖安装测试脚本
"""
import sys
import os

# 确保能导入项目模块
sys.path.insert(0, os.path.dirname(__file__))

def test_tts_installation():
    """测试TTS依赖安装"""
    print(u"TTS依赖安装测试")
    print(u"=" * 40)
    
    try:
        from text_to_speech import TextToSpeechGenerator
        
        # 创建TTS生成器
        tts = TextToSpeechGenerator()
        
        # 检查当前可用引擎
        print(u"检查当前可用的TTS引擎...")
        available = tts.check_tts_availability()
        print(u"可用引擎: {}".format(available))
        
        # 如果只有系统TTS，尝试安装其他引擎
        if len(available) == 1 and available[0] == 'system':
            print(u"\n只有系统TTS可用，尝试安装更好的TTS引擎...")
            print(u"开始安装依赖...")
            
            new_available = tts.install_dependencies()
            print(u"\n安装后可用引擎: {}".format(new_available))
            
            if len(new_available) > 1 or 'edge-tts' in new_available or 'pyttsx3' in new_available:
                print(u"✅ TTS依赖安装成功！")
                return True
            else:
                print(u"⚠️  TTS依赖安装可能未完全成功，但系统TTS仍可用")
                return False
        else:
            print(u"✅ TTS引擎已可用，无需额外安装")
            return True
            
    except Exception as e:
        print(u"❌ TTS测试失败: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_tts_installation()
    if success:
        print(u"\n🎉 可以在字幕工具中使用语音合成功能了！")
    else:
        print(u"\n💡 建议手动安装TTS依赖或使用系统TTS")
        print(u"手动安装命令:")
        print(u'  & "D:/Software/Python27/python.exe" -m pip install edge-tts')
        print(u'  & "D:/Software/Python27/python.exe" -m pip install pyttsx3')
