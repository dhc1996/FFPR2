# -*- coding: utf-8 -*-
"""
背景音乐添加模块
为视频添加背景音乐，支持音量调节、循环播放、淡入淡出等功能
"""

import os
import sys
import subprocess
import json
from config import Config

def safe_print(text):
    """安全的打印函数，处理编码问题"""
    try:
        # 对于Python 2.7，确保正确编码
        if hasattr(text, 'encode'):
            print(text.encode('gbk', 'replace'))
        else:
            print(str(text).encode('gbk', 'replace'))
    except:
        try:
            print(str(text))
        except:
            print("Error: Cannot display text")

class BackgroundMusicProcessor(object):
    """背景音乐处理器"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.ffmpeg_path = self.config.get('ffmpeg', 'path') or 'ffmpeg'
        self.ffprobe_path = self.config.get('ffmpeg', 'ffprobe_path') or 'ffprobe'
        
    def get_video_info(self, video_path):
        """获取视频信息"""
        try:
            # 使用shell=True在Windows上更可靠
            cmd = [
                self.ffprobe_path, '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            # 在Windows上使用shell=True
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
            
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
            
            if not result_str or result_str.strip() == '':
                safe_print(u"FFprobe返回空结果")
                return None
            
            data = json.loads(result_str)
            
            # 确保 streams 存在且不为 None
            streams = data.get('streams')
            if streams is None:
                safe_print(u"FFprobe输出中没有streams字段")
                return None
            
            if not isinstance(streams, list) or len(streams) == 0:
                safe_print(u"视频文件没有有效的流信息")
                return None
            
            video_stream = None
            audio_streams = []
            
            for stream in streams:
                if stream and stream.get('codec_type') == 'video':
                    video_stream = stream
                elif stream and stream.get('codec_type') == 'audio':
                    audio_streams.append(stream)
            
            if not video_stream:
                safe_print(u"视频文件中没有找到视频流")
                return None
            
            # 确保格式信息存在
            format_info = data.get('format')
            if not format_info:
                safe_print(u"FFprobe输出中没有format字段")
                return None
            
            duration = format_info.get('duration')
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
            
            # 计算帧率
            r_frame_rate = video_stream.get('r_frame_rate', '30/1')
            try:
                if r_frame_rate and '/' in str(r_frame_rate):
                    num, den = map(float, str(r_frame_rate).split('/'))
                    info['fps'] = num / den if den != 0 else 30
                elif r_frame_rate:
                    info['fps'] = float(r_frame_rate)
            except:
                info['fps'] = 30
            
            return info
            
        except subprocess.CalledProcessError as e:
            safe_print(u"FFprobe执行失败: {}".format(str(e)))
            return None
        except ValueError as e:  # Python 2.7中JSON错误是ValueError
            safe_print(u"解析FFprobe输出失败: {}".format(str(e)))
            return None
        except Exception as e:
            safe_print(u"获取视频信息失败: {}".format(str(e)))
            return None
    
    def get_audio_info(self, audio_path):
        """获取音频信息"""
        try:
            cmd = [
                self.ffprobe_path, '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', audio_path
            ]
            # 在Windows上使用shell=True
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
            
            # 尝试不同的编码方式解析结果
            try:
                if isinstance(result, bytes):
                    # 先尝试 UTF-8
                    try:
                        result_str = result.decode('utf-8')
                    except UnicodeDecodeError:
                        # 再尝试 GBK
                        try:
                            result_str = result.decode('gbk')
                        except UnicodeDecodeError:
                            # 最后使用忽略错误的方式
                            result_str = result.decode('utf-8', 'ignore')
                else:
                    result_str = result
            except Exception:
                # 如果所有解码都失败，尝试直接转为字符串
                result_str = str(result)
            
            # 额外处理JSON中的转义字符
            try:
                data = json.loads(result_str)
            except ValueError as e:
                # 如果JSON解析失败，尝试清理字符串
                safe_print(u"第一次JSON解析失败，尝试清理字符串...")
                # 移除可能的BOM标记和控制字符
                result_str = result_str.strip().replace('\ufeff', '')
                data = json.loads(result_str)
            
            # 确保 streams 存在且不为 None
            streams = data.get('streams', [])
            if not streams:
                safe_print(u"音频文件没有有效的流信息")
                return None
            
            audio_stream = None
            for stream in streams:
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                safe_print(u"音频文件中没有找到音频流")
                return None
            
            # 确保格式信息存在
            format_info = data.get('format', {})
            duration = format_info.get('duration')
            if duration is None:
                safe_print(u"无法获取音频时长信息")
                return None
            
            info = {
                'duration': float(duration),
                'sample_rate': int(audio_stream.get('sample_rate', 44100)),
                'channels': int(audio_stream.get('channels', 2)),
                'codec': audio_stream.get('codec_name', 'unknown')
            }
            
            return info
            
        except subprocess.CalledProcessError as e:
            safe_print(u"FFprobe执行失败: {}".format(str(e)))
            return None
        except ValueError as e:  # Python 2.7中JSON错误是ValueError
            safe_print(u"解析FFprobe输出失败: {}".format(str(e)))
            return None
        except Exception as e:
            safe_print(u"获取音频信息失败: {}".format(str(e)))
            return None
    
    def validate_files(self, video_path, music_path):
        """验证输入文件"""
        if not os.path.exists(video_path):
            return False, u"视频文件不存在: {}".format(video_path)
        
        if not os.path.exists(music_path):
            return False, u"音乐文件不存在: {}".format(music_path)
        
        # 检查视频信息
        video_info = self.get_video_info(video_path)
        if not video_info:
            return False, u"无法读取视频文件信息"
        
        # 检查音频信息
        audio_info = self.get_audio_info(music_path)
        if not audio_info:
            return False, u"无法读取音乐文件信息"
        
        return True, {'video': video_info, 'audio': audio_info}
    
    def add_background_music(self, video_path, music_path, output_path, **options):
        """
        为视频添加背景音乐
        
        参数:
        - video_path: 输入视频路径
        - music_path: 背景音乐路径
        - output_path: 输出视频路径
        - options: 配置选项
          - music_volume: 背景音乐音量 (0.0-1.0, 默认0.3)
          - original_volume: 原始音频音量 (0.0-1.0, 默认0.7)
          - loop_music: 是否循环音乐 (默认True)
          - fade_in: 淡入时间（秒，默认2.0）
          - fade_out: 淡出时间（秒，默认2.0）
          - start_time: 音乐开始时间（秒，默认0.0）
        """
        
        safe_print(u"开始添加背景音乐...")
        safe_print(u"输入视频: {}".format(os.path.basename(video_path)))
        safe_print(u"背景音乐: {}".format(os.path.basename(music_path)))
        
        # 验证文件
        is_valid, result = self.validate_files(video_path, music_path)
        if not is_valid:
            return False, result
        
        video_info = result['video']
        audio_info = result['audio']
        
        # 获取选项
        music_volume = options.get('music_volume', 0.3)
        original_volume = options.get('original_volume', 0.7)
        loop_music = options.get('loop_music', True)
        fade_in = options.get('fade_in', 2.0)
        fade_out = options.get('fade_out', 2.0)
        start_time = options.get('start_time', 0.0)
        
        print(u"视频时长: {:.1f}秒".format(video_info['duration']))
        print(u"音乐时长: {:.1f}秒".format(audio_info['duration']))
        print(u"配置: 背景音量{:.0%}, 原音量{:.0%}, 循环:{}, 淡入:{:.1f}s, 淡出:{:.1f}s".format(
            music_volume, original_volume, u"是" if loop_music else u"否", fade_in, fade_out
        ))
        
        # 构建FFmpeg命令
        cmd = [self.ffmpeg_path, '-y']
        
        # 输入文件
        cmd.extend(['-i', video_path])
        cmd.extend(['-i', music_path])
        
        # 构建音频滤镜
        audio_filter = self._build_audio_filter(
            video_info, audio_info, music_volume, original_volume,
            loop_music, fade_in, fade_out, start_time
        )
        
        # 添加滤镜
        if audio_filter:
            cmd.extend(['-filter_complex', audio_filter])
            if video_info['has_audio']:
                cmd.extend(['-map', '0:v', '-map', '[audio_out]'])
            else:
                cmd.extend(['-map', '0:v', '-map', '[music_out]'])
        else:
            # 简单模式：只是添加背景音乐
            cmd.extend(['-map', '0:v', '-map', '1:a'])
        
        # 视频编码设置（复制视频流以保持质量）
        cmd.extend(['-c:v', 'copy'])
        
        # 音频编码设置
        cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
        
        # 输出文件
        cmd.append(output_path)
        
        print(u"执行FFmpeg命令...")
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                if os.path.exists(output_path):
                    print(u"背景音乐添加成功！")
                    print(u"输出文件: {}".format(output_path))
                    
                    # 显示文件大小
                    file_size = os.path.getsize(output_path) / (1024 * 1024.0)
                    print(u"文件大小: {:.1f}MB".format(file_size))
                    
                    return True, output_path
                else:
                    return False, u"输出文件未生成"
            else:
                print(u"FFmpeg执行失败:")
                print(u"返回码: {}".format(process.returncode))
                if stderr:
                    print(u"错误信息: {}".format(stderr[-500:]))  # 只显示最后500字符
                return False, stderr
                
        except Exception as e:
            error_msg = u"执行FFmpeg时发生异常: {}".format(str(e))
            print(error_msg)
            return False, error_msg
    
    def _build_audio_filter(self, video_info, audio_info, music_volume, 
                           original_volume, loop_music, fade_in, fade_out, start_time):
        """构建音频滤镜"""
        
        video_duration = video_info['duration']
        music_duration = audio_info['duration']
        
        # 音乐处理滤镜部分
        music_filters = []
        
        # 如果需要循环音乐
        if loop_music and music_duration < video_duration:
            # 计算需要循环的次数
            loop_count = int(video_duration / music_duration) + 1
            music_filters.append("[1:a]aloop=loop={}:size={}[music_looped]".format(
                loop_count - 1, int(music_duration * 44100)  # 样本数
            ))
            music_input = "[music_looped]"
        else:
            music_input = "[1:a]"
        
        # 音乐时间裁剪（匹配视频时长）
        if start_time > 0:
            music_filters.append("{}atrim=start={}:duration={}[music_trimmed]".format(
                music_input, start_time, video_duration
            ))
            music_input = "[music_trimmed]"
        else:
            music_filters.append("{}atrim=duration={}[music_trimmed]".format(
                music_input, video_duration
            ))
            music_input = "[music_trimmed]"
        
        # 音量调节
        music_filters.append("{}volume={}[music_vol]".format(music_input, music_volume))
        music_input = "[music_vol]"
        
        # 淡入淡出效果
        if fade_in > 0 or fade_out > 0:
            fade_filter = music_input
            if fade_in > 0:
                fade_filter += "afade=t=in:ss=0:d={}".format(fade_in)
            if fade_out > 0:
                if fade_in > 0:
                    fade_filter += ","
                fade_filter += "afade=t=out:st={}:d={}".format(
                    max(0, video_duration - fade_out), fade_out
                )
            fade_filter += "[music_faded]"
            music_filters.append(fade_filter)
            music_input = "[music_faded]"
        
        # 如果视频有原始音频，进行混合
        if video_info['has_audio']:
            # 原始音频处理
            original_filters = []
            original_filters.append("[0:a]volume={}[original_vol]".format(original_volume))
            
            # 混合音频
            mix_filter = "[original_vol]{}amix=inputs=2:duration=first[audio_out]".format(music_input)
            
            # 组合所有滤镜
            all_filters = music_filters + original_filters + [mix_filter]
            return ";".join(all_filters)
        else:
            # 视频没有原始音频，直接使用背景音乐
            music_filters.append("{}aformat=sample_rates=44100:channel_layouts=stereo[music_out]".format(music_input))
            return ";".join(music_filters)
    
    def create_silent_background(self, video_path, output_path, music_volume=0.5):
        """
        为没有音频的视频创建静音背景，然后添加音乐
        （这是一个简化的方法）
        """
        try:
            cmd = [
                self.ffmpeg_path, '-y',
                '-i', video_path,
                '-f', 'lavfi',
                '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-map', '0:v',
                '-map', '1:a',
                '-shortest',
                output_path
            ]
            
            result = subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result == 0
            
        except Exception as e:
            print(u"创建静音背景失败: {}".format(str(e)))
            return False
