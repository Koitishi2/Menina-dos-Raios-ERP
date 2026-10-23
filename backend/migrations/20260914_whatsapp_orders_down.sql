BEGIN;

DROP TABLE IF EXISTS customer_product_damage;
DROP TABLE IF EXISTS customer_product_consumption;
DROP TABLE IF EXISTS whatsapp_order_history;
DROP TABLE IF EXISTS whatsapp_order_items;
DROP TABLE IF EXISTS whatsapp_order_drafts;
DROP TABLE IF EXISTS whatsapp_events;
DROP TABLE IF EXISTS whatsapp_messages;
DROP TABLE IF EXISTS whatsapp_conversations;
DROP TABLE IF EXISTS whatsapp_consent;

COMMIT;
