# -*- coding: utf-8 -*-
import subprocess
import json
import os
import sys

def safe_print(text):
    """安全的中文输出"""
    try:
        print(text.encode('gbk'))
    except:
        print(text.encode('utf-8', 'ignore'))

def test_ffprobe(file_path):
    """测试ffprobe调用"""
    ffprobe_path = r'D:\Software\ffmpeg\bin\ffprobe.exe'
    
    safe_print(u"测试文件: {}".format(file_path))
    safe_print(u"文件存在: {}".format(os.path.exists(file_path)))
    
    try:
        cmd = [
            ffprobe_path, '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', file_path
        ]
        
        safe_print(u"执行命令: {}".format(' '.join(cmd)))
        
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=False)
        
        safe_print(u"subprocess输出类型: {}".format(type(result)))
        safe_print(u"subprocess输出长度: {}".format(len(result) if result else 0))
        
        # 尝试不同的编码方式解析结果
        try:
            if isinstance(result, bytes):
                result_str = result.decode('utf-8')
            else:
                result_str = result
        except UnicodeDecodeError:
            try:
                result_str = result.decode('gbk')
            except:
                result_str = result.decode('utf-8', 'ignore')
        
        safe_print(u"解码后的字符串长度: {}".format(len(result_str)))
        safe_print(u"JSON字符串前100字符: {}".format(result_str[:100]))
        
        data = json.loads(result_str)
        
        safe_print(u"JSON解析成功")
        safe_print(u"streams类型: {}".format(type(data.get('streams'))))
        safe_print(u"streams数量: {}".format(len(data.get('streams', []))))
        
        streams = data.get('streams', [])
        if streams:
            for i, stream in enumerate(streams):
                safe_print(u"流 {}: 类型={}".format(i, stream.get('codec_type')))
        
        format_info = data.get('format', {})
        safe_print(u"format存在: {}".format(format_info is not None))
        safe_print(u"duration: {}".format(format_info.get('duration')))
        
        return True
        
    except subprocess.CalledProcessError as e:
        safe_print(u"subprocess错误: {}".format(str(e)))
        return False
    except ValueError as e:
        safe_print(u"JSON解析错误: {}".format(str(e)))
        return False
    except Exception as e:
        safe_print(u"其他错误: {}".format(str(e)))
        return False

if __name__ == "__main__":
    video_path = r"D:\FF\FFPR\output\output_ad_20250806_174957_with_ad.mp4"
    audio_path = r"D:\FF\FFPR\sources\洗牌.mp3"
    
    safe_print(u"=== 测试视频文件 ===")
    test_ffprobe(video_path)
    
    safe_print(u"\n=== 测试音频文件 ===")
    test_ffprobe(audio_path)
