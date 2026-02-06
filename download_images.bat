@echo off
chcp 65001 >nul
title 卡牌图片下载工具

echo ========================================
echo 卡牌图片下载工具
echo ========================================
echo.

python tools\download_card_images.py

echo.
pause
