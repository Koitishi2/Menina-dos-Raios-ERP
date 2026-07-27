@echo off
title Menina dos Raios — Configuração Inicial
color 0A
echo.
echo  ============================================================
echo   MENINA DOS RAIOS — Configuracao (execute apenas uma vez)
echo  ============================================================
echo.

:: Encontrar Python
set "PYTHON=C:\Python314\python.exe"
if not exist "%PYTHON%" (
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
        if exist "%%D\python.exe" set "PYTHON=%%D\python.exe"
    )
)
if not exist "%PYTHON%" set "PYTHON=python"

echo  [1/2] Verificando Python...
"%PYTHON%" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  Python nao encontrado. Instale em: https://www.python.org/downloads/
    pause & start https://www.python.org/downloads/ & exit /b 1
)
echo        OK

echo.
echo  [2/2] Instalando dependencias Python...
"%PYTHON%" -m pip install fastapi uvicorn pandas openpyxl python-multipart ^
    --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  ERRO ao instalar dependencias. Verifique sua conexao.
    pause & exit /b 1
)
echo        OK

echo.
echo  ============================================================
echo   Configuracao concluida! Execute INICIAR.bat para abrir.
echo  ============================================================
echo.
pause
