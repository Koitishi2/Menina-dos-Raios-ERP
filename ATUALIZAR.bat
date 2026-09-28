@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Menina dos Raios - Publicacao do pacote
color 0A
cd /d "%~dp0"

set "HOST=2.24.124.76"
set "PORT=22"
set "USER=root"

set "REMOTE_BACKEND_DIR=/opt/menina/backend"
set "REMOTE_STAGING_DIR=/root/menina_refatoracao_staging"
set "REMOTE_BACKUP_DIR=/root/menina_refatoracao_backups"

set "LOCAL_CONFIG=%~dp0atualizarrefatorado.local.bat"
if exist "%LOCAL_CONFIG%" call "%LOCAL_CONFIG%"

set "REMOTE_SCRIPT=atualizar_backend_seguro.sh"
set "PACKAGE_NAME=bm_app_whatsapp_sellers_621ed74.zip"
set "PACKAGE_DIR=deploy\staging"
set "CHECKSUM_FILE=%PACKAGE_NAME:~0,-4%_SHA256SUMS.txt"

set "PACKAGE_SHA256=A383F5DBA0389E286F0A523C1E6EFC29A2EE3C75D2F2AA17AA6ACA7877A30ED4"
set "SCRIPT_SHA256=D42A614494B1E2F3BFB2BA1464C9CD18894587A8E0CAF212CC9F1F552655EEBC"
set "CHECKSUM_SHA256=4B4FA4D3A57086D12EB71D3E40E0912979F98CE4C5854C35B1B0CACFB87D75CB"

echo.
echo ============================================================
echo Menina dos Raios - Publicacao do pacote
echo ============================================================
echo.
echo Pacote: %PACKAGE_NAME%
echo Destino: %USER%@%HOST%:%REMOTE_BACKEND_DIR%
echo.

where powershell >nul 2>nul
if errorlevel 1 goto :erro_powershell

where ssh >nul 2>nul
if errorlevel 1 goto :erro_ssh

where scp >nul 2>nul
if errorlevel 1 goto :erro_scp

if not exist "%PACKAGE_DIR%\%PACKAGE_NAME%" goto :erro_pacote
if not exist "%PACKAGE_DIR%\%CHECKSUM_FILE%" goto :erro_checksum
if not exist "%REMOTE_SCRIPT%" goto :erro_script

for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "UPDATE_ID=%%T"

if not defined UPDATE_ID goto :erro_id

set "REMOTE_RUN_DIR=%REMOTE_STAGING_DIR%/quick_%UPDATE_ID%"
set "REMOTE_CODE_BACKUP=%REMOTE_BACKUP_DIR%/quick_%UPDATE_ID%"

echo [1/6] Validando pacote local...

powershell -NoProfile -Command "$h=(Get-FileHash '%PACKAGE_DIR%\%PACKAGE_NAME%' -Algorithm SHA256).Hash.ToUpper(); if($h -ne '%PACKAGE_SHA256%'){Write-Host ('HASH_ZIP_INVALIDO: '+$h); exit 1}"
if errorlevel 1 goto :erro_local

powershell -NoProfile -Command "$h=(Get-FileHash '%REMOTE_SCRIPT%' -Algorithm SHA256).Hash.ToUpper(); if($h -ne '%SCRIPT_SHA256%'){Write-Host ('HASH_SCRIPT_INVALIDO: '+$h); exit 1}"
if errorlevel 1 goto :erro_local

powershell -NoProfile -Command "$h=(Get-FileHash '%PACKAGE_DIR%\%CHECKSUM_FILE%' -Algorithm SHA256).Hash.ToUpper(); if($h -ne '%CHECKSUM_SHA256%'){Write-Host ('HASH_CHECKSUM_INVALIDO: '+$h); exit 1}"
if errorlevel 1 goto :erro_local

for /f %%C in ('dir /b /a-d "backend\*.py" 2^>nul ^| find /c /v ""') do set "PY_COUNT=%%C"

if not defined PY_COUNT goto :erro_backend
if "%PY_COUNT%"=="0" goto :erro_backend

echo Pacote validado.
echo Script SHA-256: %SCRIPT_SHA256%
echo ZIP SHA-256: %PACKAGE_SHA256%
echo Checksum SHA-256: %CHECKSUM_SHA256%
echo.

if /I "%~1"=="--check" (
    echo VALIDACAO_LOCAL_OK
    echo Nenhuma conexao com o servidor foi realizada.
    pause
    exit /b 0
)

echo Banco, .env, uploads, logs e dados persistentes nao serao tocados.
choice /C SN /N /M "Confirmar publicacao do pacote? [S/N]: "

if errorlevel 2 (
    echo Publicacao cancelada pelo usuario.
    pause
    exit /b 2
)

echo.
echo [2/6] Criando staging isolado...

ssh -o ConnectTimeout=10 -p "%PORT%" "%USER%@%HOST%" "set -e; test '%REMOTE_BACKEND_DIR%' != '/'; mkdir -p '%REMOTE_RUN_DIR%' '%REMOTE_CODE_BACKUP%'"
if errorlevel 1 goto :erro_remoto

