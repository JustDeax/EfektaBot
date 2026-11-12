@echo off
REM Cross-platform startup script for Windows

cd /d "%~dp0"

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python launch_chrome.py %*
    goto :eof
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py launch_chrome.py %*
    goto :eof
)

echo [!] Python was not found in PATH. Please install Python or launch Chrome manually.
pause
