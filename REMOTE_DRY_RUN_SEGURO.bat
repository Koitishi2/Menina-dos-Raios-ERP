@echo off
setlocal EnableExtensions
title Menina dos Raios - Remote dry-run seguro
cd /d "%~dp0"

set "HOST=2.24.124.76"
set "PORT=22"
set "USER=root"
set "APP_DIR=/opt/menina/backend"
set "SERVICE=menina"
set "PACKAGE_NAME=bm_app_whatsapp_sellers_621ed74.zip"
set "CHECKSUM_NAME=bm_app_whatsapp_sellers_621ed74_SHA256SUMS.txt"
set "UPDATER_NAME=atualizar_backend_seguro.sh"
set "DRYRUN_SCRIPT=remote_dry_run_only.sh"
set "PACKAGE_DIR=deploy\staging"
set "EXPECTED_PACKAGE_SHA256=A383F5DBA0389E286F0A523C1E6EFC29A2EE3C75D2F2AA17AA6ACA7877A30ED4"
set "EXPECTED_CHECKSUM_SHA256=4B4FA4D3A57086D12EB71D3E40E0912979F98CE4C5854C35B1B0CACFB87D75CB"
set "EXPECTED_UPDATER_SHA256=D42A614494B1E2F3BFB2BA1464C9CD18894587A8E0CAF212CC9F1F552655EEBC"

where pwsh >nul 2>nul || goto :local_error
where ssh >nul 2>nul || goto :local_error
where scp >nul 2>nul || goto :local_error
for /f %%T in ('pwsh -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "UPDATE_ID=%%T"
set "REMOTE_RUN_DIR=/root/menina_refatoracao_staging/dryrun_%UPDATE_ID%"
set "RESULT_DIR=backups\remote_dryrun_%UPDATE_ID%"

if not exist "%PACKAGE_DIR%\%PACKAGE_NAME%" goto :local_error
if not exist "%PACKAGE_DIR%\%CHECKSUM_NAME%" goto :local_error
if not exist "%UPDATER_NAME%" goto :local_error
if not exist "%PACKAGE_DIR%\%DRYRUN_SCRIPT%" goto :local_error

pwsh -NoProfile -Command "if ((Get-FileHash '%PACKAGE_DIR%\%PACKAGE_NAME%' -Algorithm SHA256).Hash -ne '%EXPECTED_PACKAGE_SHA256%') { exit 1 }; if ((Get-FileHash '%PACKAGE_DIR%\%CHECKSUM_NAME%' -Algorithm SHA256).Hash -ne '%EXPECTED_CHECKSUM_SHA256%') { exit 2 }; if ((Get-FileHash '%UPDATER_NAME%' -Algorithm SHA256).Hash -ne '%EXPECTED_UPDATER_SHA256%') { exit 3 }"
if errorlevel 1 goto :local_error

if /I "%~1"=="--check" (
  echo REMOTE_DRY_RUN_LOCAL_CHECK_OK
  echo Nenhuma conexao remota foi realizada.
  exit /b 0
)

mkdir "%RESULT_DIR%" >nul 2>nul

echo ============================================================
echo REMOTE DRY-RUN CONTROLADO - SEM DEPLOY
echo ============================================================
echo.
echo O servico real nao sera parado, iniciado ou reiniciado.
echo Digite a senha somente nos prompts SSH/SCP.
echo.

echo [1/3] Criando staging isolado...
ssh -o ConnectTimeout=10 -p "%PORT%" "%USER%@%HOST%" "set -e; mkdir -p '%REMOTE_RUN_DIR%'; test '%REMOTE_RUN_DIR%' != '/'; echo STAGING_OK"
if errorlevel 1 goto :remote_error

echo [2/3] Enviando artefatos somente ao staging...
scp -o ConnectTimeout=10 -P "%PORT%" "%PACKAGE_DIR%\%PACKAGE_NAME%" "%PACKAGE_DIR%\%CHECKSUM_NAME%" "%UPDATER_NAME%" "%PACKAGE_DIR%\%DRYRUN_SCRIPT%" "%USER%@%HOST%:%REMOTE_RUN_DIR%/"
if errorlevel 1 goto :remote_error

echo [3/3] Executando validacoes isoladas e somente leitura no runtime real...
ssh -o ConnectTimeout=10 -p "%PORT%" "%USER%@%HOST%" "RUN_DIR='%REMOTE_RUN_DIR%' APP_DIR='%APP_DIR%' SERVICE='%SERVICE%' PACKAGE_NAME='%PACKAGE_NAME%' CHECKSUM_NAME='%CHECKSUM_NAME%' UPDATER_NAME='%UPDATER_NAME%' EXPECTED_PACKAGE_SHA256='%EXPECTED_PACKAGE_SHA256%' EXPECTED_CHECKSUM_SHA256='%EXPECTED_CHECKSUM_SHA256%' EXPECTED_UPDATER_SHA256='%EXPECTED_UPDATER_SHA256%' bash '%REMOTE_RUN_DIR%/%DRYRUN_SCRIPT%'" > "%RESULT_DIR%\execution.log"
if errorlevel 1 goto :remote_error

type "%RESULT_DIR%\execution.log"
echo.
echo REMOTE_DRY_RUN_CONCLUIDO
echo Resultado local: %CD%\%RESULT_DIR%
echo Staging remoto preservado para auditoria: %REMOTE_RUN_DIR%
pause
exit /b 0

:local_error
echo.
echo DRY_RUN_BLOQUEADO_LOCALMENTE. Nenhuma conexao ou alteracao remota foi executada.
pause
exit /b 1

:remote_error
echo.
echo DRY_RUN_REMOTO_REPROVADO. Nenhum deploy ou restart foi executado.
echo Staging remoto preservado: %REMOTE_RUN_DIR%
echo Resultado local: %CD%\%RESULT_DIR%
if exist "%RESULT_DIR%\execution.log" type "%RESULT_DIR%\execution.log"
pause
exit /b 1
