# -*- coding: utf-8 -*-
import subprocess
import json
import os

def safe_print(text):
    """安全的中文输出"""
    try:
        print(text.encode('gbk'))
    except:
        try:
            print(text.encode('utf-8'))
        except:
            print(repr(text))

def debug_get_video_info(video_path):
    """调试版本的获取视频信息"""
    ffprobe_path = r'D:\Software\ffmpeg\bin\ffprobe.exe'
    
    safe_print(u"=== 开始调试 get_video_info ===")
    safe_print(u"视频路径: {}".format(video_path))
    
    try:
        cmd = [
            ffprobe_path, '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', video_path
        ]
        safe_print(u"执行命令: {}".format(' '.join(cmd)))
        
        # 在Windows上使用shell=True
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        safe_print(u"subprocess调用成功，返回结果类型: {}".format(type(result)))
        
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
        
        safe_print(u"字符串解码成功，长度: {}".format(len(result_str)))
        
        if not result_str or result_str.strip() == '':
            safe_print(u"FFprobe返回空结果")
            return None
        
        safe_print(u"JSON字符串前200字符: {}".format(result_str[:200]))
        
        data = json.loads(result_str)
        safe_print(u"JSON解析成功")
        
        # 确保 streams 存在且不为 None
        streams = data.get('streams')
        safe_print(u"streams字段类型: {}".format(type(streams)))
        safe_print(u"streams内容: {}".format(streams))
        
        if streams is None:
            safe_print(u"FFprobe输出中没有streams字段")
            return None
        
        if not isinstance(streams, list) or len(streams) == 0:
            safe_print(u"视频文件没有有效的流信息")
            return None
        
        safe_print(u"找到 {} 个流".format(len(streams)))
        
        video_stream = None
        audio_streams = []
        
        for i, stream in enumerate(streams):
            safe_print(u"处理流 {}: {}".format(i, type(stream)))
            if stream and stream.get('codec_type') == 'video':
                video_stream = stream
                safe_print(u"找到视频流")
            elif stream and stream.get('codec_type') == 'audio':
                audio_streams.append(stream)
                safe_print(u"找到音频流")
        
        if not video_stream:
            safe_print(u"视频文件中没有找到视频流")
            return None
        
        # 确保格式信息存在
        format_info = data.get('format')
        safe_print(u"format字段类型: {}".format(type(format_info)))
        
        if not format_info:
            safe_print(u"FFprobe输出中没有format字段")
            return None
        
        duration = format_info.get('duration')
        safe_print(u"duration: {}".format(duration))
        
        if duration is None:
            safe_print(u"无法获取视频时长信息")
            return None
        
        info = {
            'duration': float(duration),
            'width': int(video_stream.get('width', 0)),
            'height': int(video_stream.get('height', 0)),
            'fps': 30,  # 默认帧率
            'has_audio': len(audio_streams) > 0
        }
        
        safe_print(u"成功创建视频信息: {}".format(info))
        return info
        
    except subprocess.CalledProcessError as e:
        safe_print(u"FFprobe执行失败: {}".format(str(e)))
        return None
    except ValueError as e:  # Python 2.7中JSON错误是ValueError
        safe_print(u"解析FFprobe输出失败: {}".format(str(e)))
        return None
    except Exception as e:
        safe_print(u"获取视频信息失败: {}".format(str(e)))
        import traceback
        safe_print(u"错误详情:")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    video_path = r"D:\FF\FFPR\output\output_ad_20250806_174957_with_ad.mp4"
    debug_get_video_info(video_path)
