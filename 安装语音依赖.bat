@echo off
chcp 65001 >nul
title 安装语音合成依赖

echo.
echo ========================================
echo       安装语音合成依赖
echo ========================================
echo.
echo 正在安装推荐的TTS引擎...
echo.

echo 检测到Python 2.7环境，安装兼容的TTS包...
echo.

echo 安装pyttsx3 2.7版本（兼容Python 2.7）...
"D:/Software/Python27/python.exe" -m pip install "pyttsx3==2.7"
echo.

echo 注意：Edge-TTS不支持Python 2.7，已跳过安装
echo 系统将使用pyttsx3和系统TTS作为语音合成引擎
echo.

echo ========================================
echo       安装完成
echo ========================================
echo.
echo 现在您可以在字幕工具中启用语音合成功能！
echo 运行: 启动字幕工具.bat
echo.
echo 按任意键关闭窗口...
pause >nul
