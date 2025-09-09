# -*- coding: utf-8 -*-
"""
测试字幕生成速度修改效果
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from subtitle_generator import SubtitleGenerator

def test_normal_speed_subtitles():
    """测试正常语速字幕生成"""
    generator = SubtitleGenerator()
    
    # 测试文本
    test_texts = [
        u"这是一个短句。",
        u"这是一个稍微长一点的句子，包含更多的字符。",
        u"这是一个非常长的句子，包含了很多字符，用来测试字幕时间分配算法是否能够根据字符数合理地设置显示时间，而不是被视频长度限制。",
        u"短句，测试，效果。"
    ]
    
    print(u"=== 测试正常语速字幕生成 ===")
    
    for i, text in enumerate(test_texts):
        print(u"\n--- 测试文本 {} ---".format(i+1))
        print(u"原文: {}".format(text))
        print(u"字符数: {}".format(len(text)))
        
        # 使用智能分割生成字幕
        subtitles = generator._parse_text_content(text, split_mode='smart_split')
        
        print(u"生成字幕:")
        total_duration = 0
        for j, subtitle in enumerate(subtitles):
            duration = subtitle['end'] - subtitle['start']
            total_duration += duration
            print(u"  {}: {:.1f}s-{:.1f}s ({:.1f}s) '{}'".format(
                j+1, subtitle['start'], subtitle['end'], duration, subtitle['text']
            ))
        
        # 计算平均阅读速度
        avg_chars_per_second = len(text) / total_duration if total_duration > 0 else 0
        print(u"总时长: {:.1f}s, 平均阅读速度: {:.1f}字符/秒".format(
            total_duration, avg_chars_per_second
        ))

if __name__ == "__main__":
    test_normal_speed_subtitles()
