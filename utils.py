# -*- coding: utf-8 -*-
"""
项目工具函数模块
包含一些通用的辅助函数
"""

import os
import sys
import time
import subprocess

def format_duration(seconds):
    """格式化时间长度显示"""
    if seconds < 60:
        return u"{:.1f}秒".format(seconds)
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return u"{}分{:.1f}秒".format(minutes, secs)
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return u"{}小时{}分{:.1f}秒".format(hours, minutes, secs)

def format_file_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes < 1024:
        return u"{}B".format(size_bytes)
    elif size_bytes < 1024 * 1024:
        return u"{:.1f}KB".format(size_bytes / 1024)
    elif size_bytes < 1024 * 1024 * 1024:
        return u"{:.1f}MB".format(size_bytes / (1024 * 1024))
    else:
        return u"{:.1f}GB".format(size_bytes / (1024 * 1024 * 1024))

def safe_filename(filename):
    """生成安全的文件名"""
    invalid_chars = '<>:"/\\|?*'
    safe_name = filename
    for char in invalid_chars:
        safe_name = safe_name.replace(char, '_')
    return safe_name

def generate_timestamped_filename(input_path=None, prefix="video", suffix=""):
    """
    生成带时间戳的文件名
    
    参数:
    - input_path: 输入文件路径（可选），用于提取文件夹名称
    - prefix: 文件名前缀（默认为"video"）
    - suffix: 文件名后缀（如"_with_ad"）
    
    返回: 格式为 "文件夹名_前缀_时间戳_后缀.mp4" 的文件名
    """
    # 生成时间戳 (YYYYMMDD_HHMMSS)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # 获取文件夹名称
    if input_path:
        if os.path.isfile(input_path):
            # 如果是文件，获取其所在目录名
            folder_name = os.path.basename(os.path.dirname(input_path))
        else:
            # 如果是目录，获取目录名
            folder_name = os.path.basename(input_path.rstrip(os.sep))
        
        # 如果文件夹名为空或为根目录标识，使用默认名称
        if not folder_name or folder_name in ['', '.', '..', '\\', '/']:
            folder_name = "video"
    else:
        folder_name = "video"
    
    # 构建文件名
    parts = [safe_filename(folder_name), prefix, timestamp]
    if suffix:
        parts.append(suffix.lstrip('_'))
    
    filename = "_".join(parts) + ".mp4"
    return filename

def check_disk_space(path, required_mb):
    """检查磁盘空间是否足够"""
    try:
        if os.name == 'nt':  # Windows
            free_bytes = os.statvfs(path).f_bavail * os.statvfs(path).f_frsize
        else:
            stat = os.statvfs(path)
            free_bytes = stat.f_bavail * stat.f_frsize
        
        free_mb = free_bytes / (1024 * 1024)
        return free_mb >= required_mb, free_mb
    except:
        return True, 0  # 如果无法检查，假设有足够空间

def estimate_output_size(segments, output_settings):
    """估算输出文件大小（MB）"""
    # 基于分辨率和时长的粗略估算
    width = output_settings.get('width', 1920)
    height = output_settings.get('height', 1080)
    fps = output_settings.get('fps', 30)
    crf = output_settings.get('crf', 23)
    
    total_duration = sum(seg['duration'] for seg in segments)
    
    # 估算比特率（基于分辨率和CRF）
    pixels_per_second = width * height * fps
    
    # CRF对比特率的影响（经验值）
    crf_factor = {18: 4.0, 20: 3.0, 23: 2.0, 26: 1.5, 28: 1.0}.get(crf, 2.0)
    
    # 基础比特率估算（kbps）
    if pixels_per_second > 2000000:  # 1080p及以上
        base_bitrate = 2000
    elif pixels_per_second > 900000:  # 720p
        base_bitrate = 1200
    else:  # 480p及以下
        base_bitrate = 800
    
    estimated_bitrate = base_bitrate * crf_factor
    estimated_size_mb = (estimated_bitrate * total_duration) / (8 * 1024)
    
    return estimated_size_mb

def create_progress_bar(current, total, width=50):
    """创建进度条"""
    if total == 0:
        return "[{}] 0%".format(" " * width)
    
    progress = float(current) / total
    filled = int(width * progress)
    bar = "=" * filled + "-" * (width - filled)
    percentage = int(progress * 100)
    
    return "[{}] {}%".format(bar, percentage)

def print_system_info():
    """打印系统信息"""
    print(u"系统信息:")
    print(u"  操作系统: {}".format(os.name))
    print(u"  Python版本: {}".format(sys.version.split()[0]))
    print(u"  工作目录: {}".format(os.getcwd()))
    
    # 检查FFmpeg版本
    try:
        result = subprocess.check_output(['ffmpeg', '-version'], 
                                       stderr=subprocess.STDOUT,
                                       universal_newlines=True)
        version_line = result.split('\n')[0]
        print(u"  FFmpeg: {}".format(version_line))
    except:
        print(u"  FFmpeg: 未安装或不在PATH中")

