@echo off
setlocal
rem PADRAO OFICIAL: use este arquivo para publicar somente o APK assinado.
rem Mantem prevalidacao, backup remoto, SCP por staging, checksum remoto e GET publico SHA-256.
rem A validacao publica tem 4 tentativas com cache-busting para downloads incompletos.
set "PROJECT_ROOT=%~dp0."
set "PREPARE_SCRIPT=%~dp0scripts\prepare_apk_publish.ps1"
if not exist "%PREPARE_SCRIPT%" (
  echo Nao foi encontrado o validador oficial do APK: "%PREPARE_SCRIPT%"
  pause
  exit /b 1
)
start "Menina dos Raios - Publicar APK" /normal "%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -NoExit -File "%PREPARE_SCRIPT%" -ProjectRoot "%PROJECT_ROOT%"
exit /b 0
