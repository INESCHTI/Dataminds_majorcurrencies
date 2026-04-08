import prisma from "@/lib/prisma";

export interface TradeAggregate {
    total_closed: number;
    win_rate: number;
    total_pnl: number;
    avg_pnl: number;
    profit_factor: number;
    max_drawdown: number;
    by_pair: Array<{
        pair: string;
        closed: number;
        wins: number;
        losses: number;
        win_rate: number;
        total_pnl: number;
        avg_pnl: number;
    }>;
    recent_closed: Array<{
        id: number;
        pair: string;
        side: string;
        size: number;
        entryPrice: number;
        currentPrice: number;
        stopLoss: number | null;
        takeProfit: number | null;
        pnl: number;
        pnlPct: number;
        openedAt: string;
        closedAt: string | null;
    }>;
}

function computeMaxDrawdown(pnls: number[]): number {
    if (pnls.length === 0) return 0;
    let equity = 0;
    let peak = 0;
    let maxDd = 0;

    for (const pnl of pnls) {
        equity += pnl;
        if (equity > peak) peak = equity;
        const dd = peak - equity;
        if (dd > maxDd) maxDd = dd;
    }

    const denom = Math.max(Math.abs(peak), 1);
    return Math.max(0, Math.min(1, maxDd / denom));
}

export async function aggregateTradeMetrics(userId?: string): Promise<TradeAggregate> {
    try {
        const where = {
            status: "CLOSED",
            ...(userId ? { userId } : {}),
        };

        const closed = await prisma.position.findMany({
            where,
            orderBy: { closedAt: "desc" },
            take: 500,
        });

        if (closed.length === 0) {
            return {
                total_closed: 0,
                win_rate: 0,
                total_pnl: 0,
                avg_pnl: 0,
                profit_factor: 0,
                max_drawdown: 0,
                by_pair: [],
                recent_closed: [],
            };
        }

        const wins = closed.filter((p) => (p.pnl ?? 0) > 0);
        const losses = closed.filter((p) => (p.pnl ?? 0) < 0);
        const totalPnl = closed.reduce((acc, p) => acc + (p.pnl ?? 0), 0);
        const grossProfit = wins.reduce((acc, p) => acc + Math.max(0, p.pnl ?? 0), 0);
        const grossLoss = losses.reduce((acc, p) => acc + Math.abs(Math.min(0, p.pnl ?? 0)), 0);

        const byPairMap = new Map<string, typeof closed>();
        for (const row of closed) {
            if (!byPairMap.has(row.pair)) byPairMap.set(row.pair, [] as any);
            byPairMap.get(row.pair)?.push(row as any);
        }

        const byPair = Array.from(byPairMap.entries()).map(([pair, items]) => {
            const pairWins = items.filter((x) => (x.pnl ?? 0) > 0).length;
            const pairLosses = items.filter((x) => (x.pnl ?? 0) < 0).length;
            const pairTotal = items.reduce((acc, x) => acc + (x.pnl ?? 0), 0);
            return {
                pair,
                closed: items.length,
                wins: pairWins,
                losses: pairLosses,
                win_rate: items.length ? pairWins / items.length : 0,
                total_pnl: pairTotal,
                avg_pnl: items.length ? pairTotal / items.length : 0,
            };
        });

        const pnlsAsc = closed
            .slice()
            .sort((a, b) => Number(new Date(a.closedAt ?? a.openedAt)) - Number(new Date(b.closedAt ?? b.openedAt)))
            .map((x) => x.pnl ?? 0);

        return {
            total_closed: closed.length,
            win_rate: closed.length ? wins.length / closed.length : 0,
            total_pnl: totalPnl,
            avg_pnl: totalPnl / closed.length,
            profit_factor: grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? 99 : 0,
            max_drawdown: computeMaxDrawdown(pnlsAsc),
            by_pair: byPair,
            recent_closed: closed.slice(0, 120).map((p) => ({
                id: p.id,
                pair: p.pair,
                side: p.side,
                size: p.size,
                entryPrice: p.entryPrice,
                currentPrice: p.currentPrice,
                stopLoss: p.stopLoss,
                takeProfit: p.takeProfit,
                pnl: p.pnl,
                pnlPct: p.pnlPct,
                openedAt: p.openedAt.toISOString(),
                closedAt: p.closedAt ? p.closedAt.toISOString() : null,
            })),
        };
    } catch {
        return {
            total_closed: 0,
            win_rate: 0,
            total_pnl: 0,
            avg_pnl: 0,
            profit_factor: 0,
            max_drawdown: 0,
            by_pair: [],
            recent_closed: [],
        };
    }
}
