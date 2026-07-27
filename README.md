# 🌿 Menina dos Raios — Sistema de Vendas (Local + Produção)

Sistema de controle de vendas em **vanilla JS + FastAPI + SQLite**.
A interface inteira fica em `backend/static/index.html` (arquivo único,
servido pelo FastAPI). Sem build, sem Node, sem framework — direto ao ponto.

---

## Como usar localmente (Windows)

### Pré-requisito
- **Python 3.10+** — baixe em https://www.python.org/downloads/

### Instalação (uma vez só)

1. Extraia este ZIP numa pasta permanente (ex: `C:\Menina dos Raios\bm_app\`)
2. Duplo clique em **`CONFIGURAR.bat`** — instala as dependências Python
3. Pronto.

### Uso diário

**Duplo clique em `INICIAR.bat`**

O sistema abre em `http://localhost:8765`. Login padrão: `admin / admin123`
(altere após o primeiro acesso na aba **Registro**).

---

## Como atualizar a produção (Hostinger)

Após editar `backend/app.py` ou `backend/static/index.html` localmente,
duplo clique em **`ATUALIZAR.bat`**.

O script faz scp dos dois arquivos para `/opt/menina/backend/` na VPS
e reinicia o serviço `menina` via systemd. Acesso final:
`https://sistema.meninadosraios.com.br`

Você precisará digitar a senha root do servidor **3 vezes** (uma para cada scp/ssh).

---

## Funcionalidades

| Aba              | O que faz                                                          |
|------------------|--------------------------------------------------------------------|
| **Consolidado**  | Todas as vendas + formulário para adicionar manualmente            |
| **NF / PR / Avulso / Avaria** | Filtra por tipo de venda                              |
| **Gráfico Anual**| Receita mensal por canal (barra empilhada — Chart.js)              |
| **Importar Excel** | Importa a planilha do SharePoint automaticamente                 |

---

## Importar planilha do SharePoint

1. No SharePoint: **Arquivo → Exportar → Baixar como .xlsx**
2. No app, abra a aba **"Importar Excel"**
3. Arraste o arquivo ou clique para selecionar
4. Clique em **Importar**

Os dados ficam em `backend/bm_monteiro.db` (SQLite).

---

## Backup do banco

O arquivo `backend/bm_monteiro.db` contém todos os dados.
Copie esse arquivo periodicamente para fazer backup.
A pasta `backend/backups/` guarda snapshots automáticos.

---

## Estrutura de pastas

```
bm_app/
├── ATUALIZAR.bat        ← Deploy para a Hostinger (scp + restart)
├── CONFIGURAR.bat       ← Executar só na primeira vez (instala Python deps)
├── INICIAR.bat          ← Executar todo dia (sobe o servidor local)
├── README.md
├── changelog.txt        ← Histórico de alterações (mais recente no topo)
└── backend/
    ├── app.py           ← Servidor FastAPI
    ├── bm_monteiro.db   ← Banco de dados SQLite (gerado automaticamente)
    ├── requirements.txt
    ├── backups/         ← Snapshots automáticos do banco
    └── static/
        ├── index.html   ← Interface completa (vanilla JS)
        └── logo.png
```

---

## Produção

- **Servidor**: Hostinger VPS (`2.24.124.76`)
- **Domínio**: `https://sistema.meninadosraios.com.br`
- **Serviço systemd**: `menina`
- **Diretório no servidor**: `/opt/menina/backend/`
- **Deploy**: via `ATUALIZAR.bat` (scp dos arquivos modificados + restart)

---

## Suporte
Gerado para Menina dos Raios Ltda.
