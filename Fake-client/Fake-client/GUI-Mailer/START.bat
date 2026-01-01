@echo off
title Email Sender Pro - GUI Edition
echo.
echo ================================================
echo    Email Sender Pro - GUI Edition
echo ================================================
echo.
echo Starting application...
echo.

python gui_mailer.py

if %errorlevel% neq 0 (
    echo.
    echo ================================================
    echo    ERROR: Failed to start application
    echo ================================================
    echo.
    echo Please check:
    echo 1. Python is installed
    echo 2. Dependencies are installed: pip install -r requirements.txt
    echo.
    pause
)
