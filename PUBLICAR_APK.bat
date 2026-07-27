@echo off
title Menina dos Raios - Publicar APK
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0PUBLICAR_APK.ps1"
if errorlevel 1 (
  echo.
  echo A publicacao nao foi concluida. Veja o erro acima.
) else (
  echo.
  echo Publicacao concluida.
)
echo.
pause
