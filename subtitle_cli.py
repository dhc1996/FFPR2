# -*- coding: utf-8 -*-
"""
字幕功能命令行界面
支持为视频添加字幕
"""

import os
import sys
import time
from subtitle_inserter import SubtitleInserter
from subtitle_generator import SubtitleGenerator
from utils import format_duration, format_file_size

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

def print_header():
    """打印程序头部信息"""
    print(u"=" * 60)
    print(u"      视频字幕添加工具 (Python 2.7.18 + FFmpeg)")
    print(u"=" * 60)
    print(u"功能特性:")
    print(u"  - 支持多种文案文档格式 (.txt, .md, .srt)")
    print(u"  - 自动时间分配和字幕分割")
    print(u"  - 多种字幕样式选择")
    print(u"  - 智能字幕时间调整")
    print(u"  - 带时间戳的输出文件命名")
    print(u"=" * 60)
    print()

def get_video_path():
    """获取视频文件路径"""
    while True:
        video_path = safe_input(u"请输入视频文件路径: ").strip().strip('"')
        
        if not video_path:
            print(u"请输入有效的视频文件路径")
            continue
        
        if not os.path.exists(video_path):
            print(u"视频文件不存在，请检查路径")
            continue
        
        # 检查是否为视频文件
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
        if not any(video_path.lower().endswith(ext) for ext in video_extensions):
            print(u"不支持的视频格式，支持的格式: {}".format(', '.join(video_extensions)))
            continue
        
        return video_path

def get_subtitle_source():
    """获取字幕源"""
    print(u"\n视频字幕工具 - 字幕添加功能:")
    print(u"1. 文案文档 (.txt, .md)")
    print(u"2. 现有字幕文件 (.srt)")
    print(u"3. 手动输入文本")
    
    while True:
        choice = safe_input(u"请选择字幕来源 (1-3): ").strip()
        
        if choice == '1':
            return get_document_path()
        elif choice == '2':
            return get_srt_path()
        elif choice == '3':
            return get_manual_text()
        else:
            print(u"请输入有效选择 (1-3)")

def get_document_path():
    """获取文案文档路径"""
    while True:
        doc_path = safe_input(u"请输入文案文档路径: ").strip().strip('"')
        
        if not doc_path:
            print(u"请输入有效的文档路径")
            continue
        
        if not os.path.exists(doc_path):
            print(u"文档文件不存在，请检查路径")
            continue
        
        # 检查文件格式
        supported_formats = ['.txt', '.md', '.docx']
        if not any(doc_path.lower().endswith(ext) for ext in supported_formats):
            print(u"不支持的文档格式，支持的格式: {}".format(', '.join(supported_formats)))
            continue
        
        return doc_path

def get_srt_path():
    """获取SRT字幕文件路径"""
    while True:
        srt_path = safe_input(u"请输入SRT字幕文件路径: ").strip().strip('"')
        
        if not srt_path:
            print(u"请输入有效的SRT文件路径")
            continue
        
        if not os.path.exists(srt_path):
            print(u"SRT文件不存在，请检查路径")
            continue
        
        if not srt_path.lower().endswith('.srt'):
            print(u"请选择SRT格式的字幕文件")
            continue
        
        return srt_path

def get_manual_text():
    """获取手动输入的文本"""
    print(u"\n手动输入字幕文本:")
    print(u"格式说明:")
    print(u"  - 每行一条字幕")
    print(u"  - 可使用时间戳格式: [1:30] 文本内容")
    print(u"  - 输入空行结束输入")
    print()
    
    lines = []
    while True:
        line = safe_input(u"字幕内容: ").strip()
        if not line:
            break
        lines.append(line)
    
    if not lines:
        print(u"没有输入任何内容")
        return get_subtitle_source()
    
    # 创建临时文本文件
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    temp_file = os.path.join(temp_dir, "manual_subtitle_{}.txt".format(int(time.time())))
    
    with open(temp_file, 'w') as f:
        for line in lines:
            f.write(line.encode('utf-8') + '\n')
    
    return temp_file

def get_split_mode():
    """获取字幕分割模式"""
    print(u"\n字幕分割模式:")
    print(u"1. 智能分割 - 按句子和语义分割，每条1秒（推荐）")
    print(u"2. 按秒分割 - 简单按每秒分割文本")
    print(u"3. 自动模式 - 根据文本长度智能分配时间")
    
    while True:
        choice = safe_input(u"请选择分割模式 (1-3，默认1): ").strip()
        
        if choice == '' or choice == '1':
            return 'smart_split'
        elif choice == '2':
            return 'one_second'
        elif choice == '3':
            return 'auto'
        else:
            print(u"请输入有效选择 (1-3)")

