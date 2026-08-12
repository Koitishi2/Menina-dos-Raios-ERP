@echo off
title Menina dos Raios - Publicar APK Oficial
cd /d "%~dp0"
echo.
echo ============================================================
echo  Menina dos Raios - Publicar APK Oficial
echo ============================================================
echo.
echo APK fixo:
echo C:\Users\adria\OneDrive\Documentos\vendas APK\Menina-dos-Raios-Vendas-OFICIAL.apk
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0PUBLICAR_APK.ps1" %*
if errorlevel 1 (
  echo.
  echo A publicacao nao foi concluida. Veja o erro acima.
) else (
  echo.
  echo Publicacao concluida.
)
echo.
pause
