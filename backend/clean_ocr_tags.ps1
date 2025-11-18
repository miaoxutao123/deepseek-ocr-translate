# Clean OCR Tags - PowerShell Script
# 清理 OCR 历史记录中的坐标标签

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "OCR Tags Cleaning Tool" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to backend directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Check if virtual environment exists
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "Error: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run test_local.ps1 first to set up the environment." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    exit 1
}

# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Parse arguments
$mode = if ($args.Count -gt 0) { $args[0] } else { "" }

# Run the cleaning script
switch ($mode) {
    "--apply" {
        python clean_ocr_tags.py --apply
    }
    "--backup" {
        python clean_ocr_tags.py --backup
    }
    default {
        # Preview mode by default
        python clean_ocr_tags.py

        Write-Host ""
        Write-Host "To execute cleaning, run:" -ForegroundColor Yellow
        Write-Host "  .\clean_ocr_tags.ps1 --apply       (Clean without backup)" -ForegroundColor Gray
        Write-Host "  .\clean_ocr_tags.ps1 --backup      (Clean with database backup)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
