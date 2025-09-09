# -*- coding: utf-8 -*-
"""
语音合成模块
支持将文本转换为语音音频文件
"""

import os
import time
import subprocess

class TextToSpeechGenerator(object):
    """文本转语音生成器"""
    
    def __init__(self):
        self.voice_configs = {
            'zh-CN-XiaoxiaoNeural': u'晓晓（温柔女声）',
            'zh-CN-YunxiNeural': u'云希（活泼男声）',
            'zh-CN-XiaoyiNeural': u'小艺（知性女声）',
            'zh-CN-YunjianNeural': u'云健（稳重男声）'
        }
    
    def check_tts_availability(self):
        """检查TTS引擎可用性"""
        available_engines = []
        
        # 检查 edge-tts
        try:
            with open(os.devnull, 'w') as devnull:
                result = subprocess.call(['edge-tts', '--version'], 
                                       stdout=devnull, 
                                       stderr=devnull)
                if result == 0:
                    available_engines.append('edge-tts')
        except (OSError, subprocess.CalledProcessError):
            pass
        
        # 检查 pyttsx3
        try:
            import pyttsx3
            available_engines.append('pyttsx3')
        except ImportError:
            pass
        
        # 系统TTS总是可用（作为备选）
        available_engines.append('system')
        
        return available_engines
    
    def generate_speech_for_subtitles(self, subtitles, voice='zh-CN-XiaoxiaoNeural', 
                                    output_dir=None, engine='auto'):
        """
        为字幕列表生成对应的语音文件
        """
        if not subtitles:
            raise ValueError(u"字幕列表为空")
        
        # 确定输出目录
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(__file__), 'audio')
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 检查可用引擎
        available_engines = self.check_tts_availability()
        if engine == 'auto':
            engine = available_engines[0] if available_engines else 'system'
        
        print(u"使用语音引擎: {}".format(engine))
        print(u"使用语音: {}".format(self.voice_configs.get(voice, voice)))
        
        audio_files = []
        total_duration = 0.0
        
        # 为每条字幕生成语音
        for i, subtitle_data in enumerate(subtitles):
            # 兼容不同的数据格式
            if isinstance(subtitle_data, dict):
                # 字典格式: {'start': ..., 'end': ..., 'text': ...}
                start_time = subtitle_data.get('start', 0)
                end_time = subtitle_data.get('end', 0)
                text = subtitle_data.get('text', '')
            elif isinstance(subtitle_data, (tuple, list)) and len(subtitle_data) >= 3:
                # 元组/列表格式: (start_time, end_time, text)
                start_time, end_time, text = subtitle_data[:3]
            else:
                print(u"无效的字幕数据格式，跳过: {}".format(subtitle_data))
                continue
            
            if not text.strip():
                continue
            
            # 确保时间是浮点数类型
            try:
                start_time = float(start_time)
                end_time = float(end_time)
            except (ValueError, TypeError):
                print(u"时间格式错误，跳过: {} - {}".format(start_time, end_time))
                continue
                
            duration = end_time - start_time
            total_duration += duration
            
            # 生成音频文件名
            timestamp = int(time.time())
            audio_filename = "speech_{}_part_{:03d}.wav".format(timestamp, i + 1)
            audio_path = os.path.join(output_dir, audio_filename)
            
            print(u"生成语音 {}/{}: {}".format(i + 1, len(subtitles), text[:20] + "..."))
            
            # 生成语音文件
            success = self._generate_single_speech(text, audio_path, voice, engine, duration)
            
            if success:
                audio_files.append({
                    'path': audio_path,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': duration,
                    'text': text,
                    'index': i
                })
            else:
                print(u"警告: 第{}条字幕语音生成失败".format(i + 1))
        
        # 合并所有语音片段
        if audio_files:
            # 由于每个音频片段都已经匹配字幕时长，可以使用简单顺序合并
            merged_audio_path = self._smooth_merge_audio_segments(audio_files, output_dir)
            
            # 清理中间生成的分段文件（只在有多个文件时清理）
            if len(audio_files) > 1:
                print(u"清理临时音频片段...")
                for audio_info in audio_files:
                    try:
                        if os.path.exists(audio_info['path']) and audio_info['path'] != merged_audio_path:
                            os.remove(audio_info['path'])
                    except Exception as e:
                        print(u"清理文件失败: {} - {}".format(audio_info['path'], str(e)))
            
            return {
                'merged_audio': merged_audio_path,
                'total_duration': total_duration,
                'voice_used': voice,
                'engine_used': engine,
                'segments_count': len(audio_files)
            }
        else:
            raise RuntimeError(u"没有成功生成任何语音文件")
    
    def _generate_single_speech(self, text, output_path, voice, engine, target_duration=None):
        """生成单个语音片段"""
        try:
            if engine == 'edge-tts':
                return self._generate_with_edge_tts(text, output_path, voice, target_duration)
            elif engine == 'pyttsx3':
                return self._generate_with_pyttsx3(text, output_path, target_duration)
            else:
                return self._generate_with_system_tts(text, output_path, target_duration)
        except Exception as e:
            print(u"语音生成失败: {}".format(str(e)))
            return False
    
    def _generate_with_edge_tts(self, text, output_path, voice, target_duration=None):
        """使用Edge-TTS生成语音"""
        try:
            # 构建edge-tts命令
            cmd = [
                'edge-tts',
                '--voice', voice,
                '--text', text.encode('utf-8'),
                '--write-media', output_path
            ]
            
            # 如果指定了目标时长，精确调整语速以匹配字幕时间
            if target_duration and target_duration > 0.5:  # 只对合理的时长进行调整
                # 更精确的语速估算：基于中文字符数和目标时长
                text_length = len(text.strip())
                if text_length > 0:
                    # 中文平均语速：每秒4-6个字符，根据目标时长调整
                    target_chars_per_sec = text_length / target_duration
                    normal_chars_per_sec = 4.5  # 稍慢的正常语速，更自然
                    speed_ratio = target_chars_per_sec / normal_chars_per_sec
                    
                    # 限制语速范围：0.6-1.8倍速，避免过于极端的语速
                    speed_ratio = max(0.6, min(1.8, speed_ratio))
                    rate_percent = int((speed_ratio - 1) * 100)
                    
                    if abs(rate_percent) > 5:  # 只有显著差异时才调整语速
                        rate = "{:+d}%".format(rate_percent)
                        cmd.extend(['--rate', rate])
                        print(u"调整语速{}以匹配{:.1f}秒时长 ({}字符)".format(rate, target_duration, text_length))
            
            # 执行命令
            result = subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 验证生成的音频时长是否符合预期
            success = result == 0 and os.path.exists(output_path)
            if success and target_duration:
                actual_duration = self._get_audio_duration(output_path)
                if actual_duration:
                    duration_diff = abs(actual_duration - target_duration)
                    if duration_diff > 0.3:  # 允许0.3秒的误差
                        print(u"  音频时长{:.1f}s，目标{:.1f}s，差异{:.1f}s".format(
                            actual_duration, target_duration, duration_diff))
                        
                        # 如果时长差异较大，尝试使用FFmpeg调整音频速度
                        if duration_diff > 1.0 and actual_duration > 0.5:
                            success = self._adjust_audio_speed(output_path, actual_duration, target_duration)
            
            return success
        
        except Exception as e:
            print(u"Edge-TTS执行失败: {}".format(str(e)))
            return False
    
    def _adjust_audio_speed(self, audio_path, actual_duration, target_duration):
        """使用FFmpeg调整音频播放速度以匹配目标时长"""
        try:
            speed_ratio = actual_duration / target_duration  # >1表示需要加速，<1表示需要减速
            
            # 限制速度调整范围，避免音质严重下降
            speed_ratio = max(0.7, min(1.4, speed_ratio))
            
            if abs(speed_ratio - 1.0) < 0.05:  # 差异很小，不需要调整
                return True
            
            temp_path = audio_path + ".temp.wav"
            
            # 使用FFmpeg的atempo滤镜调整播放速度（保持音调）
            cmd = [
                'ffmpeg', '-y',
                '-i', audio_path,
                '-filter:a', 'atempo={:.3f}'.format(speed_ratio),
                temp_path
            ]
            
            result = subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if result == 0 and os.path.exists(temp_path):
                # 替换原文件
                import shutil
                shutil.move(temp_path, audio_path)
                print(u"    已调整音频速度: {:.1f}x (时长{:.1f}s→{:.1f}s)".format(
                    speed_ratio, actual_duration, target_duration))
                return True
            else:
                print(u"    音频速度调整失败")
                # 清理临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return True  # 即使调整失败，也返回原文件
        
        except Exception as e:
            print(u"音频速度调整出错: {}".format(str(e)))
            return True  # 出错时返回原文件
    
    def _get_audio_duration(self, audio_path):
        """获取音频文件时长"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', audio_path
            ]
            result = subprocess.check_output(cmd)
            return float(result.strip())
        except:
            return None
    
    def _generate_with_pyttsx3(self, text, output_path, target_duration=None):
        """使用pyttsx3生成语音"""
        try:
            import pyttsx3
            
            # 检查pyttsx3版本是否支持save_to_file
            engine = pyttsx3.init()
            
            # 设置语音参数
            voices = engine.getProperty('voices')
            if voices:
                # 尝试找到中文语音
                for voice in voices:
                    voice_name = getattr(voice, 'name', str(voice))
                    if 'chinese' in voice_name.lower() or 'zh' in str(voice).lower():
                        engine.setProperty('voice', voice.id)
                        break
            
            # 根据目标时长精确调整语速
            if target_duration and target_duration > 0.5:
                text_length = len(text.strip())
                if text_length > 0:
                    # 计算合适的语速：基于字符数和目标时长
                    target_chars_per_sec = text_length / target_duration
                    # pyttsx3的rate单位通常是每分钟词数，需要换算
                    # 中文平均每秒4.5字符 = 270字符/分钟 = 基准rate 150
                    base_rate = 150
                    target_rate = int(target_chars_per_sec * 60 / 4.5 * (base_rate / 150))
                    target_rate = max(80, min(250, target_rate))  # 限制在合理范围内
                    
                    engine.setProperty('rate', target_rate)
                    print(u"调整pyttsx3语速至{}以匹配{:.1f}秒时长".format(target_rate, target_duration))
            
            # 检查是否有save_to_file方法
            if hasattr(engine, 'save_to_file'):
                # 新版本pyttsx3
                engine.save_to_file(text, output_path)
                engine.runAndWait()
            else:
                # 旧版本pyttsx3，使用系统TTS备用方案
                print(u"pyttsx3版本较旧，使用系统TTS生成语音文件")
                return self._generate_with_system_tts(text, output_path, target_duration)
            
            # 验证并调整音频时长
            success = os.path.exists(output_path)
            if success and target_duration:
                actual_duration = self._get_audio_duration(output_path)
                if actual_duration and abs(actual_duration - target_duration) > 0.5:
                    print(u"  pyttsx3音频时长{:.1f}s，目标{:.1f}s".format(actual_duration, target_duration))
                    # 使用FFmpeg进行后处理调整
                    success = self._adjust_audio_speed(output_path, actual_duration, target_duration)
            
            return success
        
        except Exception as e:
            print(u"pyttsx3执行失败: {}".format(str(e)))
            # 如果pyttsx3失败，回退到系统TTS
            return self._generate_with_system_tts(text, output_path, target_duration)
    
    def _generate_with_system_tts(self, text, output_path, target_duration=None):
        """使用系统TTS生成语音（备用方案）"""
        try:
            # Windows系统使用SAPI
            if os.name == 'nt':
                # 创建临时VBS脚本
                # 处理文本编码
                safe_text = text.replace('"', '""')
                safe_output_path = output_path.replace('\\', '\\\\')
                
                # 根据目标时长调整语速
                rate_setting = "0"  # 默认语速
                if target_duration and target_duration > 0.5:
                    text_length = len(text.strip())
                    if text_length > 0:
                        target_chars_per_sec = text_length / target_duration
                        # SAPI语速范围：-10到10，0为正常语速
                        if target_chars_per_sec > 5.5:  # 需要加速
                            rate_setting = str(min(8, int((target_chars_per_sec - 4.5) * 2)))
                        elif target_chars_per_sec < 3.5:  # 需要减速
                            rate_setting = str(max(-8, int((target_chars_per_sec - 4.5) * 2)))
                        
                        print(u"调整系统TTS语速至{}以匹配{:.1f}秒时长".format(rate_setting, target_duration))
                
                vbs_script = u'''
Set speech = CreateObject("SAPI.SpVoice")
Set file = CreateObject("SAPI.SpFileStream")
speech.Rate = {}
file.Open "{}", 3
Set speech.AudioOutputStream = file
speech.Speak "{}"
file.Close
'''.format(rate_setting, safe_output_path, safe_text)
                
                temp_vbs = os.path.join(os.path.dirname(output_path), 'temp_tts.vbs')
                
                # 写入VBS文件时使用UTF-8编码
                import codecs
                with codecs.open(temp_vbs, 'w', encoding='utf-8') as f:
                    f.write(vbs_script)
                
                # 执行VBS脚本
                result = subprocess.call(['cscript', '//nologo', temp_vbs])
                
                # 清理临时文件
                if os.path.exists(temp_vbs):
                    os.remove(temp_vbs)
                
                success = result == 0 and os.path.exists(output_path)
                
                # 验证并调整音频时长
                if success and target_duration:
                    actual_duration = self._get_audio_duration(output_path)
                    if actual_duration and abs(actual_duration - target_duration) > 0.5:
                        print(u"  系统TTS音频时长{:.1f}s，目标{:.1f}s".format(actual_duration, target_duration))
                        # 使用FFmpeg进行后处理调整
                        success = self._adjust_audio_speed(output_path, actual_duration, target_duration)
                
                return success
            else:
                # Linux/macOS使用espeak或festival，也尝试调整语速
                text_utf8 = text.encode('utf-8')
                speed_param = '150'  # 默认语速
                
                if target_duration and target_duration > 0.5:
                    text_length = len(text.strip())
                    if text_length > 0:
                        target_chars_per_sec = text_length / target_duration
                        # espeak语速单位是每分钟词数
                        speed = max(80, min(300, int(target_chars_per_sec * 15)))
                        speed_param = str(speed)
                        print(u"调整espeak语速至{}以匹配{:.1f}秒时长".format(speed_param, target_duration))
                
                cmd = ['espeak', '-s', speed_param, '-v', 'zh', '-w', output_path, text_utf8]
                result = subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                success = result == 0 and os.path.exists(output_path)
                
                # 验证并调整音频时长
                if success and target_duration:
                    actual_duration = self._get_audio_duration(output_path)
                    if actual_duration and abs(actual_duration - target_duration) > 0.8:
                        print(u"  espeak音频时长{:.1f}s，目标{:.1f}s".format(actual_duration, target_duration))
                        success = self._adjust_audio_speed(output_path, actual_duration, target_duration)
                
                return success
        
        except Exception as e:
            print(u"系统TTS执行失败: {}".format(str(e)))
            return False
    
    def _smooth_merge_audio_segments(self, audio_files, output_dir):
        """平滑合并音频片段，保持自然的语音节奏"""
        try:
            timestamp = int(time.time())
            merged_path = os.path.join(output_dir, "merged_speech_{}.wav".format(timestamp))
            
            # 如果只有一个文件，直接移动
            if len(audio_files) == 1:
                import shutil
                source_path = audio_files[0]['path']
                shutil.move(source_path, merged_path)
                audio_files[0]['path'] = merged_path
                return merged_path
            
            # 按开始时间排序
            sorted_audio_files = sorted(audio_files, key=lambda x: x['start_time'])
            total_duration = max([af['end_time'] for af in sorted_audio_files])
            
            print(u"正在平滑合并{}个音频片段，总时长{:.1f}秒...".format(len(sorted_audio_files), total_duration))
            
            # 计算每个音频片段之间的间隔
            segments_with_gaps = []
            for i, audio_info in enumerate(sorted_audio_files):
                segments_with_gaps.append(audio_info['path'])
                
                # 添加间隔（除了最后一个片段）
                if i < len(sorted_audio_files) - 1:
                    next_audio = sorted_audio_files[i + 1]
                    gap_duration = next_audio['start_time'] - audio_info['end_time']
                    
                    if gap_duration > 0.1:  # 间隔大于0.1秒时添加静音
                        gap_duration = min(gap_duration, 2.0)  # 最大间隔限制为2秒
                        gap_file = os.path.join(output_dir, "gap_{}.wav".format(i))
                        
                        # 生成静音间隔
                        cmd_gap = [
                            'ffmpeg', '-y',
                            '-f', 'lavfi',
                            '-i', 'anullsrc=channel_layout=mono:sample_rate=22050',
                            '-t', str(gap_duration),
                            gap_file
                        ]
                        
                        result = subprocess.call(cmd_gap, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        if result == 0 and os.path.exists(gap_file):
                            segments_with_gaps.append(gap_file)
                            print(u"  添加{:.1f}秒间隔".format(gap_duration))
            
            # 使用FFmpeg concat方式合并所有片段
            concat_file = os.path.join(output_dir, "temp_concat_{}.txt".format(timestamp))
            
            with open(concat_file, 'w') as f:
                for segment_path in segments_with_gaps:
                    f.write("file '{}'\n".format(os.path.basename(segment_path)))
            
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',
                merged_path
            ]
            
            result = subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 清理临时文件
            if os.path.exists(concat_file):
                os.remove(concat_file)
            
            # 清理间隔文件
            for i in range(len(sorted_audio_files) - 1):
                gap_file = os.path.join(output_dir, "gap_{}.wav".format(i))
                if os.path.exists(gap_file):
                    try:
                        os.remove(gap_file)
                    except:
                        pass
            
            if result == 0 and os.path.exists(merged_path):
                actual_duration = self._get_audio_duration(merged_path)
                print(u"平滑合并成功！实际时长: {:.2f}秒".format(actual_duration or 0))
                return merged_path
            else:
                print(u"平滑合并失败，使用时间同步方案")
                return self._timing_sync_merge_audio_segments(audio_files, output_dir)
                
        except Exception as e:
            print(u"平滑合并出错: {}".format(str(e)))
            return self._timing_sync_merge_audio_segments(audio_files, output_dir)
    
    def _timing_sync_merge_audio_segments(self, audio_files, output_dir):
        """时间同步合并音频片段，严格按照字幕时间间隔"""
        try:
            timestamp = int(time.time())
            merged_path = os.path.join(output_dir, "merged_speech_{}.wav".format(timestamp))
            
            # 如果只有一个文件，直接移动
            if len(audio_files) == 1:
                import shutil
                source_path = audio_files[0]['path']
                shutil.move(source_path, merged_path)
                audio_files[0]['path'] = merged_path
                return merged_path
            
            # 按开始时间排序
            sorted_audio_files = sorted(audio_files, key=lambda x: x['start_time'])
            
            # 计算总时长（到最后一个字幕结束）
            total_duration = max([af['end_time'] for af in sorted_audio_files])
            
            print(u"正在时间同步合并{}个音频片段，总时长{:.1f}秒...".format(len(sorted_audio_files), total_duration))
            
            # 验证所有音频文件是否存在
            missing_files = []
            for i, audio_info in enumerate(sorted_audio_files):
                if not os.path.exists(audio_info['path']):
                    missing_files.append(i)
            
            if missing_files:
                print(u"错误: 以下音频文件不存在: {}".format(missing_files))
                return self._fallback_timing_merge(sorted_audio_files, merged_path, total_duration)
            
            # 方案1：使用FFmpeg的adelay滤镜精确控制时间
            input_args = []
            filter_parts = []
            
            for i, audio_info in enumerate(sorted_audio_files):
                # 验证音频文件路径
                abs_path = os.path.abspath(audio_info['path'])
                input_args.extend(['-i', abs_path])
                
                # 计算延迟时间（毫秒）
                delay_ms = int(audio_info['start_time'] * 1000)
                
                if delay_ms > 0:
                    # 使用adelay滤镜添加延迟
                    filter_parts.append('[{}:a]adelay={}|{}[a{}]'.format(i, delay_ms, delay_ms, i))
                else:
                    # 不需要延迟，直接标记
                    filter_parts.append('[{}:a]anull[a{}]'.format(i, i))
                
                print(u"  音频{}: {:.1f}s-{:.1f}s, 延迟{}ms".format(
                    i+1, audio_info['start_time'], audio_info['end_time'], delay_ms))
            
            # 构建混合滤镜
            mix_inputs = ''.join('[a{}]'.format(i) for i in range(len(sorted_audio_files)))
            mix_filter = '{}amix=inputs={}:duration=longest:dropout_transition=0[out]'.format(
                mix_inputs, len(sorted_audio_files)
            )
            
            # 完整的滤镜链
            complete_filter = ';'.join(filter_parts) + ';' + mix_filter
            
            print(u"滤镜链: {}".format(complete_filter))
            
            # 执行FFmpeg命令
            cmd = ['ffmpeg', '-y'] + input_args + [
                '-filter_complex', complete_filter,
                '-map', '[out]',
                '-t', str(total_duration),
                '-ar', '22050', '-ac', '1',
                merged_path
            ]
            
            print(u"执行FFmpeg命令:")
            print(u"  {}".format(' '.join(cmd)))
            
            # 执行并捕获详细错误信息
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            print(u"FFmpeg返回码: {}".format(process.returncode))
            
            # 显示详细的错误信息
            if stderr:
                stderr_text = stderr.decode('utf-8', errors='ignore')
                if process.returncode != 0:
                    print(u"FFmpeg错误输出:")
                    print(stderr_text)
                else:
                    # 只在调试模式下显示正常的stderr输出
                    if "error" in stderr_text.lower() or "fail" in stderr_text.lower():
                        print(u"FFmpeg警告:")
                        print(stderr_text[-500:])  # 只显示最后500字符
            
            if process.returncode == 0 and os.path.exists(merged_path):
                print(u"时间同步合并成功！音频时长: {:.2f}秒".format(total_duration))
                
                # 验证输出文件的时长
                try:
                    actual_duration = self._get_audio_duration(merged_path)
                    if actual_duration:
                        print(u"实际音频时长: {:.2f}秒".format(actual_duration))
                        if abs(actual_duration - total_duration) > 0.5:
                            print(u"警告: 实际时长与预期不匹配")
                except:
                    pass
                
                return merged_path
            else:
                print(u"FFmpeg时间同步合并失败，尝试备用方案...")
                return self._fallback_timing_merge(sorted_audio_files, merged_path, total_duration)
                
        except Exception as e:
            print(u"时间同步合并出错: {}".format(str(e)))
            import traceback
            traceback.print_exc()
            return self._fallback_timing_merge(sorted_audio_files, merged_path, total_duration)
    
    def _fallback_timing_merge(self, sorted_audio_files, merged_path, total_duration):
        """备用时间同步合并方案"""
        try:
            print(u"使用备用时间同步方案...")
            
            # 创建静音轨道作为基础
            silent_base = os.path.join(os.path.dirname(merged_path), "silent_base.wav")
            
            print(u"生成{:.1f}秒静音基础轨道...".format(total_duration))
            
            # 生成静音基础轨道
            cmd_silent = [
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', 'anullsrc=channel_layout=mono:sample_rate=22050',
                '-t', str(total_duration),
                silent_base
            ]
            
            result_silent = subprocess.call(cmd_silent, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result_silent != 0 or not os.path.exists(silent_base):
                print(u"生成静音轨道失败")
                return self._fast_merge_audio_segments(sorted_audio_files, os.path.dirname(merged_path))
            
            print(u"逐个混合音频片段...")
            
            # 逐个将音频段混合到静音轨道上
            current_output = silent_base
            
            for i, audio_info in enumerate(sorted_audio_files):
                print(u"  混合音频{}/{}: {:.1f}s位置".format(i+1, len(sorted_audio_files), audio_info['start_time']))
                
                temp_output = os.path.join(os.path.dirname(merged_path), "temp_mix_{}.wav".format(i))
                
                # 使用amix在指定时间点混合音频
                cmd_mix = [
                    'ffmpeg', '-y',
                    '-i', current_output,
                    '-i', audio_info['path'],
                    '-filter_complex', 
                    '[1:a]adelay={}|{}[delayed];[0:a][delayed]amix=inputs=2:duration=first[out]'.format(
                        int(audio_info['start_time'] * 1000), 
                        int(audio_info['start_time'] * 1000)
                    ),
                    '-map', '[out]',
                    temp_output
                ]
                
                process = subprocess.Popen(cmd_mix, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                
                if process.returncode == 0 and os.path.exists(temp_output):
                    # 删除前一个临时文件
                    if current_output != silent_base and os.path.exists(current_output):
                        os.remove(current_output)
                    current_output = temp_output
                else:
                    print(u"混合音频段{}失败，返回码: {}".format(i, process.returncode))
                    if stderr:
                        print(u"错误: {}".format(stderr.decode('utf-8', errors='ignore')[-200:]))
                    # 继续处理下一个
            
            # 最终文件重命名
            if current_output != merged_path and os.path.exists(current_output):
                import shutil
                shutil.move(current_output, merged_path)
            
            # 清理临时文件
            cleanup_files = [silent_base]
            for i in range(len(sorted_audio_files)):
                cleanup_files.append(os.path.join(os.path.dirname(merged_path), "temp_mix_{}.wav".format(i)))
            
            for cleanup_file in cleanup_files:
                if os.path.exists(cleanup_file):
                    try:
                        os.remove(cleanup_file)
                    except:
                        pass
            
            if os.path.exists(merged_path):
                print(u"备用时间同步合并成功！")
                return merged_path
            else:
                print(u"备用方案也失败，返回简单连接结果")
                return self._fast_merge_audio_segments(sorted_audio_files, os.path.dirname(merged_path))
                
        except Exception as e:
            print(u"备用时间同步方案出错: {}".format(str(e)))
            import traceback
            traceback.print_exc()
            print(u"回退到简单连接方案")
            return self._fast_merge_audio_segments(sorted_audio_files, os.path.dirname(merged_path))
    
    def _fast_merge_audio_segments(self, audio_files, output_dir):
        """快速合并音频片段，优先速度而非完美时间同步"""
        try:
            timestamp = int(time.time())
            merged_path = os.path.join(output_dir, "merged_speech_{}.wav".format(timestamp))
            
            # 如果只有一个文件，直接移动
            if len(audio_files) == 1:
                import shutil
                source_path = audio_files[0]['path']
                shutil.move(source_path, merged_path)
                audio_files[0]['path'] = merged_path
                return merged_path
            
            # 按开始时间排序
            sorted_audio_files = sorted(audio_files, key=lambda x: x['start_time'])
            
            print(u"正在快速合并{}个音频片段（简化模式）...".format(len(sorted_audio_files)))
            
            # 使用最简单的concat方式 - 速度最快
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
                print(u"快速合并失败，返回第一个文件")
                return sorted_audio_files[0]['path']
                
        except Exception as e:
            print(u"快速合并出错: {}".format(str(e)))
            return sorted_audio_files[0]['path'] if sorted_audio_files else None
    
    def _merge_audio_segments(self, audio_files, output_dir):
        """合并音频片段为完整的音频文件，保持字幕时间同步 - 优化版"""
        try:
            timestamp = int(time.time())
            merged_path = os.path.join(output_dir, "merged_speech_{}.wav".format(timestamp))
            
            # 如果只有一个文件，重命名而不是复制
            if len(audio_files) == 1:
                import shutil
                source_path = audio_files[0]['path']
                shutil.move(source_path, merged_path)
                audio_files[0]['path'] = merged_path
                return merged_path
            
            # 按开始时间排序
            sorted_audio_files = sorted(audio_files, key=lambda x: x['start_time'])
            total_duration = max([af['end_time'] for af in sorted_audio_files])
            
            print(u"正在快速合并{}个音频片段...".format(len(sorted_audio_files)))
            
            # 方案1：尝试使用Python音频库快速合并（如果可用）
            try:
                return self._fast_python_merge(sorted_audio_files, merged_path, total_duration)
            except:
                pass  # 如果失败，继续使用FFmpeg方案
            
            # 方案2：使用优化的FFmpeg单命令合并
            return self._optimized_ffmpeg_merge(sorted_audio_files, merged_path, total_duration)
                
        except Exception as e:
            print(u"音频合并过程出错: {}".format(str(e)))
            return self._fallback_concat_merge(audio_files, output_dir)
    
    def _fast_python_merge(self, sorted_audio_files, merged_path, total_duration):
        """使用Python音频库快速合并（如果可用）"""
        try:
            # 尝试使用pydub进行快速合并
            try:
                from pydub import AudioSegment
            except ImportError:
                raise Exception("pydub not available")
            
            # 创建空的音频段，长度为总时长
            final_audio = AudioSegment.silent(duration=int(total_duration * 1000))  # pydub使用毫秒
            
            # 将每个音频片段放置到正确位置
            for audio_info in sorted_audio_files:
                # 加载音频文件
                audio_segment = AudioSegment.from_wav(audio_info['path'])
                start_ms = int(audio_info['start_time'] * 1000)
                
                # 将音频段叠加到指定位置
                final_audio = final_audio.overlay(audio_segment, position=start_ms)
            
            # 导出最终音频
            final_audio.export(merged_path, format="wav")
            print(u"Python快速合并成功，总时长: {:.2f}秒".format(total_duration))
            return merged_path
            
        except ImportError:
            print(u"pydub不可用，回退到FFmpeg方案...")
            raise Exception("pydub not available")
        except Exception as e:
            print(u"Python合并失败: {}".format(str(e)))
            raise e
    
    def _optimized_ffmpeg_merge(self, sorted_audio_files, merged_path, total_duration):
        """使用优化的FFmpeg单命令合并"""
        try:
            # 创建临时的带时间信息的音频文件列表
            temp_files = []
            
            for i, audio_info in enumerate(sorted_audio_files):
                # 为每个音频文件创建一个带延迟的临时版本
                temp_file = os.path.join(os.path.dirname(merged_path), 
                                       "temp_delayed_{}.wav".format(i))
                
                delay_seconds = audio_info['start_time']
                
                if delay_seconds > 0:
                    # 在音频前添加静音
                    cmd = [
                        'ffmpeg', '-y',
                        '-f', 'lavfi', '-t', str(delay_seconds), 
                        '-i', 'anullsrc=channel_layout=mono:sample_rate=22050',
                        '-i', audio_info['path'],
                        '-filter_complex', '[0:a][1:a]concat=n=2:v=0:a=1[out]',
                        '-map', '[out]',
                        temp_file
                    ]
                else:
                    # 直接复制
                    cmd = ['ffmpeg', '-y', '-i', audio_info['path'], '-c', 'copy', temp_file]
                
                result = subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result == 0:
                    temp_files.append(temp_file)
                else:
                    print(u"创建临时文件{}失败".format(i))
            
            if not temp_files:
                raise Exception("No temporary files created")
            
            # 使用amix混合所有临时文件
            input_args = []
            for temp_file in temp_files:
                input_args.extend(['-i', temp_file])
            
            mix_filter = 'amix=inputs={}:duration=longest:dropout_transition=0'.format(len(temp_files))
            
            cmd = ['ffmpeg', '-y'] + input_args + [
                '-filter_complex', mix_filter,
                '-t', str(total_duration),
                '-ar', '22050', '-ac', '1',
                merged_path
            ]
            
            result = subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 清理临时文件
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass
            
            if result == 0 and os.path.exists(merged_path):
                print(u"FFmpeg优化合并成功，总时长: {:.2f}秒".format(total_duration))
                return merged_path
            else:
                raise Exception("FFmpeg merge failed")
                
        except Exception as e:
            print(u"优化FFmpeg合并失败: {}".format(str(e)))
            # 回退到简单连接合并
            return self._fallback_concat_merge(sorted_audio_files, os.path.dirname(merged_path))
    
    def _fallback_concat_merge(self, audio_files, output_dir):
        """备用的简单连接合并方案"""
        try:
            timestamp = int(time.time())
            merged_path = os.path.join(output_dir, "merged_speech_{}.wav".format(timestamp))
            
            # 创建concat文件列表
            concat_file = os.path.join(output_dir, "temp_concat_{}.txt".format(timestamp))
            
            with open(concat_file, 'w') as f:
                for audio_info in sorted(audio_files, key=lambda x: x['start_time']):
                    f.write("file '{}'\n".format(os.path.basename(audio_info['path'])))
            
            # 使用FFmpeg合并
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',
                '-y',
                merged_path
            ]
            
            result = subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 清理临时文件
            if os.path.exists(concat_file):
                os.remove(concat_file)
            
            if result == 0 and os.path.exists(merged_path):
                print(u"使用备用方案合并成功")
                return merged_path
            else:
                print(u"备用合并方案也失败，返回第一个音频文件")
                return audio_files[0]['path'] if audio_files else None
                
        except Exception as e:
            print(u"备用合并方案出错: {}".format(str(e)))
            return audio_files[0]['path'] if audio_files else None
    
    def install_dependencies(self):
        """安装TTS依赖"""
        print(u"正在检查和安装TTS依赖...")
        
        # 获取Python可执行文件路径
        python_exe = self._get_python_executable()
        
        try:
            # 尝试安装edge-tts
            print(u"安装edge-tts...")
            subprocess.check_call([python_exe, '-m', 'pip', 'install', 'edge-tts'])
            print(u"✓ edge-tts安装成功")
        except subprocess.CalledProcessError as e:
            print(u"✗ edge-tts安装失败: {}".format(str(e)))
        except OSError as e:
            print(u"✗ edge-tts安装失败 - Python路径错误: {}".format(str(e)))
        
        try:
            # 尝试安装pyttsx3
            print(u"安装pyttsx3...")
            subprocess.check_call([python_exe, '-m', 'pip', 'install', 'pyttsx3'])
            print(u"✓ pyttsx3安装成功")
        except subprocess.CalledProcessError as e:
            print(u"✗ pyttsx3安装失败: {}".format(str(e)))
        except OSError as e:
            print(u"✗ pyttsx3安装失败 - Python路径错误: {}".format(str(e)))
        
        print(u"依赖安装完成，重新检查可用引擎...")
        return self.check_tts_availability()
    
    def _get_python_executable(self):
        """获取Python可执行文件路径"""
        import sys
        return sys.executable
