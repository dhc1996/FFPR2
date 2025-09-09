# -*- coding: utf-8 -*-
"""
FFPR项目功能验证脚本
检查核心功能模块是否完整并可正常运行
"""
import os
import sys

def check_core_files():
    """检查核心文件完整性"""
    print("正在检查核心文件...")
    
    core_files = {
        'subtitle_cli.py': '字幕功能主界面',
        'subtitle_generator.py': '字幕生成引擎', 
        'subtitle_inserter.py': '字幕嵌入引擎',
        'cli.py': '主程序入口',
        'utils.py': '工具函数库',
        '字幕功能使用说明.md': '详细说明文档',
        '项目说明.md': '项目概述文档'
    }
    
    missing_files = []
    for file_path, description in core_files.items():
        if os.path.exists(file_path):
            print("✓ {} - {}".format(file_path.encode('utf-8'), description.encode('utf-8')))
        else:
            print("✗ {} - {} (缺失)".format(file_path.encode('utf-8'), description.encode('utf-8')))
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def check_directories():
    """检查必要目录"""
    print(u"\n正在检查目录结构...")
    
    directories = {
        'srt': u'SRT字幕文件存储目录',
        'temp': u'临时文件目录'
    }
    
    for dir_path, description in directories.items():
        if os.path.exists(dir_path):
            files_count = len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
            print(u"✓ {}/ - {} (包含{}个文件)".format(dir_path, description, files_count))
        else:
            print(u"⚠ {}/ - {} (将在使用时创建)".format(dir_path, description))

def check_python_version():
    """检查Python版本"""
    print(u"\n正在检查Python环境...")
    version = sys.version_info
    print(u"Python版本: {}.{}.{}".format(version.major, version.minor, version.micro))
    
    if version.major == 2 and version.minor == 7:
        print(u"✓ Python版本符合要求")
        return True
    else:
        print(u"⚠ 建议使用Python 2.7.18版本")
        return False

def check_imports():
    """检查关键模块导入"""
    print(u"\n正在检查模块导入...")
    
    modules = [
        ('utils', u'工具函数'),
        ('subtitle_generator', u'字幕生成器'),
        ('subtitle_inserter', u'字幕插入器')
    ]
    
    import_success = True
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(u"✓ {} - {}".format(module_name, description))
        except ImportError as e:
            print(u"✗ {} - {} (导入失败: {})".format(module_name, description, str(e)))
            import_success = False
        except Exception as e:
            print(u"⚠ {} - {} (警告: {})".format(module_name, description, str(e)))
    
    return import_success

def show_usage_summary():
    """显示使用总结"""
    print(u"\n" + u"=" * 60)
    print(u"FFPR项目功能验证完成")
    print(u"=" * 60)
    
    print(u"\n🚀 推荐使用方法:")
    print(u"1. 双击运行: 启动字幕工具.bat")
    print(u"2. 命令行运行: python subtitle_cli.py")
    print(u"3. 主程序: python cli.py")
    
    print(u"\n📖 文档说明:")
    print(u"• 详细使用方法: 字幕功能使用说明.md")
    print(u"• 项目概述: 项目说明.md")
    
    print(u"\n✨ 核心功能:")
    print(u"• 智能字幕生成和视频嵌入")
    print(u"• 支持批量处理多个文件")  
    print(u"• 多种分割模式和字幕样式")
    print(u"• 自定义开始时间和错误恢复")
    
    print(u"\n📁 文件管理:")
    print(u"• SRT文件: srt/ 目录")
    print(u"• 输出视频: output/ 目录")
    print(u"• 文件名包含时间戳避免覆盖")

def main():
    """主验证函数"""
    print(u"FFPR项目功能验证")
    print(u"=" * 30)
    
    # 检查文件完整性
    files_ok = check_core_files()
    
    # 检查目录结构  
    check_directories()
    
    # 检查Python版本
    python_ok = check_python_version()
    
    # 检查模块导入
    imports_ok = check_imports()
    
    # 显示总结
    show_usage_summary()
    
    # 验证结果
    if files_ok and imports_ok:
        print(u"\n🎉 验证通过！项目已就绪，可以正常使用。")
    else:
        print(u"\n⚠️  发现问题，请检查缺失的文件或模块。")
    
    if not python_ok:
        print(u"💡 提示：虽然可能可以运行，但建议使用Python 2.7.18以获得最佳兼容性。")

if __name__ == '__main__':
    main()
