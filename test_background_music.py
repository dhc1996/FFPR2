# -*- coding: utf-8 -*-
"""
背景音乐功能测试脚本
"""

import os
import sys
from background_music import BackgroundMusicProcessor
from config import Config

def test_background_music():
    """测试背景音乐功能"""
    print(u"=" * 60)
    print(u"        背景音乐功能测试")
    print(u"=" * 60)
    
    # 创建处理器
    config = Config()
    processor = BackgroundMusicProcessor(config)
    
    # 测试视频路径（需要用户提供）
    test_video = raw_input(u"请输入测试视频路径: ").strip().strip('"').decode('utf-8')
    if not os.path.exists(test_video):
        print(u"视频文件不存在")
        return
    
    # 测试音乐路径（需要用户提供）
    test_music = raw_input(u"请输入测试音乐路径: ").strip().strip('"').decode('utf-8')
    if not os.path.exists(test_music):
        print(u"音乐文件不存在")
        return
    
    # 输出路径
    output_dir = "test_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_path = os.path.join(output_dir, "test_with_music.mp4")
    
    print(u"\n测试配置:")
    print(u"视频: {}".format(os.path.basename(test_video)))
    print(u"音乐: {}".format(os.path.basename(test_music)))
    print(u"输出: {}".format(output_path))
    
    # 测试文件验证
    print(u"\n1. 测试文件验证...")
    is_valid, result = processor.validate_files(test_video, test_music)
    if not is_valid:
        print(u"文件验证失败: {}".format(result))
        return
    
    video_info = result['video']
    audio_info = result['audio']
    
    print(u"✓ 文件验证成功")
    print(u"  视频: {:.1f}秒, {}x{}, {}".format(
        video_info['duration'], video_info['width'], video_info['height'],
        u"有音频" if video_info['has_audio'] else u"无音频"
    ))
    print(u"  音乐: {:.1f}秒, {}Hz, {}声道".format(
        audio_info['duration'], audio_info['sample_rate'], audio_info['channels']
    ))
    
    # 测试背景音乐添加
    print(u"\n2. 测试背景音乐添加...")
    options = {
        'music_volume': 0.4,        # 背景音乐音量40%
        'original_volume': 0.6,     # 原始音频音量60%
        'loop_music': True,         # 循环播放
        'fade_in': 3.0,            # 3秒淡入
        'fade_out': 3.0,           # 3秒淡出
        'start_time': 0.0          # 从开始播放
    }
    
    success, result = processor.add_background_music(
        test_video, test_music, output_path, **options
    )
    
    if success:
        print(u"\n✓ 背景音乐添加成功！")
        print(u"输出文件: {}".format(result))
        
        # 检查输出文件
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / (1024 * 1024.0)
            print(u"文件大小: {:.1f}MB".format(file_size))
            
            # 验证输出文件信息
            print(u"\n3. 验证输出文件...")
            output_info = processor.get_video_info(output_path)
            if output_info:
                print(u"✓ 输出文件验证成功")
                print(u"  时长: {:.1f}秒".format(output_info['duration']))
                print(u"  分辨率: {}x{}".format(output_info['width'], output_info['height']))
                print(u"  帧率: {:.1f}fps".format(output_info['fps']))
                print(u"  音频: {}".format(u"是" if output_info['has_audio'] else u"否"))
            else:
                print(u"✗ 输出文件验证失败")
        else:
            print(u"✗ 输出文件不存在")
    else:
        print(u"\n✗ 背景音乐添加失败")
        print(u"错误: {}".format(result))

def main():
    """主函数"""
    try:
        test_background_music()
    except KeyboardInterrupt:
        print(u"\n\n测试被用户中断")
    except Exception as e:
        print(u"\n测试过程中发生错误: {}".format(str(e)))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
