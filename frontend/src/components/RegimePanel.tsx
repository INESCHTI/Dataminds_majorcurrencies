"use client";

import { useRegimeClassification, useRegimeMutation } from "@/hooks/useFastAPI";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { 
    TrendingUp, 
    Minus, 
    AlertTriangle, 
    Activity, 
    RefreshCw,
    TrendingDown,
    Brain,
    Shield,
    BarChart3
} from "lucide-react";

interface RegimePanelProps {
    pair: string;
}

const regimeConfig: Record<string, { 
    icon: React.ElementType; 
    color: string; 
    bgColor: string;
    label: string;
    description: string;
}> = {
    trending: {
        icon: TrendingUp,
        color: "text-green-600",
        bgColor: "bg-green-50",
        label: "Trending",
        description: "Strong directional momentum - Technical agent dominates"
    },
    ranging: {
        icon: Minus,
        color: "text-blue-600",
        bgColor: "bg-blue-50",
        label: "Ranging",
        description: "Mean-reversion environment - Balanced weights"
    },
    crisis: {
        icon: AlertTriangle,
        color: "text-red-600",
        bgColor: "bg-red-50",
        label: "Crisis",
        description: "High volatility - Geopolitical & Macro agents critical"
    },
    recovery: {
        icon: Activity,
        color: "text-purple-600",
        bgColor: "bg-purple-50",
        label: "Recovery",
        description: "Normalization phase - Macro agent leads"
    }
};

export function RegimePanel({ pair }: RegimePanelProps) {
    const { data: regime, isLoading, error, refetch } = useRegimeClassification(pair);
    const classifyMutation = useRegimeMutation();

    const handleReclassify = () => {
        classifyMutation.mutate({ pair, periods: 50 });
    };

    if (isLoading) {
        return (
            <Card>
                <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                        <CardTitle className="text-lg font-semibold flex items-center gap-2">
                            <Brain className="w-5 h-5" />
                            Market Regime
                        </CardTitle>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-20 w-full" />
                    <Skeleton className="h-16 w-full" />
                </CardContent>
            </Card>
        );
    }

    if (error || !regime?.success) {
        return (
            <Card>
                <CardHeader className="pb-3">
                    <CardTitle className="text-lg font-semibold flex items-center gap-2">
                        <Brain className="w-5 h-5" />
                        Market Regime
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-2 text-red-500">
                        <AlertTriangle className="w-5 h-5" />
                        <span>Failed to classify regime</span>
                    </div>
                    <Button 
                        onClick={() => refetch()} 
                        variant="outline" 
                        size="sm" 
                        className="mt-2"
                    >
                        <RefreshCw className="w-4 h-4 mr-1" />
                        Retry
                    </Button>
                </CardContent>
            </Card>
        );
    }

    const config = regimeConfig[regime.regime] || regimeConfig.ranging;
    const Icon = config.icon;

    return (
        <Card className={`${config.bgColor} border-l-4 border-l-current`}>
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-semibold flex items-center gap-2">
                        <Brain className="w-5 h-5" />
                        Market Regime
                    </CardTitle>
                    <div className="flex items-center gap-2">
                        <Button 
                            onClick={handleReclassify} 
                            disabled={classifyMutation.isPending}
                            variant="outline"
                            size="sm"
                        >
                            {classifyMutation.isPending ? (
                                <RefreshCw className="w-4 h-4 animate-spin" />
                            ) : (
                                <RefreshCw className="w-4 h-4" />
                            )}
                        </Button>
                        <Badge className={`${config.color} bg-white`}>
                            HMM
                        </Badge>
                    </div>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Regime Display */}
                <div className={`flex items-center gap-4 p-3 rounded-lg bg-white/50`}>
                    <div className={`p-3 rounded-full bg-white ${config.color}`}>
                        <Icon className="w-8 h-8" />
                    </div>
                    <div>
                        <div className={`text-2xl font-bold ${config.color}`}>
                            {config.label}
                        </div>
                        <div className="text-sm text-muted-foreground">
                            {config.description}
                        </div>
                    </div>
                </div>

                {/* Confidence & Metrics */}
                <div className="grid grid-cols-3 gap-2">
                    <div className="p-2 rounded bg-white/50 text-center">
                        <div className="text-xs text-muted-foreground">Confidence</div>
                        <div className="font-semibold">{(regime.confidence * 100).toFixed(0)}%</div>
                    </div>
                    <div className="p-2 rounded bg-white/50 text-center">
                        <div className="text-xs text-muted-foreground">Volatility</div>
                        <div className="font-semibold">{(regime.volatility * 100).toFixed(1)}%</div>
                    </div>
                    <div className="p-2 rounded bg-white/50 text-center">
                        <div className="text-xs text-muted-foreground">Risk Adj</div>
                        <div className="font-semibold">{regime.risk_adjustment.toFixed(1)}x</div>
                    </div>
                </div>

                {/* Adaptive Weights */}
                <div>
                    <div className="text-sm font-medium mb-2 flex items-center gap-2">
                        <BarChart3 className="w-4 h-4" />
                        Adaptive Agent Weights
                    </div>
                    <div className="space-y-2">
                        {Object.entries(regime.agent_recommendations).map(([agent, weight]) => (
                            <div key={agent} className="flex items-center gap-2">
                                <span className="text-sm capitalize w-24">{agent}</span>
                                <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full transition-all duration-500 ${
                                            weight > 0.35 ? 'bg-green-500' :
                                            weight > 0.25 ? 'bg-blue-500' :
                                            'bg-gray-500'
                                        }`}
                                        style={{ width: `${weight * 100}%` }}
                                    />
                                </div>
                                <span className="text-xs w-10 text-right">{(weight * 100).toFixed(0)}%</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Risk Warning for Crisis */}
                {regime.regime === 'crisis' && (
                    <div className="p-3 rounded bg-red-100 text-red-800 text-sm flex items-start gap-2">
                        <Shield className="w-4 h-4 mt-0.5" />
                        <div>
                            <strong>Crisis regime detected.</strong> Position size reduced by {Math.round((1 - regime.risk_adjustment) * 100)}%. 
                            Geopolitical and Macro agents have increased weight.
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
