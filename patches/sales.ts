// BM Monteiro — API local (substitui Supabase)
const API = "http://localhost:8765";

export type SaleType = "NF" | "PR" | "AVULSO" | "AVARIA";

export interface Sale {
  id: string;
  sale_type: SaleType;
  sale_date: string;
  client: string | null;
  product: string | null;
  nf_number: string | null;
  quantity: number;
  unit_price: number;
  total: number;
  notes: string | null;
  source: string;
  created_at: string;
}

export interface SummaryRow {
  month: string;
  sale_type: SaleType;
  total_val: number;
  total_qty: number;
}

export const SALE_TYPE_LABEL: Record<SaleType, string> = {
  AVULSO: "Avulso",
  NF: "Nota Fiscal (NF-e)",
  PR: "Produtor Rural",
  AVARIA: "Avarias",
};

export const SALE_TYPE_COLOR: Record<SaleType, string> = {
  NF:     "bg-green-600",
  PR:     "bg-emerald-600",
  AVULSO: "bg-purple-600",
  AVARIA: "bg-red-600",
};

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Erro na API");
  }
  return res.json();
}

export async function listSales(params?: {
  sale_type?: string;
  month?: number;
  year?: number;
  search?: string;
}): Promise<Sale[]> {
  const qs = new URLSearchParams();
  if (params?.sale_type) qs.set("sale_type", params.sale_type);
  if (params?.month)     qs.set("month",     String(params.month));
  if (params?.year)      qs.set("year",      String(params.year));
  if (params?.search)    qs.set("search",    params.search);
  return api<Sale[]>(`/api/sales?${qs}`);
}

export async function createSale(
  input: Omit<Sale, "id" | "created_at" | "total"> & { total?: number }
): Promise<Sale> {
  return api<Sale>("/api/sales", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export async function deleteSale(id: string): Promise<void> {
  await api(`/api/sales/${id}`, { method: "DELETE" });
}

export async function getSummary(year?: number): Promise<SummaryRow[]> {
  const qs = year ? `?year=${year}` : "";
  return api<SummaryRow[]>(`/api/summary${qs}`);
}

export async function clearImports(): Promise<void> {
  await api("/api/sales/clear-imports", { method: "DELETE" });
}

export async function getImportLog(): Promise<any[]> {
  return api("/api/import-log");
}

export function formatBRL(n: number) {
  return Number(n || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
