# Atualizacoes do servidor

O `ATUALIZAR.bat` cria uma release a partir do `HEAD` local, que precisa estar
commitado e publicado em uma branch remota. O pacote recebe o identificador do
commit, checksum e manifesto de arquivos. `/health` informa o commit ativo. O atualizador nao envia mudancas
locais sem commit.

## Comandos

```bat
ATUALIZAR.bat
ATUALIZAR.bat --remote-dry-run
ATUALIZAR.bat --apply
```

Sem argumento, o script valida e monta o pacote localmente, sem SSH/SCP. O
`--remote-dry-run` envia o pacote para staging e valida os arquivos sem parar os
servicos nem substituir o codigo ativo. O `--apply` aplica a release depois de
pedir confirmacao. O fluxo preserva bancos, `.env`, uploads, logs, `app-updates`
e a sessao do Baileys; o backup remoto contem os arquivos de codigo substituidos.

## Identificar uma falha

Cada execucao recebe um ID e grava um log em `logs_deploy/`. O log registra
branch, commit, pacote, SHA-256, arquivo de manifesto, fase atual e saida do SSH
e SCP. Se a execucao remota falhar, o staging fica no servidor e o atualizador
traz `deploy.log` e `deploy_status.log` para o log local. A mensagem final
mostra a fase que falhou e o caminho do staging que deve ser preservado.

Fases comuns: `GIT`, `PACKAGE`, `CONFIG`, `REMOTE-STAGING`, `SCP`,
`REMOTE-CHECKSUM`, `REMOTE-DRY-RUN`, `REMOTE-APPLY`, `HEALTHCHECK` e
`REMOTE-CLEANUP`.

O modo `--apply` exige `HEALTHCHECK_URL` HTTPS no arquivo local
`atualizarrefatorado.local.bat`. A rota `/health` responde JSON identificando o
servico; o deploy confere essa resposta depois do restart. Uma falha nessa
validacao ativa o rollback automatico de codigo.

O pacote e seus manifestos locais ficam em `backups/deploy_runs/<ID>/`. Nao
apague o staging remoto quando houver falha: ele contem a evidencia da
execucao. Para corrigir, use o ID no log para localizar a primeira fase com
erro e preserve o commit, pacote e checksum daquela tentativa.

## Publicar o APK

PUBLICAR_APK.bat usa por padrao o APK oficial dentro do repositorio. Para
publicar um APK recem-compilado em outro local, configure APK_SOURCE_PATH no
arquivo local atualizarrefatorado.local.bat ou passe -SourceApkPath ao
PowerShell. APP_UPDATES_DIR tambem pode ser configurado; o padrao e
backend/static/app-updates dentro deste repositorio.

O publicador grava um transcript em logs_apk_publicacao/ e informa a fase
que falhou. As fases distinguem configuracao, leitura/assinatura do APK,
metadados locais, backup remoto, envio e validacao. Apos o upload, o servidor
confere o SHA-256 do APK e os metadados de versao em latest.json.
