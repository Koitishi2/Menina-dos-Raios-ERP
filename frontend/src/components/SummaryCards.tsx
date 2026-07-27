import { Card, CardContent } from "@/components/ui/card";
import {
  formatBRL,
  SALE_TYPE_LABEL,
  SALE_TYPE_BG_LIGHT,
  SALE_TYPE_FG,
  type Sale,
  type SaleType,
} from "@/lib/sales";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

const TYPES: SaleType[] = ["NF", "PR", "AVULSO", "AVARIA"];

/**
 * Mobile-first KPI block.
 *  - Hero card: total + month-over-month delta (5-second rule)
 *  - 2×2 tinted grid: subtotals per channel, each with share-of-total %
 *  - Single column on phones, side-by-side on tablet, 1+4 horizontal on desktop
 */
export function SummaryCards({ sales }: { sales: Sale[] }) {
  const now = new Date();
  const currentMonth = now.getMonth(); // 0-11
  const currentYear = now.getFullYear();

  // Aggregate
  let total = 0;
  let totalThisMonth = 0;
  let totalPrevMonth = 0;
  const byType: Record<SaleType, number> = { NF: 0, PR: 0, AVULSO: 0, AVARIA: 0 };

  for (const s of sales) {
    const v = Number(s.total) || 0;
    total += v;
    byType[s.sale_type] = (byType[s.sale_type] ?? 0) + v;

    if (s.sale_date) {
      const d = new Date(s.sale_date + "T00:00:00");
      if (d.getFullYear() === currentYear) {
        if (d.getMonth() === currentMonth) totalThisMonth += v;
        else if (
          d.getMonth() === (currentMonth === 0 ? 11 : currentMonth - 1) &&
          (currentMonth !== 0 || d.getFullYear() === currentYear - 1)
        )
          totalPrevMonth += v;
      }
    }
  }

  const delta =
    totalPrevMonth > 0
      ? ((totalThisMonth - totalPrevMonth) / totalPrevMonth) * 100
      : null;

  const TrendIcon = delta === null ? Minus : delta >= 0 ? TrendingUp : TrendingDown;
  const trendColor =
    delta === null
      ? "text-white/70"
      : delta >= 0
        ? "text-emerald-200"
        : "text-red-200";
  const trendLabel =
    delta === null
      ? "Sem dados do mês anterior"
      : `${delta >= 0 ? "+" : ""}${delta.toFixed(1)}% vs mês anterior`;

  return (
    <div className="grid gap-3 md:grid-cols-5">
      {/* HERO — total + delta */}
      <Card className="md:col-span-2 bg-primary text-primary-foreground border-0 shadow-md overflow-hidden relative">
        <CardContent className="p-5">
          <div className="text-xs uppercase tracking-wider opacity-80">
            Total consolidado
          </div>
          <div className="mt-1 text-3xl md:text-4xl font-bold leading-tight break-words">
            {formatBRL(total)}
          </div>
          <div className={`mt-3 flex items-center gap-1.5 text-xs ${trendColor}`}>
            <TrendIcon className="h-3.5 w-3.5 flex-shrink-0" />
            <span className="truncate">{trendLabel}</span>
          </div>
          <div className="mt-1 text-[11px] opacity-75">
            {sales.length} registro{sales.length === 1 ? "" : "s"} no total
          </div>
        </CardContent>
      </Card>

      {/* 2×2 grid of channel subtotals */}
      <div className="grid grid-cols-2 gap-3 md:col-span-3 md:grid-cols-4">
        {TYPES.map((k) => {
          const val = byType[k] ?? 0;
          const share = total > 0 ? (val / total) * 100 : 0;
          return (
            <Card
              key={k}
              className={`${SALE_TYPE_BG_LIGHT[k]} border shadow-none`}
            >
              <CardContent className="p-3 md:p-4">
                <div
                  className={`text-[11px] font-medium uppercase tracking-wider ${SALE_TYPE_FG[k]} truncate`}
                >
                  {SALE_TYPE_LABEL[k]}
                </div>
                <div className="mt-1 text-base md:text-xl font-semibold text-foreground break-words leading-tight">
                  {formatBRL(val)}
                </div>
                <div className="mt-1.5 text-[10px] text-muted-foreground">
                  {share.toFixed(1)}% do total
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
