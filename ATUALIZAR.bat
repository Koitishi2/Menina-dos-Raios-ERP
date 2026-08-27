@echo off
title Menina dos Raios — Atualizando...
color 0A

echo.
echo  ============================================================
echo   Menina dos Raios Ltda - Atualizacao do Sistema
echo  ============================================================
echo.
echo  Voce precisara digitar a senha do servidor 4 vezes.
echo  Senha: (a senha root que voce criou na Hostinger)
echo.
pause

cd /d "%~dp0"

echo.
echo  [1/4] Enviando rbac.py...
scp backend\rbac.py root@2.24.124.76:/opt/menina/backend/rbac.py
if errorlevel 1 goto :erro

echo.
echo  [2/4] Enviando app.py...
scp backend\app.py root@2.24.124.76:/opt/menina/backend/
if errorlevel 1 goto :erro

echo.
echo  [3/4] Enviando interface (index.html)...
scp backend\static\index.html root@2.24.124.76:/opt/menina/backend/static/
if errorlevel 1 goto :erro

echo.
echo  [4/4] Reiniciando sistema...
ssh root@2.24.124.76 "systemctl restart menina && sleep 2 && systemctl is-active menina && echo SISTEMA_OK"
if errorlevel 1 goto :erro

echo.
echo  ============================================================
echo   Pronto! Acesse: https://sistema.meninadosraios.com.br
echo  ============================================================
echo.
choice /C SN /N /M "Deseja publicar tambem o APK do aplicativo? [S/N]: "
if errorlevel 2 goto :fim
if exist "%~dp0PUBLICAR_APK.bat" call "%~dp0PUBLICAR_APK.bat"
if not exist "%~dp0PUBLICAR_APK.bat" echo ERRO: PUBLICAR_APK.bat nao encontrado.

:fim
echo.
pause
exit /b 0

:erro
echo.
echo  ============================================================
echo   ERRO: a atualizacao nao foi concluida.
echo   Veja a mensagem acima para identificar a etapa que falhou.
echo  ============================================================
echo.
pause
exit /b 1
