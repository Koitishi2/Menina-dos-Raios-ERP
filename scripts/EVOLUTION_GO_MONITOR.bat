@echo off
setlocal
set "SERVER=root@2.24.124.76"
set "SSH_PORT=22"

echo Conectando ao monitor remoto do Evolution GO...
ssh.exe -tt -p %SSH_PORT% %SERVER% "umask 077; touch /root/evolution-go-manager.log; chmod 600 /root/evolution-go-manager.log; echo '--- monitor Evolution GO iniciado ---' | tee -a /root/evolution-go-manager.log; podman logs --follow --since 5m menina-evolution-go 2>&1 | tee -a /root/evolution-go-manager.log"
echo.
echo SSH encerrou com codigo %errorlevel%. Esta janela fica aberta para mostrar o motivo.
pause
