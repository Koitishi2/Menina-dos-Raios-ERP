# Menina dos Raios ERP

Aplicacao de gestao operacional para vendas, entregas, boletos, notas, orcamentos, pagamentos, calendario e integracoes de comunicacao.

Versao atual do servidor: `2.0.0`

Este repositorio contem a versao estavel da aplicacao, mantida no checkpoint `88fef18` e implantada como versao de servidor `2.0.0`. O foco desta versao e manter os modulos atuais operando com seguranca, preservando contratos existentes, dados persistentes e integracoes em producao.

## Estado da Versao Estavel

Dominios finalizados no ciclo atual:

- Notas APP;
- Calendario APP;
- WhatsApp;
- Boletos e Pagamentos;
- remocao da funcionalidade de Import Excel.

A funcionalidade de upload/importacao Excel foi removida por nao fazer mais parte do uso atual. Dados historicos, tabelas, compatibilidades e rotas auxiliares necessarias para registros antigos foram preservados quando aplicavel.

Deploy controlado por pacote `.zip`, preservando configuracoes locais, bancos, uploads, logs, backups e sessoes de integracao. O componente WhatsApp/Baileys permanece no ciclo de producao validado com Baileys 6.7.x; Baileys 7 RC segue bloqueado para producao ate novo ciclo especifico.

## Qualidade e Validacao

A validacao da versao estavel registra:

- `234 passed` na suite completa de testes;
- duas execucoes consecutivas bem-sucedidas;
- validacao de sintaxe dos modulos Python relevantes;
- verificacao de integridade com `git diff --check`.

Os testes usam ambiente temporario e bloqueiam chamadas externas reais quando aplicavel.

## Arquitetura Geral

O backend principal e baseado em FastAPI com persistencia SQLite. O frontend principal servido pela aplicacao fica em `backend/static/index.html`.

Modulos internos da aplicacao incluem:

- `backend/app_notes_domain.py`;
- `backend/app_notes_service.py`;
- `backend/backup_admin.py`;
- `backend/company_config.py`;
- `backend/monteiro_periods.py`;
- `backend/monteiro_permissions.py`;
- `backend/orcamentos.py`;
- `backend/permissions_tabs.py`;
- `backend/security_auth.py`;
- `backend/security_request.py`;
- `backend/schemas.py`;
- `backend/utils.py`.

Rotas, infraestrutura de banco, autenticacao, autorizacao, migracoes e regras de negocio que dependem do contexto da aplicacao permanecem no backend principal.

## APK Android

Este repositorio tambem contempla o aplicativo Android interno **Menina dos Raios Vendas**. O app complementa o sistema web e e usado em operacoes de campo e rotinas moveis.

Em alto nivel, o aplicativo permite:

- montar pedidos no celular;
- enviar pedidos pelo fluxo integrado do sistema;
- consultar e informar entregas;
- usar o mesmo login e senha do sistema web;
- desbloquear o app com PIN local de 4 digitos apos o login inicial.

### Estrutura do app

O codigo-fonte do aplicativo Android fica no projeto `VendasWhatsApp/`.

O APK oficial compilado usa o nome padrao:

```text
Menina-dos-Raios-Vendas-OFICIAL.apk
```

O arquivo APK pode ou nao estar versionado no Git, conforme a politica operacional do ambiente. O item mais importante para manutencao e auditoria e o projeto Android fonte, pois o APK deve ser gerado a partir dele.

### Build e publicacao do APK

O APK deve ser compilado localmente com Android Studio ou Gradle, em uma maquina autorizada. A assinatura do aplicativo usa uma chave privada mantida apenas nas maquinas dos desenvolvedores autorizados.

Depois da compilacao e assinatura, o APK e publicado em um servidor de atualizacoes usado pelo proprio app. O projeto possui um script de publicacao, por exemplo `PUBLICAR_APK.bat`, que executa o fluxo operacional de alto nivel:

1. localiza o APK oficial gerado;
2. extrai `versionName`, `versionCode` e identificador do pacote;
3. calcula o hash SHA-256 do APK;
4. atualiza o catalogo de versao usado pelo app;
5. envia o APK e os metadados para o servidor de atualizacoes via SSH/SCP.

