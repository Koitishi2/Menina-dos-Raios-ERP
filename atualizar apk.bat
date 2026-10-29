@echo off
setlocal
set "PROJECT_ROOT=%~dp0."
set "PREPARE_SCRIPT=%~dp0scripts\prepare_apk_publish.ps1"
start "Menina dos Raios - Preparando APK" "%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%PREPARE_SCRIPT%" -ProjectRoot "%PROJECT_ROOT%"
exit /b 0
