# -*- coding: utf-8 -*-
"""
简化的音频合并工具 - 专门优化音频合并速度
"""

import os
import time
import subprocess

def fast_merge_audio_segments(audio_files, output_dir):
    """快速合并音频片段，优化版本"""
    try:
        timestamp = int(time.time())
        merged_path = os.path.join(output_dir, "merged_speech_{}.wav".format(timestamp))
        
        # 如果只有一个文件，直接移动
        if len(audio_files) == 1:
            import shutil
            source_path = audio_files[0]['path']
            shutil.move(source_path, merged_path)
            return merged_path
        
        # 按开始时间排序
        sorted_audio_files = sorted(audio_files, key=lambda x: x['start_time'])
        total_duration = max([af['end_time'] for af in sorted_audio_files])
        
        print(u"正在快速合并{}个音频片段...".format(len(sorted_audio_files)))
        
        # 方案：使用最简单但有效的concat方式（不管时间同步）
        # 这样速度最快，音频会连续播放但可能与字幕时间不完全匹配
        concat_file = os.path.join(output_dir, "temp_concat_{}.txt".format(timestamp))
        
        with open(concat_file, 'w') as f:
            for audio_info in sorted_audio_files:
                f.write("file '{}'\n".format(os.path.basename(audio_info['path'])))
        
        # 使用FFmpeg快速连接
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',  # 直接复制，不重新编码
            merged_path
        ]
        
        result = subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 清理临时文件
        if os.path.exists(concat_file):
            os.remove(concat_file)
        
        if result == 0 and os.path.exists(merged_path):
            print(u"快速合并成功！")
            return merged_path
        else:
            print(u"快速合并失败")
            return None
            
    except Exception as e:
        print(u"音频合并出错: {}".format(str(e)))
        return None

def test_fast_merge():
    """测试快速合并功能"""
    # 这里可以添加测试代码
    pass

if __name__ == "__main__":
    test_fast_merge()
