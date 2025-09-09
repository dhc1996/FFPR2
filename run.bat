@echo off
chcp 65001 >nul
echo 自动化视频剪辑工具启动脚本
echo =============================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请确保Python 2.7.18已安装
    pause
    exit /b 1
)

:: 检查FFmpeg是否安装
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到FFmpeg，请确保FFmpeg已安装并添加到PATH环境变量
    echo 下载地址：https://ffmpeg.org/download.html
    pause
    exit /b 1
)

echo Python和FFmpeg检查通过
echo.

:: 询问运行模式
echo 请选择运行模式：
echo 1. 简单模式 (video_editor.py)
echo 2. 完整模式 (cli.py) - 推荐
echo.
set /p mode="请输入选择 (1 或 2, 默认2): "

if "%mode%"=="1" (
    echo 启动简单模式...
    python video_editor.py
) else (
    echo 启动完整模式...
    python cli.py
)

echo.
echo 程序结束
pause
