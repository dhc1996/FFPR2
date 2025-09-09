@echo off
chcp 65001 >nul
title 视频字幕工具 - 字幕添加功能

echo.
echo ========================================
echo    视频字幕工具 - 字幕添加功能
echo ========================================
echo.
echo 功能包括:
echo - 为视频添加字幕文件
echo - 多种字幕样式选择
echo - 自动时间分配和字幕分割
echo - 智能字幕时间调整
echo - 支持多种文案文档格式
echo.
echo 正在启动字幕添加工具...
echo.

python subtitle_cli.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 程序运行出错，错误代码: %ERRORLEVEL%
    echo 请检查Python环境和依赖包安装
)

echo.
echo 程序已退出，按任意键关闭窗口...
pause >nul
