@echo off
title Menina dos Raios Ltda — Servidor
color 0A

set "PYTHON=C:\Python314\python.exe"
if not exist "%PYTHON%" (
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
        if exist "%%D\python.exe" set "PYTHON=%%D\python.exe"
    )
)
if not exist "%PYTHON%" set "PYTHON=python"

:: Instalar dependencias silenciosamente
echo Verificando dependencias...
"%PYTHON%" -m pip install fastapi uvicorn openpyxl python-multipart ^
    --quiet --disable-pip-version-check 2>nul

:: Descobrir IP local
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /c:"IPv4"') do (
    set "LOCAL_IP=%%i"
    goto :found
)
:found
set "LOCAL_IP=%LOCAL_IP: =%"

:: Liberar porta 8765 no firewall
netsh advfirewall firewall show rule name="Menina dos Raios" >nul 2>&1
if %errorlevel% neq 0 (
    netsh advfirewall firewall add rule name="Menina dos Raios" ^
        dir=in action=allow protocol=TCP localport=8765 >nul 2>&1
)

echo.
echo  ============================================================
echo   Menina dos Raios Ltda -- Controle de Vendas
echo.
echo   Acesso local:   http://localhost:8765
echo   Acesso em rede: http://%LOCAL_IP%:8765
echo.
echo   Login padrao:   admin / admin123
echo   (Altere a senha apos o primeiro acesso na aba Registro)
echo.
echo   Feche esta janela para ENCERRAR o servidor.
echo  ============================================================
echo.

"%PYTHON%" "%~dp0backend\app.py"
