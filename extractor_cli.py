# -*- coding: utf-8 -*-
"""
视频提取工具命令行界面
提供音频和字幕提取功能
"""

import os
import sys
import subprocess
import tempfile
import wave
import json
import base64
import time
from config import Config
from utils import generate_timestamped_filename, get_video_info

def safe_input(prompt):
    """安全的输入函数，处理Python 2.7的编码问题"""
    try:
        # Python 2.7兼容处理
        if sys.version_info[0] == 2:
            if isinstance(prompt, unicode):
                prompt = prompt.encode('utf-8')
            return raw_input(prompt).decode('utf-8')
        else:
            return input(prompt)
    except (UnicodeDecodeError, UnicodeEncodeError):
        try:
            # Python 2.7兼容处理
            if sys.version_info[0] == 2:
                return raw_input(prompt)
            else:
                return input(prompt)
        except:
            return ""
    except KeyboardInterrupt:
        raise
    except:
        return ""

class ExtractorCLI(object):
    """视频提取工具命令行界面"""
    
    def __init__(self):
        self.config = Config()
        self.ffmpeg_path = self.config.get('ffmpeg', 'path')
        # ffprobe通常和ffmpeg在同一目录
        self.ffprobe_path = self.ffmpeg_path.replace('ffmpeg.exe', 'ffprobe.exe')
    
    def print_banner(self):
        """打印程序横幅"""
        print(u"=" * 60)
        print(u"      视频提取工具 (Python 2.7.18 + FFmpeg)")
        print(u"=" * 60)
        print(u"功能特性:")
        print(u"  - 提取视频中的音频文件")
        print(u"  - 提取视频中的字幕文件")
        print(u"  - 音频语音识别生成字幕")
        print(u"  - 去除视频音频/水印/字幕")
        print(u"  - 支持多种音频格式输出")
        print(u"  - 自动检测字幕轨道")
        print(u"  - 批量处理多个视频")
        print(u"=" * 60)
        print()
    
    def get_video_path(self):
        """获取视频文件路径"""
        while True:
            video_path = safe_input(u"请输入视频文件路径: ").strip().strip('"')
            if not video_path:
                print(u"请输入有效的路径")
                continue
            
            if not os.path.exists(video_path):
                print(u"文件不存在，请重新输入")
                continue
            
            if not video_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v')):
                print(u"不支持的视频格式，请选择常见的视频文件")
                continue
            
            # 获取视频信息
            video_info = get_video_info(video_path)
            if video_info:
                print(u"✓ 视频信息: {:.1f}秒, {}x{}".format(
                    video_info['duration'], 
                    video_info['width'], 
                    video_info['height']
                ))
                
                # 检查音频流
                has_audio = self.check_audio_stream(video_path)
                if has_audio:
                    print(u"✓ 检测到音频流")
                else:
                    print(u"⚠ 未检测到音频流")
                
                # 检查字幕流
                subtitle_count = self.check_subtitle_streams(video_path)
                if subtitle_count > 0:
                    print(u"✓ 检测到 {} 个字幕轨道".format(subtitle_count))
                else:
                    print(u"⚠ 未检测到字幕轨道")
                
                return video_path, video_info, has_audio, subtitle_count
            else:
                print(u"无法读取视频文件信息，请检查文件是否损坏")
    
    def check_audio_stream(self, video_path):
        """检查视频是否包含音频流"""
        try:
            cmd = [
                self.ffmpeg_path, '-i', video_path, '-hide_banner'
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = process.communicate()
            
            output = stderr + (stdout or "")
            
            # 更宽泛的音频流检测
            audio_indicators = ['Audio:', 'Stream #0:1', 'Stream #0:1(', 'aac', 'mp3', 'wav']
            return any(indicator in output for indicator in audio_indicators)
        except Exception:
            return False
    
    def check_subtitle_streams(self, video_path):
        """检查视频包含的字幕流数量"""
        try:
            cmd = [self.ffmpeg_path, '-i', video_path, '-hide_banner']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = process.communicate()
            
            output = stderr + (stdout or "")
            
            # 计算字幕流数量
            subtitle_count = 0
            for line in output.split('\n'):
                if 'Stream #' in line and ('Subtitle:' in line or 'srt' in line or 'ass' in line or 'ssa' in line):
                    subtitle_count += 1
            
            return subtitle_count
        except Exception:
            return 0
    
    def extract_audio(self, video_path, video_info):
        """提取音频文件"""
        print(u"\n=== 音频提取模式 ===")
        
        # 选择音频格式
        print(u"请选择输出音频格式:")
        print(u"1. MP3 (推荐) - 压缩格式，文件较小")
        print(u"2. WAV - 无损格式，文件较大")
        print(u"3. AAC - 高质量压缩格式")
        print(u"4. FLAC - 无损压缩格式")
        
        formats = {
            1: {'ext': 'mp3', 'codec': 'mp3', 'params': ['-b:a', '192k']},
            2: {'ext': 'wav', 'codec': 'pcm_s16le', 'params': []},
            3: {'ext': 'aac', 'codec': 'aac', 'params': ['-b:a', '128k']},
            4: {'ext': 'flac', 'codec': 'flac', 'params': []}
        }
        
        while True:
            try:
                choice = int(safe_input(u"请选择格式 (1-4，默认1): ").strip() or "1")
                if choice in formats:
                    break
                print(u"请输入1-4之间的数字")
            except ValueError:
                print(u"请输入有效的数字")
        
        format_info = formats[choice]
        
        # 生成输出文件名
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        default_output = "{}_audio.{}".format(base_name, format_info['ext'])
        
        output_name = safe_input(u"输出文件名（默认：{}）: ".format(default_output)).strip()
        if not output_name:
            output_name = default_output
        
        # 确保文件扩展名正确
        if not output_name.lower().endswith('.' + format_info['ext']):
            output_name = os.path.splitext(output_name)[0] + '.' + format_info['ext']
        
        # 选择输出目录
        output_dir = safe_input(u"输出目录（默认：audio）: ").strip() or "audio"
        
        # 创建输出目录
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                print(u"创建输出目录: {}".format(output_dir))
            except Exception as e:
                print(u"创建目录失败: {}".format(str(e)))
                output_dir = '.'
        
        output_path = os.path.join(output_dir, output_name)
        
        # 显示配置
        print(u"\n" + u"=" * 40)
        print(u"音频提取配置")
        print(u"=" * 40)
        print(u"输入视频: {}".format(os.path.basename(video_path)))
        print(u"视频时长: {:.1f}秒".format(video_info['duration']))
        print(u"输出格式: {}".format(format_info['ext'].upper()))
        print(u"输出文件: {}".format(output_path))
        print(u"=" * 40)
        
        confirm = safe_input(u"\n确认开始提取？(Y/n): ").strip().lower()
        if confirm == 'n':
            print(u"操作已取消")
            return False
        
        # 执行音频提取
        print(u"\n开始提取音频...")
        
        cmd = [
            self.ffmpeg_path, '-y', '-i', video_path,
            '-vn',  # 不要视频流
            '-acodec', format_info['codec']
        ]
        cmd.extend(format_info['params'])
        cmd.append(output_path)
        
        try:
            print(u"执行命令: {}".format(' '.join(cmd)))
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0 and os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024 * 1024)
                print(u"\n" + u"=" * 40)
                print(u"音频提取完成！")
                print(u"=" * 40)
                print(u"输出文件: {}".format(output_path))
                print(u"文件大小: {:.2f} MB".format(file_size))
                print(u"音频时长: {:.1f}秒".format(video_info['duration']))
                return True
            else:
                print(u"音频提取失败:")
                if stderr:
                    print(stderr.decode('utf-8') if isinstance(stderr, bytes) else stderr)
                return False
                
        except Exception as e:
            print(u"音频提取出错: {}".format(str(e)))
            return False
    
    def extract_subtitles(self, video_path, video_info, subtitle_count):
        """提取字幕文件"""
        print(u"\n=== 字幕提取模式 ===")
        
        if subtitle_count == 0:
            print(u"该视频文件不包含字幕轨道")
            return False
        
        # 生成输出文件名
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # 选择输出目录
        output_dir = safe_input(u"输出目录（默认：srt）: ").strip() or "srt"
        
        # 创建输出目录
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                print(u"创建输出目录: {}".format(output_dir))
            except Exception as e:
                print(u"创建目录失败: {}".format(str(e)))
                output_dir = '.'
        
        # 显示配置
        print(u"\n" + u"=" * 40)
        print(u"字幕提取配置")
        print(u"=" * 40)
        print(u"输入视频: {}".format(os.path.basename(video_path)))
        print(u"字幕轨道数: {}".format(subtitle_count))
        print(u"输出目录: {}".format(output_dir))
        print(u"=" * 40)
        
        confirm = safe_input(u"\n确认开始提取？(Y/n): ").strip().lower()
        if confirm == 'n':
            print(u"操作已取消")
            return False
        
        # 执行字幕提取
        print(u"\n开始提取字幕...")
        success_count = 0
        
        for i in range(subtitle_count):
            output_name = "{}_subtitle_{}.srt".format(base_name, i + 1)
            output_path = os.path.join(output_dir, output_name)
            
            cmd = [
                self.ffmpeg_path, '-y', '-i', video_path,
                '-map', '0:s:{}'.format(i),  # 选择字幕流
                '-c:s', 'srt',  # 转换为SRT格式
                output_path
            ]
            
            try:
                print(u"提取字幕轨道 {} ...".format(i + 1))
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                
                if process.returncode == 0 and os.path.exists(output_path):
                    file_size = os.path.getsize(output_path) / 1024
                    print(u"✓ 字幕轨道 {} 提取成功: {} ({:.1f} KB)".format(
                        i + 1, output_name, file_size
                    ))
                    success_count += 1
                else:
                    print(u"✗ 字幕轨道 {} 提取失败".format(i + 1))
                    if stderr:
                        error_msg = stderr.decode('utf-8') if isinstance(stderr, bytes) else stderr
                        print(u"  错误信息: {}".format(error_msg))
                        
            except Exception as e:
                print(u"✗ 字幕轨道 {} 提取出错: {}".format(i + 1, str(e)))
        
        if success_count > 0:
            print(u"\n" + u"=" * 40)
            print(u"字幕提取完成！")
            print(u"=" * 40)
            print(u"成功提取: {} / {} 个字幕轨道".format(success_count, subtitle_count))
            print(u"输出目录: {}".format(output_dir))
            return True
        else:
            print(u"\n字幕提取失败，没有成功提取任何字幕轨道")
            return False
    
    def speech_recognition_to_subtitle(self, video_path, video_info):
        """语音识别生成字幕"""
        print(u"\n=== 语音识别生成字幕 ===")
        
        # 获取基本信息
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = os.path.dirname(video_path)
        
        # 生成临时音频文件路径
        temp_audio = os.path.join(output_dir, "{}_temp_audio.wav".format(base_name))
        subtitle_output = os.path.join(output_dir, "{}_speech_subtitle.srt".format(base_name))
        
        try:
            # 步骤1: 提取高质量WAV音频用于语音识别
            print(u"步骤1: 提取音频文件用于语音识别...")
            audio_cmd = [
                self.ffmpeg_path, '-y', '-i', video_path,
                '-vn',  # 不包含视频
                '-acodec', 'pcm_s16le',  # 16位PCM编码
                '-ar', '16000',  # 16kHz采样率（语音识别最佳）
                '-ac', '1',  # 单声道
                temp_audio
            ]
            
            process = subprocess.Popen(audio_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0 or not os.path.exists(temp_audio):
                print(u"✗ 音频提取失败")
                if stderr:
                    error_msg = stderr.decode('utf-8') if isinstance(stderr, bytes) else stderr
                    print(u"  错误信息: {}".format(error_msg))
                return False
            
            print(u"✓ 音频提取成功: {}".format(os.path.basename(temp_audio)))
            
            # 步骤2: 获取音频时长信息
            duration = self.get_audio_duration(temp_audio)
            if not duration:
                print(u"✗ 无法获取音频时长")
                return False
            
            print(u"✓ 音频时长: {:.2f} 秒".format(duration))
            
            # 步骤3: 语音识别选择
            print(u"\n步骤2: 选择语音识别方式")
            print(u"1. 本地语音识别 (需要安装speech_recognition库)")
            print(u"2. 简单音频分析生成模板字幕")
            print(u"3. 手动创建字幕模板")
            
            while True:
                try:
                    choice = int(safe_input(u"请选择识别方式 (1-3): ").strip())
                    if 1 <= choice <= 3:
                        break
                    print(u"请输入有效的选择")
                except ValueError:
                    print(u"请输入数字")
            
            # 执行相应的语音识别方法
            success = False
            if choice == 1:
                success = self.local_speech_recognition(temp_audio, subtitle_output, duration)
            elif choice == 2:
                success = self.create_audio_template_subtitle(temp_audio, subtitle_output, duration)
            else:  # choice == 3
                success = self.create_manual_subtitle_template(subtitle_output, duration)
            
            return success
            
        except Exception as e:
            print(u"语音识别过程出错: {}".format(str(e)))
            return False
        finally:
            # 清理临时文件
            if os.path.exists(temp_audio):
                try:
                    os.remove(temp_audio)
                    print(u"已清理临时音频文件")
                except:
                    pass
    
    def get_audio_duration(self, audio_path):
        """获取音频文件时长"""
        try:
            # 使用ffmpeg获取音频时长
            cmd = [
                self.ffmpeg_path, '-i', audio_path, '-hide_banner', '-f', 'null', '-'
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            # 从ffmpeg的输出中解析时长
            output = stderr.decode('utf-8') if isinstance(stderr, bytes) else stderr
            
            import re
            # 查找Duration: HH:MM:SS.ms格式
            duration_match = re.search(r'Duration: (\d+):(\d+):(\d+)\.(\d+)', output)
            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = int(duration_match.group(3))
                milliseconds = int(duration_match.group(4))
                
                total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 100.0
                return total_seconds
                
        except Exception:
            pass
        return None
    
    def local_speech_recognition(self, audio_path, output_path, duration):
        """本地语音识别"""
        try:
            import speech_recognition as sr
            
            print(u"使用本地语音识别...")
            recognizer = sr.Recognizer()
            
            # 优化识别器设置
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 0.8
            recognizer.operation_timeout = None
            
            # 分段识别以提高准确性
            segment_duration = 10.0  # 每段10秒
            segments = int(duration / segment_duration) + 1
            all_recognized_text = []
            
            print(u"正在分段识别语音内容...")
            
            for segment in range(segments):
                start_time = segment * segment_duration
                if start_time >= duration:
                    break
                
                segment_duration_actual = min(segment_duration, duration - start_time)
                print(u"识别第 {} 段 ({:.1f}s - {:.1f}s)...".format(
                    segment + 1, start_time, start_time + segment_duration_actual
                ))
                
                try:
                    with sr.AudioFile(audio_path) as source:
                        # 跳到指定位置并读取指定长度的音频
                        recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio_data = recognizer.record(source, offset=start_time, duration=segment_duration_actual)
                    
                    # 尝试多种识别引擎
                    engines = [
                        (u'Google', lambda: recognizer.recognize_google(audio_data, language='zh-CN')),
                        (u'Google(备选)', lambda: recognizer.recognize_google(audio_data, language='zh')),
                        (u'Sphinx(英语)', lambda: recognizer.recognize_sphinx(audio_data, language='en-US'))
                    ]
                    
                    segment_text = None
                    for engine_name, recognize_func in engines:
                        try:
                            print(u"  尝试 {} 引擎...".format(engine_name))
                            segment_text = recognize_func()
                            if segment_text and segment_text.strip():
                                # 确保文本是unicode格式
                                if isinstance(segment_text, str):
                                    segment_text = segment_text.decode('utf-8')
                                display_text = segment_text[:30] + u"..." if len(segment_text) > 30 else segment_text
                                print(u"  ✓ {} 识别成功: {}".format(engine_name, display_text))
                                break
                        except Exception as e:
                            error_msg = str(e)
                            if isinstance(error_msg, str):
                                try:
                                    error_msg = error_msg.decode('utf-8')
                                except:
                                    error_msg = u"识别失败"
                            print(u"  ✗ {} 识别失败: {}".format(engine_name, error_msg))
                            continue
                    
                    if segment_text and segment_text.strip():
                        all_recognized_text.append(segment_text.strip())
                    else:
                        print(u"  ⚠ 该段未识别到内容")
                        all_recognized_text.append(u"[语音内容 {}]".format(segment + 1))
                        
                except Exception as e:
                    error_msg = str(e)
                    if isinstance(error_msg, str):
                        try:
                            error_msg = error_msg.decode('utf-8')
                        except:
                            error_msg = u"识别出错"
                    print(u"  ✗ 第 {} 段识别出错: {}".format(segment + 1, error_msg))
                    all_recognized_text.append(u"[语音内容 {}]".format(segment + 1))
            
            # 合并所有识别结果
            if any(text and not text.startswith(u"[语音内容") for text in all_recognized_text):
                final_text = u" ".join([text for text in all_recognized_text if text])
                print(u"\n✓ 语音识别完成，识别到内容")
                return self.generate_subtitle_file(output_path, final_text, duration, all_recognized_text)
            else:
                print(u"\n⚠ 未识别到有效语音内容，生成手动编辑模板...")
                return self.create_manual_subtitle_template(output_path, duration)
            
        except ImportError:
            print(u"未安装 speech_recognition 库")
            print(u"请执行: pip install SpeechRecognition pyaudio")
            print(u"转为创建字幕模板...")
            return self.create_manual_subtitle_template(output_path, duration)
        except Exception as e:
            print(u"本地语音识别出错: {}".format(str(e)))
            return self.create_manual_subtitle_template(output_path, duration)
    
    def create_audio_template_subtitle(self, audio_path, output_path, duration):
        """基于音频分析创建字幕模板"""
        print(u"分析音频特征生成字幕模板...")
        
        try:
            # 简单的音频分析 - 检测音频强度变化来分段
            segments = self.analyze_audio_segments(audio_path, duration)
            
            # 生成基于分段的字幕模板
            subtitle_content = []
            for i, (start_time, end_time) in enumerate(segments, 1):
                subtitle_content.append(u"{}\n{} --> {}\n[语音内容 {}]\n".format(
                    i,
                    self.format_time(start_time),
                    self.format_time(end_time),
                    i
                ))
            
            # 写入字幕文件
            try:
                with open(output_path, 'w') as f:
                    content = u"\n".join(subtitle_content)
                    f.write(content.encode('utf-8'))
            except:
                import codecs
                with codecs.open(output_path, 'w', 'utf-8') as f:
                    content = u"\n".join(subtitle_content)
                    f.write(content)
            
            print(u"✓ 字幕模板生成成功: {}".format(os.path.basename(output_path)))
            print(u"包含 {} 个字幕段落，请手动填写语音内容".format(len(segments)))
            return True
            
        except Exception as e:
            print(u"音频分析失败: {}".format(str(e)))
            return self.create_manual_subtitle_template(output_path, duration)
    
    def analyze_audio_segments(self, audio_path, duration):
        """简单的音频分段分析"""
        # 基于时长创建合理的分段
        segment_duration = min(5.0, duration / 4)  # 每段最多5秒，至少4段
        segments = []
        
        current_time = 0.0
        while current_time < duration:
            end_time = min(current_time + segment_duration, duration)
            segments.append((current_time, end_time))
            current_time = end_time
        
        return segments
    
    def create_manual_subtitle_template(self, output_path, duration):
        """创建手动字幕模板"""
        print(u"生成手动编辑字幕模板...")
        
        try:
            # 基于时长创建合理数量的字幕条目
            segment_count = max(3, int(duration / 3))  # 每3秒一段，最少3段
            segment_duration = duration / segment_count
            
            subtitle_content = []
            for i in range(segment_count):
                start_time = i * segment_duration
                end_time = min((i + 1) * segment_duration, duration)
                
                subtitle_content.append(u"{}\n{} --> {}\n[请在此处输入语音内容 {}]\n".format(
                    i + 1,
                    self.format_time(start_time),
                    self.format_time(end_time),
                    i + 1
                ))
            
            # 写入字幕文件
            try:
                with open(output_path, 'w') as f:
                    content = u"\n".join(subtitle_content)
                    f.write(content.encode('utf-8'))
            except:
                import codecs
                with codecs.open(output_path, 'w', 'utf-8') as f:
                    content = u"\n".join(subtitle_content)
                    f.write(content)
            
            print(u"✓ 手动字幕模板生成成功: {}".format(os.path.basename(output_path)))
            print(u"包含 {} 个时间段，请使用文本编辑器填写语音内容".format(segment_count))
            print(u"模板格式: [请在此处输入语音内容 N] - 替换为实际的语音文字")
            return True
            
        except Exception as e:
            print(u"创建字幕模板失败: {}".format(str(e)))
            return False
    
    def generate_subtitle_file(self, output_path, text, duration, segments_text=None):
        """根据识别的文本生成字幕文件"""
        try:
            # 如果有分段文本，优先使用分段结果
            if segments_text:
                subtitle_content = []
                time_per_segment = duration / len(segments_text)
                
                for i, segment_text in enumerate(segments_text):
                    start_time = i * time_per_segment
                    end_time = min((i + 1) * time_per_segment, duration)
                    
                    subtitle_content.append(u"{}\n{} --> {}\n{}\n".format(
                        i + 1,
                        self.format_time(start_time),
                        self.format_time(end_time),
                        segment_text.strip()
                    ))
            else:
                # 将长文本分割为合适的字幕段落
                sentences = self.split_text_to_sentences(text)
                if not sentences:
                    sentences = [text]
                
                # 计算每个句子的时间分配
                time_per_sentence = duration / len(sentences)
                
                subtitle_content = []
                for i, sentence in enumerate(sentences):
                    start_time = i * time_per_sentence
                    end_time = min((i + 1) * time_per_sentence, duration)
                    
                    subtitle_content.append(u"{}\n{} --> {}\n{}\n".format(
                        i + 1,
                        self.format_time(start_time),
                        self.format_time(end_time),
                        sentence.strip()
                    ))
            
            # 写入字幕文件
            try:
                # Python 2.7 兼容的文件写入
                with open(output_path, 'w') as f:
                    content = u"\n".join(subtitle_content)
                    f.write(content.encode('utf-8'))
            except:
                # 备选方案
                import codecs
                with codecs.open(output_path, 'w', 'utf-8') as f:
                    content = u"\n".join(subtitle_content)
                    f.write(content)
            
            segment_count = len(segments_text) if segments_text else len(sentences)
            print(u"✓ 字幕文件生成成功: {}".format(os.path.basename(output_path)))
            print(u"包含 {} 个字幕条目".format(segment_count))
            return True
            
        except Exception as e:
            print(u"生成字幕文件失败: {}".format(str(e)))
            return False
    
    def split_text_to_sentences(self, text):
        """将文本分割为句子"""
        import re
        # 简单的中文句子分割
        sentences = re.split(r'[。！？.!?]+', text)
        # 过滤空句子并限制长度
        result = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # 如果句子太长，进一步分割
                if len(sentence) > 20:
                    sub_sentences = re.split(r'[，、,]', sentence)
                    result.extend([s.strip() for s in sub_sentences if s.strip()])
                else:
                    result.append(sentence)
        return result[:20]  # 最多20个句子
    
    def format_time(self, seconds):
        """格式化时间为字幕格式 (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return u"{:02d}:{:02d}:{:02d},{:03d}".format(hours, minutes, secs, millisecs)
    
    def remove_video_elements(self, video_path, video_info):
        """去除视频中的音频、水印、字幕等元素"""
        print(u"\n=== 视频元素去除模式 ===")
        
        # 获取基本信息
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # 选择要去除的元素
        print(u"请选择要去除的元素（可多选）:")
        print(u"1. 去除音频轨道")
        print(u"2. 去除字幕轨道（内嵌软字幕）")
        print(u"3. 去除水印（需要指定水印位置）")
        print(u"4. 去除烧录字幕（视频中的硬字幕）")
        print(u"5. 全部去除（音频 + 字幕 + 水印 + 烧录字幕）")
        
        while True:
            try:
                choices_input = safe_input(u"请选择 (1-5，多选用逗号分隔，如1,2,3): ").strip()
                if choices_input == '5':
                    remove_audio = True
                    remove_subtitles = True
                    remove_watermark = True
                    remove_burned_subtitles = True
                    break
                else:
                    choices = [int(x.strip()) for x in choices_input.split(',') if x.strip()]
                    if all(1 <= choice <= 4 for choice in choices):
                        remove_audio = 1 in choices
                        remove_subtitles = 2 in choices
                        remove_watermark = 3 in choices
                        remove_burned_subtitles = 4 in choices
                        break
                print(u"请输入有效的选择")
            except ValueError:
                print(u"请输入有效的数字")
        
        # 水印去除配置
        watermark_filter = None
        if remove_watermark:
            print(u"\n=== 水印去除配置 ===")
            print(u"请选择水印去除方式:")
            print(u"1. 模糊指定区域")
            print(u"2. 用纯色填充指定区域")
            print(u"3. 裁剪视频去除边缘水印")
            
            while True:
                try:
                    watermark_method = int(safe_input(u"请选择方式 (1-3): ").strip())
                    if 1 <= watermark_method <= 3:
                        break
                    print(u"请输入1-3之间的数字")
                except ValueError:
                    print(u"请输入有效的数字")
            
            if watermark_method == 1:  # 模糊
                watermark_filter = self._configure_blur_filter()
            elif watermark_method == 2:  # 纯色填充
                watermark_filter = self._configure_fill_filter()
            else:  # 裁剪
                watermark_filter = self._configure_crop_filter(video_info)
        
        # 烧录字幕去除配置
        burned_subtitle_filter = None
        if remove_burned_subtitles:
            print(u"\n=== 烧录字幕去除配置 ===")
            print(u"烧录字幕通常位于视频底部。请选择去除方式:")
            print(u"1. 模糊字幕区域")
            print(u"2. 用纯色遮盖字幕区域")
            print(u"3. 裁剪视频去除底部字幕区域")
            print(u"4. 自定义字幕区域位置")
            
            while True:
                try:
                    subtitle_method = int(safe_input(u"请选择方式 (1-4): ").strip())
                    if 1 <= subtitle_method <= 4:
                        break
                    print(u"请输入1-4之间的数字")
                except ValueError:
                    print(u"请输入有效的数字")
            
            if subtitle_method == 1:  # 模糊字幕区域
                burned_subtitle_filter = self._configure_burned_subtitle_blur_filter(video_info)
            elif subtitle_method == 2:  # 纯色遮盖
                burned_subtitle_filter = self._configure_burned_subtitle_fill_filter(video_info)
            elif subtitle_method == 3:  # 裁剪去除
                burned_subtitle_filter = self._configure_burned_subtitle_crop_filter(video_info)
            else:  # 自定义区域
                burned_subtitle_filter = self._configure_custom_subtitle_filter(video_info)
        
        # 生成输出文件名
        suffix = []
        if remove_audio:
            suffix.append("no_audio")
        if remove_subtitles:
            suffix.append("no_sub")
        if remove_watermark:
            suffix.append("no_watermark")
        if remove_burned_subtitles:
            suffix.append("no_burned_sub")
        
        suffix_str = "_" + "_".join(suffix) if suffix else "_processed"
        default_output = "{}{}.mp4".format(base_name, suffix_str)
        
        output_name = safe_input(u"输出文件名（默认：{}）: ".format(default_output)).strip()
        if not output_name:
            output_name = default_output
        
        # 确保文件扩展名正确
        if not output_name.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            output_name = os.path.splitext(output_name)[0] + '.mp4'
        
        # 选择输出目录
        output_dir = safe_input(u"输出目录（默认：processed）: ").strip() or "processed"
        
        # 创建输出目录
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                print(u"创建输出目录: {}".format(output_dir))
            except Exception as e:
                print(u"创建目录失败: {}".format(str(e)))
                output_dir = '.'
        
        output_path = os.path.join(output_dir, output_name)
        
        # 显示配置
        print(u"\n" + u"=" * 50)
        print(u"视频处理配置")
        print(u"=" * 50)
        print(u"输入视频: {}".format(os.path.basename(video_path)))
        print(u"视频信息: {:.1f}秒, {}x{}".format(
            video_info['duration'], video_info['width'], video_info['height']
        ))
        print(u"处理操作:")
        if remove_audio:
            print(u"  ✓ 去除音频轨道")
        if remove_subtitles:
            print(u"  ✓ 去除字幕轨道（软字幕）")
        if remove_watermark:
            print(u"  ✓ 去除水印")
        if remove_burned_subtitles:
            print(u"  ✓ 去除烧录字幕（硬字幕）")
        print(u"输出文件: {}".format(output_path))
        print(u"=" * 50)
        
        confirm = safe_input(u"\n确认开始处理？(Y/n): ").strip().lower()
        if confirm == 'n':
            print(u"操作已取消")
            return False
        
        # 构建FFmpeg命令
        cmd = [self.ffmpeg_path, '-y', '-i', video_path]
        
        # 视频流处理
        video_filters = []
        if watermark_filter:
            video_filters.append(watermark_filter)
        if burned_subtitle_filter:
            video_filters.append(burned_subtitle_filter)
        
        if video_filters:
            cmd.extend(['-vf', ','.join(video_filters)])
        else:
            cmd.extend(['-c:v', 'copy'])  # 如果没有视频滤镜，直接复制视频流
        
        # 音频处理
        if remove_audio:
            cmd.append('-an')  # 不包含音频
        else:
            cmd.extend(['-c:a', 'copy'])  # 复制音频流
        
        # 字幕处理
        if remove_subtitles:
            cmd.append('-sn')  # 不包含字幕
        else:
            cmd.extend(['-c:s', 'copy'])  # 复制字幕流
        
        cmd.append(output_path)
        
        # 执行处理
        print(u"\n开始处理视频...")
        print(u"执行命令: {}".format(' '.join(cmd)))
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0 and os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024 * 1024)
                print(u"\n" + u"=" * 50)
                print(u"视频处理完成！")
                print(u"=" * 50)
                print(u"输出文件: {}".format(output_path))
                print(u"文件大小: {:.2f} MB".format(file_size))
                return True
            else:
                print(u"视频处理失败:")
                if stderr:
                    error_msg = stderr.decode('utf-8') if isinstance(stderr, bytes) else stderr
                    print(error_msg)
                return False
                
        except Exception as e:
            print(u"视频处理出错: {}".format(str(e)))
            return False
    
    def _configure_blur_filter(self):
        """配置模糊滤镜"""
        print(u"请输入要模糊的区域坐标:")
        
        while True:
            try:
                x = int(safe_input(u"X坐标（左上角）: ").strip())
                y = int(safe_input(u"Y坐标（左上角）: ").strip())
                width = int(safe_input(u"区域宽度: ").strip())
                height = int(safe_input(u"区域高度: ").strip())
                
                if all(v >= 0 for v in [x, y, width, height]):
                    break
                print(u"坐标和尺寸必须为非负数")
            except ValueError:
                print(u"请输入有效的数字")
        
        blur_strength = safe_input(u"模糊强度 (1-10，默认5): ").strip() or "5"
        
        # 创建模糊滤镜
        return "boxblur={}:enable='between(t,0,999999)':x={}:y={}:w={}:h={}".format(
            blur_strength, x, y, width, height
        )
    
    def _configure_fill_filter(self):
        """配置填充滤镜"""
        print(u"请输入要填充的区域坐标:")
        
        while True:
            try:
                x = int(safe_input(u"X坐标（左上角）: ").strip())
                y = int(safe_input(u"Y坐标（左上角）: ").strip())
                width = int(safe_input(u"区域宽度: ").strip())
                height = int(safe_input(u"区域高度: ").strip())
                
                if all(v >= 0 for v in [x, y, width, height]):
                    break
                print(u"坐标和尺寸必须为非负数")
            except ValueError:
                print(u"请输入有效的数字")
        
        # 颜色选择
        print(u"请选择填充颜色:")
        print(u"1. 黑色")
        print(u"2. 白色") 
        print(u"3. 自定义颜色(RGB)")
        
        while True:
            try:
                color_choice = int(safe_input(u"请选择 (1-3): ").strip())
                if color_choice == 1:
                    color = "black"
                    break
                elif color_choice == 2:
                    color = "white"
                    break
                elif color_choice == 3:
                    r = int(safe_input(u"红色值 (0-255): ").strip())
                    g = int(safe_input(u"绿色值 (0-255): ").strip())
                    b = int(safe_input(u"蓝色值 (0-255): ").strip())
                    if all(0 <= v <= 255 for v in [r, g, b]):
                        color = "0x{:02x}{:02x}{:02x}".format(r, g, b)
                        break
                    print(u"RGB值必须在0-255之间")
                else:
                    print(u"请输入1-3之间的数字")
            except ValueError:
                print(u"请输入有效的数字")
        
        # 创建填充滤镜
        return "drawbox=x={}:y={}:w={}:h={}:color={}:t=fill".format(
            x, y, width, height, color
        )
    
    def _configure_crop_filter(self, video_info):
        """配置裁剪滤镜"""
        print(u"当前视频尺寸: {}x{}".format(video_info['width'], video_info['height']))
        print(u"请输入裁剪参数:")
        
        while True:
            try:
                new_width = int(safe_input(u"新宽度: ").strip())
                new_height = int(safe_input(u"新高度: ").strip())
                crop_x = int(safe_input(u"裁剪起始X坐标（默认居中）: ").strip() or 
                           str((video_info['width'] - new_width) // 2))
                crop_y = int(safe_input(u"裁剪起始Y坐标（默认居中）: ").strip() or 
                           str((video_info['height'] - new_height) // 2))
                
                if (new_width > 0 and new_height > 0 and 
                    crop_x >= 0 and crop_y >= 0 and
                    crop_x + new_width <= video_info['width'] and
                    crop_y + new_height <= video_info['height']):
                    break
                print(u"裁剪参数超出视频范围，请重新输入")
            except ValueError:
                print(u"请输入有效的数字")
        
        # 创建裁剪滤镜
        return "crop={}:{}:{}:{}".format(new_width, new_height, crop_x, crop_y)
    
    def _configure_burned_subtitle_blur_filter(self, video_info):
        """配置烧录字幕模糊滤镜"""
        print(u"配置字幕区域模糊处理...")
        print(u"视频尺寸: {}x{}".format(video_info['width'], video_info['height']))
        
        # 提供常见的字幕区域预设
        print(u"请选择字幕区域:")
        print(u"1. 底部字幕区域 (推荐，底部20%区域)")
        print(u"2. 自定义区域")
        
        while True:
            try:
                choice = int(safe_input(u"请选择 (1-2): ").strip())
                if choice in [1, 2]:
                    break
                print(u"请输入1或2")
            except ValueError:
                print(u"请输入有效的数字")
        
        if choice == 1:
            # 底部20%区域
            subtitle_height = int(video_info['height'] * 0.2)
            x = 0
            y = video_info['height'] - subtitle_height
            width = video_info['width']
            height = subtitle_height
            print(u"使用底部字幕区域: {}x{} 位置({}, {})".format(width, height, x, y))
        else:
            # 自定义区域
            while True:
                try:
                    x = int(safe_input(u"字幕区域X坐标: ").strip())
                    y = int(safe_input(u"字幕区域Y坐标: ").strip())
                    width = int(safe_input(u"字幕区域宽度: ").strip())
                    height = int(safe_input(u"字幕区域高度: ").strip())
                    
                    if (x >= 0 and y >= 0 and width > 0 and height > 0 and
                        x + width <= video_info['width'] and y + height <= video_info['height']):
                        break
                    print(u"区域参数超出视频范围，请重新输入")
                except ValueError:
                    print(u"请输入有效的数字")
        
        blur_strength = safe_input(u"模糊强度 (1-20，默认10): ").strip() or "10"
        
        # 使用复合滤镜实现区域模糊：先裁剪出字幕区域，模糊后叠加回原视频
        blur_filter = "[0:v]split[main][subtitle];[subtitle]crop=w={}:h={}:x={}:y={},boxblur={}[blurred];[main][blurred]overlay={}:{}".format(
            width, height, x, y, blur_strength, x, y
        )
        return blur_filter
    
    def _configure_burned_subtitle_fill_filter(self, video_info):
        """配置烧录字幕填充滤镜"""
        print(u"配置字幕区域填充处理...")
        print(u"视频尺寸: {}x{}".format(video_info['width'], video_info['height']))
        
        # 提供常见的字幕区域预设
        print(u"请选择字幕区域:")
        print(u"1. 底部字幕区域 (推荐，底部20%区域)")
        print(u"2. 自定义区域")
        
        while True:
            try:
                choice = int(safe_input(u"请选择 (1-2): ").strip())
                if choice in [1, 2]:
                    break
                print(u"请输入1或2")
            except ValueError:
                print(u"请输入有效的数字")
        
        if choice == 1:
            # 底部20%区域
            subtitle_height = int(video_info['height'] * 0.2)
            x = 0
            y = video_info['height'] - subtitle_height
            width = video_info['width']
            height = subtitle_height
            print(u"使用底部字幕区域: {}x{} 位置({}, {})".format(width, height, x, y))
        else:
            # 自定义区域
            while True:
                try:
                    x = int(safe_input(u"字幕区域X坐标: ").strip())
                    y = int(safe_input(u"字幕区域Y坐标: ").strip())
                    width = int(safe_input(u"字幕区域宽度: ").strip())
                    height = int(safe_input(u"字幕区域高度: ").strip())
                    
                    if (x >= 0 and y >= 0 and width > 0 and height > 0 and
                        x + width <= video_info['width'] and y + height <= video_info['height']):
                        break
                    print(u"区域参数超出视频范围，请重新输入")
                except ValueError:
                    print(u"请输入有效的数字")
        
        # 选择填充颜色
        print(u"请选择填充颜色:")
        print(u"1. 黑色 (推荐)")
        print(u"2. 白色")
        print(u"3. 自定义颜色(RGB)")
        
        while True:
            try:
                color_choice = int(safe_input(u"请选择 (1-3): ").strip())
                if color_choice == 1:
                    color = "black"
                    break
                elif color_choice == 2:
                    color = "white"
                    break
                elif color_choice == 3:
                    r = int(safe_input(u"红色值 (0-255): ").strip())
                    g = int(safe_input(u"绿色值 (0-255): ").strip())
                    b = int(safe_input(u"蓝色值 (0-255): ").strip())
                    if all(0 <= v <= 255 for v in [r, g, b]):
                        color = "0x{:02x}{:02x}{:02x}".format(r, g, b)
                        break
                    print(u"RGB值必须在0-255之间")
                else:
                    print(u"请输入1-3之间的数字")
            except ValueError:
                print(u"请输入有效的数字")
        
        # 创建填充滤镜
        return "drawbox=x={}:y={}:w={}:h={}:color={}:t=fill".format(
            x, y, width, height, color
        )
    
    def _configure_burned_subtitle_crop_filter(self, video_info):
        """配置去除烧录字幕的裁剪滤镜"""
        print(u"配置裁剪去除字幕区域...")
        print(u"当前视频尺寸: {}x{}".format(video_info['width'], video_info['height']))
        
        # 提供预设选项
        print(u"请选择裁剪方式:")
        print(u"1. 去除底部字幕区域 (保留上方80%)")
        print(u"2. 去除顶部字幕区域 (保留下方80%)")
        print(u"3. 自定义裁剪区域")
        
        while True:
            try:
                choice = int(safe_input(u"请选择 (1-3): ").strip())
                if choice in [1, 2, 3]:
                    break
                print(u"请输入1-3之间的数字")
            except ValueError:
                print(u"请输入有效的数字")
        
        if choice == 1:
            # 去除底部20%，保留上方80%
            new_width = video_info['width']
            new_height = int(video_info['height'] * 0.8)
            crop_x = 0
            crop_y = 0
            print(u"保留视频上方80%，去除底部字幕区域")
        elif choice == 2:
            # 去除顶部20%，保留下方80%
            new_width = video_info['width']
            new_height = int(video_info['height'] * 0.8)
            crop_x = 0
            crop_y = int(video_info['height'] * 0.2)
            print(u"保留视频下方80%，去除顶部字幕区域")
        else:
            # 自定义裁剪
            while True:
                try:
                    new_width = int(safe_input(u"新宽度: ").strip())
                    new_height = int(safe_input(u"新高度: ").strip())
                    crop_x = int(safe_input(u"裁剪起始X坐标: ").strip())
                    crop_y = int(safe_input(u"裁剪起始Y坐标: ").strip())
                    
                    if (new_width > 0 and new_height > 0 and
                        crop_x >= 0 and crop_y >= 0 and
                        crop_x + new_width <= video_info['width'] and
                        crop_y + new_height <= video_info['height']):
                        break
                    print(u"裁剪参数超出视频范围，请重新输入")
                except ValueError:
                    print(u"请输入有效的数字")
        
        print(u"裁剪后尺寸: {}x{} 位置({}, {})".format(new_width, new_height, crop_x, crop_y))
        return "crop={}:{}:{}:{}".format(new_width, new_height, crop_x, crop_y)
    
    def _configure_custom_subtitle_filter(self, video_info):
        """配置自定义字幕区域处理"""
        print(u"自定义字幕区域处理...")
        print(u"视频尺寸: {}x{}".format(video_info['width'], video_info['height']))
        
        # 让用户选择处理方式
        print(u"请选择处理方式:")
        print(u"1. 模糊自定义区域")
        print(u"2. 填充自定义区域")
        
        while True:
            try:
                method = int(safe_input(u"请选择 (1-2): ").strip())
                if method in [1, 2]:
                    break
                print(u"请输入1或2")
            except ValueError:
                print(u"请输入有效的数字")
        
        # 获取自定义区域坐标
        while True:
            try:
                x = int(safe_input(u"字幕区域X坐标: ").strip())
                y = int(safe_input(u"字幕区域Y坐标: ").strip())
                width = int(safe_input(u"字幕区域宽度: ").strip())
                height = int(safe_input(u"字幕区域高度: ").strip())
                
                if (x >= 0 and y >= 0 and width > 0 and height > 0 and
                    x + width <= video_info['width'] and y + height <= video_info['height']):
                    break
                print(u"区域参数超出视频范围，请重新输入")
            except ValueError:
                print(u"请输入有效的数字")
        
        if method == 1:  # 模糊
            blur_strength = safe_input(u"模糊强度 (1-20，默认10): ").strip() or "10"
            # 使用复合滤镜实现区域模糊
            return "[0:v]split[main][subtitle];[subtitle]crop=w={}:h={}:x={}:y={},boxblur={}[blurred];[main][blurred]overlay={}:{}".format(
                width, height, x, y, blur_strength, x, y
            )
        else:  # 填充
            print(u"请选择填充颜色:")
            print(u"1. 黑色")
            print(u"2. 白色")
            print(u"3. 自定义颜色(RGB)")
            
            while True:
                try:
                    color_choice = int(safe_input(u"请选择 (1-3): ").strip())
                    if color_choice == 1:
                        color = "black"
                        break
                    elif color_choice == 2:
                        color = "white"
                        break
                    elif color_choice == 3:
                        r = int(safe_input(u"红色值 (0-255): ").strip())
                        g = int(safe_input(u"绿色值 (0-255): ").strip())
                        b = int(safe_input(u"蓝色值 (0-255): ").strip())
                        if all(0 <= v <= 255 for v in [r, g, b]):
                            color = "0x{:02x}{:02x}{:02x}".format(r, g, b)
                            break
                        print(u"RGB值必须在0-255之间")
                    else:
                        print(u"请输入1-3之间的数字")
                except ValueError:
                    print(u"请输入有效的数字")
            
            return "drawbox=x={}:y={}:w={}:h={}:color={}:t=fill".format(
                x, y, width, height, color
            )
    
    def batch_extract_mode(self):
        """批量提取模式"""
        print(u"\n=== 批量提取模式 ===")
        
        # 获取文件夹路径
        folder_path = safe_input(u"请输入视频文件夹路径: ").strip().strip('"')
        if not folder_path or not os.path.exists(folder_path):
            print(u"文件夹不存在")
            return
        
        # 扫描视频文件
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v')
        video_files = []
        
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(video_extensions):
                video_files.append(os.path.join(folder_path, filename))
        
        if not video_files:
            print(u"文件夹中没有找到视频文件")
            return
        
        print(u"找到 {} 个视频文件:".format(len(video_files)))
        for i, video_path in enumerate(video_files[:10], 1):
            print(u"{}. {}".format(i, os.path.basename(video_path)))
        
        if len(video_files) > 10:
            print(u"  ... 还有 {} 个文件".format(len(video_files) - 10))
        
        # 选择提取类型
        print(u"\n请选择批量提取类型:")
        print(u"1. 仅提取音频")
        print(u"2. 仅提取字幕")
        print(u"3. 同时提取音频和字幕")
        
        while True:
            try:
                choice = int(safe_input(u"请选择 (1-3): ").strip())
                if choice in [1, 2, 3]:
                    break
                print(u"请输入1-3之间的数字")
            except ValueError:
                print(u"请输入有效的数字")
        
        extract_audio = choice in [1, 3]
        extract_subs = choice in [2, 3]
        
        confirm = safe_input(u"\n确认开始批量处理？(Y/n): ").strip().lower()
        if confirm == 'n':
            print(u"操作已取消")
            return
        
        # 批量处理
        success_count = 0
        total_count = len(video_files)
        
        print(u"\n开始批量处理...")
        
        for i, video_path in enumerate(video_files, 1):
            print(u"\n处理文件 {}/{}: {}".format(i, total_count, os.path.basename(video_path)))
            
            try:
                video_info = get_video_info(video_path)
                if not video_info:
                    print(u"✗ 无法读取视频信息，跳过")
                    continue
                
                file_success = True
                
                if extract_audio:
                    print(u"  提取音频...")
                    has_audio = self.check_audio_stream(video_path)
                    if has_audio:
                        # 使用默认设置提取音频
                        if not self._extract_audio_simple(video_path, video_info):
                            file_success = False
                    else:
                        print(u"  ⚠ 该文件没有音频流")
                
                if extract_subs:
                    print(u"  提取字幕...")
                    subtitle_count = self.check_subtitle_streams(video_path)
                    if subtitle_count > 0:
                        if not self._extract_subtitles_simple(video_path, video_info, subtitle_count):
                            file_success = False
                    else:
                        print(u"  ⚠ 该文件没有字幕轨道")
                
                if file_success:
                    success_count += 1
                    print(u"  ✓ 处理完成")
                else:
                    print(u"  ✗ 处理失败")
                    
            except Exception as e:
                print(u"  ✗ 处理出错: {}".format(str(e)))
        
        print(u"\n" + u"=" * 40)
        print(u"批量提取完成！")
        print(u"=" * 40)
        print(u"成功处理: {} / {} 个文件".format(success_count, total_count))
    
    def _extract_audio_simple(self, video_path, video_info):
        """简单音频提取（用于批量处理）"""
        try:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_dir = "audio"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            output_path = os.path.join(output_dir, base_name + "_audio.mp3")
            
            cmd = [
                self.ffmpeg_path, '-y', '-i', video_path,
                '-vn', '-acodec', 'mp3', '-b:a', '192k',
                output_path
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            return process.returncode == 0 and os.path.exists(output_path)
            
        except Exception:
            return False
    
    def _extract_subtitles_simple(self, video_path, video_info, subtitle_count):
        """简单字幕提取（用于批量处理）"""
        try:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_dir = "srt"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            success = True
            for i in range(subtitle_count):
                output_path = os.path.join(output_dir, "{}_subtitle_{}.srt".format(base_name, i + 1))
                
                cmd = [
                    self.ffmpeg_path, '-y', '-i', video_path,
                    '-map', '0:s:{}'.format(i),
                    '-c:s', 'srt',
                    output_path
                ]
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                if process.returncode != 0 or not os.path.exists(output_path):
                    success = False
            
            return success
            
        except Exception:
            return False
    
    def run(self):
        """运行主程序"""
        self.print_banner()
        
        while True:
            print(u"请选择操作模式:")
            print(u"1. 单个视频提取")
            print(u"2. 批量视频提取")
            print(u"3. 视频元素去除（音频/水印/字幕）")
            print(u"4. 返回主菜单")
            print()
            
            try:
                choice = safe_input(u"请选择模式 (1-4): ").strip()
                
                if choice == '1':
                    self.single_video_mode()
                elif choice == '2':
                    self.batch_extract_mode()
                elif choice == '3':
                    self.video_processing_mode()
                elif choice == '4':
                    break
                else:
                    print(u"无效选择，请重新输入")
                    continue
                    
                # 询问是否继续
                continue_choice = safe_input(u"\n是否继续使用提取功能？(Y/n): ").strip().lower()
                if continue_choice == 'n':
                    break
                        
            except KeyboardInterrupt:
                print(u"\n\n用户中断操作")
                break
            except Exception as e:
                print(u"\n程序执行出错: {}".format(str(e)))
                import traceback
                traceback.print_exc()
                continue
    
    def video_processing_mode(self):
        """视频处理模式"""
        # 获取视频文件
        video_path, video_info, has_audio, subtitle_count = self.get_video_path()
        
        # 执行视频元素去除
        self.remove_video_elements(video_path, video_info)
    
    def single_video_mode(self):
        """单个视频提取模式"""
        # 获取视频文件
        video_path, video_info, has_audio, subtitle_count = self.get_video_path()
        
        # 选择提取类型
        print(u"\n请选择提取类型:")
        options = []
        
        if has_audio:
            options.append((1, u"提取音频文件"))
        
        if subtitle_count > 0:
            options.append((len(options) + 1, u"提取字幕文件"))
        
        # 语音识别生成字幕（只要有音频就可以）
        if has_audio:
            options.append((len(options) + 1, u"语音识别生成字幕"))
        
        if has_audio and subtitle_count > 0:
            options.append((len(options) + 1, u"同时提取音频和字幕"))
        
        if not options:
            print(u"该视频文件既没有音频流也没有字幕轨道，无法提取")
            return
        
        for num, desc in options:
            print(u"{}. {}".format(num, desc))
        
        while True:
            try:
                choice = int(safe_input(u"请选择 (1-{}): ".format(len(options))).strip())
                if 1 <= choice <= len(options):
                    break
                print(u"请输入有效的选择")
            except ValueError:
                print(u"请输入数字")
        
        selected_option = options[choice - 1]
        
        # 执行对应操作
        if u"音频" in selected_option[1] and u"字幕" not in selected_option[1] and u"语音识别" not in selected_option[1]:
            self.extract_audio(video_path, video_info)
        elif u"字幕" in selected_option[1] and u"音频" not in selected_option[1] and u"语音识别" not in selected_option[1]:
            self.extract_subtitles(video_path, video_info, subtitle_count)
        elif u"语音识别" in selected_option[1]:
            self.speech_recognition_to_subtitle(video_path, video_info)
        elif u"同时提取" in selected_option[1]:
            print(u"同时提取音频和字幕...")
            audio_success = self.extract_audio(video_path, video_info)
            subtitle_success = self.extract_subtitles(video_path, video_info, subtitle_count)
            
            if audio_success and subtitle_success:
                print(u"\n音频和字幕提取全部完成！")
            elif audio_success or subtitle_success:
                print(u"\n部分提取成功")
            else:
                print(u"\n提取失败")


def main():
    """主入口函数"""
    try:
        print("Starting extractor CLI...")
        extractor = ExtractorCLI()
        print("ExtractorCLI created successfully")
        extractor.run()
        print("ExtractorCLI finished")
    except Exception as e:
        print("Error in main: {}".format(str(e)))
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
