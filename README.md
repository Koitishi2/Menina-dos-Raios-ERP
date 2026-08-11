# Menina dos Raios ERP

Aplicacao de gestao operacional para vendas, entregas, boletos, notas, orcamentos, pagamentos, calendario e integracoes de comunicacao.

Versao atual do servidor: `2.0.0`

Este repositorio contem a versao refatorada estavel da aplicacao, encerrada no checkpoint `c180c81` (`remove: retire unused Excel import`) e implantada como versao de servidor `2.0.0`. O ciclo de refatoracao priorizou preservacao de contratos existentes, reducao de acoplamento e correcoes de ciclo de vida de conexoes e transacoes.

## Estado da Versao Refatorada

Dominios finalizados no ciclo atual:

- Notas APP;
- Calendario APP;
- WhatsApp;
- Boletos e Pagamentos;
- remocao da funcionalidade de Import Excel.

A funcionalidade de upload/importacao Excel foi removida por nao fazer mais parte do uso atual. Dados historicos, tabelas, compatibilidades e rotas auxiliares necessarias para registros antigos foram preservados quando aplicavel.

Deploy controlado concluido com pacote `bm_app_refatorado_c180c81.zip`, preservando configuracoes locais, bancos, uploads, logs, backups e sessoes de integracao. O componente WhatsApp/Baileys permanece no ciclo de producao validado com Baileys 6.7.x; Baileys 7 RC segue bloqueado para producao ate novo ciclo especifico.

## Qualidade e Validacao

A validacao final da versao refatorada registrou:

- `234 passed` na suite completa de testes;
- duas execucoes consecutivas bem-sucedidas;
- validacao de sintaxe dos modulos Python relevantes;
- verificacao de integridade com `git diff --check`.

Os testes usam ambiente temporario e bloqueiam chamadas externas reais quando aplicavel.

## Arquitetura Geral

O backend principal e baseado em FastAPI com persistencia SQLite. O frontend principal servido pela aplicacao fica em `backend/static/index.html`.

Modulos extraidos durante a refatoracao incluem:

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

## Pacote Refatorado

A distribuicao empacotada da versao estavel deve usar o nome:

```text
bm_app_refatorado_c180c81.zip
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
