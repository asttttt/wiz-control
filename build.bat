@echo off
echo ============================================
echo   WizControl Build Script
echo ============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python from https://python.org
    echo         Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [2/3] Building executable with PyInstaller...
python -m PyInstaller wiz_control.spec --noconfirm

if errorlevel 1 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo [3/3] Build complete!
echo.
echo Output: dist\WizControl.exe
echo.
echo Next steps:
echo 1. Test: dist\WizControl.exe
echo 2. Build installer: Open wiz_control_installer.iss in Inno Setup
echo.
pause
