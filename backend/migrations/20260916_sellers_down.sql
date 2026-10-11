DROP INDEX IF EXISTS idx_paladar_sales_seller_date;
DROP INDEX IF EXISTS idx_sales_seller_date;
DROP INDEX IF EXISTS idx_seller_history_seller;
DROP INDEX IF EXISTS idx_sellers_company_active;
DROP TABLE IF EXISTS seller_history;
DROP TABLE IF EXISTS sellers;

-- Limitação deliberada:
-- SQLite não permite remover colunas com segurança universal nas versões usadas
-- pelo projeto. Este rollback remove apenas estruturas auxiliares e índices.
-- As colunas seller_id/seller_name_snapshot em sales e paladar_sales permanecem.
-- Para rollback físico completo, restaurar backup validado ou executar rebuild
-- controlado em janela separada. Reaplicação segura deve usar o runner oficial
-- apply_sellers_schema(), que detecta colunas existentes e bloqueia schema parcial.
