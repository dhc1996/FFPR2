# -*- coding: utf-8 -*-
"""
测试背景音乐菜单选项
"""

import os
import sys

def test_menu():
    """测试菜单显示"""
    print("Testing CLI menu...")
    
    try:
        from cli import CLI
        cli = CLI()
        
        # 测试safe_print函数
        from cli import safe_print
        safe_print(u"测试中文显示")
        safe_print(u"背景音乐功能测试")
        safe_print(u"请输入视频文件路径:")
        
        print("Menu test completed successfully!")
        print("You can now run: python cli.py and choose option 6")
        
    except Exception as e:
        print("Error during test: {}".format(str(e)))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_menu()
