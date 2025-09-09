# -*- coding: utf-8 -*-
"""
自动化脚本示例
演示如何以编程方式使用视频剪辑工具
"""

import os
import sys
from config import Config
from video_processor import VideoProcessor
from ffmpeg_renderer import FFmpegRenderer

def auto_process_example():
    """自动化处理示例"""
    
    # 配置参数
    input_folder = r"D:\Videos\Input"  # 替换为你的视频文件夹路径
    output_file = r"D:\Videos\Output\auto_mixed.mp4"  # 输出文件路径
    target_duration = 120  # 目标时长（秒）
    
    # 输出设置
    output_settings = {
        'width': 1920,
        'height': 1080,
        'fps': 30,
        'crf': 23,
        'preset': 'medium'
    }
    
    print(u"自动化视频处理示例")
    print(u"==================")
    print(u"输入文件夹: {}".format(input_folder))
    print(u"输出文件: {}".format(output_file))
    print(u"目标时长: {}秒".format(target_duration))
    print()
    
    # 初始化组件
    config = Config()
    processor = VideoProcessor(config)
    renderer = FFmpegRenderer(config)
    
    # 检查FFmpeg
    if not processor.check_ffmpeg():
        print(u"错误：FFmpeg不可用")
        return False
    
    # 扫描视频文件
    print(u"扫描视频文件...")
    video_files, invalid_files = processor.scan_videos(input_folder, recursive=True)
    
    if not video_files:
        print(u"错误：未找到有效的视频文件")
        return False
    
    print(u"找到 {} 个有效视频文件".format(len(video_files)))
    if invalid_files:
        print(u"跳过 {} 个无效文件".format(len(invalid_files)))
    
    # 创建处理计划
    print(u"创建处理计划...")
    segments = processor.create_segments_plan(video_files, target_duration, 'random')
    
    if not segments:
        print(u"错误：无法创建处理计划")
        return False
    
    print(u"创建了 {} 个视频片段".format(len(segments)))
    
    # 显示计划摘要
    total_duration = sum(seg['duration'] for seg in segments)
    print(u"计划总时长: {:.2f}秒".format(total_duration))
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 开始渲染
    print(u"开始渲染...")
    success, result = renderer.render_video(segments, output_file, **output_settings)
    
    if success:
        print(u"渲染成功！")
        print(u"输出文件: {}".format(output_file))
        
        # 显示输出信息
        output_info = renderer.get_output_info(output_file)
        if output_info:
            file_size = os.path.getsize(output_file) / (1024 * 1024)
            print(u"文件大小: {:.2f} MB".format(file_size))
            print(u"实际时长: {:.2f}秒".format(output_info['duration']))
        
        return True
    else:
        print(u"渲染失败: {}".format(result))
        return False

def batch_process_example():
    """批量处理示例"""
    
    # 定义多个任务
    tasks = [
        {
            'input_folder': r"D:\Videos\Project1",
            'output_file': r"D:\Videos\Output\project1_mixed.mp4",
            'duration': 60,
            'strategy': 'random'
        },
        {
            'input_folder': r"D:\Videos\Project2", 
            'output_file': r"D:\Videos\Output\project2_mixed.mp4",
            'duration': 90,
            'strategy': 'balanced'
        }
    ]
    
    print(u"批量处理示例")
    print(u"============")
    print(u"计划处理 {} 个任务".format(len(tasks)))
    print()
    
    # 初始化组件
    config = Config()
    processor = VideoProcessor(config)
    renderer = FFmpegRenderer(config)
    
    successful_tasks = 0
    
    for i, task in enumerate(tasks, 1):
        print(u"处理任务 {}/{}...".format(i, len(tasks)))
        print(u"输入: {}".format(task['input_folder']))
        print(u"输出: {}".format(task['output_file']))
        
        # 扫描视频
        video_files, _ = processor.scan_videos(task['input_folder'], recursive=True)
        if not video_files:
            print(u"跳过：未找到视频文件")
            continue
        
        # 创建计划
        segments = processor.create_segments_plan(
            video_files, task['duration'], task['strategy']
        )
        if not segments:
            print(u"跳过：无法创建处理计划")
            continue
        
        # 确保输出目录存在
        output_dir = os.path.dirname(task['output_file'])
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 渲染
        success, result = renderer.render_video(segments, task['output_file'])
        
        if success:
            print(u"✓ 任务完成")
            successful_tasks += 1
        else:
            print(u"✗ 任务失败: {}".format(result))
        print()
    
    print(u"批量处理完成")
    print(u"成功: {}/{} 个任务".format(successful_tasks, len(tasks)))

def custom_settings_example():
    """自定义设置示例"""
    
    print(u"自定义设置示例")
    print(u"==============")
    
    # 创建自定义配置
    config = Config()
    
    # 修改一些设置
    config.set(5.0, 'processing', 'min_segment_duration')  # 最小片段5秒
    config.set('fast', 'video', 'default_preset')  # 使用快速预设
    config.set(25, 'video', 'default_fps')  # 25fps
    
    # 保存配置
    config.save_config()
    
    print(u"自定义配置已保存")
    print(u"最小片段时长: {}秒".format(config.get('processing', 'min_segment_duration')))
    print(u"默认预设: {}".format(config.get('video', 'default_preset')))
    print(u"默认帧率: {}fps".format(config.get('video', 'default_fps')))

def main():
    """主函数"""
    print(u"视频剪辑工具 - 自动化脚本示例")
    print(u"=============================")
    print()
    print(u"请选择示例:")
    print(u"1. 自动化处理示例")
    print(u"2. 批量处理示例")
    print(u"3. 自定义设置示例")
    print()
    
    try:
        choice = int(raw_input(u"请选择 (1-3): ").strip())
        
        if choice == 1:
            print()
            print(u"注意：请先修改脚本中的路径设置")
            confirm = raw_input(u"继续执行？(Y/n): ").strip().lower()
            if confirm not in ['n', 'no']:
                auto_process_example()
        elif choice == 2:
            print()
            print(u"注意：请先修改脚本中的任务设置")
            confirm = raw_input(u"继续执行？(Y/n): ").strip().lower()
            if confirm not in ['n', 'no']:
                batch_process_example()
        elif choice == 3:
            custom_settings_example()
        else:
            print(u"无效选择")
    
    except ValueError:
        print(u"请输入有效的数字")
    except KeyboardInterrupt:
        print(u"\n用户中断")

if __name__ == "__main__":
    main()