Detalhes de infraestrutura, como servidor, usuario, portas, caminhos remotos, provedor, senhas e chaves, nao devem aparecer no README nem ser versionados.

### Seguranca do APK

Nunca commitar:

- keystores ou certificados privados de assinatura;
- senhas de servidor;
- arquivos `.env`;
- configuracoes locais com dados de infraestrutura;
- scripts locais contendo segredos;
- tokens, chaves de API ou credenciais.

O `.gitignore` deve excluir arquivos sensiveis, como keystore, configuracoes locais privadas, bancos de dados, logs, backups, ambientes virtuais e artefatos temporarios. Caso um novo arquivo sensivel seja criado durante manutencao, ele deve ser incluido no `.gitignore` antes de qualquer commit.

### Uso pelo usuario final

O usuario final deve instalar o app apenas a partir de fonte confiavel, como o canal oficial interno da empresa ou link disponibilizado pela equipe responsavel.

Fluxo basico de uso:

1. baixar o APK oficial de fonte confiavel;
2. instalar no Android;
3. abrir o app;
4. fazer login com usuario e senha do sistema;
5. criar um PIN local de 4 digitos;
6. usar as funcionalidades disponiveis, como pedidos e entregas.

O PIN de 4 digitos e local do aparelho e nao substitui a senha do sistema web. Ele serve apenas para desbloquear o app apos o login inicial.

## Pacote de Atualizacao

A distribuicao empacotada da versao estavel deve usar o nome:

```text
bm_app_refatorado_88fef18.zip
```

O pacote publicado nao deve conter:

- credenciais, tokens, chaves privadas ou arquivos `.env`;
- bancos de dados locais ou dados persistentes;
- uploads, logs, caches, backups ou artefatos temporarios;
- ambientes virtuais ou `node_modules`;
- metadados Git.

O checksum SHA-256 deve ser publicado junto ao pacote quando o arquivo for disponibilizado.

## Atualizador Seguro

O arquivo `atualizarrefatorado.bat` e fornecido como modelo operacional
bloqueado por padrao. Ele deve iniciar em modo de simulacao e exigir
configuracao explicita antes de qualquer conexao externa.

O script nao deve conter credenciais, caminhos privados ou comandos de servico
na versao publica. Detalhes de infraestrutura devem ser preenchidos apenas por
operador autorizado em copia operacional local.

## Instalacao e Atualizacao

A implantacao deve ser feita somente por operador autorizado.

Fluxo generico recomendado:

1. Fazer backup consistente dos dados persistentes existentes.
2. Validar variaveis de ambiente e configuracoes fora do repositorio.
3. Conferir o checksum do pacote recebido.
4. Substituir apenas arquivos de aplicacao, preservando bancos, uploads, logs e configuracoes locais.
5. Executar validacoes de sintaxe e testes cabiveis antes de liberar uso.
6. Executar migracoes somente quando houver instrucao explicita e janela de manutencao aprovada.

Credenciais e configuracoes de producao devem ser fornecidas fora do repositorio e nunca devem ser versionadas.

## Uso Local

Requisitos gerais:

- Python 3.10 ou superior;
- dependencias Python listadas em `backend/requirements.txt`;
- ambiente com suporte a FastAPI e SQLite.

Comandos locais uteis:

```bat
python -m py_compile backend\app.py
python -X faulthandler -m pytest -q tests
```

Scripts operacionais incluidos no repositorio devem ser revisados antes de uso e executados apenas em ambiente autorizado.

## Seguranca e Privacidade

Este README publico evita expor detalhes de infraestrutura. Nao devem ser publicados:

- enderecos, dominios, hostnames ou portas de servidor;
- usuarios, senhas, tokens, chaves ou certificados;
- nomes de servicos de producao;
- caminhos locais ou remotos de ambientes privados;
- nomes de bancos, tenants, clientes reais ou dados persistentes;
- conteudo de arquivos de configuracao sensivel.

## Dados Persistentes

Arquivos de banco, uploads, logs e backups sao dados sensiveis e devem permanecer fora do pacote publico. A atualizacao da aplicacao deve preservar esses dados no ambiente de destino.

## Git

Antes de publicar alteracoes:

```bat
git status --short
git diff --stat
git diff --check
```

Nao use force push para publicar esta versao estavel.
