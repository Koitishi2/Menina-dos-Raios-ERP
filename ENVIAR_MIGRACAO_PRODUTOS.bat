@echo off
setlocal
title Enviar scripts de migracao de produtos
color 0A

set "ROOT_DIR=%~dp0"
set "SCRIPT_DIR=%ROOT_DIR%scripts_migracao_produtos"
set "REMOTE_USER=root"
set "REMOTE_HOST=2.24.124.76"
set "REMOTE_DIR=/opt/menina/scripts_migracao_produtos"

echo.
echo  ============================================================
echo   Enviar scripts de migracao de produtos
echo  ============================================================
echo.
echo  Este BAT apenas envia os arquivos para o servidor.
echo  Ele NAO executa a parte 1, NAO executa a parte 2,
echo  NAO altera banco de dados e NAO reinicia o sistema.
echo.

if not exist "%SCRIPT_DIR%\parte1_backup_e_diagnostico.sh" (
  echo  ERRO: parte1_backup_e_diagnostico.sh nao encontrado.
  echo  Pasta esperada: %SCRIPT_DIR%
  goto :erro
)

if not exist "%SCRIPT_DIR%\parte2_aplicar_migracao.sh" (
  echo  ERRO: parte2_aplicar_migracao.sh nao encontrado.
  echo  Pasta esperada: %SCRIPT_DIR%
  goto :erro
)

where ssh >nul 2>nul
if errorlevel 1 (
  echo  ERRO: comando ssh nao encontrado no Windows.
  goto :erro
)

where scp >nul 2>nul
if errorlevel 1 (
  echo  ERRO: comando scp nao encontrado no Windows.
  goto :erro
)

echo  Arquivos que serao enviados:
echo   - %SCRIPT_DIR%\parte1_backup_e_diagnostico.sh
echo   - %SCRIPT_DIR%\parte2_aplicar_migracao.sh
echo.
echo  Destino:
echo   - %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
echo.
pause

echo.
echo  [1/4] Criando pasta no servidor...
ssh %REMOTE_USER%@%REMOTE_HOST% "mkdir -p %REMOTE_DIR%"
if errorlevel 1 goto :erro

echo.
echo  [2/4] Enviando parte 1...
scp "%SCRIPT_DIR%\parte1_backup_e_diagnostico.sh" %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%/
if errorlevel 1 goto :erro

echo.
echo  [3/4] Enviando parte 2...
scp "%SCRIPT_DIR%\parte2_aplicar_migracao.sh" %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%/
if errorlevel 1 goto :erro

echo.
echo  [4/4] Aplicando permissao de execucao e conferindo arquivos...
ssh %REMOTE_USER%@%REMOTE_HOST% "chmod 700 %REMOTE_DIR%/parte1_backup_e_diagnostico.sh %REMOTE_DIR%/parte2_aplicar_migracao.sh && ls -lh %REMOTE_DIR%"
if errorlevel 1 goto :erro

echo.
echo  ============================================================
echo   Scripts enviados com sucesso.
echo  ============================================================
echo.
echo  Proximo passo manual:
echo   1. Entre no servidor por SSH.
echo   2. Localize o caminho real do bm_monteiro.db.
echo   3. Rode primeiro APENAS a parte 1 para diagnostico.
echo   4. Cole aqui o resultado antes de rodar a parte 2.
echo.
pause
exit /b 0

:erro
echo.
echo  ============================================================
echo   ERRO: envio nao concluido.
echo   Nenhuma migracao foi executada por este BAT.
echo  ============================================================
echo.
pause
exit /b 1
