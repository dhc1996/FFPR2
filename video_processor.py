# -*- coding: utf-8 -*-
"""
视频处理工具模块
包含视频信息获取、片段处理等功能
"""

import os
import subprocess
import json
import random
import tempfile
from config import Config

class VideoProcessor(object):
    """视频处理器"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.ffmpeg_path = self.config.get('ffmpeg', 'path')
        self.ffprobe_path = self.config.get('ffmpeg', 'ffprobe_path')
        self.log_level = self.config.get('ffmpeg', 'log_level')
    
    def check_ffmpeg(self):
        """检查ffmpeg是否可用"""
        try:
            subprocess.check_output([self.ffmpeg_path, '-version'], 
                                   stderr=subprocess.STDOUT)
            return True
        except Exception:
            return False
    
    def get_video_info(self, video_path):
        """获取视频详细信息"""
        try:
            cmd = [
                self.ffprobe_path, '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            data = json.loads(result)
            
            video_info = {
                'path': video_path,
                'format': data.get('format', {}),
                'streams': data.get('streams', [])
            }
            
            # 提取主要信息
            format_info = video_info['format']
            video_info['duration'] = float(format_info.get('duration', 0))
            video_info['size'] = int(format_info.get('size', 0))
            video_info['bitrate'] = int(format_info.get('bit_rate', 0))
            
            # 查找视频流
            video_stream = None
            audio_streams = []
            
            for stream in video_info['streams']:
                if stream['codec_type'] == 'video':
                    video_stream = stream
                elif stream['codec_type'] == 'audio':
                    audio_streams.append(stream)
            
            if video_stream:
                video_info['width'] = int(video_stream.get('width', 0))
                video_info['height'] = int(video_stream.get('height', 0))
                
                # 计算帧率
                r_frame_rate = video_stream.get('r_frame_rate', '30/1')
                try:
                    if '/' in r_frame_rate:
                        num, den = map(float, r_frame_rate.split('/'))
                        video_info['fps'] = num / den if den != 0 else 30
                    else:
                        video_info['fps'] = float(r_frame_rate)
                except:
                    video_info['fps'] = 30
                
                video_info['codec'] = video_stream.get('codec_name', 'unknown')
            
            video_info['has_audio'] = len(audio_streams) > 0
            video_info['audio_streams'] = len(audio_streams)
            
            return video_info
            
        except Exception as e:
            print(u"获取视频信息失败: {} - {}".format(video_path, str(e)))
            return None
    
    def validate_video_file(self, video_path):
        """验证视频文件是否有效"""
        if not os.path.exists(video_path):
            return False, u"文件不存在"
        
        if not os.path.isfile(video_path):
            return False, u"不是文件"
        
        # 检查文件扩展名
        supported_formats = self.config.get('video', 'supported_formats')
        ext = os.path.splitext(video_path)[1].lower()
        if ext not in supported_formats:
            return False, u"不支持的文件格式: {}".format(ext)
        
        # 检查文件是否可读
        try:
            with open(video_path, 'rb') as f:
                f.read(1024)  # 尝试读取前1KB
        except Exception as e:
            return False, u"文件不可读: {}".format(str(e))
        
        # 使用ffprobe验证
        info = self.get_video_info(video_path)
        if not info or info['duration'] <= 0:
            return False, u"无效的视频文件"
        
        return True, u"有效"
    
    def scan_videos(self, folder_path, recursive=True):
        """扫描文件夹中的视频文件"""
        video_files = []
        invalid_files = []
        
        if not os.path.exists(folder_path):
            print(u"错误：路径不存在: {}".format(folder_path))
            return video_files, invalid_files
        
        if os.path.isfile(folder_path):
            # 单个文件
            is_valid, message = self.validate_video_file(folder_path)
            if is_valid:
                video_files.append(folder_path)
            else:
                invalid_files.append((folder_path, message))
            return video_files, invalid_files
        
        # 文件夹扫描
        supported_formats = self.config.get('video', 'supported_formats')
        
        if recursive:
            walker = os.walk(folder_path)
        else:
            items = []
            try:
                for item in os.listdir(folder_path):
                    item_path = os.path.join(folder_path, item)
                    if os.path.isfile(item_path):
                        items.append(item)
                walker = [(folder_path, [], items)]
            except Exception as e:
                print(u"读取文件夹失败: {}".format(str(e)))
                return video_files, invalid_files
        
        for root, dirs, files in walker:
            for file in files:
                file_lower = file.lower()
                for ext in supported_formats:
                    if file_lower.endswith(ext):
                        full_path = os.path.join(root, file)
                        is_valid, message = self.validate_video_file(full_path)
                        if is_valid:
                            video_files.append(full_path)
                            print(u"发现有效视频: {}".format(file))
                        else:
                            invalid_files.append((full_path, message))
                            print(u"无效视频: {} - {}".format(file, message))
                        break
        
        return video_files, invalid_files
    
    def create_segments_plan(self, video_files, target_duration, strategy='random'):
        """创建视频片段计划"""
        if not video_files:
            return []
        
        # 获取所有视频信息
        video_infos = []
        total_duration = 0
        
        for video_path in video_files:
            info = self.get_video_info(video_path)
            if info and info['duration'] > 0:
                video_infos.append(info)
                total_duration += info['duration']
        
        if not video_infos:
            print(u"没有有效的视频文件")
            return []
        
        print(u"总可用时长: {:.2f}秒".format(total_duration))
        
        if total_duration < target_duration:
            print(u"警告：可用视频总时长小于目标时长，将循环使用视频")
        
        # 根据策略生成片段
        if strategy == 'random':
            return self._create_random_segments(video_infos, target_duration)
        elif strategy == 'sequential':
            return self._create_sequential_segments(video_infos, target_duration)
        elif strategy == 'balanced':
            return self._create_balanced_segments(video_infos, target_duration)
        else:
            return self._create_random_segments(video_infos, target_duration)
    
    def _create_random_segments(self, video_infos, target_duration):
        """随机策略创建片段"""
        segments = []
        remaining_duration = target_duration
        min_segment_duration = self.config.get('processing', 'min_segment_duration')
        
        # 设置随机种子（如果配置了的话）
        seed = self.config.get('processing', 'random_seed')
        if seed is not None:
            random.seed(seed)
        
        video_list = video_infos[:]
        random.shuffle(video_list)
        
        segment_id = 0
        while remaining_duration > 0:
            if not video_list:
                video_list = video_infos[:]
                random.shuffle(video_list)
            
            video_info = video_list.pop(0)
            video_duration = video_info['duration']
            
            # 计算片段时长
            max_segment_duration = min(remaining_duration, video_duration)
            if max_segment_duration < min_segment_duration:
                segment_duration = max_segment_duration
            else:
                segment_duration = random.uniform(min_segment_duration, max_segment_duration)
            
            # 随机选择起始点
            if video_duration > segment_duration:
                max_start = video_duration - segment_duration
                start_time = random.uniform(0, max_start)
            else:
                start_time = 0
                segment_duration = video_duration
            
            segments.append({
                'id': segment_id,
                'video_path': video_info['path'],
                'start_time': start_time,
                'duration': segment_duration,
                'video_info': video_info
            })
            
            remaining_duration -= segment_duration
            segment_id += 1
        
        return segments
    
    def _create_sequential_segments(self, video_infos, target_duration):
        """顺序策略创建片段"""
        segments = []
        remaining_duration = target_duration
        min_segment_duration = self.config.get('processing', 'min_segment_duration')
        
        segment_id = 0
        video_index = 0
        current_start = 0
        
        while remaining_duration > 0:
            if video_index >= len(video_infos):
                video_index = 0
                current_start = 0
            
            video_info = video_infos[video_index]
            video_duration = video_info['duration']
            
            # 检查当前视频是否还有可用时长
            available_duration = video_duration - current_start
            if available_duration <= 0:
                video_index += 1
                current_start = 0
                continue
            
            # 计算片段时长
            segment_duration = min(remaining_duration, available_duration)
            if segment_duration < min_segment_duration and remaining_duration > min_segment_duration:
                video_index += 1
                current_start = 0
                continue
            
            segments.append({
                'id': segment_id,
                'video_path': video_info['path'],
                'start_time': current_start,
                'duration': segment_duration,
                'video_info': video_info
            })
            
            current_start += segment_duration
            remaining_duration -= segment_duration
            segment_id += 1
            
            # 如果当前视频用完了，移到下一个
            if current_start >= video_duration:
                video_index += 1
                current_start = 0
        
        return segments
    
    def _create_balanced_segments(self, video_infos, target_duration):
        """平衡策略创建片段"""
        # 尝试让每个视频都贡献大致相同的时长
        segments = []
        num_videos = len(video_infos)
        duration_per_video = target_duration / num_videos
        min_segment_duration = self.config.get('processing', 'min_segment_duration')
        
        segment_id = 0
        for video_info in video_infos:
            video_duration = video_info['duration']
            target_from_this_video = duration_per_video
            
            # 如果视频太短，就用全部
            if video_duration <= target_from_this_video:
                segments.append({
                    'id': segment_id,
                    'video_path': video_info['path'],
                    'start_time': 0,
                    'duration': video_duration,
                    'video_info': video_info
                })
                segment_id += 1
            else:
                # 视频较长，随机选择片段
                start_time = random.uniform(0, video_duration - target_from_this_video)
                segments.append({
                    'id': segment_id,
                    'video_path': video_info['path'],
                    'start_time': start_time,
                    'duration': target_from_this_video,
                    'video_info': video_info
                })
                segment_id += 1
        
        # 如果总时长不够，添加更多片段
        current_total = sum(seg['duration'] for seg in segments)
        if current_total < target_duration:
            remaining = target_duration - current_total
            additional_segments = self._create_random_segments(video_infos, remaining)
            for seg in additional_segments:
                seg['id'] = segment_id
                segment_id += 1
            segments.extend(additional_segments)
        
        return segments
