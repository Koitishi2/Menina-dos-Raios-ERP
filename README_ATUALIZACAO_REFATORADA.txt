# Atualizacao da Versao Estavel

Pacote esperado: `bm_app_refatorado_f4c02b4_r3.zip`
Checkpoint de codigo: `f4c02b4`
Branch publica: `main`

## Importante

O arquivo `atualizarrefatorado.bat` usa o mesmo metodo operacional comprovado
pelo atualizador legado: transferencia por `scp` e comandos remotos por `ssh`.
Ele foi adaptado para trabalhar com o pacote refatorado e para preservar dados
persistentes.

O script continua seguro por padrao.
Ele nasce com:

- `DRY_RUN=1`;
- configuracao remota em variaveis no inicio do arquivo;
- senha solicitada pelas ferramentas `ssh`/`scp`, sem ser gravada no script.

Em `DRY_RUN=1`, o script valida ZIP, checksum, ferramentas locais e exibe o
plano. Ele nao inicia conexao externa, nao copia arquivos, nao extrai pacote,
nao reinicia servico e nao altera o servidor.

## Variaveis que precisam ser confirmadas

Copiar o exemplo local e preencher somente no computador autorizado:

```bat
copy atualizarrefatorado.local.example.bat atualizarrefatorado.local.bat
```

O arquivo `atualizarrefatorado.local.bat` e ignorado pelo Git e nao deve ser
publicado.

Revisar nesse arquivo local:

- `HOST`;
- `PORT`;
- `USER`;
- `REMOTE_APP_DIR`;
- `REMOTE_STAGING_DIR`;
- `REMOTE_BACKUP_DIR`;
- `HEALTHCHECK_URL`, se houver endpoint confirmado;
- comando de reinicio, somente se o procedimento for documentado e autorizado.

Nao coloque senhas, tokens, chaves privadas, certificados ou dados reais no
script, no ZIP, no README ou no Git.

## Ferramentas esperadas

No computador que executara o `.bat`:

- PowerShell;
- `ssh`;
- `scp`.

No servidor, somente depois de confirmado pelo operador:

- shell compativel;
- `sha256sum`;
- `tar`;
- Python 3 para extrair o ZIP via `python3 -m zipfile`.
- Node.js 20 ou superior;
- npm.

Se qualquer ferramenta nao existir, nao continue sem adaptar e revisar o
procedimento.

## Dados preservados

O pacote e o script foram desenhados para nao substituir:

- `.env`;
- bancos SQLite ou dumps;
- diretorios `database`, `databases` ou `data`;
- uploads;
- backups;
- logs;
- storage/media/instance;
- certificados, chaves, tokens ou arquivos enviados por usuarios.

## Como validar antes de aplicar

1. Conferir o checksum:

```bat
type CHECKSUM_REFATORADO_SHA256.txt
```

2. Revisar o conteudo do ZIP antes de enviar.

3. Executar o script sem parametros. O resultado esperado inicial e somente
   simulacao local, sem `ssh` e sem `scp`.

4. Revisar o plano que o modo `DRY_RUN=1` imprime e confirmar que nenhum item
   persistente sera tocado.

5. Para validar staging remoto sem aplicar a atualizacao ativa, usar:

```bat
atualizarrefatorado.bat --remote-dry-run
```

Esse modo pode criar e remover somente um diretorio temporario de staging da
propria execucao. Ele nao substitui arquivos da aplicacao, nao reinicia servico
e nao executa migracao.

O modo remoto tambem valida o componente `baileys-api` em staging. Ele copia o
diretorio ativo para a area temporaria, preservando `.env` e sessao/autenticacao
existentes, aplica apenas no staging:

```bat
npm install github:WhiskeySockets/Baileys
```

e registra versoes de Node/npm, dependencia resolvida, lockfile e commit quando
disponivel. Essa etapa exige Node.js 20 ou superior e nao inicia o servico, nao
gera QR code e nao envia mensagens.

6. Somente depois de validado, usar:

```bat
atualizarrefatorado.bat --apply
```

O script ainda pedira confirmacao interativa antes da atualizacao real.

## Backup e rollback

O script cria, quando executado de verdade, um backup remoto somente dos
arquivos da aplicacao que seriam substituidos. O backup exclui dados
persistentes e deve ser mantido ate a validacao final.

Rollback deve restaurar somente os arquivos da aplicacao a partir desse backup.
Nao restaurar banco, uploads, logs, backups ou `.env` por esse fluxo.

No modo real, se uma etapa de copia, reinicio ou validacao falhar depois do
backup, o script tenta rollback automatico controlado usando apenas o pacote de
backup gerado na mesma execucao. Se o rollback tambem falhar, o backup e
preservado para restauracao manual auditavel.

Para restauracao completa de um snapshot pre-refatoracao, use
`rollbackrefatorado.bat`. Ele tambem inicia em DRY_RUN, exige `--apply`, exige o
nome exato do snapshot e valida SHA-256 antes da restauracao. Esse fluxo pode
restaurar codigo, `.env`, bancos, uploads, storage, media, data e demais
persistentes contidos no snapshot. Nao execute esse rollback sem janela
operacional e confirmacao explicita.

## Limitacoes

Este documento nao inclui endereco, usuario, porta, caminho remoto, servico de
producao, credenciais ou comandos privados. Esses detalhes ficam no arquivo
local ignorado pelo Git e precisam ser revisados antes de qualquer atualizacao
real.

Nenhum deploy, migracao, acesso a banco real ou chamada externa foi executado na
preparacao deste pacote.
