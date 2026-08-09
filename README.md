# Menina dos Raios ERP

Sistema de gestão de vendas, entregas, boletos, notas, orçamentos, pagamentos e WhatsApp para as operações Menina dos Raios, Menina da Estrada e Monteiro.

O projeto principal roda com **FastAPI + SQLite + frontend vanilla em HTML/JS**. A interface atual fica em `backend/static/index.html` e é servida pelo próprio backend.

## Estado Atual

- Backend principal: `backend/app.py`
- Modelos Pydantic extraídos: `backend/schemas.py`
- Helpers puros extraídos: `backend/utils.py`
- Frontend principal: `backend/static/index.html`
- Banco SQLite local principal: `backend/bm_monteiro.db`
- Testes de caracterização: `tests/`
- Scripts de migração controlada de produtos: `scripts_migracao_produtos/`

As rotas, SQL, schema e regras de negócio foram preservados durante a refatoração inicial. A suíte local validada chegou a `84 passed` após a inclusão dos testes de `_normalize_name()`.

## Requisitos

- Python 3.10 ou superior
- Windows PowerShell ou Prompt de Comando
- Dependências Python listadas em `backend/requirements.txt`

## Uso Local

Na primeira configuração:

```bat
CONFIGURAR.bat
```

Para iniciar o sistema local:

```bat
INICIAR.bat
```

Endereço local padrão:

```text
http://localhost:8765
```

Login padrão em banco novo:

```text
admin / admin123
```

Altere a senha após o primeiro acesso.

## Estrutura

```text
bm_app/
├── backend/
│   ├── app.py                 # FastAPI, rotas e regras principais
│   ├── schemas.py             # Modelos Pydantic extraídos
│   ├── utils.py               # Helpers puros extraídos
│   ├── requirements.txt
│   ├── bm_monteiro.db         # Banco SQLite local
│   ├── monteiro_notas/        # Arquivos/anexos locais de notas
│   └── static/
│       ├── index.html         # Frontend principal
│       ├── assets/
│       └── app-updates/
├── tests/                     # Testes de caracterização e regressão
├── scripts_migracao_produtos/ # Scripts seguros de migração de grafias
├── baileys-api/               # Integração WhatsApp local/auxiliar
├── frontend/                  # Código frontend legado/auxiliar
├── ATUALIZAR.bat              # Deploy manual para VPS
├── CONFIGURAR.bat
├── INICIAR.bat
└── changelog.txt
```

## Módulos Cobertos

- Autenticação e sessões
- Permissões e configurações
- Vendas
- Clientes
- Produtos e preços
- Entregadores e veículos
- Boletos
- Notas e entregas
- Avarias
- Pagamentos
- Monteiro/Paladar
- Orçamentos
- Calendário e notificações
- WhatsApp
- Importação Excel

## Testes

Os testes usam banco temporário e bloqueiam serviços externos. Não devem usar bancos reais.

Venv local utilizado nas últimas validações:

```text
C:\Users\adria\AppData\Local\Temp\bm_app_fase2_test_venv_codexpy
```

Comandos úteis:

```bat
python -m py_compile backend\app.py backend\schemas.py backend\utils.py
pytest -q tests
python -X faulthandler -m pytest -q -p no:cacheprovider tests
```

Para rodar pelo venv temporário aprovado:

```bat
C:\Users\adria\AppData\Local\Temp\bm_app_fase2_test_venv_codexpy\Scripts\python.exe -X faulthandler -m pytest -q -p no:cacheprovider tests
```

## Produção

Servidor atual:

```text
Hostinger VPS
Diretório: /opt/menina/backend/
Serviço systemd: menina
```

Deploy manual:

```bat
ATUALIZAR.bat
```

Use deploy somente após testes locais. Não substitua arquivos `.db` de produção com cópia manual enquanto o sistema estiver rodando.

## Migração de Produtos

Os scripts em `scripts_migracao_produtos/` foram criados para migração controlada de grafias de produtos com mojibake histórico.

Fluxo seguro:

1. Enviar scripts ao servidor.
2. Rodar somente a parte 1 de diagnóstico.
3. Conferir contagens.
4. Rodar parte 2 apenas após aprovação.

Os scripts não devem ser executados automaticamente por deploy.

## Backups e Dados

Arquivos `.db` são dados sensíveis. Não copie nem sobrescreva banco ativo sem janela de manutenção e backup consistente via SQLite.

Backups antigos e arquivos `.bak` duplicados foram removidos do projeto para reduzir ruído. O Git deve conter somente código, scripts necessários e artefatos realmente usados.

## Regras de Segurança do Projeto

- Não usar banco de produção em testes.
- Não enviar WhatsApp real em testes.
- Não executar migração sem diagnóstico.
- Não fazer `git add .` sem revisar o status.
- Não alterar `backend/app.py` e `backend/static/index.html` fora do escopo aprovado.
- Manter o `changelog.txt` atualizado em correções funcionais.

## Git

Antes de commitar:

```bat
git status --short
git diff --stat
git diff --check
```

Evite commitar:

- `.env`
- `__pycache__`
- `.pytest_cache`
- bancos `.db` novos
- backups temporários
- diretórios de migração descartáveis

## Observações

O código ainda está em processo de refatoração gradual. A estratégia atual é extrair pequenas partes com testes antes, mantendo comportamento e contratos existentes.
