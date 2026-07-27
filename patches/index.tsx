import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState, useRef } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  listSales, SALE_TYPE_LABEL, type SaleType, importExcel,
  clearImports, getImportLog, getSummary, formatBRL,
} from "@/lib/sales";
import { SaleForm } from "@/components/SaleForm";
import { SalesTable } from "@/components/SalesTable";
import { SummaryCards } from "@/components/SummaryCards";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Upload, Trash2, RefreshCw, BarChart3, FileSpreadsheet, PlusCircle, History } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/")(({
  head: () => ({
    meta: [
      { title: "BM Monteiro — Controle de Vendas" },
      { name: "description", content: "Plataforma local de registro e consolidação de vendas." },
    ],
  }),
  component: Index,
}));

const MONTHS = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"];

function ConsolidadoChart({ year }: { year: number }) {
  const { data = [] } = useQuery({
    queryKey: ["summary", year],
    queryFn: () => getSummary(year),
  });

  // Build monthly totals
  const months: Record<string, Record<string, number>> = {};
  for (const row of data) {
    const m = String(parseInt(row.month) - 1); // 0-indexed
    if (!months[m]) months[m] = {};
    months[m][row.sale_type] = (months[m][row.sale_type] ?? 0) + row.total_val;
  }

  const types: SaleType[] = ["NF","PR","AVULSO","AVARIA"];
  const colors: Record<string, string> = {
    NF:"#1B5E20", PR:"#2E7D32", AVULSO:"#6A1B9A", AVARIA:"#B71C1C"
  };

  const maxVal = Math.max(...Object.values(months).map(m =>
    Object.values(m).reduce((a, b) => a + b, 0)
  ), 1);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-2 text-xs">
        {types.map(t => (
          <div key={t} className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-sm flex-shrink-0" style={{ background: colors[t] }} />
            <span className="text-muted-foreground">{SALE_TYPE_LABEL[t]}</span>
          </div>
        ))}
      </div>
      <div className="flex gap-1 items-end h-40">
        {MONTHS.map((mn, mi) => {
          const mData = months[String(mi)] ?? {};
          const total = Object.values(mData).reduce((a, b) => a + b, 0);
          const pct   = total / maxVal;
          return (
            <div key={mi} className="flex-1 flex flex-col items-center gap-1">
              <div className="w-full flex flex-col-reverse" style={{ height: "120px" }}>
                {types.map(t => {
                  const v = mData[t] ?? 0;
                  if (!v) return null;
                  const h = (v / maxVal) * 120;
                  return (
                    <div key={t} title={`${SALE_TYPE_LABEL[t]}: ${formatBRL(v)}`}
                      style={{ height: h, background: colors[t], width: "100%" }} />
                  );
                })}
              </div>
              <span className="text-[9px] text-muted-foreground">{mn}</span>
            </div>
          );
        })}
      </div>
      <div className="text-xs text-muted-foreground text-center">
        Total {year}: {formatBRL(data.reduce((a, r) => a + r.total_val, 0))}
      </div>
    </div>
  );
}

