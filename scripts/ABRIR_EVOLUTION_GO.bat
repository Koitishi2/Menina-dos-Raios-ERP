@echo off
setlocal EnableExtensions

set "SERVER=root@2.24.124.76"
set "SSH_PORT=22"
set "LOCAL_PORT=18766"
set "MANAGER_URL=http://localhost:18766/manager/login"
set "HEALTH_URL=http://127.0.0.1:18766/server/ok"
set "LOG_DIR=%~dp0..\logs_evolution_go"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1
for /f %%I in ('powershell.exe -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "RUN_ID=%%I"
set "LOCAL_LOG=%LOG_DIR%\manager_%RUN_ID%.log"

where ssh.exe >nul 2>&1
if errorlevel 1 (
    echo ERRO: ssh.exe nao encontrado. Ative o OpenSSH Client do Windows.
    pause
    exit /b 1
)

echo [%date% %time%] INICIO run=%RUN_ID%>>"%LOCAL_LOG%"
echo Verificando se o Evolution GO ja esta acessivel nesta porta...
powershell.exe -NoProfile -Command "$ErrorActionPreference='SilentlyContinue'; try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 '%HEALTH_URL%'; if ($r.StatusCode -eq 200 -and $r.Content -match 'status') { exit 0 } } catch {}; exit 1"
if errorlevel 1 (
    echo [%date% %time%] TUNNEL=starting>>"%LOCAL_LOG%"
    echo Abrindo SSH. Digite a senha quando solicitada e mantenha a janela aberta.
    start "Evolution GO - conexao e log" /D "%~dp0" "%ComSpec%" /d /k EVOLUTION_GO_CONEXAO.bat
) else (
    echo [%date% %time%] TUNNEL=already_responding>>"%LOCAL_LOG%"
    echo A porta local ja responde. Abrindo monitor remoto do Evolution GO.
    start "Evolution GO - log" /D "%~dp0" "%ComSpec%" /d /k EVOLUTION_GO_MONITOR.bat
)

echo Aguardando resposta do servidor (ate 90 segundos)...
powershell.exe -NoProfile -Command "$limit=(Get-Date).AddSeconds(90); do { try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 '%HEALTH_URL%'; if ($r.StatusCode -eq 200 -and $r.Content -match 'status') { exit 0 } } catch {}; Start-Sleep -Seconds 1 } while ((Get-Date) -lt $limit); exit 1"
if errorlevel 1 (
    echo [%date% %time%] HEALTH=failed>>"%LOCAL_LOG%"
    echo ERRO: o servidor nao respondeu pelo tunel.
    echo Veja a janela SSH: erro de senha, conexao ou encaminhamento aparecera la.
    echo Log local: %LOCAL_LOG%
    echo Log remoto: /root/evolution-go-manager.log
    pause
    exit /b 1
)

echo [%date% %time%] HEALTH=ok>>"%LOCAL_LOG%"
echo [%date% %time%] MANAGER=open>>"%LOCAL_LOG%"
echo Conexao OK. Abrindo Manager; faca uma tentativa de login.
echo A janela SSH mostra os logs completos e os grava no servidor.
echo Log remoto: /root/evolution-go-manager.log
echo Log local: %LOCAL_LOG%
start "" "%MANAGER_URL%"
exit /b 0
