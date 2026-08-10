import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState, useRef, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  listSales,
  SALE_TYPE_LABEL,
  type SaleType,
  getSummary,
  formatBRL,
  SALE_TYPE_HEX,
  sebraeVerifyNF,
  type SebraeVerifyResult,
} from "@/lib/sales";
import { SaleForm } from "@/components/SaleForm";
import { SalesTable } from "@/components/SalesTable";
import { SummaryCards } from "@/components/SummaryCards";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
  DrawerClose,
} from "@/components/ui/drawer";
import {
  RefreshCw,
  BarChart3,
  Plus,
  Wifi,
  WifiOff,
  Search,
  X,
  FileSearch,
  Settings,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { toast } from "sonner";
import { useIsMobile } from "@/hooks/use-mobile";
import { useOnlineStatus } from "@/hooks/useOnlineStatus";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "BM Monteiro — Controle de Vendas" },
      {
        name: "description",
        content: "Plataforma local de registro e consolidação de vendas.",
      },
    ],
  }),
  component: Index,
});

const MONTHS = [
  "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
  "Jul", "Ago", "Set", "Out", "Nov", "Dez",
];

// ────────────────────────────────────────────────────────────────
// Gráfico mensal (SVG, sem dependências)
// ────────────────────────────────────────────────────────────────
function ConsolidadoChart({ year }: { year: number }) {
  const { data = [], isLoading } = useQuery({
    queryKey: ["summary", year],
    queryFn: () => getSummary(year),
  });

  const months: Record<string, Record<string, number>> = {};
  for (const row of data) {
    const m = String(parseInt(row.month) - 1);
    if (!months[m]) months[m] = {};
    months[m][row.sale_type] =
      (months[m][row.sale_type] ?? 0) + row.total_val;
  }

  const types: SaleType[] = ["NF", "PR", "AVULSO", "AVARIA"];
  const maxVal = Math.max(
    ...Object.values(months).map((m) =>
      Object.values(m).reduce((a, b) => a + b, 0),
    ),
    1,
  );

  if (isLoading) {
    return <Skeleton className="h-48 w-full" />;
  }

  const totalYear = data.reduce((a, r) => a + r.total_val, 0);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-x-3 gap-y-1.5 text-xs">
        {types.map((t) => (
          <div key={t} className="flex items-center gap-1.5">
            <div
              className="w-3 h-3 rounded-sm flex-shrink-0"
              style={{ background: SALE_TYPE_HEX[t] }}
            />
            <span className="text-muted-foreground">{SALE_TYPE_LABEL[t]}</span>
          </div>
        ))}
      </div>

      <div className="flex gap-1 items-end h-40">
        {MONTHS.map((mn, mi) => {
          const mData = months[String(mi)] ?? {};
          const total = Object.values(mData).reduce((a, b) => a + b, 0);
          return (
            <div
              key={mi}
              className="flex-1 flex flex-col items-center gap-1 group"
              title={total > 0 ? `${mn}: ${formatBRL(total)}` : mn}
            >
              <div
                className="w-full flex flex-col-reverse rounded-t overflow-hidden"
                style={{ height: "120px" }}
              >
                {types.map((t) => {
                  const v = mData[t] ?? 0;
                  if (!v) return null;
                  const h = (v / maxVal) * 120;
                  return (
                    <div
                      key={t}
                      title={`${SALE_TYPE_LABEL[t]}: ${formatBRL(v)}`}
                      style={{
                        height: h,
                        background: SALE_TYPE_HEX[t],
                        width: "100%",
                      }}
                      className="transition-opacity group-hover:opacity-90"
                    />
                  );
                })}
              </div>
              <span className="text-[10px] text-muted-foreground">{mn}</span>
            </div>
          );
        })}
      </div>

      <div className="text-xs text-muted-foreground text-center pt-2 border-t">
        Total {year}:{" "}
        <span className="font-semibold text-foreground">
          {formatBRL(totalYear)}
        </span>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────
// Pílula de conectividade (canto do header)
// ────────────────────────────────────────────────────────────────
function ConnectivityPill() {
  const { online } = useOnlineStatus();
  return (
    <Badge
      variant={online ? "secondary" : "destructive"}
      className="gap-1 px-2 py-0.5"
      title={online ? "Conectado" : "Sem conexão"}
    >
      {online ? (
        <Wifi className="h-3 w-3" />
      ) : (
        <WifiOff className="h-3 w-3" />
      )}
      <span className="hidden sm:inline">{online ? "Online" : "Offline"}</span>
    </Badge>
  );
}

// ────────────────────────────────────────────────────────────────
// Aba Configurações — Verificação de NF Sebrae
// ────────────────────────────────────────────────────────────────
function SebraeVerifyTab() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SebraeVerifyResult | null>(null);
  const [filter, setFilter] = useState<"all" | "missing" | "found">("missing");
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleVerify() {
    if (!file) return;
    setLoading(true);
    setResult(null);
    try {
      const r = await sebraeVerifyNF(file);
      setResult(r);
      if (r.missing_count === 0) {
        toast.success("Todas as notas do Sebrae já estão no sistema!");
      } else {
        toast.warning(`${r.missing_count} nota(s) pendente(s) de inserção no sistema.`);
      }
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setLoading(false);
    }
  }

  const displayEntries = result
    ? filter === "missing"
      ? result.entries.filter((e) => !e.in_system)
      : filter === "found"
      ? result.entries.filter((e) => e.in_system)
      : result.entries
    : [];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSearch className="h-5 w-5 text-primary" />
            Verificar NF-e Pendentes (Sebrae)
          </CardTitle>
          <CardDescription>
            Envie o PDF de notas fiscais exportado do Sebrae. O sistema comparará
            as NF-e emitidas com os registros de NF e Avulso já inseridos,
            mostrando quais ainda faltam ser lançadas.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div
            className="border-2 border-dashed border-primary/40 rounded-lg p-6 text-center cursor-pointer hover:bg-primary/5 transition-colors"
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const f = e.dataTransfer.files[0];
              if (f) setFile(f);
            }}
          >
            <FileSearch className="h-10 w-10 text-primary mx-auto mb-3" />
            <p className="font-medium text-primary">
              {file ? file.name : "Clique ou arraste o PDF do Sebrae aqui"}
            </p>
            <p className="text-sm text-muted-foreground mt-1">Formato: .pdf</p>
            <input
              ref={inputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => e.target.files?.[0] && setFile(e.target.files[0])}
            />
          </div>

          <Button
            className="w-full h-11"
            onClick={handleVerify}
            disabled={!file || loading}
          >
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Verificando...
              </>
            ) : (
              <>
                <FileSearch className="h-4 w-4 mr-2" />
                Verificar NF-e
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              Resultado da Verificação
            </CardTitle>
            <div className="flex flex-wrap gap-3 mt-2">
              <div className="flex items-center gap-1.5 text-sm">
                <span className="text-muted-foreground">Total no Sebrae:</span>
                <Badge variant="secondary">{result.total_sebrae}</Badge>
              </div>
              <div className="flex items-center gap-1.5 text-sm">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span className="text-muted-foreground">No sistema:</span>
                <Badge className="bg-green-600">{result.found_in_system}</Badge>
              </div>
              <div className="flex items-center gap-1.5 text-sm">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <span className="text-muted-foreground">Pendentes:</span>
                <Badge variant="destructive">{result.missing_count}</Badge>
              </div>
              {result.canceladas_ignoradas > 0 && (
                <div className="flex items-center gap-1.5 text-sm">
                  <span className="text-muted-foreground">Canceladas ignoradas:</span>
                  <Badge variant="outline">{result.canceladas_ignoradas}</Badge>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <Button
                size="sm"
                variant={filter === "missing" ? "default" : "outline"}
                onClick={() => setFilter("missing")}
                className={filter === "missing" ? "bg-red-600 hover:bg-red-700" : ""}
              >
                Pendentes ({result.missing_count})
              </Button>
              <Button
                size="sm"
                variant={filter === "found" ? "default" : "outline"}
                onClick={() => setFilter("found")}
                className={filter === "found" ? "bg-green-600 hover:bg-green-700" : ""}
              >
                No sistema ({result.found_in_system})
              </Button>
              <Button
                size="sm"
                variant={filter === "all" ? "default" : "outline"}
                onClick={() => setFilter("all")}
              >
                Todas ({result.total_sebrae})
              </Button>
            </div>

            {displayEntries.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground text-sm">
                {filter === "missing"
                  ? "Nenhuma nota pendente — tudo inserido!"
                  : "Nenhum resultado neste filtro."}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-muted-foreground text-xs">
                      <th className="text-left py-2 pr-4 font-medium">NF</th>
                      <th className="text-left py-2 pr-4 font-medium">Data</th>
                      <th className="text-right py-2 font-medium">Valor</th>
                      <th className="text-center py-2 pl-4 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayEntries.map((e, i) => (
                      <tr key={i} className="border-b last:border-0 hover:bg-muted/40">
                        <td className="py-2 pr-4 font-mono font-medium">{e.nf_full}</td>
                        <td className="py-2 pr-4 text-muted-foreground">{e.date}</td>
                        <td className="py-2 text-right tabular-nums">
                          {formatBRL(e.value)}
                        </td>
                        <td className="py-2 pl-4 text-center">
                          {e.in_system ? (
                            <Badge className="bg-green-600 text-xs gap-1">
                              <CheckCircle2 className="h-3 w-3" /> Inserida
                            </Badge>
                          ) : (
                            <Badge variant="destructive" className="text-xs gap-1">
                              <AlertCircle className="h-3 w-3" /> Pendente
                            </Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ────────────────────────────────────────────────────────────────
// Página principal
// ────────────────────────────────────────────────────────────────
type TabKey = "CONSOLIDADO" | SaleType | "GRAFICO" | "CONFIGURACOES";

function Index() {
  const qc = useQueryClient();
  const isMobile = useIsMobile();
  const year = new Date().getFullYear();

  const { data: sales = [], isLoading, isFetching } = useQuery({
    queryKey: ["sales"],
    queryFn: () => listSales(),
  });

  const [tab, setTab] = useState<TabKey>("CONSOLIDADO");
  const [search, setSearch] = useState("");
  const [showSearch, setShowSearch] = useState(false);
  const [formOpen, setFormOpen] = useState(false);

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["sales"] });
    qc.invalidateQueries({ queryKey: ["summary"] });
  };

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const types: SaleType[] = ["NF", "PR", "AVULSO", "AVARIA"];
    return sales.filter((s) => {
      if (types.includes(tab as SaleType) && s.sale_type !== tab) return false;
      if (!q) return true;
      return [s.client, s.product, s.nf_number].some((f) =>
        f?.toLowerCase().includes(q),
      );
    });
  }, [sales, tab, search]);

  const isDataTab =
    tab === "CONSOLIDADO" || tab === "NF" || tab === "PR" ||
    tab === "AVULSO" || tab === "AVARIA";

  // Ensure FAB hides when the in-app form-drawer is open
  useEffect(() => {
    if (!isDataTab && formOpen) setFormOpen(false);
  }, [isDataTab, formOpen]);

  return (
    <div className="min-h-screen bg-background">
      {/* ─── Sticky header ────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80 shadow-sm">
        <div className="container mx-auto px-3 sm:px-4 py-3 sm:py-4 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            <div className="w-9 h-9 sm:w-10 sm:h-10 bg-primary rounded-lg flex items-center justify-center text-primary-foreground font-bold text-lg flex-shrink-0">
              🌿
            </div>
            <div className="min-w-0">
              <h1 className="text-base sm:text-2xl font-bold leading-tight truncate">
                BM Monteiro
              </h1>
              <p className="text-muted-foreground text-[11px] sm:text-sm leading-tight hidden sm:block truncate">
                Controle de Vendas — Avulso · NF · Produtor Rural
              </p>
              <p className="text-muted-foreground text-[10px] leading-tight sm:hidden">
                {sales.length} registros
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 sm:gap-2 flex-shrink-0">
            <ConnectivityPill />
            <Badge className="hidden sm:inline-flex bg-primary gap-1">
              {sales.length} registros
            </Badge>
            <Button
              variant="outline"
              size="icon"
              className="h-9 w-9"
              onClick={refresh}
              disabled={isFetching}
              title="Atualizar"
            >
              <RefreshCw
                className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`}
              />
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-3 sm:px-4 py-4 sm:py-6 space-y-4 sm:space-y-6 pb-24 sm:pb-6">
        {/* KPIs */}
        {isLoading ? (
          <div className="grid gap-3 md:grid-cols-5">
            <Skeleton className="h-28 md:col-span-2" />
            <div className="grid grid-cols-2 gap-3 md:col-span-3 md:grid-cols-4">
              {[0, 1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-20" />
              ))}
            </div>
          </div>
        ) : (
          <SummaryCards sales={sales} />
        )}

        <Tabs value={tab} onValueChange={(v) => setTab(v as TabKey)}>
          {/* ── Segmented tab bar: horizontal scroll on mobile ── */}
          <div className="space-y-3">
            <div className="-mx-3 sm:mx-0 overflow-x-auto no-scrollbar">
              <TabsList className="inline-flex w-max gap-1 px-3 sm:px-0">
                <TabsTrigger value="CONSOLIDADO" className="gap-1 whitespace-nowrap">
                  <BarChart3 className="h-3.5 w-3.5" /> Consolidado
                </TabsTrigger>
                {(Object.keys(SALE_TYPE_LABEL) as SaleType[]).map((k) => (
                  <TabsTrigger key={k} value={k} className="whitespace-nowrap">
                    {SALE_TYPE_LABEL[k]}
                  </TabsTrigger>
                ))}
                <TabsTrigger value="GRAFICO" className="gap-1 whitespace-nowrap">
                  <BarChart3 className="h-3.5 w-3.5" /> Gráfico Anual
                </TabsTrigger>
                <TabsTrigger value="CONFIGURACOES" className="gap-1 whitespace-nowrap">
                  <Settings className="h-3.5 w-3.5" /> Configurações
                </TabsTrigger>
              </TabsList>
            </div>

            {/* Search row — toggle icon on mobile, inline on desktop */}
            {isDataTab && (
              <div className="flex items-center gap-2">
                {/* Mobile: collapsible search */}
                <div className="flex-1 sm:hidden">
                  {showSearch ? (
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        autoFocus
                        placeholder="Buscar cliente, produto ou NF..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="h-10 pl-9 pr-9"
                      />
                      <Button
                        variant="ghost"
                        size="icon"
                        className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8"
                        onClick={() => {
                          setSearch("");
                          setShowSearch(false);
                        }}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full h-9 justify-start text-muted-foreground"
                      onClick={() => setShowSearch(true)}
                    >
                      <Search className="h-4 w-4 mr-2" /> Buscar...
                    </Button>
                  )}
                </div>

                {/* Desktop: persistent inline search */}
                <div className="hidden sm:block ml-auto">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Buscar cliente, produto ou NF..."
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      className="pl-9 w-72"
                    />
                  </div>
                </div>

                {filtered.length !== sales.length && (
                  <Badge variant="secondary" className="flex-shrink-0">
                    {filtered.length} de {sales.length}
                  </Badge>
                )}
              </div>
            )}
          </div>

          {/* ── Data tabs ── */}
          {(["CONSOLIDADO", "NF", "PR", "AVULSO", "AVARIA"] as const).map(
            (t) => (
              <TabsContent key={t} value={t} className="mt-4">
                {isMobile ? (
                  /* Mobile: just the data, form moves to FAB+Drawer */
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base">
                        {t === "CONSOLIDADO"
                          ? "Todos os registros"
                          : SALE_TYPE_LABEL[t as SaleType]}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="px-3 sm:px-6">
                      {isLoading ? (
                        <div className="space-y-2">
                          {[0, 1, 2, 3].map((i) => (
                            <Skeleton key={i} className="h-20 w-full" />
                          ))}
                        </div>
                      ) : (
                        <SalesTable
                          sales={filtered}
                          onChanged={refresh}
                          canDelete
                        />
                      )}
                    </CardContent>
                  </Card>
                ) : (
                  /* Desktop: form + table side by side */
                  <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
                    <SaleForm onSaved={refresh} />
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">
                          {t === "CONSOLIDADO"
                            ? "Todos os registros"
                            : SALE_TYPE_LABEL[t as SaleType]}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        {isLoading ? (
                          <div className="space-y-2">
                            {[0, 1, 2, 3, 4].map((i) => (
                              <Skeleton key={i} className="h-10 w-full" />
                            ))}
                          </div>
                        ) : (
                          <SalesTable
                            sales={filtered}
                            onChanged={refresh}
                            canDelete
                          />
                        )}
                      </CardContent>
                    </Card>
                  </div>
                )}
              </TabsContent>
            ),
          )}

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


          <TabsContent value="CONFIGURACOES" className="mt-4">
            <SebraeVerifyTab />
          </TabsContent>
        </Tabs>
      </main>

      {/* ─── Mobile FAB + Drawer for "Nova venda" ─── */}
      {isMobile && isDataTab && (
        <>
          <Button
            size="icon"
            className="fixed right-4 bottom-safe-or-4 z-40 h-14 w-14 rounded-full shadow-xl"
            onClick={() => setFormOpen(true)}
            aria-label="Nova venda"
          >
            <Plus className="h-6 w-6" />
          </Button>

          <Drawer open={formOpen} onOpenChange={setFormOpen}>
            <DrawerContent className="max-h-[92vh]">
              <DrawerHeader className="text-left">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <DrawerTitle>Nova venda</DrawerTitle>
                    <DrawerDescription>
                      Preencha os campos abaixo. O total é calculado automaticamente.
                    </DrawerDescription>
                  </div>
                  <DrawerClose asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8 -mt-1">
                      <X className="h-4 w-4" />
                    </Button>
                  </DrawerClose>
                </div>
              </DrawerHeader>
              <div className="px-4 pb-2 overflow-y-auto">
                <SaleForm
                  embedded
                  defaultType={
                    tab === "CONSOLIDADO" ? "AVULSO" : (tab as SaleType)
                  }
                  onSaved={() => {
                    refresh();
                    setFormOpen(false);
                  }}
                />
              </div>
            </DrawerContent>
          </Drawer>
        </>
      )}
    </div>
  );
}