def get_start_time():
    """获取字幕开始时间"""
    print(u"\n字幕时间设置:")
    print(u"请输入字幕开始时间（秒），例如：")
    print(u"  0    - 从视频开始（默认）")
    print(u"  10   - 从第10秒开始")
    print(u"  30.5 - 从第30.5秒开始")
    
    while True:
        time_input = safe_input(u"开始时间（秒，默认0）: ").strip()
        
        if not time_input:
            return 0.0
        
        try:
            start_time = float(time_input)
            if start_time < 0:
                print(u"开始时间不能为负数，请重新输入")
                continue
            return start_time
        except ValueError:
            print(u"请输入有效的数字，如：0、10、30.5")
            continue

def get_subtitle_style():
    """获取字幕样式"""
    print(u"\n字幕样式选择:")
    print(u"1. 默认 (24号字体)")
    print(u"2. 大字体 (32号字体)")
    print(u"3. 小字体 (18号字体)")
    
    while True:
        choice = safe_input(u"请选择字幕样式 (1-3，默认1): ").strip()
        
        if choice == '' or choice == '1':
            return 'default'
        elif choice == '2':
            return 'large'
        elif choice == '3':
            return 'small'
        else:
            print(u"请输入有效选择 (1-3)")

def get_speech_settings():
    """获取语音合成设置"""
    print(u"\n语音合成设置:")
    print(u"是否启用语音合成功能？")
    print(u"  - 启用后将根据字幕文本生成语音，与原视频音频混合")
    print(u"  - 自动清理临时音频片段，只保留最终合成文件")
    print(u"  - 需要安装额外的语音合成依赖包")
    
    while True:
        enable = safe_input(u"启用语音合成？(Y/n，默认Y): ").strip().lower()
        if enable in ['', 'y', 'yes']:
            break
        elif enable in ['n', 'no']:
            return False, None
        else:
            print(u"请输入 Y 或 N")
    
    # 选择语音类型
    print(u"\n语音类型选择:")
    print(u"1. 晓晓 - 温柔女声（推荐）")
    print(u"2. 云希 - 活泼男声")
    print(u"3. 小艺 - 知性女声")  
    print(u"4. 云健 - 稳重男声")
    
    voice_map = {
        '1': 'zh-CN-XiaoxiaoNeural',
        '2': 'zh-CN-YunxiNeural', 
        '3': 'zh-CN-XiaoyiNeural',
        '4': 'zh-CN-YunjianNeural'
    }
    
    while True:
        choice = safe_input(u"请选择语音类型 (1-4，默认1): ").strip()
        if choice == '' or choice == '1':
            return True, voice_map['1']
        elif choice in voice_map:
            return True, voice_map[choice]
        else:
            print(u"请输入有效选择 (1-4)")

def get_voice_name(voice_id):
    """根据语音ID获取友好的显示名称"""
    voice_names = {
        'zh-CN-XiaoxiaoNeural': u'晓晓-温柔女声',
        'zh-CN-YunxiNeural': u'云希-活泼男声',
        'zh-CN-XiaoyiNeural': u'小艺-知性女声',
        'zh-CN-YunjianNeural': u'云健-稳重男声'
    }
    # Python 2.7兼容处理
    result = voice_names.get(voice_id, voice_id)
    if sys.version_info[0] == 2 and not isinstance(result, unicode):
        try:
            result = unicode(result, 'utf-8')
        except:
            result = unicode(result)
    return result

