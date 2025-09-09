# -*- coding: utf-8 -*-
"""
简单视频提取工具
"""

import os
import sys
import subprocess
from config import Config

def safe_input(prompt):
    """安全输入函数"""
    try:
        if sys.version_info[0] == 2:
            return raw_input(prompt.encode('utf-8')).decode('utf-8')
        else:
            return input(prompt)
    except:
        return ''

def extract_audio():
    """提取音频"""
    print(u'=== 视频音频提取工具 ===')
    
    video_path = safe_input(u'请输入视频文件路径: ').strip().strip('"')
    if not os.path.exists(video_path):
        print(u'文件不存在')
        return
    
    config = Config()
    ffmpeg_path = config.get('ffmpeg', 'path')
    
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = 'audio'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_path = os.path.join(output_dir, base_name + '_audio.mp3')
    
    cmd = [ffmpeg_path, '-y', '-i', video_path, '-vn', '-acodec', 'mp3', '-b:a', '192k', output_path]
    
    print(u'开始提取音频...')
    try:
        subprocess.check_call(cmd)
        print(u'音频提取完成: ' + output_path)
        
        # 显示文件大小
        file_size = os.path.getsize(output_path) / (1024.0 * 1024.0)
        print(u'文件大小: {:.2f} MB'.format(file_size))
        
    except Exception as e:
        print(u'音频提取失败: {}'.format(str(e)))

if __name__ == '__main__':
    extract_audio()
    safe_input(u'按回车键退出...')
