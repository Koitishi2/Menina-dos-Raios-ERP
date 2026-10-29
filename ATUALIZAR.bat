@echo off
setlocal
set "PROJECT_ROOT=%~dp0."
set "RUNNER=%TEMP%\menina-atualizar-%RANDOM%-%RANDOM%.ps1"
copy /y "%~dp0scripts\atualizar.ps1" "%RUNNER%" >nul
if errorlevel 1 (
  echo Nao foi possivel preparar o atualizador PowerShell.
  pause
  exit /b 1
)
start "Menina dos Raios - Atualizar" "%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -NoExit -File "%RUNNER%" -ProjectRoot "%PROJECT_ROOT%"
exit /b 0
