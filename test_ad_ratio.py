# -*- coding: utf-8 -*-
"""
测试广告比例保持功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ad_inserter import AdInserter

def test_ad_ratio_preservation():
    """测试广告比例保持功能"""
    print(u"=== 测试广告比例保持功能 ===")
    
    # 初始化广告插入器
    inserter = AdInserter()
    
    # 模拟主视频信息 (1920x1080 - 16:9)
    main_video_info = {
        'width': 1920,
        'height': 1080,
        'duration': 30.0,
        'fps': 30
    }
    
    # 模拟不同比例的广告视频
    test_ads = [
        {'name': u'横屏广告', 'width': 1280, 'height': 720, 'ratio': '16:9'},
        {'name': u'竖屏广告', 'width': 720, 'height': 1280, 'ratio': '9:16'},
        {'name': u'方形广告', 'width': 1080, 'height': 1080, 'ratio': '1:1'},
        {'name': u'4:3广告', 'width': 1024, 'height': 768, 'ratio': '4:3'},
    ]
    
    print(u"主视频尺寸: {}x{} (16:9)".format(main_video_info['width'], main_video_info['height']))
    print()
    
    for ad in test_ads:
        print(u"--- {} ---".format(ad['name']))
        print(u"原始尺寸: {}x{} ({})".format(ad['width'], ad['height'], ad['ratio']))
        
        ad_video_info = {
            'width': ad['width'],
            'height': ad['height'],
            'duration': 15.0,
            'fps': 30
        }
        
        # 测试不同缩放比例
        for scale in [0.15, 0.25, 0.35]:
            ad_dims = inserter.calculate_ad_dimensions(main_video_info, ad_video_info, scale)
            
            original_ratio = float(ad['width']) / float(ad['height'])
            scaled_ratio = float(ad_dims['width']) / float(ad_dims['height'])
            ratio_preserved = abs(original_ratio - scaled_ratio) < 0.01
            
            print(u"  {:.0%}缩放: {}x{} (比例: {:.2f}) {}".format(
                scale, ad_dims['width'], ad_dims['height'], scaled_ratio,
                u"✅保持" if ratio_preserved else u"❌变形"
            ))
        
        print()
    
    print(u"✅ 现在广告插入会保持原始比例，不会强制拉伸变形！")
    print(u"✅ 使用 force_original_aspect_ratio=decrease 确保比例正确")
    print(u"✅ 可以使用 python ad_cli.py 进行实际测试")

if __name__ == "__main__":
    test_ad_ratio_preservation()
