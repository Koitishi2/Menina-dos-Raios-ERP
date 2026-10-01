@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo ERRO [LOCAL.PYTHON]: Python nao encontrado no PATH.
  exit /b 10
)

python scripts\deploy_server.py %*
exit /b %errorlevel%
