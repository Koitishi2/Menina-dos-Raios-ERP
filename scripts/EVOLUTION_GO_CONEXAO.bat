@echo off
setlocal
set "SERVER=root@2.24.124.76"
set "SSH_PORT=22"
set "LOCAL_PORT=18766"

echo Conectando por SSH e iniciando o log remoto...
ssh.exe -tt -o ExitOnForwardFailure=yes -L %LOCAL_PORT%:127.0.0.1:8766 -p %SSH_PORT% %SERVER% "umask 077; touch /root/evolution-go-manager.log; chmod 600 /root/evolution-go-manager.log; echo '--- monitor Evolution GO iniciado ---' | tee -a /root/evolution-go-manager.log; podman logs --follow --since 5m menina-evolution-go 2>&1 | tee -a /root/evolution-go-manager.log"
echo.
echo SSH encerrou com codigo %errorlevel%. Esta janela fica aberta para mostrar o motivo.
pause