echo.
echo [3/6] Enviando pacote, checksum e script...

scp -o ConnectTimeout=10 -P "%PORT%" ^
    "%PACKAGE_DIR%\%PACKAGE_NAME%" ^
    "%USER%@%HOST%:%REMOTE_RUN_DIR%/%PACKAGE_NAME%"
if errorlevel 1 goto :erro_remoto

scp -o ConnectTimeout=10 -P "%PORT%" ^
    "%PACKAGE_DIR%\%CHECKSUM_FILE%" ^
    "%USER%@%HOST%:%REMOTE_RUN_DIR%/%CHECKSUM_FILE%"
if errorlevel 1 goto :erro_remoto

scp -o ConnectTimeout=10 -P "%PORT%" ^
    "%REMOTE_SCRIPT%" ^
    "%USER%@%HOST%:%REMOTE_RUN_DIR%/%REMOTE_SCRIPT%"
if errorlevel 1 goto :erro_remoto

echo.
echo [4/6] Validando integridade dos artefatos no staging...

ssh -o ConnectTimeout=10 -p "%PORT%" "%USER%@%HOST%" ^
    "set -e; cd '%REMOTE_RUN_DIR%'; test \"$(sha256sum '%PACKAGE_NAME%' | awk '{print $1}')\" = '%PACKAGE_SHA256%'; test \"$(sha256sum '%REMOTE_SCRIPT%' | awk '{print $1}')\" = '%SCRIPT_SHA256%'; test \"$(sha256sum '%CHECKSUM_FILE%' | awk '{print $1}')\" = '%CHECKSUM_SHA256%'; sha256sum -c '%CHECKSUM_FILE%'"
if errorlevel 1 goto :erro_remoto

echo.
echo [5/6] Aplicando atualizacao com rollback automatico...

ssh -o ConnectTimeout=10 -p "%PORT%" "%USER%@%HOST%" ^
    "RUN_DIR='%REMOTE_RUN_DIR%' APP_DIR='%REMOTE_BACKEND_DIR%' BACKUP_DIR='%REMOTE_CODE_BACKUP%' SERVICE='menina' EXPECTED_PY_COUNT='%PY_COUNT%' PACKAGE_NAME='%PACKAGE_NAME%' EXPECTED_PACKAGE_SHA256='%PACKAGE_SHA256%' EXPECTED_SCRIPT_SHA256='%SCRIPT_SHA256%' bash '%REMOTE_RUN_DIR%/%REMOTE_SCRIPT%'"
if errorlevel 1 goto :erro_remoto

echo.
echo [6/6] Removendo staging desta execucao...

ssh -o ConnectTimeout=10 -p "%PORT%" "%USER%@%HOST%" ^
    "set -e; test -n '%REMOTE_RUN_DIR%'; case '%REMOTE_RUN_DIR%' in '%REMOTE_STAGING_DIR%'/quick_*) rm -rf -- '%REMOTE_RUN_DIR%' ;; *) echo INVALID_STAGING_PATH >&2; exit 90 ;; esac"
if errorlevel 1 goto :erro_remoto

echo.
echo ============================================================
echo PUBLICACAO_OK
echo ============================================================
echo Pacote: %PACKAGE_NAME%
echo ZIP SHA-256: %PACKAGE_SHA256%
echo Backup remoto: %REMOTE_CODE_BACKUP%
echo.
pause
exit /b 0


:erro_powershell
echo.
echo ERRO: Windows PowerShell nao encontrado.
echo Verifique se powershell.exe esta disponivel no PATH.
pause
exit /b 1

:erro_ssh
echo.
echo ERRO: ssh nao encontrado no PATH.
pause
exit /b 1

:erro_scp
echo.
echo ERRO: scp nao encontrado no PATH.
pause
exit /b 1

:erro_pacote
echo.
echo ERRO: pacote nao encontrado:
echo %PACKAGE_DIR%\%PACKAGE_NAME%
pause
exit /b 1

:erro_checksum
echo.
echo ERRO: arquivo de checksum nao encontrado:
echo %PACKAGE_DIR%\%CHECKSUM_FILE%
pause
exit /b 1

:erro_script
echo.
echo ERRO: script remoto nao encontrado:
echo %REMOTE_SCRIPT%
pause
exit /b 1

:erro_backend
echo.
echo ERRO: backend local nao encontrado ou sem arquivos Python na raiz.
pause
exit /b 1

:erro_id
echo.
echo ERRO: nao foi possivel gerar o identificador da execucao.
pause
exit /b 1

:erro_local
echo.
echo ERRO: validacao local falhou.
echo Nenhum arquivo foi enviado.
pause
exit /b 1

:erro_remoto
echo.
echo ERRO: publicacao remota nao foi concluida.
echo O staging foi preservado para diagnostico:
echo %REMOTE_RUN_DIR%
pause
exit /b 1