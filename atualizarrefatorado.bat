@echo off
setlocal EnableExtensions
title Menina dos Raios - Atualizacao refatorada segura
color 0A

rem Atualizador seguro da versao estavel.
rem Commit do pacote: 88fef18
rem Modo padrao: validacao local, sem ssh/scp.
rem Use --remote-dry-run para validar staging remoto sem aplicar.
rem Use --apply somente para atualizacao real controlada.
rem Nao grave senha, token ou chave privada neste arquivo.

set "VERSION_COMMIT=88fef18"
set "ZIP_NAME=bm_app_refatorado_88fef18.zip"
set "CHECKSUM_FILE=CHECKSUM_REFATORADO_SHA256.txt"
set "REMOTE_STAGE_SCRIPT=%~dp0atualizarrefatorado_remote_stage.sh"
set "REMOTE_CLEANUP_SCRIPT=%~dp0atualizarrefatorado_remote_cleanup.sh"
set "REMOTE_APPLY_SCRIPT=%~dp0atualizarrefatorado_remote_apply.sh"
set "REMOTE_STAGE_SCRIPT_NAME=atualizarrefatorado_remote_stage.sh"
set "REMOTE_CLEANUP_SCRIPT_NAME=atualizarrefatorado_remote_cleanup.sh"
set "REMOTE_APPLY_SCRIPT_NAME=atualizarrefatorado_remote_apply.sh"

set "SSH_TOOL=ssh"
set "SCP_TOOL=scp"
set "REMOTE_UNZIP_TOOL=python3 -m zipfile -e"
set "REMOTE_HASH_TOOL=sha256sum"
set "REMOTE_TAR_TOOL=tar"

set "HOST=CONFIGURAR_HOST"
set "PORT=CONFIGURAR_PORT"
set "USER=CONFIGURAR_USER"
set "REMOTE_APP_DIR=CONFIGURAR_REMOTE_APP_DIR"
set "REMOTE_BACKEND_DIR=CONFIGURAR_REMOTE_BACKEND_DIR"
set "REMOTE_STATIC_DIR=CONFIGURAR_REMOTE_STATIC_DIR"
set "REMOTE_BAILEYS_DIR=CONFIGURAR_REMOTE_BAILEYS_DIR"
set "REMOTE_STAGING_DIR=CONFIGURAR_REMOTE_STAGING_DIR"
set "REMOTE_BACKUP_DIR=CONFIGURAR_REMOTE_BACKUP_DIR"
set "REMOTE_SERVER_BACKUP_DIR=CONFIGURAR_REMOTE_SERVER_BACKUP_DIR"
set "REMOTE_SERVICE_RESTART=CONFIGURAR_REMOTE_SERVICE_RESTART"
set "HEALTHCHECK_URL="

set "LOCAL_CONFIG=%~dp0atualizarrefatorado.local.bat"
if exist "%LOCAL_CONFIG%" call "%LOCAL_CONFIG%"

set "MODE=LOCAL"
if /I "%~1"=="--remote-dry-run" set "MODE=REMOTE_DRY_RUN"
if /I "%~2"=="--remote-dry-run" set "MODE=REMOTE_DRY_RUN"
if /I "%~1"=="--apply" set "MODE=APPLY"
if /I "%~2"=="--apply" set "MODE=APPLY"

cd /d "%~dp0"

set "LOCAL_LOG_DIR=%~dp0logs_atualizacao_refatorada"
if not exist "%LOCAL_LOG_DIR%" mkdir "%LOCAL_LOG_DIR%" >nul 2>nul
for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "UPDATE_ID=%%T"
for /f %%G in ('powershell -NoProfile -Command "[guid]::NewGuid().ToString('N').Substring(0,8)"') do set "RUN_SUFFIX=%%G"
set "LOG_FILE=%LOCAL_LOG_DIR%\atualizarrefatorado_%UPDATE_ID%_%RUN_SUFFIX%.log"

