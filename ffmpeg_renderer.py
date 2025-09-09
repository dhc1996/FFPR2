# -*- coding: utf-8 -*-
"""
FFmpeg渲染器模块
负责实际的视频合成和渲染工作
"""

import os
import subprocess
import tempfile
import json
from config import Config

class FFmpegRenderer(object):
    """FFmpeg渲染器"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.ffmpeg_path = self.config.get('ffmpeg', 'path')
        self.log_level = self.config.get('ffmpeg', 'log_level')
        self.temp_folder = self.config.get('processing', 'temp_folder')
        self._ensure_temp_folder()
    
    def _ensure_temp_folder(self):
        """确保临时文件夹存在"""
        if not os.path.exists(self.temp_folder):
            try:
                os.makedirs(self.temp_folder)
            except Exception as e:
                print(u"创建临时文件夹失败: {}".format(str(e)))
                self.temp_folder = tempfile.gettempdir()
    
    def create_filter_complex(self, segments, first_video_info=None):
        """创建复杂滤镜字符串，保持第一个视频的原始比例"""
        filter_parts = []
        input_labels = []
        
        # 如果有第一个视频信息，使用其分辨率作为输出分辨率
        if first_video_info:
            output_width = first_video_info['width']
            output_height = first_video_info['height']
            print(u"使用第一个视频的分辨率: {}x{}".format(output_width, output_height))
        else:
            output_width = 1920
            output_height = 1080
        
        for i, segment in enumerate(segments):
            # 为每个输入创建标签
            label = "v{}".format(i)
            
            # 缩放视频到第一个视频的分辨率，保持原始纵横比，使用黑边填充
            simplified_filter = "[{}:v]scale={}:{}:force_original_aspect_ratio=decrease,pad={}:{}:(ow-iw)/2:(oh-ih)/2:black,setpts=PTS-STARTPTS[{}]".format(
                i, output_width, output_height, output_width, output_height, label
            )
            
            filter_parts.append(simplified_filter)
            input_labels.append("[{}]".format(label))
        
        # 连接所有片段
        if len(segments) > 1:
            concat_filter = "{}concat=n={}:v=1:a=0[outv]".format(
                "".join(input_labels), len(segments)
            )
            filter_parts.append(concat_filter)
            output_label = "[outv]"
        else:
            output_label = input_labels[0]
        
        return ";".join(filter_parts), output_label
    
    def render_video(self, segments, output_path, first_video_info=None, **kwargs):
        """渲染最终视频，可选择保持第一个视频的原始比例"""
        # 获取输出参数
        if first_video_info and 'width' not in kwargs and 'height' not in kwargs:
            # 使用第一个视频的分辨率
            output_width = first_video_info['width']
            output_height = first_video_info['height']
            print(u"使用第一个视频的分辨率: {}x{}".format(output_width, output_height))
        else:
            # 使用指定或默认分辨率
            output_width = kwargs.get('width', self.config.get('video', 'default_output_width'))
            output_height = kwargs.get('height', self.config.get('video', 'default_output_height'))
        
        if first_video_info and 'fps' not in kwargs:
            # 使用第一个视频的帧率
            output_fps = int(first_video_info['fps'])
            print(u"使用第一个视频的帧率: {}fps".format(output_fps))
        else:
            output_fps = kwargs.get('fps', self.config.get('video', 'default_fps'))
        
        crf = kwargs.get('crf', self.config.get('video', 'default_crf'))
        preset = kwargs.get('preset', self.config.get('video', 'default_preset'))
        
        print(u"开始渲染视频...")
        print(u"输出参数: {}x{} @ {}fps, CRF={}, preset={}".format(
            output_width, output_height, output_fps, crf, preset
        ))
        
        # 构建ffmpeg命令
        cmd = [self.ffmpeg_path, '-y']  # -y 覆盖输出文件
        
        # 添加日志级别
        cmd.extend(['-loglevel', self.log_level])
        
        # 添加输入文件
        for segment in segments:
            cmd.extend([
                '-ss', str(segment['start_time']),
                '-t', str(segment['duration']),
                '-i', segment['video_path']
            ])
        
        # 创建滤镜
        if len(segments) > 1:
            filter_complex, output_label = self.create_filter_complex(
                segments, first_video_info
            )
            cmd.extend(['-filter_complex', filter_complex])
            cmd.extend(['-map', output_label])
        else:
            # 单个片段，使用简单滤镜（保持原始比例，使用黑边填充）
            cmd.extend([
                '-vf', 'scale={}:{}:force_original_aspect_ratio=decrease,pad={}:{}:(ow-iw)/2:(oh-ih)/2:black'.format(
                    output_width, output_height, output_width, output_height
                )
            ])
        
        # 视频编码参数
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', preset,
            '-crf', str(crf),
            '-r', str(output_fps),
            '-pix_fmt', 'yuv420p'
        ])
        
        # 不包含音频
        cmd.extend(['-an'])
        
        # 输出文件
        cmd.append(output_path)
        
        print(u"FFmpeg命令: {}".format(' '.join(['"{}"'.format(arg) if ' ' in arg else arg for arg in cmd])))
        
        try:
            # 执行命令
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                print(u"视频渲染成功!")
                return True, output_path
            else:
                print(u"FFmpeg执行失败:")
                print(u"返回码: {}".format(process.returncode))
                if stderr:
                    print(u"错误信息:")
                    print(stderr)
                return False, stderr
        
        except Exception as e:
            error_msg = u"执行FFmpeg时发生异常: {}".format(str(e))
            print(error_msg)
            return False, error_msg
    
    def create_concat_file(self, segments, concat_file_path):
        """创建concat文件（备用方法）"""
        try:
            with open(concat_file_path, 'w') as f:
                for segment in segments:
                    # 为每个片段创建临时文件
                    temp_file = self._create_segment_file(segment)
                    if temp_file:
                        f.write("file '{}'\n".format(temp_file.replace('\\', '/')))
            return True
        except Exception as e:
            print(u"创建concat文件失败: {}".format(str(e)))
            return False
    
    def _create_segment_file(self, segment):
        """创建单个片段的临时文件"""
        try:
            temp_name = "segment_{}_{}.mp4".format(
                segment['id'], 
                os.path.basename(segment['video_path']).split('.')[0]
            )
            temp_path = os.path.join(self.temp_folder, temp_name)
            
            cmd = [
                self.ffmpeg_path, '-y',
                '-ss', str(segment['start_time']),
                '-t', str(segment['duration']),
                '-i', segment['video_path'],
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-an',  # 去除音频
                temp_path
            ]
            
            subprocess.check_call(cmd, 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
            return temp_path
        except Exception as e:
            print(u"创建片段文件失败: {}".format(str(e)))
            return None
    
    def render_with_concat(self, segments, output_path, first_video_info=None, **kwargs):
        """使用concat方法渲染（备用方案），支持保持第一个视频的原始比例"""
        concat_file = os.path.join(self.temp_folder, "concat_list.txt")
        
        try:
            # 创建所有片段文件
            print(u"创建临时片段文件...")
            if not self.create_concat_file(segments, concat_file):
                return False, u"创建concat文件失败"
            
            # 合并视频
            print(u"合并视频片段...")
            if first_video_info and 'width' not in kwargs and 'height' not in kwargs:
                # 使用第一个视频的分辨率
                output_width = first_video_info['width']
                output_height = first_video_info['height']
                print(u"使用第一个视频的分辨率: {}x{}".format(output_width, output_height))
            else:
                output_width = kwargs.get('width', self.config.get('video', 'default_output_width'))
                output_height = kwargs.get('height', self.config.get('video', 'default_output_height'))
            
            cmd = [
                self.ffmpeg_path, '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-vf', 'scale={}:{}:force_original_aspect_ratio=decrease,pad={}:{}:(ow-iw)/2:(oh-ih)/2:black'.format(
                    output_width, output_height, output_width, output_height
                ),
                '-c:v', 'libx264',
                '-preset', kwargs.get('preset', 'medium'),
                '-crf', str(kwargs.get('crf', 23)),
                '-an',
                output_path
            ]
            
            subprocess.check_call(cmd)
            return True, output_path
            
        except Exception as e:
            error_msg = u"concat方法渲染失败: {}".format(str(e))
            print(error_msg)
            return False, error_msg
        finally:
            # 清理临时文件
            self.cleanup_temp_files()
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            if os.path.exists(self.temp_folder):
                for file in os.listdir(self.temp_folder):
                    if file.startswith('segment_') or file == 'concat_list.txt':
                        file_path = os.path.join(self.temp_folder, file)
                        try:
                            os.remove(file_path)
                        except:
                            pass
        except Exception as e:
            print(u"清理临时文件时出错: {}".format(str(e)))
    
    def get_output_info(self, output_path):
        """获取输出视频信息"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', output_path
            ]
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            data = json.loads(result)
            
            format_info = data.get('format', {})
            streams = data.get('streams', [])
            
            video_stream = None
            for stream in streams:
                if stream['codec_type'] == 'video':
                    video_stream = stream
                    break
            
            info = {
                'duration': float(format_info.get('duration', 0)),
                'size': int(format_info.get('size', 0)),
                'bitrate': int(format_info.get('bit_rate', 0))
            }
            
            if video_stream:
                info['width'] = int(video_stream.get('width', 0))
                info['height'] = int(video_stream.get('height', 0))
                r_frame_rate = video_stream.get('r_frame_rate', '30/1')
                try:
                    if '/' in r_frame_rate:
                        num, den = map(float, r_frame_rate.split('/'))
                        info['fps'] = num / den if den != 0 else 30
                    else:
                        info['fps'] = float(r_frame_rate)
                except:
                    info['fps'] = 30
            
            return info
        except Exception as e:
            print(u"获取输出视频信息失败: {}".format(str(e)))
            return None
