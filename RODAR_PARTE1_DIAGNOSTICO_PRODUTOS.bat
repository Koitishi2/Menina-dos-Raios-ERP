@echo off
setlocal
title Rodar Parte 1 - Diagnostico Produtos
color 0A

set "REMOTE_USER=root"
set "REMOTE_HOST=2.24.124.76"
set "REMOTE_SCRIPT=/opt/menina/scripts_migracao_produtos/parte1_backup_e_diagnostico.sh"

echo.
echo  ============================================================
echo   Rodar PARTE 1 - Backup e diagnostico de produtos
echo  ============================================================
echo.
echo  Esta etapa cria backup seguro e gera diagnostico.
echo  Ela NAO executa a migracao.
echo  Ela NAO altera dados.
echo  Ela NAO reinicia o sistema.
echo.
echo  O script tentara localizar o bm_monteiro.db nos caminhos comuns.
echo  Se encontrar mais de um ou nenhum, ele para sem rodar.
echo.
pause

echo.
echo  Executando diagnostico no servidor...
echo.

ssh %REMOTE_USER%@%REMOTE_HOST% "set -e; SCRIPT='%REMOTE_SCRIPT%'; if [ ! -x \"$SCRIPT\" ]; then echo 'ERRO: script parte 1 nao encontrado ou sem permissao:' \"$SCRIPT\"; exit 1; fi; CANDIDATES='/opt/menina/bm_monteiro.db /opt/menina/backend/bm_monteiro.db /opt/menina/data/bm_monteiro.db'; FOUND=''; COUNT=0; for DB in $CANDIDATES; do if [ -f \"$DB\" ]; then FOUND=\"$FOUND $DB\"; COUNT=$((COUNT+1)); fi; done; if [ \"$COUNT\" -eq 0 ]; then echo 'ERRO: bm_monteiro.db nao encontrado nos caminhos comuns.'; echo 'Procure manualmente com: find /opt/menina -name bm_monteiro.db -type f'; exit 2; fi; if [ \"$COUNT\" -gt 1 ]; then echo 'ERRO: mais de um bm_monteiro.db encontrado:'; for DB in $FOUND; do echo ' -' \"$DB\"; done; echo 'Rode manualmente a parte 1 com o caminho correto.'; exit 3; fi; DB_PATH=$(echo $FOUND | xargs); echo 'Banco encontrado:' \"$DB_PATH\"; echo; \"$SCRIPT\" \"$DB_PATH\""
if errorlevel 1 goto :erro

echo.
echo  ============================================================
echo   Parte 1 concluida.
echo  ============================================================
echo.
echo  Copie o resultado acima e cole aqui para eu conferir.
echo  NAO rode a parte 2 ainda.
echo.
pause
exit /b 0

:erro
echo.
echo  ============================================================
echo   ERRO: a parte 1 nao foi concluida.
echo   Nenhuma migracao foi executada.
echo  ============================================================
echo.
pause
exit /b 1
