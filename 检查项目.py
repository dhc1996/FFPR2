# -*- coding: utf-8 -*-
"""
FFPR项目简单验证脚本
"""
import os

def main():
    print("FFPR项目功能验证")
    print("=" * 30)
    
    # 检查核心文件
    core_files = [
        'subtitle_cli.py',
        'subtitle_generator.py', 
        'subtitle_inserter.py',
        'cli.py',
        'utils.py'
    ]
    
    print("检查核心文件:")
    missing = 0
    for f in core_files:
        if os.path.exists(f):
            print("✓ " + f)
        else:
            print("✗ " + f + " (缺失)")
            missing += 1
    
    # 检查文档
    print("\n检查文档:")
    docs = ['字幕功能使用说明.md', '项目说明.md']
    for d in docs:
        if os.path.exists(d):
            print("✓ " + d)
        else:
            print("✗ " + d + " (缺失)")
            missing += 1
    
    # 检查目录
    print("\n检查目录:")
    dirs = ['srt', 'temp']
    for dir_name in dirs:
        if os.path.exists(dir_name):
            count = len(os.listdir(dir_name))
            print("✓ {}/ (包含{}个文件)".format(dir_name, count))
        else:
            print("⚠ {}/ (将在使用时创建)".format(dir_name))
    
    # 检查启动脚本
    print("\n检查启动脚本:")
    scripts = ['启动字幕工具.bat', '启动主程序.bat']
    for s in scripts:
        if os.path.exists(s):
            print("✓ " + s)
        else:
            print("✗ " + s)
    
    print("\n" + "=" * 50)
    if missing == 0:
        print("🎉 验证通过！所有核心文件完整。")
        print("\n使用方法:")
        print("1. 双击: 启动字幕工具.bat")
        print("2. 命令行: python subtitle_cli.py")
        print("3. 详细说明: 字幕功能使用说明.md")
    else:
        print("⚠️  发现{}个缺失文件，请检查。".format(missing))

if __name__ == '__main__':
    main()