def validate_output_path(output_path):
    """验证输出路径"""
    # 检查目录是否存在
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except Exception as e:
            return False, u"无法创建输出目录: {}".format(str(e))
    
    # 检查是否有写权限
    try:
        test_file = os.path.join(output_dir, "test_write_permission.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
    except Exception as e:
        return False, u"输出目录无写权限: {}".format(str(e))
    
    # 检查文件是否已存在
    if os.path.exists(output_path):
        return True, u"警告：输出文件已存在，将被覆盖"
    
    return True, u"输出路径有效"

def get_video_codec_info(video_path):
    """获取视频编码信息"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name,profile,level,pix_fmt',
            '-of', 'csv=p=0', video_path
        ]
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, 
                                       universal_newlines=True).strip()
        
        parts = result.split(',')
        if len(parts) >= 1:
            return {
                'codec': parts[0] if len(parts) > 0 else 'unknown',
                'profile': parts[1] if len(parts) > 1 else 'unknown',
                'level': parts[2] if len(parts) > 2 else 'unknown',
                'pixel_format': parts[3] if len(parts) > 3 else 'unknown'
            }
    except:
        pass
    
    return {'codec': 'unknown', 'profile': 'unknown', 'level': 'unknown', 'pixel_format': 'unknown'}

def suggest_optimal_settings(video_files, processor):
    """根据输入视频建议最优设置"""
    if not video_files:
        return {}
    
    # 分析输入视频
    total_duration = 0
    resolutions = []
    frame_rates = []
    codecs = []
    
    for video_path in video_files[:5]:  # 只分析前5个文件
        info = processor.get_video_info(video_path)
        if info:
            total_duration += info['duration']
            resolutions.append((info['width'], info['height']))
            frame_rates.append(info['fps'])
            codec_info = get_video_codec_info(video_path)
            codecs.append(codec_info['codec'])
    
    if not resolutions:
        return {}
    
    # 找到最常见的分辨率
    resolution_count = {}
    for res in resolutions:
        resolution_count[res] = resolution_count.get(res, 0) + 1
    
    most_common_resolution = max(resolution_count.items(), key=lambda x: x[1])[0]
    
    # 找到最常见的帧率
    if frame_rates:
        avg_fps = sum(frame_rates) / len(frame_rates)
        suggested_fps = int(round(avg_fps))
        if suggested_fps < 24:
            suggested_fps = 24
        elif suggested_fps > 60:
            suggested_fps = 60
    else:
        suggested_fps = 30
    
    suggestions = {
        'width': most_common_resolution[0],
        'height': most_common_resolution[1],
        'fps': suggested_fps
    }
    
    # 根据分辨率建议CRF
    total_pixels = most_common_resolution[0] * most_common_resolution[1]
    if total_pixels >= 1920 * 1080:  # 1080p+
        suggestions['crf'] = 23
        suggestions['preset'] = 'medium'
    elif total_pixels >= 1280 * 720:  # 720p
        suggestions['crf'] = 22
        suggestions['preset'] = 'fast'
    else:  # 480p及以下
        suggestions['crf'] = 21
        suggestions['preset'] = 'fast'
    
    return suggestions

class Timer(object):
    """计时器类"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """开始计时"""
        self.start_time = time.time()
        self.end_time = None
    
    def stop(self):
        """停止计时"""
        if self.start_time is not None:
            self.end_time = time.time()
    
    def elapsed(self):
        """获取已用时间（秒）"""
        if self.start_time is None:
            return 0
        
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time
    
    def elapsed_str(self):
        """获取已用时间的字符串格式"""
        return format_duration(self.elapsed())


def get_video_info(video_path):
    """
    获取视频文件信息
    
    参数:
    - video_path: 视频文件路径
    
    返回:
    字典包含 duration, width, height, fps 等信息，失败返回None
    """
    try:
        # 使用ffprobe获取视频信息
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', video_path
        ]
        
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        
        import json
        data = json.loads(result)
        
        # 查找视频流
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            return None
        
        # 提取基本信息
        duration = float(data.get('format', {}).get('duration', 0))
        width = int(video_stream.get('width', 0))
        height = int(video_stream.get('height', 0))
        
        # 计算帧率
        fps = 30.0  # 默认值
        if 'r_frame_rate' in video_stream:
            fps_str = video_stream['r_frame_rate']
            if '/' in fps_str:
                num, den = fps_str.split('/')
                if int(den) > 0:
                    fps = float(num) / float(den)
            else:
                fps = float(fps_str)
        
        return {
            'duration': duration,
            'width': width,
            'height': height,
            'fps': fps,
            'format': data.get('format', {}).get('format_name', ''),
            'size': int(data.get('format', {}).get('size', 0))
        }
        
    except Exception as e:
        # 如果ffprobe失败，尝试简单的ffmpeg方法
        try:
            cmd = [
                'ffmpeg', '-i', video_path, '-hide_banner',
                '-f', 'null', '-'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, stderr=subprocess.STDOUT)
            output = result.stderr if result.stderr else result.stdout
            
            # 从输出中解析基本信息
            duration = 0
            width = 0 
            height = 0
            fps = 30.0
            
            for line in output.split('\n'):
                if 'Duration:' in line:
                    # 解析时长: Duration: 00:01:23.45
                    import re
                    duration_match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', line)
                    if duration_match:
                        hours = int(duration_match.group(1))
                        minutes = int(duration_match.group(2))
                        seconds = float(duration_match.group(3))
                        duration = hours * 3600 + minutes * 60 + seconds
                
                if 'Video:' in line:
                    # 解析分辨率和帧率
                    import re
                    res_match = re.search(r'(\d+)x(\d+)', line)
                    if res_match:
                        width = int(res_match.group(1))
                        height = int(res_match.group(2))
                    
                    fps_match = re.search(r'(\d+(?:\.\d+)?) fps', line)
                    if fps_match:
                        fps = float(fps_match.group(1))
            
            if duration > 0 and width > 0 and height > 0:
                return {
                    'duration': duration,
                    'width': width,
                    'height': height,
                    'fps': fps,
                    'format': '',
                    'size': 0
                }
        except:
            pass
        
        return None