function ImportTab({ onImported }: { onImported: () => void }) {
  const [file, setFile]         = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult]     = useState<{imported:number;total_in_file:number}|null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const qc = useQueryClient();

  const { data: logs = [] } = useQuery({
    queryKey: ["import-log"],
    queryFn: getImportLog,
  });

  async function handleImport() {
    if (!file) return;
    setImporting(true); setResult(null);
    try {
      const r = await importExcel(file);
      setResult(r);
      toast.success(`✅ ${r.imported} registros importados de ${r.total_in_file} encontrados`);
      qc.invalidateQueries({ queryKey: ["sales"] });
      qc.invalidateQueries({ queryKey: ["summary"] });
      qc.invalidateQueries({ queryKey: ["import-log"] });
      onImported();
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setImporting(false);
    }
  }

  async function handleClear() {
    if (!confirm("Remover TODOS os registros importados do Excel? (Registros manuais não serão afetados)")) return;
    try {
      await clearImports();
      toast.success("Registros importados removidos.");
      qc.invalidateQueries({ queryKey: ["sales"] });
      qc.invalidateQueries({ queryKey: ["summary"] });
    } catch (e: any) {
      toast.error(e.message);
    }
  }

  return (
    <div className="space-y-6">
      {/* Drop zone */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5 text-green-700" />
            Importar Planilha de Vendas (.xlsx)
          </CardTitle>
          <CardDescription>
            Selecione a planilha do SharePoint (Vendas de Jan - Dez 2026.xlsx).
            O sistema extrai automaticamente dados de NF, PR, Avulsos e Avarias.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div
            className="border-2 border-dashed border-green-300 rounded-lg p-8 text-center cursor-pointer hover:bg-green-50 transition-colors"
            onClick={() => inputRef.current?.click()}
            onDragOver={e => e.preventDefault()}
            onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) setFile(f); }}
          >
            <Upload className="h-10 w-10 text-green-600 mx-auto mb-3" />
            <p className="font-medium text-green-800">{file ? file.name : "Clique ou arraste o arquivo aqui"}</p>
            <p className="text-sm text-muted-foreground mt-1">Formato: .xlsx</p>
            <input ref={inputRef} type="file" accept=".xlsx,.xls" className="hidden"
              onChange={e => e.target.files?.[0] && setFile(e.target.files[0])} />
          </div>

          <div className="flex gap-3">
            <Button
              className="flex-1 bg-green-700 hover:bg-green-800"
              onClick={handleImport}
              disabled={!file || importing}
            >
              {importing ? <><RefreshCw className="h-4 w-4 mr-2 animate-spin" />Importando...</> :
                           <><Upload className="h-4 w-4 mr-2" />Importar</>}
            </Button>
            <Button variant="outline" className="text-red-600 border-red-300" onClick={handleClear}>
              <Trash2 className="h-4 w-4 mr-1" /> Limpar importados
            </Button>
          </div>

          {result && (
            <div className="bg-green-50 border border-green-200 rounded-md p-4 text-sm">
              <p className="font-semibold text-green-800">✅ Importação concluída</p>
              <p className="text-green-700">{result.imported} registros adicionados ao banco.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Histórico */}
      {logs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <History className="h-4 w-4" /> Histórico de Importações
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {logs.slice(0, 10).map((l: any) => (
                <div key={l.id} className="flex items-center justify-between text-sm py-2 border-b last:border-0">
                  <div>
                    <span className="font-medium">{l.filename}</span>
                    <span className="text-muted-foreground ml-2">
                      {new Date(l.imported_at).toLocaleString("pt-BR")}
                    </span>
                  </div>
                  <Badge variant="secondary">{l.rows_added} registros</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Index() {
  const qc = useQueryClient();
  const year = new Date().getFullYear();

  const { data: sales = [], isLoading } = useQuery({
    queryKey: ["sales"],
    queryFn: () => listSales(),
  });

  const [tab, setTab]     = useState<"CONSOLIDADO" | SaleType | "IMPORTAR" | "GRAFICO">("CONSOLIDADO");
  const [search, setSearch] = useState("");

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["sales"] });
    qc.invalidateQueries({ queryKey: ["summary"] });
  };

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const types: SaleType[] = ["NF","PR","AVULSO","AVARIA"];
    return sales.filter(s => {
      if (types.includes(tab as SaleType) && s.sale_type !== tab) return false;
      if (!q) return true;
      return [s.client, s.product, s.nf_number].some(f => f?.toLowerCase().includes(q));
    });
  }, [sales, tab, search]);

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card shadow-sm">
        <div className="container mx-auto px-4 py-5 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-700 rounded-lg flex items-center justify-center text-white font-bold text-lg">🌿</div>
            <div>
              <h1 className="text-2xl font-bold leading-tight">BM Monteiro</h1>
              <p className="text-muted-foreground text-sm">Controle de Vendas — Avulso · NF · Produtor Rural</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge className="bg-green-700 gap-1">
              {sales.length} registros
            </Badge>
            <Button variant="outline" size="sm" onClick={refresh}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 space-y-6">
        <SummaryCards sales={sales} />

        <Tabs value={tab} onValueChange={v => setTab(v as any)}>
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <TabsList className="flex-wrap h-auto gap-1">
              <TabsTrigger value="CONSOLIDADO" className="gap-1">
                <BarChart3 className="h-3.5 w-3.5" /> Consolidado
              </TabsTrigger>
              {(Object.keys(SALE_TYPE_LABEL) as SaleType[]).map(k => (
                <TabsTrigger key={k} value={k}>{SALE_TYPE_LABEL[k]}</TabsTrigger>
              ))}
              <TabsTrigger value="GRAFICO" className="gap-1">
                <BarChart3 className="h-3.5 w-3.5" /> Gráfico Anual
              </TabsTrigger>
              <TabsTrigger value="IMPORTAR" className="gap-1">
                <Upload className="h-3.5 w-3.5" /> Importar Excel
              </TabsTrigger>
            </TabsList>

            {tab !== "IMPORTAR" && tab !== "GRAFICO" && (
              <Input
                placeholder="Buscar cliente, produto ou NF..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="max-w-xs"
              />
            )}
          </div>

          {/* Vendas tables */}
          {(["CONSOLIDADO","NF","PR","AVULSO","AVARIA"] as const).map(t => (
            <TabsContent key={t} value={t} className="mt-4">
              <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
                <SaleForm onSaved={refresh} />
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">
                      {t === "CONSOLIDADO" ? "Todos os registros" : SALE_TYPE_LABEL[t as SaleType]}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {isLoading
                      ? <div className="text-center py-12 text-muted-foreground">Carregando...</div>
                      : <SalesTable sales={filtered} onChanged={refresh} canDelete={true} />
                    }
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          ))}

          <TabsContent value="GRAFICO" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle>Consolidado Gráfico — {year}</CardTitle>
                <CardDescription>Receita mensal por canal de venda</CardDescription>
              </CardHeader>
              <CardContent>
                <ConsolidadoChart year={year} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="IMPORTAR" className="mt-4">
            <ImportTab onImported={refresh} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
