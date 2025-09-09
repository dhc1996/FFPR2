#!/bin/bash

# 自动化视频剪辑工具启动脚本 (Linux/macOS)

echo "自动化视频剪辑工具启动脚本"
echo "============================="
echo

# 检查Python是否安装
if ! command -v python2.7 &> /dev/null && ! command -v python &> /dev/null; then
    echo "错误：未找到Python，请确保Python 2.7.18已安装"
    exit 1
fi

# 检查FFmpeg是否安装
if ! command -v ffmpeg &> /dev/null; then
    echo "错误：未找到FFmpeg，请确保FFmpeg已安装"
    echo "安装方法："
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  CentOS/RHEL: sudo yum install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    exit 1
fi

echo "Python和FFmpeg检查通过"
echo

# 询问运行模式
echo "请选择运行模式："
echo "1. 简单模式 (video_editor.py)"
echo "2. 完整模式 (cli.py) - 推荐"
echo
read -p "请输入选择 (1 或 2, 默认2): " mode

# 确定Python命令
if command -v python2.7 &> /dev/null; then
    PYTHON_CMD="python2.7"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "错误：找不到合适的Python命令"
    exit 1
fi

if [ "$mode" == "1" ]; then
    echo "启动简单模式..."
    $PYTHON_CMD video_editor.py
else
    echo "启动完整模式..."
    $PYTHON_CMD cli.py
fi

echo
echo "程序结束"
read -p "按回车键退出..."
