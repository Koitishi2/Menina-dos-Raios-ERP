@echo off
setlocal
title Rodar Parte 2 - Aplicar Migracao Produtos
color 0C

set "REMOTE_USER=root"
set "REMOTE_HOST=2.24.124.76"
set "REMOTE_SCRIPT=/opt/menina/scripts_migracao_produtos/parte2_aplicar_migracao.sh"

echo.
echo  ============================================================
echo   Rodar PARTE 2 - Aplicar migracao de produtos
echo  ============================================================
echo.
echo  ATENCAO:
echo  Esta etapa pode ALTERAR dados do bm_monteiro.db.
echo  Rode somente se a PARTE 1 ja foi revisada e aprovada.
echo.
echo  O script ainda fara travas de seguranca:
echo   - compara o banco ativo com o snapshot da parte 1;
echo   - aborta se o banco mudou depois do diagnostico;
echo   - exige confirmacao manual exata no terminal remoto;
echo   - usa transacao unica com rollback em erro.
echo.
echo  Confirmacao exigida pelo script remoto:
echo   APLICAR MIGRACAO PRODUTOS
echo.
echo  Se houver usuarios usando o sistema agora, cancele.
echo.
pause

echo.
echo  Executando PARTE 2 no servidor...
echo.

ssh %REMOTE_USER%@%REMOTE_HOST% "set -e; SCRIPT='%REMOTE_SCRIPT%'; if [ ! -x \"$SCRIPT\" ]; then echo 'ERRO: script parte 2 nao encontrado ou sem permissao:' \"$SCRIPT\"; exit 1; fi; CANDIDATES='/opt/menina/bm_monteiro.db /opt/menina/backend/bm_monteiro.db /opt/menina/data/bm_monteiro.db'; FOUND=''; COUNT=0; for DB in $CANDIDATES; do if [ -f \"$DB\" ]; then FOUND=\"$FOUND $DB\"; COUNT=$((COUNT+1)); fi; done; if [ \"$COUNT\" -eq 0 ]; then echo 'ERRO: bm_monteiro.db nao encontrado nos caminhos comuns.'; echo 'Procure manualmente com: find /opt/menina -name bm_monteiro.db -type f'; exit 2; fi; if [ \"$COUNT\" -gt 1 ]; then echo 'ERRO: mais de um bm_monteiro.db encontrado:'; for DB in $FOUND; do echo ' -' \"$DB\"; done; echo 'Rode manualmente a parte 2 com o caminho correto.'; exit 3; fi; DB_PATH=$(echo $FOUND | xargs); echo 'Banco encontrado:' \"$DB_PATH\"; echo; \"$SCRIPT\" \"$DB_PATH\""
if errorlevel 1 goto :erro

echo.
echo  ============================================================
echo   Parte 2 concluida.
echo  ============================================================
echo.
echo  Copie o resultado acima e cole aqui para eu conferir a validacao POS.
echo.
pause
exit /b 0

:erro
echo.
echo  ============================================================
echo   ERRO: a parte 2 nao foi concluida.
echo   Se o script abortou antes de BEGIN/UPDATE, nenhum dado foi alterado.
echo   Se houve falha durante a transacao, o script solicitou ROLLBACK.
echo  ============================================================
echo.
pause
exit /b 1
