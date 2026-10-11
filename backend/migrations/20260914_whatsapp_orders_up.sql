BEGIN;

CREATE TABLE IF NOT EXISTS whatsapp_consent (
    id TEXT PRIMARY KEY,
    company_key TEXT NOT NULL,
    client_id TEXT NOT NULL,
    phone_e164 TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('desconhecido','opt_in','opt_out','pausado')),
    source TEXT NOT NULL DEFAULT 'manual',
    granted_at TEXT,
    revoked_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(company_key, client_id, phone_e164),
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS whatsapp_conversations (
    id TEXT PRIMARY KEY,
    company_key TEXT NOT NULL,
    client_id TEXT NOT NULL,
    contact_id TEXT,
    jid TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('nova','aguardando_resposta','identificando_produto','coletando_quantidade','coletando_avaria','calculando_reposicao','aguardando_confirmacao','pedido_rascunho','aguardando_aprovacao','concluida','cancelada','atendimento_humano','opt_out')),
    assigned_user_id TEXT,
    last_message_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE RESTRICT,
    FOREIGN KEY(contact_id) REFERENCES whatsapp_contacts(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS whatsapp_messages (
    id TEXT PRIMARY KEY,
    company_key TEXT NOT NULL,
    instance_key TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    direction TEXT NOT NULL CHECK(direction IN ('recebida','enviada')),
    external_message_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    event_hash TEXT NOT NULL,
    jid TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK(status IN ('recebida','processada','falha','bloqueada')),
    error_text TEXT,
    received_at TEXT,
    processed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(company_key, instance_key, external_message_id),
    UNIQUE(company_key, idempotency_key),
    FOREIGN KEY(conversation_id) REFERENCES whatsapp_conversations(id) ON DELETE CASCADE,
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS whatsapp_events (
    id TEXT PRIMARY KEY,
    company_key TEXT NOT NULL,
    message_id TEXT NOT NULL,
    event_hash TEXT NOT NULL,
    event_type TEXT NOT NULL DEFAULT 'incoming',
    processing_status TEXT NOT NULL DEFAULT 'registrado',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(company_key, event_hash),
    FOREIGN KEY(message_id) REFERENCES whatsapp_messages(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS whatsapp_order_drafts (
    id TEXT PRIMARY KEY,
    company_key TEXT NOT NULL,
    client_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    source_message_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('rascunho','aguardando_confirmacao','aguardando_aprovacao','aprovado','cancelado','convertido_em_venda','erro','duplicado_suspeito')),
    requested_quantity TEXT,
    suggested_quantity TEXT,
    confirmed_quantity TEXT,
    calculation_memory TEXT,
    total TEXT NOT NULL DEFAULT '0',
    block_reason TEXT,
    assigned_user_id TEXT,
    approved_by TEXT,
    confirmed_at TEXT,
    approved_at TEXT,
    converted_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(company_key, idempotency_key),
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE RESTRICT,
    FOREIGN KEY(conversation_id) REFERENCES whatsapp_conversations(id) ON DELETE RESTRICT,
    FOREIGN KEY(source_message_id) REFERENCES whatsapp_messages(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS whatsapp_order_items (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    product_key TEXT NOT NULL,
    requested_quantity TEXT,
    suggested_quantity TEXT,
    confirmed_quantity TEXT,
    average_consumption TEXT,
    maximum_consumption TEXT,
    confirmed_damage TEXT NOT NULL DEFAULT '0',
    damage_replacement_percent TEXT NOT NULL DEFAULT '0',
    informed_stock TEXT,
    unit_price TEXT NOT NULL DEFAULT '0',
    total TEXT NOT NULL DEFAULT '0',
    calculation_memory TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(order_id, product_key),
    FOREIGN KEY(order_id) REFERENCES whatsapp_order_drafts(id) ON DELETE CASCADE,
    FOREIGN KEY(product_key) REFERENCES product_prices(key) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS whatsapp_order_history (
    id TEXT PRIMARY KEY,
    company_key TEXT NOT NULL,
    order_id TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT NOT NULL,
    changed_by TEXT,
    reason TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(order_id) REFERENCES whatsapp_order_drafts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS customer_product_consumption (
    id TEXT PRIMARY KEY,
    company_key TEXT NOT NULL,
    client_id TEXT NOT NULL,
    product_key TEXT NOT NULL,
    average_consumption TEXT NOT NULL,
    maximum_consumption TEXT,
    unit TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(company_key, client_id, product_key),
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY(product_key) REFERENCES product_prices(key) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS customer_product_damage (
    id TEXT PRIMARY KEY,
    company_key TEXT NOT NULL,
    client_id TEXT NOT NULL,
    product_key TEXT NOT NULL,
    order_id TEXT,
    quantity TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('informada','aprovada','reposta','rejeitada')),
    replacement_percent TEXT NOT NULL DEFAULT '0',
    reason TEXT,
    notes TEXT,
    responsible_user_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE RESTRICT,
    FOREIGN KEY(product_key) REFERENCES product_prices(key) ON DELETE RESTRICT,
    FOREIGN KEY(order_id) REFERENCES whatsapp_order_drafts(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_wa_conversations_company_client ON whatsapp_conversations(company_key, client_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_wa_conversations_company_jid ON whatsapp_conversations(company_key, jid, status);
CREATE INDEX IF NOT EXISTS idx_wa_messages_conversation ON whatsapp_messages(company_key, conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_wa_orders_company_status ON whatsapp_order_drafts(company_key, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_wa_orders_client ON whatsapp_order_drafts(company_key, client_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_wa_history_order ON whatsapp_order_history(order_id, created_at);
CREATE INDEX IF NOT EXISTS idx_consumption_client ON customer_product_consumption(company_key, client_id);
CREATE INDEX IF NOT EXISTS idx_damage_client ON customer_product_damage(company_key, client_id, created_at DESC);

COMMIT;