set "REMOTE_RUN_DIR=%REMOTE_STAGING_DIR%/run_%VERSION_COMMIT%_%UPDATE_ID%"
set "REMOTE_BACKUP_FILE=%REMOTE_BACKUP_DIR%/app_files_%VERSION_COMMIT%_%UPDATE_ID%.tgz"
set "REMOTE_BAILEYS_BACKUP_FILE=%REMOTE_BACKUP_DIR%/baileys_api_%VERSION_COMMIT%_%UPDATE_ID%.tgz"

set "PROTECTED_REMOTE=.env *.env *.db *.sqlite *.sqlite3 database databases data instance uploads upload backups backup logs log storage media certificates certs keys backend/static/app-updates"
set "APP_FILES=backend/app.py backend/app_notes_domain.py backend/app_notes_service.py backend/backup_admin.py backend/company_config.py backend/monteiro_periods.py backend/monteiro_permissions.py backend/orcamentos.py backend/permissions_tabs.py backend/schemas.py backend/security_auth.py backend/security_request.py backend/utils.py backend/requirements.txt backend/static/index.html backend/static/assets backend/static/login-inspirador.png backend/static/logo.png README.md README_ATUALIZACAO_REFATORADA.txt"

echo.
echo  ============================================================
echo   Menina dos Raios - Atualizacao refatorada segura
echo  ============================================================
echo.
if "%MODE%"=="APPLY" (
  echo  MODO ATUALIZACAO REAL.
) else if "%MODE%"=="REMOTE_DRY_RUN" (
  echo  MODO DRY_RUN REMOTO: usa staging temporario, sem aplicar no app ativo.
) else (
  echo  MODO DRY_RUN LOCAL: nenhum ssh/scp sera executado.
)
echo.

echo Inicio
>>"%LOG_FILE%" echo Inicio
echo Commit esperado: %VERSION_COMMIT%
>>"%LOG_FILE%" echo Commit esperado: %VERSION_COMMIT%
echo MODE=%MODE%
>>"%LOG_FILE%" echo MODE=%MODE%

if not exist "%ZIP_NAME%" (
  echo ERRO: ZIP nao encontrado: %ZIP_NAME%
  >>"%LOG_FILE%" echo ERRO: ZIP nao encontrado: %ZIP_NAME%
  exit /b 1
)
if not exist "%CHECKSUM_FILE%" (
  echo ERRO: checksum nao encontrado: %CHECKSUM_FILE%
  >>"%LOG_FILE%" echo ERRO: checksum nao encontrado: %CHECKSUM_FILE%
  exit /b 1
)
if not exist "%REMOTE_STAGE_SCRIPT%" (
  echo ERRO: script remoto de staging nao encontrado: %REMOTE_STAGE_SCRIPT%
  >>"%LOG_FILE%" echo ERRO: script remoto de staging nao encontrado: %REMOTE_STAGE_SCRIPT%
  exit /b 1
)
if not exist "%REMOTE_CLEANUP_SCRIPT%" (
  echo ERRO: script remoto de cleanup nao encontrado: %REMOTE_CLEANUP_SCRIPT%
  >>"%LOG_FILE%" echo ERRO: script remoto de cleanup nao encontrado: %REMOTE_CLEANUP_SCRIPT%
  exit /b 1
)
if not exist "%REMOTE_APPLY_SCRIPT%" (
  echo ERRO: script remoto de apply nao encontrado: %REMOTE_APPLY_SCRIPT%
  >>"%LOG_FILE%" echo ERRO: script remoto de apply nao encontrado: %REMOTE_APPLY_SCRIPT%
  exit /b 1
)

