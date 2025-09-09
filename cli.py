# -*- coding: utf-8 -*-
"""
命令行界面模块
提供用户友好的交互界面
"""

import os
import sys
from config import Config, create_default_config
from video_processor import VideoProcessor
from ffmpeg_renderer import FFmpegRenderer
from background_music import BackgroundMusicProcessor
from utils import generate_timestamped_filename

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

def safe_input(prompt):
    """安全的输入函数，处理Python 2.7的编码问题"""
    try:
        # 先安全地显示提示
        if hasattr(prompt, 'encode'):
            display_prompt = prompt.encode('gbk', 'replace')
        else:
            display_prompt = str(prompt).encode('gbk', 'replace')
        
        # 使用raw_input获取输入
        user_input = raw_input(display_prompt)
        
        # 尝试解码用户输入
        try:
            return user_input.decode('gbk')
        except:
            try:
                return user_input.decode('utf-8')
            except:
                return user_input
    except KeyboardInterrupt:
        raise
    except:
        return ""

class CLI(object):
    """命令行界面类"""
    
    def __init__(self):
        self.config = Config()
        self.processor = VideoProcessor(self.config)
        self.renderer = FFmpegRenderer(self.config)
        self.music_processor = BackgroundMusicProcessor(self.config)
    
    def print_banner(self):
        """打印程序横幅"""
        print(u"=" * 60)
        print(u"      自动化视频剪辑工具 (Python 2.7.18 + FFmpeg)")
        print(u"=" * 60)
        print(u"功能特性:")
        print(u"  - 自动扫描或手动指定视频文件")
        print(u"  - 智能混剪为指定时长")
        print(u"  - 自动去除原声音频")
        print(u"  - 支持多种混剪策略")
        print(u"  - 可自定义输出参数")
        print(u"  - 视频广告插入功能")
        print(u"  - 视频字幕添加功能")
        print(u"  - 背景音乐添加功能")
        print(u"=" * 60)
        print(u"当前画质设置:")
        print(u"  - 分辨率: {}x{}".format(
            self.config.get('video', 'default_output_width'),
            self.config.get('video', 'default_output_height')
        ))
        print(u"  - 帧率: {}fps".format(self.config.get('video', 'default_fps')))
        print(u"  - 视频质量: CRF {} (高质量)".format(self.config.get('video', 'default_crf')))
        print(u"  - 编码预设: {} (高质量)".format(self.config.get('video', 'default_preset')))
        print(u"  - 输出目录: {}".format(self.config.get('video', 'default_output_dir')))
        print(u"=" * 60)
        print()
    
    def check_requirements(self):
        """检查系统要求"""
        print(u"检查系统要求...")
        
        # 检查FFmpeg
        if not self.processor.check_ffmpeg():
            print(u"错误：未找到FFmpeg，请确保已安装并添加到PATH环境变量")
            print(u"下载地址：https://ffmpeg.org/download.html")
            return False
        
        print(u"[√] FFmpeg 可用")
        return True
    
    def get_input_path(self):
        """获取输入路径"""
        print(u"请选择输入方式:")
        print(u"1. 扫描文件夹（包含子文件夹）")
        print(u"2. 扫描文件夹（仅当前文件夹）")
        print(u"3. 指定单个视频文件")
        
        while True:
            try:
                choice = int(safe_input(u"请选择 (1-3): ").strip())
                if choice in [1, 2, 3]:
                    break
                print(u"请输入有效选择")
            except ValueError:
                print(u"请输入数字")
            except KeyboardInterrupt:
                raise
            except:
                print(u"输入出错，请重新输入")
        
        while True:
            if choice == 3:
                path = safe_input(u"请输入视频文件路径: ").strip().strip('"')
            else:
                path = safe_input(u"请输入文件夹路径: ").strip().strip('"')
            
            if path and os.path.exists(path):
                break
            print(u"路径不存在，请重新输入")
        
        recursive = (choice == 1)
        return path, recursive
    
    def scan_and_validate_videos(self, path, recursive=True):
        """扫描并验证视频文件"""
        print(u"\n正在扫描视频文件...")
        
        if os.path.isfile(path):
            # 单个文件
            video_files, invalid_files = self.processor.scan_videos(path, recursive=False)
        else:
            # 文件夹
            video_files, invalid_files = self.processor.scan_videos(path, recursive)
        
        print(u"\n扫描结果:")
        print(u"有效视频文件: {} 个".format(len(video_files)))
        if invalid_files:
            print(u"无效文件: {} 个".format(len(invalid_files)))
            if len(invalid_files) <= 5:
                for invalid_path, reason in invalid_files:
                    print(u"  - {}: {}".format(os.path.basename(invalid_path), reason))
            else:
                print(u"  显示前5个:")
                for invalid_path, reason in invalid_files[:5]:
                    print(u"  - {}: {}".format(os.path.basename(invalid_path), reason))
                print(u"  ... 还有 {} 个".format(len(invalid_files) - 5))
        
        if not video_files:
            print(u"错误：未找到可用的视频文件")
            return None
        
        # 显示找到的视频文件
        print(u"\n找到的视频文件:")
        for i, video_path in enumerate(video_files[:10], 1):
            info = self.processor.get_video_info(video_path)
            if info:
                print(u"{}. {} ({:.1f}秒, {}x{})".format(
                    i, os.path.basename(video_path), 
                    info['duration'], info['width'], info['height']
                ))
            else:
                print(u"{}. {}".format(i, os.path.basename(video_path)))
        
        if len(video_files) > 10:
            print(u"  ... 还有 {} 个文件".format(len(video_files) - 10))
        
        return video_files
    
    def get_target_duration(self):
        """获取目标时长"""
        while True:
            try:
                duration_input = safe_input(u"\n请输入目标视频时长（秒）: ").strip()
                target_duration = float(duration_input)
                if target_duration > 0:
                    return target_duration
                print(u"请输入大于0的数值")
            except ValueError:
                print(u"请输入有效的数值")
    
    def get_mixing_strategy(self):
        """获取混剪策略"""
        print(u"\n请选择混剪策略:")
        print(u"1. 随机混剪 (推荐) - 随机选择片段和时间点")
        print(u"2. 顺序混剪 - 按顺序从每个视频中提取片段")
        print(u"3. 平衡混剪 - 尽量让每个视频贡献相同时长")
        
        strategies = {1: 'random', 2: 'sequential', 3: 'balanced'}
        
        while True:
            try:
                choice = int(safe_input(u"请选择 (1-3，默认1): ").strip() or "1")
                if choice in strategies:
                    return strategies[choice]
                print(u"请输入有效选择")
            except ValueError:
                print(u"请输入数字")
    
    def get_output_settings(self, input_path=None):
        """获取输出设置"""
        print(u"\n输出设置:")
        
        # 生成默认文件名（使用文件夹名和时间戳）
        default_filename = generate_timestamped_filename(input_path, "mixed", "")
        default_name = os.path.splitext(default_filename)[0]  # 去掉.mp4扩展名
        
        # 输出文件名
        while True:
            output_name = safe_input(u"输出文件名（不含扩展名，默认：{}）: ".format(default_name)).strip()
            if not output_name:
                output_name = default_name
            
            # 检查文件名是否合法
            invalid_chars = '<>:"/\\|?*'
            if any(char in output_name for char in invalid_chars):
                print(u"文件名包含非法字符，请重新输入")
                continue
            break
        
        # 输出目录
        default_output_dir = self.config.get('video', 'default_output_dir') or 'output'
        output_dir = safe_input(u"输出目录（默认：{}）: ".format(default_output_dir)).strip().strip('"')
        if not output_dir:
            output_dir = default_output_dir
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                print(u"创建输出目录: {}".format(output_dir))
            except Exception as e:
                print(u"创建输出目录失败: {}".format(str(e)))
                output_dir = '.'
        
        output_path = os.path.join(output_dir, output_name + ".mp4")
        
        # 自定义输出参数
        use_custom = safe_input(u"是否自定义输出参数？(Y/n): ").strip().lower()
        
        settings = {
            'width': self.config.get('video', 'default_output_width'),
            'height': self.config.get('video', 'default_output_height'),
            'fps': self.config.get('video', 'default_fps'),
            'crf': self.config.get('video', 'default_crf'),
            'preset': self.config.get('video', 'default_preset')
        }
        
        if use_custom in ['', 'y', 'yes']:
            try:
                width = safe_input(u"输出宽度（默认{}）: ".format(settings['width'])).strip()
                if width:
                    settings['width'] = int(width)
                
                height = safe_input(u"输出高度（默认{}）: ".format(settings['height'])).strip()
                if height:
                    settings['height'] = int(height)
                
                fps = safe_input(u"输出帧率（默认{}）: ".format(settings['fps'])).strip()
                if fps:
                    settings['fps'] = int(fps)
                
                crf = safe_input(u"视频质量CRF（默认{}，越小质量越好）: ".format(settings['crf'])).strip()
                if crf:
                    settings['crf'] = int(crf)
                
                print(u"编码预设选项：ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow")
                preset = safe_input(u"编码预设（默认{}）: ".format(settings['preset'])).strip()
                if preset:
                    settings['preset'] = preset
                
            except ValueError:
                print(u"输入参数有误，使用默认设置")
        
        # 字幕设置
        print(u"\n字幕设置:")
        add_subtitle = safe_input(u"是否添加字幕？(Y/n): ").strip().lower()
        settings['add_subtitle'] = (add_subtitle in ['', 'y', 'yes'])
        
        if settings['add_subtitle']:
            # 获取字幕源
            print(u"字幕来源:")
            print(u"1. 文案文档 (.txt, .md)")
            print(u"2. 现有字幕文件 (.srt)")
            
            while True:
                subtitle_choice = safe_input(u"请选择字幕来源 (1-2): ").strip()
                if subtitle_choice in ['1', '2']:
                    break
                print(u"请输入有效选择 (1-2)")
            
            if subtitle_choice == '1':
                subtitle_source = safe_input(u"请输入文案文档路径: ").strip().strip('"')
            else:
                subtitle_source = safe_input(u"请输入SRT字幕文件路径: ").strip().strip('"')
            
            if subtitle_source and os.path.exists(subtitle_source):
                settings['subtitle_source'] = subtitle_source
                
                # 如果是文案文档，选择分割模式
                if subtitle_choice == '1':
                    print(u"\n字幕分割模式:")
                    print(u"1. 按行分割 (每行一个字幕)")
                    print(u"2. 按时间分割 (每2秒一个字幕)")
                    print(u"3. 按秒分割 (自然语言智能分割，每秒一个字幕)")
                    
                    split_choice = safe_input(u"请选择分割模式 (1-3，默认1): ").strip()
                    if split_choice == '2':
                        settings['split_mode'] = 'time'
                    elif split_choice == '3':
                        settings['split_mode'] = 'seconds'
                    else:
                        settings['split_mode'] = 'line'
                else:
                    settings['split_mode'] = 'line'
                
                # 字幕样式
                print(u"\n字幕样式:")
                print(u"1. 默认 (24号字体)")
                print(u"2. 大字体 (32号字体)")
                print(u"3. 小字体 (18号字体)")
                
                style_choice = safe_input(u"请选择字幕样式 (1-3，默认1): ").strip()
                if style_choice == '2':
                    settings['subtitle_style'] = 'large'
                elif style_choice == '3':
                    settings['subtitle_style'] = 'small'
                else:
                    settings['subtitle_style'] = 'default'
                
                # 字幕开始时间
                print(u"\n字幕时间设置:")
                start_time_input = safe_input(u"字幕开始时间（秒，默认0）: ").strip()
                if start_time_input:
                    try:
                        start_time = float(start_time_input)
                        if start_time >= 0:
                            settings['start_time'] = start_time
                        else:
                            print(u"开始时间不能为负数，使用默认值0")
                            settings['start_time'] = 0.0
                    except ValueError:
                        print(u"无效的时间格式，使用默认值0")
                        settings['start_time'] = 0.0
                else:
                    settings['start_time'] = 0.0
            else:
                print(u"字幕文件不存在，跳过字幕添加")
                settings['add_subtitle'] = False
        
        return output_path, settings
    
    def show_processing_plan(self, segments, target_duration, output_settings):
        """显示处理计划"""
        print(u"\n" + u"=" * 50)
        print(u"处理计划")
        print(u"=" * 50)
        
        print(u"目标时长: {:.2f}秒".format(target_duration))
        print(u"片段数量: {}".format(len(segments)))
        print(u"输出分辨率: {}x{}".format(output_settings['width'], output_settings['height']))
        print(u"输出帧率: {}fps".format(output_settings['fps']))
        print(u"视频质量: CRF {}".format(output_settings['crf']))
        print(u"编码预设: {}".format(output_settings['preset']))
        
        print(u"\n片段详情:")
        total_duration = 0
        for i, segment in enumerate(segments[:10], 1):  # 只显示前10个
            filename = os.path.basename(segment['video_path'])
            print(u"  {}. {} ({:.1f}s-{:.1f}s, 时长{:.2f}s)".format(
                i, filename, 
                segment['start_time'], 
                segment['start_time'] + segment['duration'],
                segment['duration']
            ))
            total_duration += segment['duration']
        
        if len(segments) > 10:
            for segment in segments[10:]:
                total_duration += segment['duration']
            print(u"  ... 还有 {} 个片段".format(len(segments) - 10))
        
        print(u"\n实际总时长: {:.2f}秒".format(total_duration))
        
        # 确认继续
        confirm = safe_input(u"\n确认开始处理？(Y/n): ").strip().lower()
        return confirm != 'n'
    
    def process_video(self, segments, output_path, output_settings, first_video_info=None):
        """处理视频，支持保持第一个视频的原始比例"""
        print(u"\n开始处理视频...")
        
        # 先渲染基础视频（无字幕）
        temp_output = None
        if output_settings.get('add_subtitle', False):
            # 如果需要添加字幕，先生成临时视频
            base_name = os.path.splitext(output_path)[0]
            temp_output = base_name + "_temp.mp4"
            
            success, result = self.renderer.render_video(
                segments, temp_output, first_video_info, **{k: v for k, v in output_settings.items() 
                                        if k not in ['add_subtitle', 'subtitle_source', 'subtitle_style', 'split_mode', 'start_time']}
            )
        else:
            success, result = self.renderer.render_video(
                segments, output_path, first_video_info, **output_settings
            )
        
        if not success:
            print(u"\n处理失败:")
            print(result)
            
            # 尝试备用方法
            use_backup = safe_input(u"\n是否尝试备用渲染方法？(Y/n): ").strip().lower()
            if use_backup not in ['n', 'no']:
                print(u"尝试备用渲染方法...")
                success, result = self.renderer.render_with_concat(
                    segments, temp_output if temp_output else output_path, first_video_info, **output_settings
                )
                
                if not success:
                    print(u"备用方法也失败了: {}".format(result))
                    return False
            else:
                return False
        
        # 如果需要添加字幕
        if output_settings.get('add_subtitle', False) and success:
            print(u"\n添加字幕...")
            try:
                from subtitle_inserter import SubtitleInserter
                inserter = SubtitleInserter()
                
                final_output = inserter.insert_subtitles_to_video(
                    video_path=temp_output,
                    subtitle_source=output_settings['subtitle_source'],
                    output_path=output_path,
                    style=output_settings.get('subtitle_style', 'default'),
                    auto_fit=True,
                    split_mode=output_settings.get('split_mode', 'line'),
                    start_time=output_settings.get('start_time', 0.0)
                )
                
                # 清理临时文件
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                
                success = os.path.exists(final_output)
                
            except Exception as e:
                print(u"添加字幕失败: {}".format(str(e)))
                # 如果字幕添加失败，至少保留基础视频
                if temp_output and os.path.exists(temp_output):
                    import shutil
                    shutil.move(temp_output, output_path)
                    print(u"保存了无字幕版本")
                    success = True
        
        if success:
            print(u"\n" + u"=" * 50)
            print(u"处理完成！")
            print(u"=" * 50)
            print(u"输出文件: {}".format(output_path))
            
            # 获取输出文件信息
            output_info = self.renderer.get_output_info(output_path)
            if output_info:
                file_size_mb = output_info['size'] / (1024 * 1024)
                print(u"文件大小: {:.2f} MB".format(file_size_mb))
                print(u"实际时长: {:.2f}秒".format(output_info['duration']))
                print(u"分辨率: {}x{}".format(output_info['width'], output_info['height']))
                print(u"帧率: {:.2f}fps".format(output_info['fps']))
            
            subtitle_note = u"（已添加字幕）" if output_settings.get('add_subtitle', False) else u"（已去除音频，方便后续添加自定义音频和字幕）"
            print(u"\n注意：输出视频{}".format(subtitle_note))
            return True
        else:
            return False
    
    def run(self):
        """运行主程序"""
        self.print_banner()
        
        # 检查系统要求
        if not self.check_requirements():
            return
        
        while True:
            print(u"请选择操作:")
            print(u"1. 自动扫描视频文件并混剪")
            print(u"2. 手动指定视频文件并混剪")
            print(u"3. 视频广告插入")
            print(u"4. 视频字幕添加")
            print(u"5. 视频音频/字幕提取")
            print(u"6. 背景音乐添加")
            print(u"7. 退出程序")
            print()
            
            try:
                choice = safe_input(u"请输入选择 (1-7): ").strip()
                
                if choice == '1':
                    self.auto_scan_mode()
                elif choice == '2':
                    self.manual_mode()
                elif choice == '3':
                    self.ad_insert_mode()
                elif choice == '4':
                    self.subtitle_mode()
                elif choice == '5':
                    self.extract_mode()
                elif choice == '6':
                    self.background_music_mode()
                elif choice == '7':
                    print(u"谢谢使用，再见！")
                    break
                else:
                    print(u"无效选择，请重新输入")
                    continue
                    
                # 询问是否继续
                if choice in ['1', '2', '3', '4', '5', '6']:
                    continue_choice = safe_input(u"\n是否继续使用？(Y/n): ").strip().lower()
                    if continue_choice == 'n':
                        print(u"谢谢使用，再见！")
                        break
                        
            except KeyboardInterrupt:
                print(u"\n\n用户中断操作")
                break
            except Exception as e:
                print(u"\n程序执行出错: {}".format(str(e)))
                import traceback
                traceback.print_exc()
                continue
    
    def auto_scan_mode(self):
        """自动扫描模式"""
        try:
            # 获取输入路径
            input_path, recursive = self.get_input_path()
            
            # 扫描视频文件
            video_files = self.scan_and_validate_videos(input_path, recursive)
            if not video_files:
                return
            
            # 获取目标时长
            target_duration = self.get_target_duration()
            
            # 获取混剪策略
            strategy = self.get_mixing_strategy()
            
            # 创建处理计划
            print(u"\n创建处理计划...")
            segments = self.processor.create_segments_plan(video_files, target_duration, strategy)
            if not segments:
                print(u"无法创建有效的处理计划")
                return
            
            # 获取输出设置
            output_path, output_settings = self.get_output_settings(input_path)
            
            # 显示处理计划并确认
            if not self.show_processing_plan(segments, target_duration, output_settings):
                print(u"操作已取消")
                return
            
            # 获取第一个视频的信息（作为输出格式参考）
            first_video_info = None
            if video_files:
                first_video_info = self.processor.get_video_info(video_files[0])
                if first_video_info:
                    print(u"将按第一个视频的分辨率输出: {}x{} @{}fps".format(
                        first_video_info['width'], first_video_info['height'], 
                        int(first_video_info['fps'])
                    ))
            
            # 处理视频
            success = self.process_video(segments, output_path, output_settings, first_video_info)
            
            if success:
                print(u"\n视频混剪完成！")
            else:
                print(u"\n视频混剪失败！")
                
        except Exception as e:
            print(u"\n自动扫描模式执行出错: {}".format(str(e)))
    
    def manual_mode(self):
        """手动指定模式"""
        print(u"\n手动指定模式（功能待实现）")
        print(u"请使用自动扫描模式")
    
    def ad_insert_mode(self):
        """广告插入模式"""
        try:
            import ad_cli
            ad_cli_instance = ad_cli.AdInserterCLI()
            ad_cli_instance.run()
        except ImportError:
            print(u"\n广告插入模块未找到，请确保 ad_cli.py 文件存在")
        except Exception as e:
            print(u"\n广告插入执行出错: {}".format(str(e)))
            import traceback
            traceback.print_exc()
    
    def subtitle_mode(self):
        """字幕添加模式"""
        try:
            import subtitle_cli
            # 直接调用字幕CLI的主函数
            subtitle_cli.main()
        except ImportError:
            print(u"\n字幕添加模块未找到，请确保 subtitle_cli.py 文件存在")
        except Exception as e:
            print(u"\n字幕添加执行出错: {}".format(str(e)))
            import traceback
            traceback.print_exc()
    
    def extract_mode(self):
        """音频/字幕提取模式"""
        try:
            import extractor_cli
            extractor_instance = extractor_cli.ExtractorCLI()
            extractor_instance.run()
        except ImportError:
            print(u"\n提取功能模块未找到，请确保 extractor_cli.py 文件存在")
        except Exception as e:
            print(u"\n提取功能执行出错: {}".format(str(e)))
            import traceback
            traceback.print_exc()
    
    def background_music_mode(self):
        """背景音乐添加模式"""
        safe_print(u"\n" + u"=" * 50)
        safe_print(u"        背景音乐添加功能")
        safe_print(u"=" * 50)
        safe_print(u"功能说明:")
        safe_print(u"  - 为视频添加背景音乐")
        safe_print(u"  - 支持音量调节和音频混合")
        safe_print(u"  - 支持音乐循环播放")
        safe_print(u"  - 支持淡入淡出效果")
        safe_print(u"=" * 50)
        
        try:
            # 获取视频文件
            while True:
                video_path = safe_input(u"\n请输入视频文件路径: ").strip().strip('"')
                if not video_path:
                    safe_print(u"路径不能为空")
                    continue
                if not os.path.exists(video_path):
                    safe_print(u"视频文件不存在，请重新输入")
                    continue
                if not video_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')):
                    safe_print(u"不支持的视频格式，请选择mp4/avi/mov/mkv/wmv/flv格式")
                    continue
                break
            
            # 获取音乐文件
            while True:
                music_path = safe_input(u"请输入音乐文件路径: ").strip().strip('"')
                if not music_path:
                    safe_print(u"路径不能为空")
                    continue
                if not os.path.exists(music_path):
                    safe_print(u"音乐文件不存在，请重新输入")
                    continue
                if not music_path.lower().endswith(('.mp3', '.wav', '.aac', '.m4a', '.ogg', '.flac')):
                    safe_print(u"不支持的音频格式，请选择mp3/wav/aac/m4a/ogg/flac格式")
                    continue
                break
            
            # 显示文件信息
            safe_print(u"\n正在分析文件...")
            is_valid, result = self.music_processor.validate_files(video_path, music_path)
            if not is_valid:
                safe_print(u"文件验证失败: {}".format(result))
                return
            
            video_info = result['video']
            audio_info = result['audio']
            
            safe_print(u"\n文件信息:")
            safe_print(u"视频: {} ({:.1f}秒, {}x{}, {})".format(
                os.path.basename(video_path), video_info['duration'],
                video_info['width'], video_info['height'],
                u"有音频" if video_info['has_audio'] else u"无音频"
            ))
            safe_print(u"音乐: {} ({:.1f}秒, {}Hz, {}声道)".format(
                os.path.basename(music_path), audio_info['duration'],
                audio_info['sample_rate'], audio_info['channels']
            ))
            
            # 获取配置选项
            safe_print(u"\n配置选项:")
            
            # 背景音乐音量
            while True:
                try:
                    volume_input = safe_input(u"背景音乐音量 (0.0-1.0，默认0.3): ").strip()
                    if not volume_input:
                        music_volume = 0.3
                        break
                    music_volume = float(volume_input)
                    if 0.0 <= music_volume <= 1.0:
                        break
                    print(u"音量必须在0.0-1.0之间")
                except ValueError:
                    print(u"请输入有效的数值")
            
            # 原始音频音量（如果有原始音频）
            if video_info['has_audio']:
                while True:
                    try:
                        volume_input = safe_input(u"原始音频音量 (0.0-1.0，默认0.7): ").strip()
                        if not volume_input:
                            original_volume = 0.7
                            break
                        original_volume = float(volume_input)
                        if 0.0 <= original_volume <= 1.0:
                            break
                        print(u"音量必须在0.0-1.0之间")
                    except ValueError:
                        print(u"请输入有效的数值")
            else:
                original_volume = 0.0
                print(u"视频无原始音频，将只使用背景音乐")
            
            # 是否循环音乐
            loop_choice = safe_input(u"是否循环播放音乐？(Y/n): ").strip().lower()
            loop_music = loop_choice in ['', 'y', 'yes']
            
            # 淡入淡出设置
            while True:
                try:
                    fade_input = safe_input(u"淡入时间（秒，默认2.0）: ").strip()
                    if not fade_input:
                        fade_in = 2.0
                        break
                    fade_in = float(fade_input)
                    if fade_in >= 0:
                        break
                    print(u"淡入时间必须大于等于0")
                except ValueError:
                    print(u"请输入有效的数值")
            
            while True:
                try:
                    fade_input = safe_input(u"淡出时间（秒，默认2.0）: ").strip()
                    if not fade_input:
                        fade_out = 2.0
                        break
                    fade_out = float(fade_input)
                    if fade_out >= 0:
                        break
                    print(u"淡出时间必须大于等于0")
                except ValueError:
                    print(u"请输入有效的数值")
            
            # 音乐开始时间
            while True:
                try:
                    start_input = safe_input(u"音乐开始时间（秒，默认0.0）: ").strip()
                    if not start_input:
                        start_time = 0.0
                        break
                    start_time = float(start_input)
                    if start_time >= 0:
                        break
                    print(u"开始时间必须大于等于0")
                except ValueError:
                    print(u"请输入有效的数值")
            
            # 输出设置
            print(u"\n输出设置:")
            default_name = os.path.splitext(os.path.basename(video_path))[0] + "_with_music"
            output_name = safe_input(u"输出文件名（不含扩展名，默认：{}）: ".format(default_name)).strip()
            if not output_name:
                output_name = default_name
            
            # 输出目录
            default_output_dir = self.config.get('video', 'default_output_dir') or 'output'
            output_dir = safe_input(u"输出目录（默认：{}）: ".format(default_output_dir)).strip().strip('"')
            if not output_dir:
                output_dir = default_output_dir
            
            # 确保输出目录存在
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                    print(u"创建输出目录: {}".format(output_dir))
                except Exception as e:
                    print(u"创建输出目录失败: {}".format(str(e)))
                    output_dir = '.'
            
            output_path = os.path.join(output_dir, output_name + ".mp4")
            
            # 检查输出文件是否已存在
            if os.path.exists(output_path):
                overwrite = safe_input(u"输出文件已存在，是否覆盖？(y/N): ").strip().lower()
                if overwrite not in ['y', 'yes']:
                    print(u"操作已取消")
                    return
            
            # 执行背景音乐添加
            print(u"\n开始处理...")
            options = {
                'music_volume': music_volume,
                'original_volume': original_volume,
                'loop_music': loop_music,
                'fade_in': fade_in,
                'fade_out': fade_out,
                'start_time': start_time
            }
            
            success, result = self.music_processor.add_background_music(
                video_path, music_path, output_path, **options
            )
            
            if success:
                print(u"\n" + u"=" * 50)
                print(u"背景音乐添加成功！")
                print(u"输出文件: {}".format(result))
                print(u"=" * 50)
            else:
                print(u"\n背景音乐添加失败: {}".format(result))
        
        except KeyboardInterrupt:
            print(u"\n用户中断操作")
        except Exception as e:
            print(u"\n背景音乐添加执行出错: {}".format(str(e)))
            import traceback
            traceback.print_exc()


def main():
    """主入口函数"""
    # 确保配置文件存在
    if not os.path.exists('config.json'):
        print(u"创建默认配置文件...")
        create_default_config()
    
    # 运行CLI
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()
