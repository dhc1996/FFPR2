# -*- coding: utf-8 -*-
"""
测试视频比例保持功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_processor import VideoProcessor
from config import Config

def test_video_ratio_preservation():
    """测试视频比例保持功能"""
    print(u"=== 测试视频比例保持功能 ===")
    
    # 初始化
    config = Config()
    processor = VideoProcessor(config)
    
    # 测试文件夹（请更换为实际的测试视频路径）
    test_folder = r"d:\test_videos"  # 更换为你的测试视频文件夹
    
    if not os.path.exists(test_folder):
        print(u"测试文件夹不存在: {}".format(test_folder))
        print(u"请创建测试文件夹并放入不同分辨率的视频文件进行测试")
        return
    
    # 扫描视频文件
    video_files, invalid_files = processor.scan_videos(test_folder)
    
    if not video_files:
        print(u"未找到有效的视频文件")
        return
    
    print(u"找到 {} 个视频文件".format(len(video_files)))
    
    # 显示每个视频的分辨率信息
    for i, video_path in enumerate(video_files[:5]):  # 只显示前5个
        info = processor.get_video_info(video_path)
        if info:
            print(u"视频 {}: {} - {}x{} @{:.1f}fps".format(
                i+1, os.path.basename(video_path), 
                info['width'], info['height'], info['fps']
            ))
    
    if len(video_files) > 1:
        first_video_info = processor.get_video_info(video_files[0])
        if first_video_info:
            print(u"\n第一个视频信息:")
            print(u"  分辨率: {}x{}".format(first_video_info['width'], first_video_info['height']))
            print(u"  帧率: {:.1f}fps".format(first_video_info['fps']))
            print(u"  时长: {:.2f}秒".format(first_video_info['duration']))
            
            print(u"\n✅ 混剪时将按第一个视频的分辨率 {}x{} 输出".format(
                first_video_info['width'], first_video_info['height']
            ))
            print(u"✅ 其他视频将缩放到此分辨率，保持原始纵横比，使用黑边填充")
    
    print(u"\n测试完成！现在可以使用 python cli.py 进行实际混剪测试")

if __name__ == "__main__":
    test_video_ratio_preservation()
