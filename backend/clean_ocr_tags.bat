@echo off
REM Clean OCR Tags - Windows Batch Script
REM 清理 OCR 历史记录中的坐标标签

cd /d "%~dp0"

echo ==========================================
echo OCR Tags Cleaning Tool
echo ==========================================
echo.

REM Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo Error: Virtual environment not found!
    echo Please run test_local.ps1 first to set up the environment.
    pause
    exit /b 1
)

REM Check if --apply or --backup argument is provided
if "%1"=="--apply" (
    python clean_ocr_tags.py --apply
) else if "%1"=="--backup" (
    python clean_ocr_tags.py --backup
) else (
    REM Preview mode by default
    python clean_ocr_tags.py

    echo.
    echo To execute cleaning, run:
    echo   clean_ocr_tags.bat --apply       (Clean without backup)
    echo   clean_ocr_tags.bat --backup      (Clean with database backup)
)

echo.
pause
