-- Migração sellers/produtividade.
--
-- SQLite não oferece ALTER TABLE ADD COLUMN IF NOT EXISTS de forma portátil nas
-- versões usadas pelo projeto. Por isso, o mecanismo oficial de aplicação é o
-- runner idempotente apply_sellers_schema() em repositories/sellers_repository.py:
-- ele inspeciona tabelas, colunas e índices, bloqueia schema parcial e adiciona
-- somente colunas ausentes em sales/paladar_sales.
--
-- Este SQL documenta/cria as estruturas auxiliares de uma aplicação única. Para
-- reaplicação segura, inclusive depois do down.sql, use o runner oficial.

CREATE TABLE IF NOT EXISTS sellers (
    id TEXT PRIMARY KEY,
    company_key TEXT NOT NULL,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    created_by TEXT,
    updated_by TEXT,
    UNIQUE(company_key, normalized_name)
);

CREATE TABLE IF NOT EXISTS seller_history (
    id TEXT PRIMARY KEY,
    seller_id TEXT NOT NULL,
    company_key TEXT NOT NULL,
    old_name TEXT,
    new_name TEXT NOT NULL,
    changed_by TEXT,
    changed_at TEXT DEFAULT (datetime('now')),
    reason TEXT,
    FOREIGN KEY(seller_id) REFERENCES sellers(id)
);

CREATE INDEX IF NOT EXISTS idx_sellers_company_active ON sellers(company_key, active, name);
CREATE INDEX IF NOT EXISTS idx_seller_history_seller ON seller_history(seller_id, changed_at DESC);

-- Índices de sales/paladar_sales dependem das colunas adicionadas pelo runner:
-- idx_sales_seller_date e idx_paladar_sales_seller_date.
