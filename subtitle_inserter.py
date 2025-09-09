# -*- coding: utf-8 -*-
"""
字幕插入器模块
将字幕添加到视频中
"""

import os
import sys
import time
import subprocess
from subtitle_generator import SubtitleGenerator
from text_to_speech import TextToSpeechGenerator
from utils import generate_timestamped_filename, validate_output_path

class SubtitleInserter(object):
    """字幕插入器类"""
    
    def __init__(self):
        self.subtitle_generator = SubtitleGenerator()
        self.tts_generator = TextToSpeechGenerator()
    
    def insert_subtitles_to_video(self, video_path, subtitle_source, output_path=None, 
                                 style='default', auto_fit=True, split_mode='smart_split', 
                                 start_time=0.0, enable_speech=False, voice='zh-CN-XiaoxiaoNeural'):
        """
        将字幕插入视频
        
        参数:
        - video_path: 输入视频路径
        - subtitle_source: 字幕源（可以是文案文档路径或字幕数据）
        - output_path: 输出视频路径（可选）
        - style: 字幕样式
        - auto_fit: 是否自动调整字幕时间以适应视频长度
        - split_mode: 字幕分割模式
        - start_time: 字幕开始时间（秒），默认为0
        - enable_speech: 是否启用语音合成
        - voice: 语音类型
        
        返回: 输出视频路径
        """
        if not os.path.exists(video_path):
            raise ValueError(u"输入视频文件不存在: {}".format(video_path))
        
        # 获取视频信息
        video_info = self._get_video_info(video_path)
        if not video_info:
            raise ValueError(u"无法获取视频信息")
        
        # 处理字幕源
        if hasattr(subtitle_source, 'encode'):  # 检查是否为字符串类型（包括unicode）
            # 字幕源是文件路径
            if os.path.exists(subtitle_source):
                # 使用视频长度进行时间分配
                video_duration = video_info.get('duration', 30.0)
                
                # 生成字幕（使用视频长度进行时间分配）
                subtitles = self.subtitle_generator.read_text_document(
                    subtitle_source, 
                    split_mode=split_mode, 
                    start_time=start_time,
                    video_duration=video_duration  # 传递视频长度
                )
            else:
                raise ValueError(u"字幕源文件不存在: {}".format(subtitle_source))
        elif isinstance(subtitle_source, list):
            # 字幕源是字幕数据列表
            subtitles = subtitle_source
        else:
            raise ValueError(u"不支持的字幕源类型: {}".format(type(subtitle_source)))
        
        if not subtitles:
            raise ValueError(u"没有可用的字幕内容")
        
        # 验证字幕
        errors = self.subtitle_generator.validate_subtitles(subtitles)
        if errors:
            print(u"字幕验证警告:")
            for error in errors:
                print(u"  - {}".format(error))
        
        # 调整字幕时间 - 保持正常语速，不强制适应视频长度
        if auto_fit:
            subtitles = self.subtitle_generator.adjust_subtitle_timing(
                subtitles, video_info['duration'], auto_fit=False
            )
        
        # 分割过长的字幕
        subtitles = self.subtitle_generator.split_long_subtitles(subtitles)
        
        # 预览字幕
        self.subtitle_generator.preview_subtitles(subtitles)
        
        # 生成输出路径
        if not output_path:
            output_path = self._generate_output_path(video_path)
        
        # 验证输出路径
        is_valid, message = validate_output_path(output_path)
        if not is_valid:
            raise ValueError(message)
        
        # 创建临时SRT文件
        temp_srt_path = self._create_temp_srt_file(subtitles)
        
        # 生成语音音频（如果启用）
        audio_info = None
        if enable_speech:
            print(u"正在生成语音音频...")
            try:
                audio_info = self.tts_generator.generate_speech_for_subtitles(
                    subtitles, voice=voice, engine='auto'
                )
                print(u"语音生成完成！处理了{}个片段".format(audio_info.get('segments_count', 0)))
                print(u"最终语音文件: {}".format(audio_info.get('merged_audio', '未知')))
            except Exception as e:
                print(u"语音生成失败: {}".format(str(e)))
                print(u"将继续仅添加字幕...")
                enable_speech = False
        
        try:
            # 执行字幕和语音插入
            if enable_speech and audio_info:
                success = self._execute_subtitle_and_speech_insertion(
                    video_path, temp_srt_path, audio_info['merged_audio'], output_path, style, video_info
                )
            else:
                success = self._execute_subtitle_insertion(
                    video_path, temp_srt_path, output_path, style
                )
            
            if success:
                print(u"处理完成！")
                if enable_speech:
                    print(u"字幕和语音已添加到视频")
                else:
                    print(u"字幕已添加到视频")
                
                # 安全处理输出路径的显示
                try:
                    if isinstance(output_path, unicode):
                        output_display = output_path
                    else:
                        output_display = output_path.decode('utf-8') if sys.version_info[0] == 2 else output_path
                    print(u"输出文件: {}".format(output_display))
                except:
                    print(u"输出文件: {}".format(os.path.basename(output_path)))
                
                try:
                    if isinstance(temp_srt_path, unicode):
                        srt_display = temp_srt_path
                    else:
                        srt_display = temp_srt_path.decode('utf-8') if sys.version_info[0] == 2 else temp_srt_path
                    print(u"SRT字幕文件: {}".format(srt_display))
                except:
                    print(u"SRT字幕文件: {}".format(os.path.basename(temp_srt_path)))
                
                # 显示文件信息
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path) / (1024 * 1024)
                    print(u"文件大小: {:.2f} MB".format(file_size))
                
                return output_path
            else:
                raise RuntimeError(u"视频处理失败")
        
        finally:
            # SRT文件保存在srt文件夹中，不删除以便用户使用
            # 如果需要清理，用户可以手动删除srt文件夹中的文件
            pass
    
    def _get_video_info(self, video_path):
        """获取视频基本信息"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, 
                                           universal_newlines=True)
            
            import json
            data = json.loads(result)
            
            # 查找视频流和音频流
            video_stream = None
            audio_stream = None
            
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video' and not video_stream:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and not audio_stream:
                    audio_stream = stream
            
            if not video_stream:
                return None
            
            # 获取时长
            duration = float(data.get('format', {}).get('duration', 0))
            if duration == 0:
                duration = float(video_stream.get('duration', 0))
            
            # 获取分辨率
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            
            # 获取帧率
            fps_str = video_stream.get('r_frame_rate', '30/1')
            if '/' in fps_str:
                num, den = map(float, fps_str.split('/'))
                fps = num / den if den != 0 else 30
            else:
                fps = float(fps_str)
            
            return {
                'duration': duration,
                'width': width,
                'height': height,
                'fps': fps,
                'has_audio': audio_stream is not None
            }
            
            return {
                'duration': duration,
                'width': width,
                'height': height,
                'fps': fps
            }
        
        except Exception as e:
            print(u"获取视频信息时出错: {}".format(str(e)))
            return None
    
    def _generate_output_path(self, input_video_path):
        """生成输出文件路径"""
        # 使用工具函数生成带时间戳的文件名
        filename = generate_timestamped_filename(
            input_video_path, "subtitle", "_with_subtitles"
        )
        
        # 使用项目的output目录
        project_dir = os.path.dirname(__file__)
        output_dir = os.path.join(project_dir, 'output')
        
        # 确保output目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        return os.path.join(output_dir, filename)
    
    def _create_temp_srt_file(self, subtitles):
        """创建SRT文件并保存在srt文件夹中"""
        # 使用项目根目录下的srt文件夹
        srt_dir = os.path.join(os.path.dirname(__file__), 'srt')
        if not os.path.exists(srt_dir):
            os.makedirs(srt_dir)
        
        # 生成带时间戳的SRT文件名
        timestamp = int(time.time())
        srt_filename = "subtitle_generated_{}.srt".format(timestamp)
        srt_path = os.path.join(srt_dir, srt_filename)
        
        return self.subtitle_generator.generate_srt_file(subtitles, srt_path)
    
    def _execute_subtitle_and_speech_insertion(self, video_path, srt_path, audio_path, output_path, style, video_info):
        """执行字幕和语音插入"""
        try:
            # 获取工作目录和文件名
            srt_dir = os.path.dirname(srt_path)
            
            print(u"正在合成字幕和语音...")
            
            # 根据原视频是否有音频使用不同的混合策略
            has_original_audio = video_info.get('has_audio', False)
            
            # 确保使用绝对路径
            abs_video_path = os.path.abspath(video_path)
            abs_audio_path = os.path.abspath(audio_path)
            abs_output_path = os.path.abspath(output_path)
            abs_srt_path = os.path.abspath(srt_path)
            
            # 获取相对于项目根目录的SRT路径
            project_root = os.path.dirname(__file__)
            rel_srt_path = os.path.relpath(abs_srt_path, project_root).replace('\\', '/') 
            
            if has_original_audio:
                # 原视频有音频：混合原音频和语音，并烧录字幕
                print(u"检测到原视频有音频，将混合原音频和语音并烧录字幕")
                cmd = [
                    'ffmpeg', '-y',  # 覆盖输出文件
                    '-i', abs_video_path,  # 输入视频
                    '-i', abs_audio_path,  # 输入语音音频
                    '-vf', 'subtitles={}'.format(rel_srt_path),  # 烧录字幕到视频（使用相对路径）
                    '-filter_complex', '[1:a]volume=0.8[speech];[0:a][speech]amix=inputs=2:duration=first:dropout_transition=2[audio_out]',  # 音频混合
                    '-map', '0:v',  # 映射视频流
                    '-map', '[audio_out]',  # 映射混合后的音频流
                    '-c:v', 'libx264',  # 视频编码器
                    '-crf', '23',  # 质量设置
                    '-preset', 'medium',  # 编码速度
                    '-c:a', 'aac',  # 音频编码器
                    '-b:a', '192k',  # 音频比特率
                    '-t', str(video_info.get('duration', 30.0)),  # 以视频长度为准
                    abs_output_path
                ]
            else:
                # 原视频无音频：只使用生成的语音，并烧录字幕
                print(u"原视频无音频，将添加生成的语音并烧录字幕")
                cmd = [
                    'ffmpeg', '-y',  # 覆盖输出文件
                    '-i', abs_video_path,  # 输入视频
                    '-i', abs_audio_path,  # 输入语音音频
                    '-vf', 'subtitles={}'.format(rel_srt_path),  # 烧录字幕到视频（使用相对路径）
                    '-map', '0:v',  # 映射视频流
                    '-map', '1:a',  # 映射语音音频流
                    '-c:v', 'libx264',  # 视频编码器
                    '-crf', '23',  # 质量设置
                    '-preset', 'medium',  # 编码速度
                    '-c:a', 'aac',  # 音频编码器
                    '-b:a', '192k',  # 音频比特率
                    '-t', str(video_info.get('duration', 30.0)),  # 以视频长度为准
                    abs_output_path
                ]
            
            print(u"FFmpeg命令: {}".format(' '.join(cmd)))
            
            # 使用绝对路径执行命令，避免路径问题
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True
                # 移除cwd参数，使用当前工作目录
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                return True
            else:
                print(u"FFmpeg错误输出:")
                print(stderr)
                return False
        
        except Exception as e:
            print(u"执行字幕和语音插入时出错: {}".format(str(e)))
            return False
    
    def _execute_subtitle_insertion(self, video_path, srt_path, output_path, style):
        """执行字幕插入"""
        try:
            # 创建字幕过滤器
            subtitle_filter = self.subtitle_generator.create_subtitle_filter(srt_path, style)
            
            # 获取工作目录和文件名
            srt_dir = os.path.dirname(srt_path)
            srt_filename = os.path.basename(srt_path)
            
            # 确保视频路径是绝对路径
            if not os.path.isabs(video_path):
                video_path = os.path.abspath(video_path)
            
            # 确保输出路径是绝对路径
            if not os.path.isabs(output_path):
                output_path = os.path.abspath(output_path)
            
            # 构建FFmpeg命令
            cmd = [
                'ffmpeg', '-y',  # 覆盖输出文件
                '-i', video_path,  # 输入视频（绝对路径）
                '-vf', subtitle_filter,  # 视频过滤器
                '-c:a', 'copy',  # 音频直接复制
                '-c:v', 'libx264',  # 视频编码器
                '-crf', '23',  # 质量设置
                '-preset', 'medium',  # 编码速度
                output_path  # 输出路径（绝对路径）
            ]
            
            print(u"开始添加字幕...")
            print(u"FFmpeg命令: {}".format(' '.join(cmd)))
            print(u"工作目录: {}".format(srt_dir))
            
            # 在SRT文件所在目录执行命令
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True,
                cwd=srt_dir  # 设置工作目录
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                return True
            else:
                print(u"FFmpeg错误输出:")
                print(stderr)
                return False
        
        except Exception as e:
            print(u"执行字幕插入时出错: {}".format(str(e)))
            return False
    
    def create_subtitle_preview(self, subtitle_source, video_duration=None):
        """创建字幕预览"""
        if hasattr(subtitle_source, 'encode'):  # 检查是否为字符串类型（包括unicode）
            if os.path.exists(subtitle_source):
                subtitles = self.subtitle_generator.read_text_document(subtitle_source)
            else:
                raise ValueError(u"字幕源文件不存在: {}".format(subtitle_source))
        else:
            subtitles = subtitle_source
        
        if video_duration:
            # 不强制适应视频长度，保持正常语速
            subtitles = self.subtitle_generator.adjust_subtitle_timing(
                subtitles, video_duration, auto_fit=False
            )
        
        subtitles = self.subtitle_generator.split_long_subtitles(subtitles)
        
        return subtitles
    
    def batch_add_subtitles(self, video_subtitle_pairs, style='default'):
        """批量添加字幕"""
        results = []
        
        for i, (video_path, subtitle_source) in enumerate(video_subtitle_pairs, 1):
            print(u"\n处理第 {}/{} 个视频...".format(i, len(video_subtitle_pairs)))
            
            try:
                output_path = self.insert_subtitles_to_video(
                    video_path, subtitle_source, style=style
                )
                results.append({
                    'video': video_path,
                    'output': output_path,
                    'success': True,
                    'error': None
                })
            except Exception as e:
                print(u"处理失败: {}".format(str(e)))
                results.append({
                    'video': video_path,
                    'output': None,
                    'success': False,
                    'error': str(e)
                })
        
        return results
