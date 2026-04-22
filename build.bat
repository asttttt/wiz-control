@echo off
setlocal enabledelayedexpansion
title WizControl Builder

echo.
echo =========================================
echo   WizControl -- Build Script
echo =========================================
echo.

:: ── Check Python ──────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    echo         Download from https://www.python.org/downloads/
    echo         Make sure "Add Python to PATH" is checked during install.
    pause & exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [OK] Found %PYVER%

:: ── Check pip ─────────────────────────────────────────────────────────
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip not available. Run: python -m ensurepip
    pause & exit /b 1
)
echo [OK] pip available

:: ── Upgrade pip silently ──────────────────────────────────────────────
echo [..] Upgrading pip...
python -m pip install --upgrade pip --quiet

:: ── Install / verify runtime dependencies ────────────────────────────
echo [..] Checking runtime dependencies...

set DEPS=customtkinter Pillow pystray

for %%D in (%DEPS%) do (
    python -c "import %%D" >nul 2>&1
    if errorlevel 1 (
        echo [..] Installing %%D ...
        python -m pip install %%D --quiet
        if errorlevel 1 (
            echo [ERROR] Failed to install %%D
            pause & exit /b 1
        )
        echo [OK] %%D installed
    ) else (
        echo [OK] %%D already present
    )
)

:: ── Install PyInstaller ───────────────────────────────────────────────
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [..] Installing PyInstaller...
    python -m pip install pyinstaller --quiet
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller
        pause & exit /b 1
    )
    echo [OK] PyInstaller installed
) else (
    echo [OK] PyInstaller already present
)

:: ── Clean previous build ──────────────────────────────────────────────
echo.
echo [..] Cleaning previous build output...
if exist dist\WizControl.exe del /f /q dist\WizControl.exe
if exist build rmdir /s /q build

:: ── Build ─────────────────────────────────────────────────────────────
echo [..] Building WizControl.exe ...
echo.
pyinstaller wiz_control.spec
if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller failed. See output above.
    pause & exit /b 1
)

:: ── Done ──────────────────────────────────────────────────────────────
echo.
echo =========================================
echo   Build complete!
echo   Output: dist\WizControl.exe
echo =========================================
echo.
pause
