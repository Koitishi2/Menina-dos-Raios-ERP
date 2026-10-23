BEGIN;

CREATE TABLE IF NOT EXISTS whatsapp_inbound_events (
    id TEXT PRIMARY KEY,
    company_key TEXT NOT NULL,
    provider TEXT NOT NULL,
    instance_key TEXT NOT NULL,
    event_id TEXT NOT NULL,
    external_message_id TEXT NOT NULL,
    jid TEXT NOT NULL,
    phone_e164 TEXT,
    message_type TEXT NOT NULL,
    raw_type TEXT,
    body_preview TEXT NOT NULL DEFAULT '',
    received_at TEXT NOT NULL,
    processing_status TEXT NOT NULL CHECK(processing_status IN ('recebido','processado','bloqueado','nao_identificado','erro')),
    client_id TEXT,
    message_id TEXT,
    error_code TEXT,
    command TEXT,
    previous_state TEXT,
    new_state TEXT,
    actor TEXT NOT NULL DEFAULT 'system:baileys',
    duplicate_count INTEGER NOT NULL DEFAULT 0,
    last_duplicate_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(company_key, instance_key, event_id),
    UNIQUE(company_key, instance_key, external_message_id),
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE SET NULL,
    FOREIGN KEY(message_id) REFERENCES whatsapp_messages(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_wa_inbound_company_created
    ON whatsapp_inbound_events(company_key, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_wa_inbound_company_status
    ON whatsapp_inbound_events(company_key, processing_status, created_at DESC);

CREATE TABLE IF NOT EXISTS whatsapp_manual_batches (
    id TEXT PRIMARY KEY,
    company_key TEXT NOT NULL,
    created_by TEXT NOT NULL,
    message_template TEXT NOT NULL,
    message_version TEXT NOT NULL,
    filters_json TEXT NOT NULL DEFAULT '{}',
    selection_version TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('rascunho','confirmado','processando','concluido','cancelado','expirado')),
    expires_at TEXT NOT NULL,
    confirmed_at TEXT,
    cancelled_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(company_key, selection_version)
);

CREATE TABLE IF NOT EXISTS whatsapp_manual_batch_items (
    id TEXT PRIMARY KEY,
    company_key TEXT NOT NULL,
    batch_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    phone_e164 TEXT NOT NULL,
    consent_status TEXT NOT NULL,
    last_sale_at TEXT,
    days_without_purchase INTEGER,
    suggestion_reason TEXT,
    message_final TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pendente','enviado','entregue','falhou','bloqueado','cancelado','duplicado')),
    result_code TEXT,
    result_detail TEXT,
    sent_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(company_key, batch_id, client_id),
    UNIQUE(company_key, idempotency_key),
    FOREIGN KEY(batch_id) REFERENCES whatsapp_manual_batches(id) ON DELETE CASCADE,
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_wa_manual_batches_company
    ON whatsapp_manual_batches(company_key, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_wa_manual_items_batch
    ON whatsapp_manual_batch_items(company_key, batch_id, status);
CREATE INDEX IF NOT EXISTS idx_wa_manual_items_client
    ON whatsapp_manual_batch_items(company_key, client_id, created_at DESC);

COMMIT;
