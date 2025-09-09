# -*- coding: utf-8 -*-

import sys

def safe_print_test(text):
    """测试安全打印函数"""
    try:
        if hasattr(text, 'encode'):
            print(text.encode('gbk', 'replace'))
        else:
            print(str(text).encode('gbk', 'replace'))
    except:
        print("Error displaying text")

# 测试
safe_print_test(u"测试中文显示")
safe_print_test(u"请输入视频文件路径:")
safe_print_test(u"背景音乐添加功能")

print("Test completed")
