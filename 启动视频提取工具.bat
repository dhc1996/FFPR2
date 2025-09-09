@echo off
chcp 65001 >nul
title 视频提取工具 - 音频提取

echo.
echo ========================================
echo    视频提取工具 - 音频提取
echo ========================================
echo.
echo 功能包括:
echo - 提取视频中的音频文件
echo - 支持MP3格式输出
echo - 自动创建输出目录
echo - 显示处理结果和文件大小
echo.
echo 正在启动视频提取工具...
echo.

"D:\Software\Python27\python.exe" simple_extract.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 程序运行出错，错误代码: %ERRORLEVEL%
    echo 请检查Python环境和依赖包安装
)

echo.
echo 程序已退出，按任意键关闭窗口...
pause >nul
