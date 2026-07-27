import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Trash2, Inbox } from "lucide-react";
import {
  type Sale,
  formatBRL,
  deleteSale,
  SALE_TYPE_LABEL,
  SALE_TYPE_COLOR,
} from "@/lib/sales";
import { toast } from "sonner";
import { useIsMobile } from "@/hooks/use-mobile";

interface Props {
  sales: Sale[];
  onChanged?: () => void;
  canDelete?: boolean;
}

function fmtDate(d: string) {
  return new Date(d + "T00:00:00").toLocaleDateString("pt-BR");
}

export function SalesTable({ sales, onChanged, canDelete = true }: Props) {
  const isMobile = useIsMobile();
  const [pending, setPending] = useState<Sale | null>(null);
  const [deleting, setDeleting] = useState(false);

  async function confirmDelete() {
    if (!pending) return;
    setDeleting(true);
    try {
      await deleteSale(pending.id);
      toast.success("Venda excluída");
      onChanged?.();
      setPending(null);
    } catch (e: any) {
      toast.error(e.message ?? "Erro ao excluir");
    } finally {
      setDeleting(false);
    }
  }

  if (sales.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="rounded-full bg-muted p-3 mb-3">
          <Inbox className="h-6 w-6 text-muted-foreground" />
        </div>
        <div className="font-medium text-foreground">Nenhuma venda registrada</div>
        <div className="mt-1 text-sm text-muted-foreground">
          Use o botão <span className="font-medium text-primary">Nova venda</span> para começar.
        </div>
      </div>
    );
  }

  // ─── Mobile: card list (no horizontal scroll) ────────────────────────
  if (isMobile) {
    return (
      <>
        <ul className="space-y-2.5">
          {sales.map((s) => (
            <li
              key={s.id}
              className="rounded-lg border bg-card p-3 shadow-sm"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge
                      className={`${SALE_TYPE_COLOR[s.sale_type]} text-white text-[10px] px-1.5 py-0`}
                    >
                      {SALE_TYPE_LABEL[s.sale_type]}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {fmtDate(s.sale_date)}
                    </span>
                  </div>
                  <div className="mt-1.5 font-medium text-sm leading-snug truncate">
                    {s.client ?? "Sem cliente"}
                  </div>
                  <div className="text-xs text-muted-foreground truncate">
                    {s.product ?? "—"}
                    {s.nf_number ? ` · NF ${s.nf_number}` : ""}
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <div className="font-semibold text-sm text-primary">
                    {formatBRL(Number(s.total))}
                  </div>
                  <div className="text-[10px] text-muted-foreground">
                    {Number(s.quantity).toLocaleString("pt-BR")} ×{" "}
                    {formatBRL(Number(s.unit_price))}
                  </div>
                </div>
              </div>
              {canDelete && (
                <div className="mt-2 pt-2 border-t flex justify-end">
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-8 text-red-600 hover:text-red-700 hover:bg-red-50 -mr-2"
                    onClick={() => setPending(s)}
                  >
                    <Trash2 className="h-3.5 w-3.5 mr-1" /> Excluir
                  </Button>
                </div>
              )}
            </li>
          ))}
        </ul>

        <DeleteDialog
          pending={pending}
          deleting={deleting}
          onCancel={() => setPending(null)}
          onConfirm={confirmDelete}
        />
      </>
    );
  }

  // ─── Desktop: table ──────────────────────────────────────────────────
  return (
    <>
      <div className="overflow-x-auto rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Data</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Cliente</TableHead>
              <TableHead>Produto</TableHead>
              <TableHead>Nº NF</TableHead>
              <TableHead className="text-right">Qt</TableHead>
              <TableHead className="text-right">P. Unit.</TableHead>
              <TableHead className="text-right">Total</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sales.map((s) => (
              <TableRow key={s.id}>
                <TableCell>{fmtDate(s.sale_date)}</TableCell>
                <TableCell>
                  <Badge
                    className={`${SALE_TYPE_COLOR[s.sale_type]} text-white`}
                  >
                    {SALE_TYPE_LABEL[s.sale_type]}
                  </Badge>
                </TableCell>
                <TableCell className="max-w-[220px] truncate">
                  {s.client ?? "—"}
                </TableCell>
                <TableCell>{s.product ?? "—"}</TableCell>
                <TableCell>{s.nf_number ?? "—"}</TableCell>
                <TableCell className="text-right">
                  {Number(s.quantity).toLocaleString("pt-BR")}
                </TableCell>
                <TableCell className="text-right">
                  {formatBRL(Number(s.unit_price))}
                </TableCell>
                <TableCell className="text-right font-medium">
                  {formatBRL(Number(s.total))}
                </TableCell>
                <TableCell>
                  {canDelete && (
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => setPending(s)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <DeleteDialog
        pending={pending}
        deleting={deleting}
        onCancel={() => setPending(null)}
        onConfirm={confirmDelete}
      />
    </>
  );
}

function DeleteDialog({
  pending,
  deleting,
  onCancel,
  onConfirm,
}: {
  pending: Sale | null;
  deleting: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <AlertDialog open={!!pending} onOpenChange={(o) => !o && onCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Excluir esta venda?</AlertDialogTitle>
          <AlertDialogDescription>
            {pending && (
              <>
                {fmtDate(pending.sale_date)} · {pending.client ?? "Sem cliente"} ·{" "}
                <span className="font-medium">
                  {formatBRL(Number(pending.total))}
                </span>
                <br />
                Esta ação não pode ser desfeita.
              </>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleting}>Cancelar</AlertDialogCancel>
          <AlertDialogAction
            onClick={(e) => {
              e.preventDefault();
              onConfirm();
            }}
            disabled={deleting}
            className="bg-red-600 hover:bg-red-700 focus:ring-red-600"
          >
            {deleting ? "Excluindo..." : "Excluir"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