set "EXPECTED_SHA="
for /f "usebackq tokens=1" %%H in ("%CHECKSUM_FILE%") do (
  if not defined EXPECTED_SHA set "EXPECTED_SHA=%%H"
)
if "%EXPECTED_SHA%"=="" (
  echo ERRO: SHA-256 esperado vazio.
  >>"%LOG_FILE%" echo ERRO: SHA-256 esperado vazio.
  exit /b 1
)
for /f "usebackq delims=" %%H in (`powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath '%ZIP_NAME%').Hash.ToLower()"`) do set "ACTUAL_SHA=%%H"
if /I not "%EXPECTED_SHA%"=="%ACTUAL_SHA%" (
  echo ERRO: SHA-256 divergente. Esperado=%EXPECTED_SHA% Atual=%ACTUAL_SHA%
  >>"%LOG_FILE%" echo ERRO: SHA-256 divergente. Esperado=%EXPECTED_SHA% Atual=%ACTUAL_SHA%
  exit /b 1
)
where "%SSH_TOOL%" >nul 2>nul
if errorlevel 1 (
  echo ERRO: ferramenta nao encontrada: %SSH_TOOL%
  >>"%LOG_FILE%" echo ERRO: ferramenta nao encontrada: %SSH_TOOL%
  exit /b 1
)
where "%SCP_TOOL%" >nul 2>nul
if errorlevel 1 (
  echo ERRO: ferramenta nao encontrada: %SCP_TOOL%
  >>"%LOG_FILE%" echo ERRO: ferramenta nao encontrada: %SCP_TOOL%
  exit /b 1
)

echo Validacao local OK. SHA-256: %ACTUAL_SHA%
>>"%LOG_FILE%" echo Validacao local OK. SHA-256: %ACTUAL_SHA%
echo  Plano:
echo   - Protocolo/ferramentas: scp e ssh
echo   - ZIP local: %ZIP_NAME%
echo   - Checksum: %ACTUAL_SHA%
echo   - Staging remoto: [configurado fora do script publico]
echo   - Backup remoto: [configurado fora do script publico]
echo   - Snapshot completo: [configurado fora do script publico]
echo   - Baileys remoto: [configurado fora do script publico]
echo   - Arquivos protegidos: %PROTECTED_REMOTE%
echo   - Arquivos de aplicacao: %APP_FILES%
echo.
>>"%LOG_FILE%" echo Plano exibido.

if "%MODE%"=="LOCAL" (
  echo DRY_RUN local concluido. Nenhuma conexao externa foi iniciada.
  >>"%LOG_FILE%" echo DRY_RUN local concluido. Nenhuma conexao externa foi iniciada.
  echo.
  echo  Validacao local concluida.
  echo  Para validar staging remoto sem aplicar: atualizarrefatorado.bat --remote-dry-run
  echo  Para atualizacao real controlada:       atualizarrefatorado.bat --apply
  echo.
  exit /b 0
)

