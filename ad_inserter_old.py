# -*- coding: utf-8 -*-
"""
广告插入模块
在视频指定位置和时间插入小比例广告视频
"""

import os
import subprocess
import json
from config import Config

class AdInserter(object):
    """广告插入器"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.ffmpeg_path = self.config.get('ffmpeg', 'path')
        self.log_level = self.config.get('ffmpeg', 'log_level')
    
    def validate_ad_video(self, ad_path):
        """验证广告视频文件"""
        if not os.path.exists(ad_path):
            return False, u"广告文件不存在"
        
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', ad_path
            ]
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            data = json.loads(result)
            
            # 检查是否有视频流
            has_video = False
            for stream in data.get('streams', []):
                if stream['codec_type'] == 'video':
                    has_video = True
                    break
            
            if not has_video:
                return False, u"广告文件不包含视频流"
            
            duration = float(data.get('format', {}).get('duration', 0))
            if duration <= 0:
                return False, u"无法获取广告视频时长"
            
            return True, duration
            
        except Exception as e:
            return False, u"广告文件格式错误: {}".format(str(e))
    
    def get_video_info(self, video_path):
        """获取视频信息"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            data = json.loads(result)
            
            video_stream = None
            for stream in data.get('streams', []):
                if stream['codec_type'] == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                return None
            
            info = {
                'duration': float(data.get('format', {}).get('duration', 0)),
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'fps': 30  # 默认帧率
            }
            
            # 计算帧率
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
            print(u"获取视频信息失败: {}".format(str(e)))
            return None
    
    def _check_audio_stream(self, video_path):
        """检查视频文件是否有音频流"""
        try:
            probe_cmd = [
                'ffprobe', '-v', 'quiet', '-select_streams', 'a', 
                '-show_entries', 'stream=index', '-of', 'csv=p=0', 
                video_path
            ]
            result = subprocess.check_output(probe_cmd, stderr=subprocess.STDOUT)
            return len(result.strip()) > 0
        except:
            return False
    
    def _build_audio_filter(self, main_has_audio, ad_has_audio, start_time, duration, total_duration):
        """构建音频滤镜 - 智能音频切换"""
        if not main_has_audio and not ad_has_audio:
            # 都没有音频
            return None
        
        if not main_has_audio and ad_has_audio:
            # 只有广告有音频 - 在广告时间段播放广告音频
            return (
                "[1:a]atrim=0:{},"
                "asetpts=PTS-STARTPTS+{}/TB,"
                "apad=pad_dur={}[audio_out]"
            ).format(duration, start_time, total_duration)
        
        if main_has_audio and not ad_has_audio:
            # 只有主视频有音频 - 直接使用主视频音频
            return "[0:a]acopy[audio_out]"
        
        # 都有音频 - 智能切换
        end_time = start_time + duration
        
        if start_time > 0:
            # 有前置主视频音频段
            if end_time < total_duration:
                # 前置 + 广告 + 后置
                return (
                    "[0:a]atrim=0:{}[main_pre];"
                    "[1:a]atrim=0:{},"
                    "asetpts=PTS-STARTPTS[ad_audio];"
                    "[0:a]atrim={}:{},"
                    "asetpts=PTS-STARTPTS[main_post];"
                    "[main_pre][ad_audio][main_post]concat=n=3:v=0:a=1[audio_out]"
                ).format(start_time, duration, end_time, total_duration)
            else:
                # 前置 + 广告（到结尾）
                return (
                    "[0:a]atrim=0:{}[main_pre];"
                    "[1:a]atrim=0:{},"
                    "asetpts=PTS-STARTPTS[ad_audio];"
                    "[main_pre][ad_audio]concat=n=2:v=0:a=1[audio_out]"
                ).format(start_time, duration)
        else:
            # 从开头就是广告
            if end_time < total_duration:
                # 广告 + 后置
                return (
                    "[1:a]atrim=0:{}[ad_audio];"
                    "[0:a]atrim={}:{},"
                    "asetpts=PTS-STARTPTS[main_post];"
                    "[ad_audio][main_post]concat=n=2:v=0:a=1[audio_out]"
                ).format(duration, end_time, total_duration)
            else:
                # 全程广告音频
                return (
                    "[1:a]atrim=0:{},"
                    "apad=pad_dur={}[audio_out]"
                ).format(duration, total_duration)
            
        except Exception as e:
            print(u"获取视频信息失败: {}".format(str(e)))
            return None
    
    def calculate_ad_dimensions(self, main_video_info, ad_scale=0.25):
        """计算广告视频的尺寸和位置"""
        main_width = main_video_info['width']
        main_height = main_video_info['height']
        
        # 广告尺寸（按比例缩放）
        ad_width = int(main_width * ad_scale)
        ad_height = int(main_height * ad_scale)
        
        # 广告位置（右上角，留出边距）
        margin = 20
        ad_x = main_width - ad_width - margin
        ad_y = margin
        
        return {
            'width': ad_width,
            'height': ad_height,
            'x': ad_x,
            'y': ad_y
        }
    
    def insert_ad_overlay(self, main_video_path, ad_video_path, output_path, 
                         start_time, duration, position='top-right', scale=0.25):
        """
        在主视频上叠加广告视频
        
        参数:
        - main_video_path: 主视频路径
        - ad_video_path: 广告视频路径
        - output_path: 输出视频路径
        - start_time: 广告开始时间（秒）
        - duration: 广告显示时长（秒）
        - position: 广告位置 ('top-right', 'top-left', 'bottom-right', 'bottom-left')
        - scale: 广告缩放比例（0.1-0.5）
        """
        
        print(u"开始插入广告...")
        print(u"主视频: {}".format(os.path.basename(main_video_path)))
        print(u"广告视频: {}".format(os.path.basename(ad_video_path)))
        print(u"开始时间: {:.1f}秒".format(start_time))
        print(u"显示时长: {:.1f}秒".format(duration))
        print(u"显示位置: {}".format(position))
        print(u"缩放比例: {:.1%}".format(scale))
        
        # 获取主视频信息
        main_info = self.get_video_info(main_video_path)
        if not main_info:
            return False, u"无法获取主视频信息"
        
        # 验证广告视频
        is_valid, ad_duration = self.validate_ad_video(ad_video_path)
        if not is_valid:
            return False, ad_duration
        
        # 检查时间参数
        if start_time < 0:
            return False, u"开始时间不能为负数"
        
        if start_time >= main_info['duration']:
            return False, u"开始时间超出主视频长度"
        
        if start_time + duration > main_info['duration']:
            print(u"警告：广告结束时间超出主视频长度，将自动调整")
            duration = main_info['duration'] - start_time
        
        # 计算广告位置和尺寸
        ad_dims = self.calculate_ad_dimensions(main_info, scale)
        
        # 根据位置参数调整坐标
        if position == 'top-left':
            ad_dims['x'] = 20
            ad_dims['y'] = 20
        elif position == 'bottom-right':
            ad_dims['x'] = main_info['width'] - ad_dims['width'] - 20
            ad_dims['y'] = main_info['height'] - ad_dims['height'] - 20
        elif position == 'bottom-left':
            ad_dims['x'] = 20
            ad_dims['y'] = main_info['height'] - ad_dims['height'] - 20
        # top-right 已经是默认位置
        
        print(u"广告尺寸: {}x{} 位置: ({}, {})".format(
            ad_dims['width'], ad_dims['height'], ad_dims['x'], ad_dims['y']
        ))
        
        # 构建FFmpeg命令 - 保持原视频时长，智能音频切换
        cmd = [self.ffmpeg_path, '-y']
        
        # 输入文件
        cmd.extend(['-i', main_video_path])  # 主视频
        cmd.extend(['-i', ad_video_path])    # 广告视频
        
        # 检查音频流情况
        main_has_audio = self._check_audio_stream(main_video_path)
        ad_has_audio = self._check_audio_stream(ad_video_path)
        
        print(u"音频流检测: 主视频={}, 广告={}".format(
            u"有音频" if main_has_audio else u"无音频",
            u"有音频" if ad_has_audio else u"无音频"
        ))
        
        # 构建视频滤镜 - 限制到主视频时长
        video_filter = (
            "[1:v]scale={}:{}"
            ",setpts=PTS-STARTPTS+{}/TB[ad_scaled];"
            "[0:v][ad_scaled]overlay={}:{}:"
            "enable='between(t,{},{})'"
            ":shortest=1[video_out]"
        ).format(
            ad_dims['width'], ad_dims['height'],  # 缩放尺寸
            start_time,                           # 广告开始时间偏移
            ad_dims['x'], ad_dims['y'],          # 叠加位置
            start_time, start_time + duration    # 显示时间范围
        )
        
        # 构建音频滤镜 - 智能音频切换
        audio_filter = self._build_audio_filter(
            main_has_audio, ad_has_audio, start_time, duration, main_info['duration']
        )
        
        # 组合完整滤镜
        if audio_filter:
            filter_complex = video_filter + ";" + audio_filter
        else:
            filter_complex = video_filter
        
        cmd.extend(['-filter_complex', filter_complex])
        cmd.extend(['-map', '[video_out]'])
        
        if audio_filter:
            cmd.extend(['-map', '[audio_out]'])
            cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
        
        # 强制输出时长等于主视频时长
        cmd.extend(['-t', str(main_info['duration'])])
        
        # 输出参数
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            output_path
        ])
        
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
                print(u"广告插入成功！")
                return True, output_path
            else:
                print(u"FFmpeg执行失败:")
                print(u"错误信息: {}".format(stderr))
                return False, stderr
                
        except Exception as e:
            error_msg = u"执行FFmpeg时发生异常: {}".format(str(e))
            print(error_msg)
            return False, error_msg
    
    def insert_multiple_ads(self, main_video_path, ad_configs, output_path):
        """
        插入多个广告
        
        参数:
        - main_video_path: 主视频路径
        - ad_configs: 广告配置列表 [{'path': '路径', 'start': 开始时间, 'duration': 时长, 'position': 位置, 'scale': 缩放}]
        - output_path: 输出路径
        """
        if not ad_configs:
            return False, u"没有广告配置"
        
        print(u"准备插入 {} 个广告".format(len(ad_configs)))
        
        # 验证所有广告配置
        for i, config in enumerate(ad_configs):
            if not os.path.exists(config['path']):
                return False, u"广告 {} 文件不存在: {}".format(i+1, config['path'])
            
            is_valid, info = self.validate_ad_video(config['path'])
            if not is_valid:
                return False, u"广告 {} 无效: {}".format(i+1, info)
        
        # 获取主视频信息
        main_info = self.get_video_info(main_video_path)
        if not main_info:
            return False, u"无法获取主视频信息"
        
        # 构建复杂的FFmpeg命令
        cmd = [self.ffmpeg_path, '-y']
        
        # 添加主视频输入
        cmd.extend(['-i', main_video_path])
        
        # 添加所有广告视频输入
        for config in ad_configs:
            cmd.extend(['-i', config['path']])
        
        # 构建复杂滤镜
        filter_parts = []
        overlay_inputs = ['[0:v]']
        
        for i, config in enumerate(ad_configs):
            ad_index = i + 1  # 输入索引（0是主视频）
            
            # 计算广告尺寸和位置
            scale = config.get('scale', 0.25)
            position = config.get('position', 'top-right')
            start_time = config.get('start', 0)
            duration = config.get('duration', 5)
            
            ad_dims = self.calculate_ad_dimensions(main_info, scale)
            
            # 调整位置
            if position == 'top-left':
                ad_dims['x'] = 20
                ad_dims['y'] = 20
            elif position == 'bottom-right':
                ad_dims['x'] = main_info['width'] - ad_dims['width'] - 20
                ad_dims['y'] = main_info['height'] - ad_dims['height'] - 20
            elif position == 'bottom-left':
                ad_dims['x'] = 20
                ad_dims['y'] = main_info['height'] - ad_dims['height'] - 20
            
            # 缩放广告
            scale_filter = "[{}:v]scale={}:{}[ad{}_scaled]".format(
                ad_index, ad_dims['width'], ad_dims['height'], i
            )
            filter_parts.append(scale_filter)
            
            # 设置时间
            time_filter = "[ad{}_scaled]setpts=PTS-STARTPTS+{}/TB[ad{}_timed]".format(
                i, start_time, i
            )
            filter_parts.append(time_filter)
            
            # 叠加
            overlay_input = overlay_inputs[-1]
            overlay_filter = "{}[ad{}_timed]overlay={}:{}:enable='between(t,{},{})'[overlay{}]".format(
                overlay_input, i, ad_dims['x'], ad_dims['y'], 
                start_time, start_time + duration, i
            )
            filter_parts.append(overlay_filter)
            overlay_inputs.append("[overlay{}]".format(i))
        
        filter_complex = ";".join(filter_parts)
        
        cmd.extend(['-filter_complex', filter_complex])
        cmd.extend(['-map', overlay_inputs[-1]])  # 最终输出
        
        # 检查主视频是否有音频流
        has_audio = False
        try:
            # 使用 ffprobe 检查音频流
            probe_cmd = [
                'ffprobe', '-v', 'quiet', '-select_streams', 'a', 
                '-show_entries', 'stream=index', '-of', 'csv=p=0', 
                main_video_path
            ]
            result = subprocess.check_output(probe_cmd, stderr=subprocess.STDOUT)
            has_audio = len(result.strip()) > 0
        except:
            has_audio = False
        
        if has_audio:
            cmd.extend(['-map', '0:a'])  # 保持原音频
            cmd.extend(['-c:a', 'copy'])  # 复制音频流
        else:
            # 如果主视频没有音频，尝试从第一个广告视频复制音频
            for i, config in enumerate(ad_configs):
                try:
                    probe_cmd = [
                        'ffprobe', '-v', 'quiet', '-select_streams', 'a', 
                        '-show_entries', 'stream=index', '-of', 'csv=p=0', 
                        config['path']
                    ]
                    result = subprocess.check_output(probe_cmd, stderr=subprocess.STDOUT)
                    if len(result.strip()) > 0:
                        cmd.extend(['-map', '{}:a'.format(i+1)])  # 使用这个广告的音频
                        cmd.extend(['-c:a', 'aac'])  # 重新编码音频
                        break
                except:
                    continue
        
        # 输出参数
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            output_path
        ])
        
        print(u"执行复杂广告插入...")
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                print(u"多广告插入成功！")
                return True, output_path
            else:
                print(u"FFmpeg执行失败:")
                print(stderr)
                return False, stderr
                
        except Exception as e:
            error_msg = u"执行FFmpeg时发生异常: {}".format(str(e))
            print(error_msg)
            return False, error_msg
