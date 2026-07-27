
CREATE TYPE public.sale_type AS ENUM ('NF', 'PR', 'AVULSO');

CREATE TABLE public.sales (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  sale_type public.sale_type NOT NULL,
  sale_date DATE NOT NULL,
  client TEXT,
  product TEXT,
  nf_number TEXT,
  quantity NUMERIC(12,2) NOT NULL DEFAULT 0,
  unit_price NUMERIC(12,2) NOT NULL DEFAULT 0,
  total NUMERIC(14,2) NOT NULL DEFAULT 0,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sales_date ON public.sales(sale_date);
CREATE INDEX idx_sales_type ON public.sales(sale_type);

ALTER TABLE public.sales ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read sales" ON public.sales FOR SELECT USING (true);
CREATE POLICY "Public insert sales" ON public.sales FOR INSERT WITH CHECK (true);
CREATE POLICY "Public update sales" ON public.sales FOR UPDATE USING (true);
CREATE POLICY "Public delete sales" ON public.sales FOR DELETE USING (true);

CREATE OR REPLACE FUNCTION public.touch_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_sales_updated_at
BEFORE UPDATE ON public.sales
FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();
