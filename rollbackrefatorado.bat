@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Menina dos Raios - Rollback refatorado seguro
color 0E

rem ============================================================
rem  Rollback seguro para snapshot completo pre-refatoracao.
rem
rem  Modo padrao: DRY_RUN=1.
rem  Uso real exige:
rem    rollbackrefatorado.bat --snapshot NOME.tar.gz --sha NOME.sha256 --apply
rem
rem  Nao grave senha, token ou chave privada neste arquivo.
rem ============================================================

set "DRY_RUN=1"
set "SNAPSHOT_NAME="
set "SNAPSHOT_SHA_FILE="

set "SSH_TOOL=ssh"
set "SCP_TOOL=scp"
set "REMOTE_HASH_TOOL=sha256sum"
set "REMOTE_TAR_TOOL=tar"

set "HOST=CONFIGURAR_HOST"
set "PORT=CONFIGURAR_PORT"
set "USER=CONFIGURAR_USER"
set "REMOTE_APP_DIR=CONFIGURAR_REMOTE_APP_DIR"
set "REMOTE_SERVER_BACKUP_DIR=CONFIGURAR_REMOTE_SERVER_BACKUP_DIR"

set "LOCAL_CONFIG=%~dp0atualizarrefatorado.local.bat"
if exist "%LOCAL_CONFIG%" call "%LOCAL_CONFIG%"

set "LOCAL_LOG_DIR=%~dp0logs_atualizacao_refatorada"

:parse_args
if "%~1"=="" goto :args_done
if /I "%~1"=="--apply" (
  set "DRY_RUN=0"
  shift
  goto :parse_args
)
if /I "%~1"=="--snapshot" (
  set "SNAPSHOT_NAME=%~2"
  shift
  shift
  goto :parse_args
)
if /I "%~1"=="--sha" (
  set "SNAPSHOT_SHA_FILE=%~2"
  shift
  shift
  goto :parse_args
)
echo ERRO: argumento desconhecido: %~1
exit /b 2

:args_done
cd /d "%~dp0"
if not exist "%LOCAL_LOG_DIR%" mkdir "%LOCAL_LOG_DIR%" >nul 2>nul
for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "ROLLBACK_ID=%%T"
for /f %%G in ('powershell -NoProfile -Command "[guid]::NewGuid().ToString('N').Substring(0,8)"') do set "RUN_SUFFIX=%%G"
set "LOG_FILE=%LOCAL_LOG_DIR%\rollbackrefatorado_%ROLLBACK_ID%_%RUN_SUFFIX%.log"

echo.
echo  ============================================================
echo   Menina dos Raios - Rollback refatorado seguro
echo  ============================================================
echo.
if "%DRY_RUN%"=="1" (
  echo  MODO DRY_RUN: nenhuma restauracao sera aplicada.
) else (
  echo  MODO RESTAURACAO COMPLETA REAL.
)
echo.

call :log "Inicio rollback"
call :validate_inputs
if errorlevel 1 goto :erro
call :show_plan

if "%DRY_RUN%"=="1" (
  call :log "DRY_RUN de rollback concluido. Nenhum servidor foi alterado."
  exit /b 0
)

choice /C SN /N /M "Confirmar RESTAURACAO COMPLETA do snapshot informado? [S/N]: "
if errorlevel 2 (
  call :log "Rollback real cancelado pelo operador."
  exit /b 2
)

call :remote_pre_restore_backup
if errorlevel 1 goto :erro
call :remote_restore_snapshot
if errorlevel 1 goto :erro
call :log "Rollback completo concluido. Snapshot original preservado."
exit /b 0