def check_tts_dependencies():
    """检查TTS依赖"""
    try:
        print(u"正在检查和安装TTS依赖...")
        from text_to_speech import TextToSpeechGenerator
        tts = TextToSpeechGenerator()
        available_engines = tts.check_tts_availability()
        
        if available_engines and len([e for e in available_engines if e != 'system']) > 0:
            print(u"✓ TTS引擎可用: {}".format(', '.join(available_engines)))
            return True
        else:
            print(u"⚠ 建议安装TTS引擎以获得更好的语音效果")
            print(u"  可用引擎: {}".format(', '.join(available_engines)))
            
            install = safe_input(u"是否安装推荐的TTS依赖？(Y/n): ").strip().lower()
            if install in ['', 'y', 'yes']:
                print(u"正在安装依赖...")
                try:
                    tts.install_dependencies()
                    return True
                except Exception as install_error:
                    print(u"依赖安装失败: {}".format(str(install_error)))
                    return False
            return True
    except ImportError as e:
        print(u"TTS模块导入失败: {}".format(str(e)))
        print(u"TTS依赖检查失败，将禁用语音合成")
        return False
    except Exception as e:
        print(u"TTS模块检查失败: {}".format(str(e)))
        print(u"TTS依赖检查失败，将禁用语音合成")
        return False

def get_output_path(video_path):
    """获取输出路径"""
    from utils import generate_timestamped_filename
    
    default_name = generate_timestamped_filename(video_path, "subtitle", "_with_subtitles")
    
    print(u"\n输出设置:")
    output_path = safe_input(u"输出文件名（默认：{}）: ".format(default_name)).strip().strip('"')
    
    if not output_path:
        # 使用默认文件名，放在项目的output目录
        project_dir = os.path.dirname(__file__)
        output_dir = os.path.join(project_dir, 'output')
        
        # 确保output目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        output_path = os.path.join(output_dir, default_name)
    else:
        # 如果用户只输入文件名，添加默认的项目output目录
        if not os.path.dirname(output_path):
            project_dir = os.path.dirname(__file__)
            output_dir = os.path.join(project_dir, 'output')
            
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            output_path = os.path.join(output_dir, output_path)
        
        # 确保有.mp4扩展名
        if not output_path.lower().endswith('.mp4'):
            output_path += '.mp4'
    
    return output_path

