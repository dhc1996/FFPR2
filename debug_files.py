# -*- coding: utf-8 -*-
"""
调试背景音乐文件检测脚本
"""

import os
import sys
import subprocess
import json

def debug_file_info(file_path, file_type="video"):
    """调试文件信息获取"""
    print("=" * 50)
    print("Debug file: {}".format(file_path))
    print("File type: {}".format(file_type))
    print("File exists: {}".format(os.path.exists(file_path)))
    
    if not os.path.exists(file_path):
        print("File does not exist!")
        return
    
    # 获取文件大小
    file_size = os.path.getsize(file_path)
    print("File size: {:.1f}MB".format(file_size / (1024 * 1024.0)))
    
    # 使用FFprobe直接检查
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', file_path
        ]
        print("Running command: {}".format(' '.join(cmd)))
        
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        print("FFprobe output length: {} bytes".format(len(result)))
        
        # 解析JSON
        data = json.loads(result)
        print("JSON parsed successfully")
        
        # 检查结构
        print("Data keys: {}".format(data.keys()))
        
        if 'streams' in data:
            streams = data['streams']
            print("Streams count: {}".format(len(streams) if streams else 0))
            
            if streams:
                for i, stream in enumerate(streams):
                    print("Stream {}: codec_type={}".format(i, stream.get('codec_type')))
                    if stream.get('codec_type') == 'video':
                        print("  Video: {}x{}, fps={}".format(
                            stream.get('width'), stream.get('height'), stream.get('r_frame_rate')
                        ))
                    elif stream.get('codec_type') == 'audio':
                        print("  Audio: {}Hz, {} channels".format(
                            stream.get('sample_rate'), stream.get('channels')
                        ))
        else:
            print("No 'streams' in data")
        
        if 'format' in data:
            format_info = data['format']
            print("Format duration: {}".format(format_info.get('duration')))
            print("Format format_name: {}".format(format_info.get('format_name')))
        else:
            print("No 'format' in data")
            
    except subprocess.CalledProcessError as e:
        print("FFprobe failed: {}".format(str(e)))
    except json.JSONDecodeError as e:
        print("JSON decode failed: {}".format(str(e)))
        print("Raw output: {}".format(result[:200]))
    except Exception as e:
        print("Error: {}".format(str(e)))

def main():
    video_path = r"D:\FF\FFPR\output\output_ad_20250806_174957_with_ad.mp4"
    audio_path = r"D:\FF\FFPR\sources\洗牌.mp3"
    
    print("Testing background music files...")
    
    debug_file_info(video_path, "video")
    debug_file_info(audio_path, "audio")

if __name__ == "__main__":
    main()