if "%HOST%"=="" goto :bad_config
if "%PORT%"=="" goto :bad_config
if "%USER%"=="" goto :bad_config
if "%REMOTE_APP_DIR%"=="" goto :bad_config
if "%REMOTE_BACKEND_DIR%"=="" goto :bad_config
if "%REMOTE_STATIC_DIR%"=="" goto :bad_config
if "%REMOTE_BAILEYS_DIR%"=="" goto :bad_config
if "%REMOTE_STAGING_DIR%"=="" goto :bad_config
if "%REMOTE_BACKUP_DIR%"=="" goto :bad_config
if "%REMOTE_SERVER_BACKUP_DIR%"=="" goto :bad_config
echo(%HOST% %PORT% %USER% %REMOTE_APP_DIR% %REMOTE_BACKEND_DIR% %REMOTE_STATIC_DIR% %REMOTE_BAILEYS_DIR% %REMOTE_STAGING_DIR% %REMOTE_BACKUP_DIR% %REMOTE_SERVER_BACKUP_DIR%| findstr /I "CONFIGURAR" >nul
if not errorlevel 1 goto :bad_config

if "%MODE%"=="REMOTE_DRY_RUN" goto :remote_dry_run
if "%MODE%"=="APPLY" goto :apply_real

echo ERRO: modo desconhecido.
>>"%LOG_FILE%" echo ERRO: modo desconhecido.
exit /b 1

:bad_config
echo ERRO: configuracao remota obrigatoria ausente ou marcada como CONFIGURAR.
>>"%LOG_FILE%" echo ERRO: configuracao remota obrigatoria ausente ou marcada como CONFIGURAR.
exit /b 1

:remote_dry_run
echo DRY_RUN remoto: comando de servico sera ignorado.
>>"%LOG_FILE%" echo DRY_RUN remoto: comando de servico sera ignorado.
echo Comando remoto sanitizado: validacao Ubuntu somente leitura; sem comando de servico mutavel.
>>"%LOG_FILE%" echo Comando remoto sanitizado: validacao Ubuntu somente leitura; sem comando de servico mutavel.
1>>"%LOG_FILE%" "%SSH_TOOL%" -p "%PORT%" "%USER%@%HOST%" "set -e; test -d '%REMOTE_APP_DIR%'; test -d '%REMOTE_BACKEND_DIR%'; test -d '%REMOTE_STATIC_DIR%'; test -d '%REMOTE_BAILEYS_DIR%'; test '%REMOTE_APP_DIR%' != '/'; command -v %REMOTE_TAR_TOOL% >/dev/null; command -v %REMOTE_HASH_TOOL% >/dev/null; command -v python3 >/dev/null; command -v node >/dev/null; command -v npm >/dev/null; node --version; npm --version; node -e ""const major=Number(process.versions.node.split('.')[0]); if(major < 20){ console.error('NODE_VERSION_LT_20'); process.exit(20) }""; test -f '%REMOTE_BAILEYS_DIR%/package.json'; if test -f '%REMOTE_BAILEYS_DIR%/.env'; then echo BAILEYS_ENV_PRESENT; else echo BAILEYS_ENV_NOT_FOUND; fi; if test -d '%REMOTE_BAILEYS_DIR%/auth_info_baileys'; then echo BAILEYS_AUTH_DIR_PRESENT; else echo BAILEYS_AUTH_DIR_NOT_FOUND; fi; systemctl is-active menina; df -h '%REMOTE_APP_DIR%'; echo REMOTE_READONLY_OK"
if errorlevel 1 goto :fail

echo Comando remoto sanitizado: criar somente staging temporario; sem aplicacao ativa.
>>"%LOG_FILE%" echo Comando remoto sanitizado: criar somente staging temporario; sem aplicacao ativa.
1>>"%LOG_FILE%" "%SSH_TOOL%" -p "%PORT%" "%USER%@%HOST%" "set -e; mkdir -p '%REMOTE_RUN_DIR%'; echo STAGING_DIR_OK"
if errorlevel 1 goto :fail
1>>"%LOG_FILE%" "%SCP_TOOL%" -P "%PORT%" "%ZIP_NAME%" "%REMOTE_STAGE_SCRIPT%" "%REMOTE_CLEANUP_SCRIPT%" "%USER%@%HOST%:%REMOTE_RUN_DIR%/"
if errorlevel 1 goto :fail

echo Comando remoto sanitizado: validar checksum, extrair pacote e testar Baileys apenas no staging.
>>"%LOG_FILE%" echo Comando remoto sanitizado: validar checksum, extrair pacote e testar Baileys apenas no staging.
1>>"%LOG_FILE%" "%SSH_TOOL%" -p "%PORT%" "%USER%@%HOST%" "python3 -c ""from pathlib import Path; p=Path('%REMOTE_RUN_DIR%/%REMOTE_STAGE_SCRIPT_NAME%'); p.write_bytes(p.read_bytes().replace(b'\r\n', b'\n'))""; REMOTE_RUN_DIR='%REMOTE_RUN_DIR%' REMOTE_BAILEYS_DIR='%REMOTE_BAILEYS_DIR%' ZIP_NAME='%ZIP_NAME%' EXPECTED_SHA='%EXPECTED_SHA%' REMOTE_UNZIP_TOOL='%REMOTE_UNZIP_TOOL%' REMOTE_HASH_TOOL='%REMOTE_HASH_TOOL%' bash '%REMOTE_RUN_DIR%/%REMOTE_STAGE_SCRIPT_NAME%'"
if errorlevel 1 goto :fail

echo Comando remoto sanitizado: remover somente staging temporario criado por este DRY_RUN.
>>"%LOG_FILE%" echo Comando remoto sanitizado: remover somente staging temporario criado por este DRY_RUN.
1>>"%LOG_FILE%" "%SSH_TOOL%" -p "%PORT%" "%USER%@%HOST%" "RUN_DIR='%REMOTE_RUN_DIR%' BASE_DIR='%REMOTE_STAGING_DIR%' PREFIX='run_%VERSION_COMMIT%_' bash '%REMOTE_RUN_DIR%/%REMOTE_CLEANUP_SCRIPT_NAME%'"
if errorlevel 1 goto :fail

echo DRY_RUN remoto concluido. Nenhuma alteracao funcional foi feita na aplicacao ativa.
>>"%LOG_FILE%" echo DRY_RUN remoto concluido. Nenhuma alteracao funcional foi feita na aplicacao ativa.
exit /b 0

:apply_real
if not "%REMOTE_SERVICE_RESTART%"=="systemctl restart menina" (
  echo ERRO: REMOTE_SERVICE_RESTART deve ser exatamente: systemctl restart menina
  >>"%LOG_FILE%" echo ERRO: REMOTE_SERVICE_RESTART deve ser exatamente: systemctl restart menina
  exit /b 1
)
if "%HEALTHCHECK_URL%"=="" (
  echo ERRO: HEALTHCHECK_URL deve estar configurado para o modo --apply.
  >>"%LOG_FILE%" echo ERRO: HEALTHCHECK_URL vazio no modo --apply.
  exit /b 1
)
echo.
choice /C SN /N /M "Confirmar atualizacao REAL no servidor usando scp/ssh? [S/N]: "
if errorlevel 2 (
  echo Atualizacao real cancelada pelo operador.
  >>"%LOG_FILE%" echo Atualizacao real cancelada pelo operador.
  exit /b 2
)
echo.
echo  ATENCAO:
echo   - Baileys em producao sera mantido em 6.7.23.
echo   - Nenhum npm install sera executado em %REMOTE_BAILEYS_DIR%.
echo   - .env, bancos, uploads, backups, logs, auth_info_baileys e app-updates serao preservados.
echo   - O snapshot completo nao sera tocado por este fluxo.
echo.
>>"%LOG_FILE%" echo APPLY confirmado pelo operador.
>>"%LOG_FILE%" echo Baileys em producao mantido em 6.7.23 - nenhuma alteracao aplicada.

echo Validacao remota somente leitura antes do APPLY.
>>"%LOG_FILE%" echo Validacao remota somente leitura antes do APPLY.
1>>"%LOG_FILE%" "%SSH_TOOL%" -p "%PORT%" "%USER%@%HOST%" "set -e; test -d '%REMOTE_APP_DIR%'; test -d '%REMOTE_BACKEND_DIR%'; test -d '%REMOTE_STATIC_DIR%'; test '%REMOTE_APP_DIR%' != '/'; test '%REMOTE_APP_DIR%' != '$HOME'; test -d '%REMOTE_BAILEYS_DIR%'; test -f '%REMOTE_BAILEYS_DIR%/package.json'; test -f '%REMOTE_BAILEYS_DIR%/.env'; test -d '%REMOTE_BAILEYS_DIR%/auth_info_baileys'; command -v %REMOTE_TAR_TOOL% >/dev/null; command -v %REMOTE_HASH_TOOL% >/dev/null; command -v python3 >/dev/null; systemctl is-active menina; echo APPLY_REMOTE_READONLY_OK"
if errorlevel 1 goto :fail

echo Criando staging temporario para APPLY.
>>"%LOG_FILE%" echo Criando staging temporario para APPLY.
1>>"%LOG_FILE%" "%SSH_TOOL%" -p "%PORT%" "%USER%@%HOST%" "set -e; mkdir -p '%REMOTE_RUN_DIR%'; echo APPLY_STAGING_DIR_OK"
if errorlevel 1 goto :fail

echo Enviando ZIP e scripts de APPLY para staging.
>>"%LOG_FILE%" echo Enviando ZIP e scripts de APPLY para staging.
1>>"%LOG_FILE%" "%SCP_TOOL%" -P "%PORT%" "%ZIP_NAME%" "%REMOTE_APPLY_SCRIPT%" "%REMOTE_CLEANUP_SCRIPT%" "%USER%@%HOST%:%REMOTE_RUN_DIR%/"
if errorlevel 1 goto :fail

echo Executando APPLY remoto controlado com backup e rollback automatico.
>>"%LOG_FILE%" echo Executando APPLY remoto controlado com backup e rollback automatico.
1>>"%LOG_FILE%" "%SSH_TOOL%" -p "%PORT%" "%USER%@%HOST%" "python3 -c ""from pathlib import Path; base=Path('%REMOTE_RUN_DIR%'); [ (base/name).write_bytes((base/name).read_bytes().replace(b'\r\n', b'\n')) for name in ('%REMOTE_APPLY_SCRIPT_NAME%','%REMOTE_CLEANUP_SCRIPT_NAME%') ]""; REMOTE_RUN_DIR='%REMOTE_RUN_DIR%' REMOTE_APP_DIR='%REMOTE_APP_DIR%' REMOTE_BACKUP_FILE='%REMOTE_BACKUP_FILE%' ZIP_NAME='%ZIP_NAME%' EXPECTED_SHA='%EXPECTED_SHA%' REMOTE_UNZIP_TOOL='%REMOTE_UNZIP_TOOL%' REMOTE_HASH_TOOL='%REMOTE_HASH_TOOL%' APP_FILES='%APP_FILES%' REMOTE_SERVICE_RESTART='%REMOTE_SERVICE_RESTART%' HEALTHCHECK_URL='%HEALTHCHECK_URL%' bash '%REMOTE_RUN_DIR%/%REMOTE_APPLY_SCRIPT_NAME%'"
if errorlevel 1 goto :fail

echo Limpando somente staging temporario do APPLY.
>>"%LOG_FILE%" echo Limpando somente staging temporario do APPLY.
1>>"%LOG_FILE%" "%SSH_TOOL%" -p "%PORT%" "%USER%@%HOST%" "RUN_DIR='%REMOTE_RUN_DIR%' BASE_DIR='%REMOTE_STAGING_DIR%' PREFIX='run_%VERSION_COMMIT%_' bash '%REMOTE_RUN_DIR%/%REMOTE_CLEANUP_SCRIPT_NAME%'"
if errorlevel 1 goto :fail

echo APPLY concluido com sucesso. Baileys em producao mantido em 6.7.23.
>>"%LOG_FILE%" echo APPLY concluido com sucesso. Baileys em producao mantido em 6.7.23.
exit /b 0

:fail
>>"%LOG_FILE%" echo ERRO: etapa falhou ou foi interrompida. Nenhuma aplicacao ativa deve ter sido alterada por este fluxo.
echo.
echo  ============================================================
echo   ERRO: atualizacao refatorada nao concluida.
echo   Consulte o log: %LOG_FILE%
echo  ============================================================
echo.
exit /b 1