:validate_inputs
where "%SSH_TOOL%" >nul 2>nul
if errorlevel 1 (
  call :log "ERRO: ferramenta nao encontrada: %SSH_TOOL%"
  exit /b 1
)
call :reject_config "%HOST%" "HOST"
if errorlevel 1 exit /b 1
call :reject_config "%PORT%" "PORT"
if errorlevel 1 exit /b 1
call :reject_config "%USER%" "USER"
if errorlevel 1 exit /b 1
call :reject_config "%REMOTE_APP_DIR%" "REMOTE_APP_DIR"
if errorlevel 1 exit /b 1
call :reject_config "%REMOTE_SERVER_BACKUP_DIR%" "REMOTE_SERVER_BACKUP_DIR"
if errorlevel 1 exit /b 1
if "%SNAPSHOT_NAME%"=="" (
  call :log "ERRO: informe --snapshot NOME.tar.gz"
  exit /b 1
)
echo %SNAPSHOT_NAME% | findstr /R "[/\\]" >nul
if not errorlevel 1 (
  call :log "ERRO: snapshot deve ser apenas nome de arquivo, sem barras."
  exit /b 1
)
if "%SNAPSHOT_SHA_FILE%"=="" (
  call :log "ERRO: informe --sha ARQUIVO.sha256"
  exit /b 1
)
exit /b 0

:show_plan
echo  Plano de rollback:
echo   - Snapshot: %SNAPSHOT_NAME%
echo   - SHA local: %SNAPSHOT_SHA_FILE%
echo   - App remoto: [configurado fora do script publico]
echo   - Backup pre-restore: criado antes da restauracao real
echo   - Migracoes: nao executadas
echo   - Snapshot original: preservado
echo.
exit /b 0

:remote_pre_restore_backup
call :log "Criando backup remoto do estado atual antes da restauracao completa."
"%SSH_TOOL%" -p "%PORT%" "%USER%@%HOST%" "set -e; PRE='%REMOTE_SERVER_BACKUP_DIR%/pre_rollback_refatorado_%ROLLBACK_ID%.tar.gz'; %REMOTE_TAR_TOOL% -C '%REMOTE_APP_DIR%' --one-file-system --warning=no-file-changed -czf ""$PRE"" .; test -s ""$PRE""; %REMOTE_TAR_TOOL% -tzf ""$PRE"" >/dev/null; echo PRE_RESTORE_BACKUP_OK=""$PRE"""
exit /b %ERRORLEVEL%

:remote_restore_snapshot
call :log "Validando e restaurando snapshot completo."
for /f "usebackq tokens=1" %%H in ("%SNAPSHOT_SHA_FILE%") do set "EXPECTED_SNAPSHOT_SHA=%%H"
"%SSH_TOOL%" -p "%PORT%" "%USER%@%HOST%" "set -e; cd '%REMOTE_SERVER_BACKUP_DIR%'; echo '%EXPECTED_SNAPSHOT_SHA%  %SNAPSHOT_NAME%' > rollback_sha256_%ROLLBACK_ID%.txt; %REMOTE_HASH_TOOL% -c rollback_sha256_%ROLLBACK_ID%.txt; %REMOTE_TAR_TOOL% -tzf '%SNAPSHOT_NAME%' >/dev/null; %REMOTE_TAR_TOOL% -C '%REMOTE_APP_DIR%' -xzf '%SNAPSHOT_NAME%'; echo SNAPSHOT_RESTORED"
exit /b %ERRORLEVEL%

:reject_config
set "VALUE_TO_CHECK=%~1"
set "NAME_TO_CHECK=%~2"
echo %VALUE_TO_CHECK% | findstr /I "CONFIGURAR" >nul
if not errorlevel 1 (
  call :log "ERRO: variavel obrigatoria sem configurar: %NAME_TO_CHECK%"
  exit /b 1
)
exit /b 0

:log
echo %~1
>>"%LOG_FILE%" echo %~1
exit /b 0

:erro
echo.
echo  ============================================================
echo   ERRO: rollback nao concluido.
echo   Consulte o log: %LOG_FILE%
echo  ============================================================
echo.
exit /b 1
