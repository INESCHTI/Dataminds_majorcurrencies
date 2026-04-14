"use client";

import { useCOTSignal } from "@/hooks/useFastAPI";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, TrendingDown, Minus, AlertTriangle, Users, Building2, LucideIcon } from "lucide-react";
import type { COTSignalResponse } from "@/types/fastapi";

interface COTPanelProps {
    pair: string;
}

interface SignalConfig {
    color: string;
    text: string;
    label: string;
    icon: LucideIcon;
}

type SignalType = 'strong_buy' | 'buy' | 'neutral' | 'sell' | 'strong_sell';

const signalConfig: Record<SignalType, SignalConfig> = {
    strong_buy: { color: "bg-green-600", text: "text-green-700", label: "Strong Buy", icon: TrendingUp },
    buy: { color: "bg-green-500", text: "text-green-600", label: "Buy", icon: TrendingUp },
    neutral: { color: "bg-gray-500", text: "text-gray-600", label: "Neutral", icon: Minus },
    sell: { color: "bg-red-500", text: "text-red-600", label: "Sell", icon: TrendingDown },
    strong_sell: { color: "bg-red-600", text: "text-red-700", label: "Strong Sell", icon: TrendingDown },
};

export function COTPanel({ pair }: COTPanelProps) {
    const { data: cot, isLoading, error } = useCOTSignal(pair);

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">COT Positioning</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                </CardContent>
            </Card>
        );
    }

    if (error || !cot) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">COT Positioning</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-2 text-red-500">
                        <AlertTriangle className="w-5 h-5" />
                        <span>Failed to load COT data</span>
                    </div>
                </CardContent>
            </Card>
        );
    }

    const safeSignal = (cot.signal as SignalType) || 'neutral';
    const config = signalConfig[safeSignal];
    const Icon = config.icon;

    const base = cot.base_positioning;
    const quote = cot.quote_positioning;

    return (
        <Card>
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-semibold">COT Positioning</CardTitle>
                    <Badge variant="outline" className="text-xs">
                        Institutional
                    </Badge>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Main Signal */}
                <div className="flex items-center gap-4">
                    <div className={`p-3 rounded-full ${config.color} bg-opacity-20`}>
                        <Icon className={`w-8 h-8 ${config.text}`} />
                    </div>
                    <div>
                        <div className={`text-2xl font-bold ${config.text}`}>
                            {config.label}
                        </div>
                        <div className="text-sm text-muted-foreground">
                            Contrarian Signal: {(cot.confidence * 100).toFixed(0)}% confidence
                        </div>
                    </div>
                </div>

                {/* Positioning Bars */}
                <div className="space-y-3 pt-2">
                    {/* Base Currency */}
                    <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                            <span className="font-medium">{pair.slice(0, 3)} (Base)</span>
                            <span className={base.positioning?.signal === 'bullish' ? 'text-green-600' : 
                                            base.positioning?.signal === 'bearish' ? 'text-red-600' : 'text-gray-600'}>
                                {base.positioning?.managed_net?.toLocaleString()} net
                            </span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden flex">
                            <div 
                                className={`h-full ${base.positioning?.managed_net > 0 ? 'bg-green-500' : 'bg-red-500'}`}
                                style={{ width: `${Math.min(100, Math.abs(base.positioning?.managed_extreme_pct || 0) * 100)}%` }}
                            />
                        </div>
                        <div className="text-xs text-muted-foreground">
                            Hedge funds: {(base.positioning?.managed_extreme_pct * 100).toFixed(0)}% extreme
                        </div>
                    </div>

                    {/* Quote Currency */}
                    <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                            <span className="font-medium">{pair.slice(3, 6)} (Quote)</span>
                            <span className={quote.positioning?.signal === 'bullish' ? 'text-green-600' : 
                                            quote.positioning?.signal === 'bearish' ? 'text-red-600' : 'text-gray-600'}>
                                {quote.positioning?.managed_net?.toLocaleString()} net
                            </span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden flex">
                            <div 
                                className={`h-full ${quote.positioning?.managed_net > 0 ? 'bg-green-500' : 'bg-red-500'}`}
                                style={{ width: `${Math.min(100, Math.abs(quote.positioning?.managed_extreme_pct || 0) * 100)}%` }}
                            />
                        </div>
                        <div className="text-xs text-muted-foreground">
                            Hedge funds: {(quote.positioning?.managed_extreme_pct * 100).toFixed(0)}% extreme
                        </div>
                    </div>
                </div>

                {/* Explanation */}
                <div className="p-3 rounded-lg bg-blue-50 text-sm">
                    <div className="flex items-start gap-2">
                        <Building2 className="w-4 h-4 text-blue-600 mt-0.5" />
                        <div>
                            <span className="font-medium text-blue-900">Contrarian Strategy:</span>
                            <span className="text-blue-800"> When hedge funds are extremely positioned, the market often reverses. This signal is opposite to managed money positioning.</span>
                        </div>
                    </div>
                </div>

                {/* Open Interest */}
                <div className="flex justify-between text-xs text-muted-foreground pt-2 border-t">
                    <span>Open Interest</span>
                    <span>{(base.positioning?.total_open_interest || 0).toLocaleString()}</span>
                </div>
            </CardContent>
        </Card>
    );
}
