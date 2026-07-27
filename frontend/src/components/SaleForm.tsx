import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { createSale, SALE_TYPE_LABEL, type SaleType, formatBRL } from "@/lib/sales";

interface Props {
  defaultType?: SaleType;
  onSaved?: () => void;
  /**
   * When true, render without the outer <Card> wrapper. The host
   * (e.g. mobile Drawer) provides its own chrome and footer.
   * The submit button is then absent — the host must render a sticky CTA
   * that calls onSubmit().
   */
  embedded?: boolean;
}

const today = () => new Date().toISOString().slice(0, 10);

export function SaleForm({ defaultType = "AVULSO", onSaved, embedded = false }: Props) {
  const [saleType, setSaleType] = useState<SaleType>(defaultType);
  const [saleDate, setSaleDate] = useState(today());
  const [client, setClient] = useState("");
  const [product, setProduct] = useState("");
  const [nfNumber, setNfNumber] = useState("");
  const [quantity, setQuantity] = useState("");
  const [unitPrice, setUnitPrice] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);

  // BR-format numeric inputs: accept comma OR dot
  const parseBR = (s: string) => parseFloat(s.replace(",", ".") || "0");
  const q = parseBR(quantity);
  const p = parseBR(unitPrice);
  const total = isFinite(q) && isFinite(p) ? q * p : 0;

  async function submit(e?: React.FormEvent) {
    e?.preventDefault();
    if (!saleDate) return toast.error("Informe a data");
    setLoading(true);
    try {
      await createSale({
        sale_type: saleType,
        sale_date: saleDate,
        client: client.trim() || null,
        product: product.trim() || null,
        nf_number: nfNumber.trim() || null,
        quantity: q,
        unit_price: p,
        notes: notes.trim() || null,
        source: "manual",
      });
      toast.success("Venda adicionada!");
      setClient("");
      setProduct("");
      setNfNumber("");
      setQuantity("");
      setUnitPrice("");
      setNotes("");
      onSaved?.();
    } catch (err: any) {
      toast.error(err.message ?? "Erro ao salvar");
    } finally {
      setLoading(false);
    }
  }

  const fields = (
    <form
      onSubmit={submit}
      className={`grid gap-4 ${embedded ? "" : "md:grid-cols-2"}`}
    >
      <div className="space-y-2">
        <Label>Tipo</Label>
        <Select value={saleType} onValueChange={(v) => setSaleType(v as SaleType)}>
          <SelectTrigger className="h-11">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(SALE_TYPE_LABEL) as SaleType[]).map((k) => (
              <SelectItem key={k} value={k}>
                {SALE_TYPE_LABEL[k]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Data</Label>
        <Input
          type="date"
          className="h-11"
          value={saleDate}
          onChange={(e) => setSaleDate(e.target.value)}
          required
        />
      </div>

      <div className={`space-y-2 ${embedded ? "" : "md:col-span-2"}`}>
        <Label>Cliente</Label>
        <Input
          className="h-11"
          value={client}
          onChange={(e) => setClient(e.target.value)}
          placeholder="Ex.: GOIANA / LIBERDADE"
        />
      </div>

      <div className="space-y-2">
        <Label>Produto</Label>
        <Input
          className="h-11"
          value={product}
          onChange={(e) => setProduct(e.target.value)}
          placeholder="Ex.: MACAXEIRA"
        />
      </div>

      <div className="space-y-2">
        <Label>Nº Nota / NF-e</Label>
        <Input
          className="h-11"
          value={nfNumber}
          onChange={(e) => setNfNumber(e.target.value)}
          placeholder="Opcional"
          inputMode="numeric"
        />
      </div>

      <div className={`grid grid-cols-2 gap-3 ${embedded ? "" : "md:col-span-2"}`}>
        <div className="space-y-2">
          <Label>Quantidade</Label>
          <Input
            className="h-11"
            type="text"
            inputMode="decimal"
            pattern="[0-9.,]*"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="0"
          />
        </div>
        <div className="space-y-2">
          <Label>Preço unit. (R$)</Label>
          <Input
            className="h-11"
            type="text"
            inputMode="decimal"
            pattern="[0-9.,]*"
            value={unitPrice}
            onChange={(e) => setUnitPrice(e.target.value)}
            placeholder="0,00"
          />
        </div>
      </div>

      <div className={`space-y-2 ${embedded ? "" : "md:col-span-2"}`}>
        <Label>Observações</Label>
        <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} />
      </div>

      {/* Desktop / non-embedded mode: traditional inline footer */}
      {!embedded && (
        <div className="md:col-span-2 flex items-center justify-between gap-4 pt-2">
          <div className="text-lg">
            Total: <span className="font-semibold">{formatBRL(total)}</span>
          </div>
          <Button type="submit" disabled={loading} className="h-11">
            {loading ? "Salvando..." : "Adicionar venda"}
          </Button>
        </div>
      )}
    </form>
  );

  if (embedded) {
    // Drawer footer (live total + CTA) is rendered separately for sticky behavior.
    return (
      <>
        {fields}
        {/* Sticky live-total bar — rendered inside the embedded layout's scroll area */}
        <div className="sticky bottom-0 left-0 right-0 -mx-1 mt-4 pt-3 pb-safe-or-4 bg-background border-t z-10">
          <div className="flex items-center justify-between gap-3 px-1">
            <div>
              <div className="text-xs text-muted-foreground">Total</div>
              <div className="text-xl font-bold text-primary leading-tight">
                {formatBRL(total)}
              </div>
            </div>
            <Button
              type="button"
              onClick={() => submit()}
              disabled={loading}
              className="h-12 px-6 text-base"
            >
              {loading ? "Salvando..." : "Adicionar venda"}
            </Button>
          </div>
        </div>
      </>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Nova venda</CardTitle>
      </CardHeader>
      <CardContent>{fields}</CardContent>
    </Card>
  );
}