def preview_subtitles(subtitle_source, split_mode='smart_split', start_time=0.0):
    """预览字幕内容"""
    try:
        generator = SubtitleGenerator()
        
        # 检查是否为有效的文件路径
        if hasattr(subtitle_source, 'encode') and os.path.exists(subtitle_source):
            print(u"\n正在读取字幕文档...")
            subtitles = generator.read_text_document(subtitle_source, split_mode, start_time)
        else:
            print(u"无法预览字幕：文件不存在")
            print(u"尝试的路径: {}".format(subtitle_source))
            return False
        
        if not subtitles:
            print(u"没有可预览的字幕内容")
            return False
        
        print(u"\n字幕内容预览:")
        generator.preview_subtitles(subtitles, max_lines=5)
        
        while True:
            confirm = safe_input(u"字幕内容确认无误？(Y/n): ").strip().lower()
            if confirm in ['', 'y', 'yes']:
                return True
            elif confirm in ['n', 'no']:
                return False
            else:
                print(u"请输入 Y 或 N")
    
    except Exception as e:
        print(u"预览字幕时出错: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        # 出错时询问是否继续
        while True:
            continue_choice = safe_input(u"是否继续处理？(Y/n): ").strip().lower()
            if continue_choice in ['', 'y', 'yes']:
                return True
            elif continue_choice in ['n', 'no']:
                return False
            else:
                print(u"请输入 Y 或 N")

def main():
    """主函数"""
    print_header()
    
    # 选择功能模式
    print(u"功能模式选择:")
    print(u"1. 添加字幕到视频 (生成带字幕的视频文件)")
    print(u"2. 仅生成SRT文件 (只生成字幕文件，不处理视频)")
    
    while True:
        mode_choice = safe_input(u"请选择功能模式 (1-2，默认1): ").strip()
        if mode_choice == '' or mode_choice == '1':
            mode = 'video'
            break
        elif mode_choice == '2':
            mode = 'srt_only'
            break
        else:
            print(u"请输入有效选择 (1-2)")
    
    try:
        if mode == 'srt_only':
            generate_srt_only()
        else:
            add_subtitle_to_video()
            
    except KeyboardInterrupt:
        print(u"\n用户中止操作")
    except Exception as e:
        print(u"错误: {}".format(str(e)))
        
def generate_srt_only():
    """仅生成SRT文件模式"""
    print(u"\n=== 仅生成SRT文件模式 ===")
    
    while True:
        try:
            subtitle_source = get_subtitle_source()
            
            # 确定字幕来源显示名称
            try:
                if hasattr(subtitle_source, 'encode') and os.path.exists(subtitle_source):
                    source_display = os.path.basename(subtitle_source)
                else:
                    source_display = u"手动输入"
            except:
                source_display = u"未知来源"
            
            print(u"✓ 字幕来源: {}".format(source_display))
            
            # 获取分割模式
            split_mode = get_split_mode()
            print(u"✓ 分割模式: {}".format(split_mode))
            
            # 获取字幕开始时间
            start_time = get_start_time()
            print(u"✓ 开始时间: {:.1f}秒".format(start_time))
            
            # 预览字幕
            if not preview_subtitles(subtitle_source, split_mode, start_time):
                print(u"用户取消操作")
                continue
            
            # 生成SRT文件
            from subtitle_generator import SubtitleGenerator
            generator = SubtitleGenerator()
            
            # 读取字幕内容
            if hasattr(subtitle_source, 'encode') and os.path.exists(subtitle_source):
                subtitles = generator.read_text_document(subtitle_source, split_mode, start_time)
            else:
                print(u"无效的字幕源")
                continue
            
            # 生成SRT文件路径
            import time as time_module
            timestamp = int(time_module.time())
            srt_dir = os.path.join(os.path.dirname(__file__), 'srt')
            if not os.path.exists(srt_dir):
                os.makedirs(srt_dir)
            
            srt_filename = "subtitle_generated_{}.srt".format(timestamp)
            srt_path = os.path.join(srt_dir, srt_filename)
            
            # 生成SRT文件
            result_path = generator.generate_srt_file(subtitles, srt_path)
            
            print(u"\n" + u"=" * 50)
            print(u"SRT文件生成完成！")
            print(u"=" * 50)
            print(u"SRT文件: {}".format(result_path))
            if os.path.exists(result_path):
                file_size = os.path.getsize(result_path) / 1024.0
                print(u"文件大小: {:.1f} KB".format(file_size))
            print(u"字幕条数: {}".format(len(subtitles)))
            
            # 询问是否继续生成其他SRT文件
            print(u"\n" + u"=" * 30)
            print(u"生成完成")
            print(u"=" * 30)
            
            while True:
                continue_choice = safe_input(u"是否继续生成其他SRT文件？(Y/n): ").strip().lower()
                if continue_choice in ['', 'y', 'yes']:
                    print(u"\n继续生成下一个SRT文件...")
                    break
                elif continue_choice in ['n', 'no']:
                    print(u"感谢使用字幕工具！")
                    return
                else:
                    print(u"请输入 Y 或 N")
        
        except KeyboardInterrupt:
            print(u"\n用户中止操作")
            while True:
                exit_choice = safe_input(u"是否退出程序？(Y/n): ").strip().lower()
                if exit_choice in ['', 'y', 'yes']:
                    return
                elif exit_choice in ['n', 'no']:
                    print(u"继续...")
                    break
                else:
                    print(u"请输入 Y 或 N")
        
        except Exception as e:
            print(u"生成SRT文件失败: {}".format(str(e)))
            import traceback
            traceback.print_exc()
            
            while True:
                continue_choice = safe_input(u"是否继续生成其他SRT文件？(Y/n): ").strip().lower()
                if continue_choice in ['', 'y', 'yes']:
                    print(u"\n继续生成下一个SRT文件...")
                    break
                elif continue_choice in ['n', 'no']:
                    print(u"程序结束")
                    return
                else:
                    print(u"请输入 Y 或 N")

def add_subtitle_to_video():
    """添加字幕到视频模式"""
    print(u"\n=== 添加字幕到视频模式 ===")
    
    while True:
        try:
            # 获取输入参数
            video_path = get_video_path()
            print(u"✓ 选择视频: {}".format(os.path.basename(video_path)))
            
            subtitle_source = get_subtitle_source()
            
            # 确定字幕来源显示名称
            try:
                if hasattr(subtitle_source, 'encode') and os.path.exists(subtitle_source):
                    source_display = os.path.basename(subtitle_source)
                else:
                    source_display = u"手动输入"
            except:
                source_display = u"未知来源"
            
            print(u"✓ 字幕来源: {}".format(source_display))
            
            # 获取分割模式
            split_mode = get_split_mode()
            print(u"✓ 分割模式: {}".format(split_mode))
            
            # 获取字幕开始时间
            start_time = get_start_time()
            print(u"✓ 开始时间: {:.1f}秒".format(start_time))
            
            # 预览字幕
            if not preview_subtitles(subtitle_source, split_mode, start_time):
                print(u"用户取消操作")
                continue
            
            # 获取字幕样式
            style = get_subtitle_style()
            print(u"✓ 选择样式: {}".format(style))
            
            # 获取语音合成设置
            enable_speech, voice = get_speech_settings()
            if enable_speech:
                print(u"✓ 语音合成: 启用 ({})".format(voice))
                # 检查TTS依赖
                if not check_tts_dependencies():
                    print(u"TTS依赖检查失败，将禁用语音合成")
                    enable_speech = False
            else:
                print(u"✓ 语音合成: 禁用")
            
            output_path = get_output_path(video_path)
            
            # 显示配置摘要
            print(u"\n" + u"=" * 50)
            print(u"字幕添加配置")
            print(u"=" * 50)
            print(u"输入视频: {}".format(os.path.basename(video_path)))
            print(u"字幕来源: {}".format(
                os.path.basename(subtitle_source) if isinstance(subtitle_source, str) and os.path.exists(subtitle_source)
                else u"手动输入"
            ))
            print(u"字幕样式: {}".format(style))
            if enable_speech:
                voice_name = get_voice_name(voice)
                # 确保voice_name是unicode类型，避免编码错误
                if sys.version_info[0] == 2 and not isinstance(voice_name, unicode):
                    try:
                        voice_name = voice_name.decode('utf-8')
                    except:
                        voice_name = unicode(str(voice_name), 'utf-8', errors='ignore')
                print(u"语音合成: 启用 ({})".format(voice_name))
            else:
                print(u"语音合成: 禁用")
            print(u"输出文件: {}".format(output_path))
            print(u"=" * 50)
            
            # 确认开始处理
            while True:
                confirm = safe_input(u"确认开始处理？(Y/n): ").strip().lower()
                if confirm in ['', 'y', 'yes']:
                    break
                elif confirm in ['n', 'no']:
                    print(u"用户取消操作")
                    break
                else:
                    print(u"请输入 Y 或 N")
            
            if confirm in ['n', 'no']:
                continue
            
            # 开始处理
            if enable_speech:
                print(u"\n开始添加字幕和语音...")
            else:
                print(u"\n开始添加字幕...")
            
            inserter = SubtitleInserter()
            result_path = inserter.insert_subtitles_to_video(
                video_path=video_path,
                subtitle_source=subtitle_source,
                output_path=output_path,
                style=style,
                auto_fit=True,
                split_mode=split_mode,
                start_time=start_time,
                enable_speech=enable_speech,
                voice=voice if enable_speech else None
            )
            
            print(u"\n" + u"=" * 50)
            if enable_speech:
                print(u"字幕和语音添加完成！")
            else:
                print(u"字幕添加完成！")
            print(u"=" * 50)
            print(u"输出文件: {}".format(result_path))
            
            if os.path.exists(result_path):
                file_size = os.path.getsize(result_path)
                print(u"文件大小: {}".format(format_file_size(file_size)))
            
            # 询问是否继续处理其他视频
            print(u"\n" + u"=" * 30)
            print(u"处理完成")
            print(u"=" * 30)
            
            while True:
                continue_choice = safe_input(u"是否继续处理其他视频？(Y/n): ").strip().lower()
                if continue_choice in ['', 'y', 'yes']:
                    print(u"\n继续处理下一个视频...")
                    break
                elif continue_choice in ['n', 'no']:
                    print(u"感谢使用字幕工具！")
                    return
                else:
                    print(u"请输入 Y 或 N")
        
        except KeyboardInterrupt:
            print(u"\n用户中止操作")
            while True:
                exit_choice = safe_input(u"是否退出程序？(Y/n): ").strip().lower()
                if exit_choice in ['', 'y', 'yes']:
                    return
                elif exit_choice in ['n', 'no']:
                    print(u"继续...")
                    break
                else:
                    print(u"请输入 Y 或 N")
        
        except Exception as e:
            print(u"处理视频时出错: {}".format(str(e)))
            import traceback
            traceback.print_exc()
            
            while True:
                continue_choice = safe_input(u"是否继续处理其他视频？(Y/n): ").strip().lower()
                if continue_choice in ['', 'y', 'yes']:
                    print(u"\n继续处理下一个视频...")
                    break
                elif continue_choice in ['n', 'no']:
                    print(u"程序结束")
                    return
                else:
                    print(u"请输入 Y 或 N")

if __name__ == '__main__':
    main()
