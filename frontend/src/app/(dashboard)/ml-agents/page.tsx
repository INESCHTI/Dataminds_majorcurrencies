"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { 
    useLSTMSignal, 
    useXGBoostMacroSignal, 
    useXGBoostFusion,
    useRiskMetrics 
} from "@/hooks/useFastAPI";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { 
    Brain, 
    TrendingUp, 
    BarChart3, 
    Shield, 
    Activity,
    Cpu,
    AlertTriangle,
    CheckCircle,
    RefreshCw,
    Play,
    Zap,
    Target,
    LineChart,
    PieChart,
    Info,
    Sparkles
} from "lucide-react";

const CURRENCY_PAIRS = [
    { value: "EURUSD", label: "EUR/USD" },
    { value: "GBPUSD", label: "GBP/USD" },
    { value: "USDJPY", label: "USD/JPY" },
    { value: "USDCHF", label: "USD/CHF" },
    { value: "AUDUSD", label: "AUD/USD" },
    { value: "NZDUSD", label: "NZD/USD" },
    { value: "USDCAD", label: "USD/CAD" },
];

export default function MLAgentsPage() {
    const [selectedPair, setSelectedPair] = useState("EURUSD");
    const queryClient = useQueryClient();
    
    const { data: lstm, isLoading: lstmLoading, error: lstmError } = useLSTMSignal(selectedPair);
    const { data: macro, isLoading: macroLoading, error: macroError } = useXGBoostMacroSignal(selectedPair);
    const { data: fusion, isLoading: fusionLoading, error: fusionError } = useXGBoostFusion(selectedPair);
    const { data: risk, isLoading: riskLoading, error: riskError } = useRiskMetrics(selectedPair);

    const refreshAll = () => {
        queryClient.invalidateQueries({ queryKey: ["lstm", selectedPair] });
        queryClient.invalidateQueries({ queryKey: ["xgboost-macro", selectedPair] });
        queryClient.invalidateQueries({ queryKey: ["fusion", selectedPair] });
        queryClient.invalidateQueries({ queryKey: ["risk", selectedPair] });
    };

    const getDirectionColor = (direction: string) => {
        switch (direction) {
            case 'BUY': return 'bg-green-600 text-green-50';
            case 'SELL': return 'bg-red-600 text-red-50';
            default: return 'bg-gray-600 text-gray-50';
        }
    };

    const getDirectionBg = (direction: string) => {
        switch (direction) {
            case 'BUY': return 'bg-green-900 border-green-700';
            case 'SELL': return 'bg-red-900 border-red-700';
            default: return 'bg-gray-800 border-gray-600';
        }
    };

    const getRiskColor = (level: string) => {
        switch (level) {
            case 'LOW': return 'text-green-600';
            case 'MODERATE': return 'text-yellow-600';
            case 'HIGH': return 'text-orange-600';
            case 'EXTREME': return 'text-red-600';
            default: return 'text-gray-600';
        }
    };

    const getRiskMargin = (data: any) => {
        // Use real risk margins from API if available
        if (data?.risk_margins) {
            const rm = data.risk_margins;
            return {
                margin: rm.margin_pct?.toFixed(2) || '2.00',
                stopLoss: `-${rm.stop_loss_pct?.toFixed(2) || '2.00'}%`,
                takeProfit: `+${rm.take_profit_pct?.toFixed(2) || '4.00'}%`,
                riskReward: `1:${rm.risk_reward?.toFixed(2) || '2.00'}`,
                positionSize: `${rm.position_size_pct?.toFixed(0) || '100'}%`,
                leverage: rm.recommended_leverage?.toFixed(1) || '1.0',
                direction: rm.direction || 'NEUTRAL'
            };
        }
        
        // Fallback: calculate based on direction and confidence
        const direction = data?.direction || 'NEUTRAL';
        const confidence = data?.confidence || 0.5;
        const baseMargin = direction === 'BUY' ? 1.5 : direction === 'SELL' ? 2.0 : 1.0;
        const confidenceAdjustment = (1 - confidence) * 1.0;
        const margin = baseMargin + confidenceAdjustment;
        
        return {
            margin: margin.toFixed(2),
            stopLoss: `-${margin.toFixed(2)}%`,
            takeProfit: `+${(margin * 2).toFixed(2)}%`,
            riskReward: '1:2',
            positionSize: direction === 'BUY' ? '100%' : direction === 'SELL' ? '80%' : '50%',
            leverage: (10 / margin).toFixed(1),
            direction: direction
        };
    };

    const LoadingSkeleton = () => (
        <div className="space-y-4">
            <div className="flex items-center gap-4">
                <Skeleton className="h-16 w-16 rounded-full bg-slate-700" />
                <div className="space-y-2">
                    <Skeleton className="h-8 w-32 bg-slate-700" />
                    <Skeleton className="h-4 w-48 bg-slate-700" />
                </div>
            </div>
            <Skeleton className="h-4 w-full bg-slate-700" />
            <Skeleton className="h-4 w-3/4 bg-slate-700" />
            <div className="grid grid-cols-2 gap-4">
                <Skeleton className="h-20 bg-slate-700" />
                <Skeleton className="h-20 bg-slate-700" />
            </div>
        </div>
    );

    const ErrorState = ({ message, onRetry }: { message: string; onRetry: () => void }) => (
        <div className="flex flex-col items-center justify-center py-8 text-center">
            <AlertTriangle className="h-12 w-12 text-red-400 mb-4" />
            <h3 className="text-lg font-semibold text-red-300 mb-2">Error Loading Data</h3>
            <p className="text-sm text-slate-400 mb-4 max-w-md">{message}</p>
            <Button variant="outline" onClick={onRetry} className="gap-2 border-slate-600 hover:bg-slate-800">
                <RefreshCw className="h-4 w-4" />
                Retry
            </Button>
        </div>
    );

    return (
        <div className="container mx-auto p-6 space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-gradient-to-br from-purple-500 to-blue-600">
                            <Brain className="h-6 w-6 text-purple-50" />
                        </div>
                        <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                            ML Agents
                        </span>
                    </h1>
                    <p className="text-muted-foreground mt-2">
                        Deep learning & gradient boosting ensemble for FX signal generation
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <select
                        value={selectedPair}
                        onChange={(e) => setSelectedPair(e.target.value)}
                        className="px-4 py-2 border rounded-lg bg-background hover:border-purple-400 transition-colors"
                    >
                        {CURRENCY_PAIRS.map((pair) => (
                            <option key={pair.value} value={pair.value}>
                                {pair.label}
                            </option>
                        ))}
                    </select>
                    <Button 
                        variant="outline" 
                        size="icon"
                        onClick={refreshAll}
                        className="hover:bg-purple-900"
                    >
                        <RefreshCw className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            {/* Status Bar */}
            <div className="flex flex-wrap gap-2">
                <Badge variant="outline" className="bg-green-900 text-green-100 border-green-700">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    LSTM Active
                </Badge>
                <Badge variant="outline" className="bg-blue-900 text-blue-100 border-blue-700">
                    <Zap className="w-3 h-3 mr-1" />
                    XGBoost Ready
                </Badge>
                <Badge variant="outline" className="bg-purple-900 text-purple-100 border-purple-700">
                    <Sparkles className="w-3 h-3 mr-1" />
                    Fusion Engine
                </Badge>
            </div>

            {/* Tabs */}
            <Tabs defaultValue="fusion" className="w-full" suppressHydrationWarning>
                <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="fusion" className="flex items-center gap-2">
                        <Brain className="w-4 h-4" />
                        XGBoost Fusion
                    </TabsTrigger>
                    <TabsTrigger value="lstm" className="flex items-center gap-2">
                        <Cpu className="w-4 h-4" />
                        LSTM
                    </TabsTrigger>
                    <TabsTrigger value="macro" className="flex items-center gap-2">
                        <BarChart3 className="w-4 h-4" />
                        XGBoost Macro
                    </TabsTrigger>
                    <TabsTrigger value="risk" className="flex items-center gap-2">
                        <Shield className="w-4 h-4" />
                        Risk
                    </TabsTrigger>
                </TabsList>

                {/* XGBoost Fusion Tab */}
                <TabsContent value="fusion" className="mt-4">
                    <Card className="border-purple-800 shadow-lg shadow-purple-900/20 bg-slate-900">
                        <CardHeader className="bg-gradient-to-r from-purple-900 to-blue-900 border-b border-purple-800">
                            <CardTitle className="flex items-center gap-2 text-purple-100">
                                <Brain className="w-5 h-5 text-purple-600" />
                                XGBoost Fusion (Meta-Learner)
                                <Badge variant="outline" className="ml-auto text-xs">
                                    Ensemble Model
                                </Badge>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6 pt-6">
                            {fusionLoading ? (
                                <LoadingSkeleton />
                            ) : fusionError ? (
                                <ErrorState 
                                    message="Failed to load fusion signal. The meta-learner may need training." 
                                    onRetry={() => queryClient.invalidateQueries({ queryKey: ["fusion", selectedPair] })}
                                />
                            ) : fusion?.success ? (
                                <>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <div className={`p-4 rounded-2xl ${getDirectionBg(fusion.direction)} border shadow-inner`}>
                                                <TrendingUp className={`w-10 h-10 ${
                                                    fusion.direction === 'BUY' ? 'text-green-600' :
                                                    fusion.direction === 'SELL' ? 'text-red-600' :
                                                    'text-gray-600'
                                                }`} />
                                            </div>
                                            <div>
                                                <div className="text-3xl font-bold tracking-tight">{fusion.direction}</div>
                                                <div className="text-sm text-muted-foreground flex items-center gap-1">
                                                    <Target className="w-3 h-3" />
                                                    Expected Return: {(fusion.expected_return * 100).toFixed(2)}%
                                                </div>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <Badge className={`${getDirectionColor(fusion.direction)} text-lg px-3 py-1`}>
                                                {(fusion.confidence * 100).toFixed(1)}%
                                            </Badge>
                                            <div className="text-xs text-muted-foreground mt-1">confidence</div>
                                        </div>
                                    </div>

                                    <Separator />

                                    <div className="space-y-3">
                                        <div className="flex items-center gap-2 text-sm font-medium text-purple-900">
                                            <PieChart className="w-4 h-4" />
                                            Agent Contributions
                                        </div>
                                        <div className="space-y-2">
                                            {Object.entries(fusion.agent_contributions || {}).map(([agent, weight]) => (
                                                <div key={agent} className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-700 transition-colors">
                                                    <span className="text-sm capitalize w-28 font-medium">{agent}</span>
                                                    <div className="flex-1">
                                                        <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                                                            <div 
                                                                className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full transition-all"
                                                                style={{ width: `${(weight as number) * 100}%` }}
                                                            />
                                                        </div>
                                                    </div>
                                                    <span className="text-xs font-mono w-12 text-right">{((weight as number) * 100).toFixed(0)}%</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Risk Margin for Fusion */}
                                    {(() => {
                                        const margin = getRiskMargin(fusion);
                                        return (
                                            <div className="p-4 rounded-xl bg-gradient-to-r from-slate-800 to-slate-900 border border-slate-700">
                                                <div className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
                                                    <Shield className="w-4 h-4" />
                                                    Risk Margin ({fusion.direction})
                                                </div>
                                                <div className="grid grid-cols-5 gap-3">
                                                    <div className="text-center">
                                                        <div className="text-xs text-slate-400 mb-1">Margin</div>
                                                        <div className="text-lg font-bold text-yellow-400">{margin.margin}%</div>
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-xs text-slate-400 mb-1">Stop Loss</div>
                                                        <div className={`text-lg font-bold ${fusion.direction === 'BUY' ? 'text-red-400' : 'text-orange-400'}`}>{margin.stopLoss}</div>
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-xs text-slate-400 mb-1">Take Profit</div>
                                                        <div className="text-lg font-bold text-green-400">{margin.takeProfit}</div>
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-xs text-slate-400 mb-1">R:R</div>
                                                        <div className="text-lg font-bold text-blue-400">{margin.riskReward}</div>
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-xs text-slate-400 mb-1">Leverage</div>
                                                        <div className="text-lg font-bold text-purple-400">{margin.leverage}x</div>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })()}

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700">
                                            <div className="flex items-center gap-2 text-sm text-slate-300 mb-1">
                                                <Activity className="w-4 h-4" />
                                                Agent Disagreement
                                            </div>
                                            <div className="text-2xl font-bold text-slate-100">{(fusion.agent_disagreement * 100).toFixed(1)}%</div>
                                        </div>
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700">
                                            <div className="flex items-center gap-2 text-sm text-slate-300 mb-1">
                                                <Sparkles className="w-4 h-4" />
                                                Regime Adjusted
                                            </div>
                                            <div className="text-2xl font-bold">{fusion.regime_adjusted ? 'Yes' : 'No'}</div>
                                        </div>
                                    </div>

                                    <div className="p-4 rounded-xl bg-gradient-to-r from-blue-900 to-purple-900 border border-blue-700">
                                        <div className="flex items-start gap-2">
                                            <Info className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
                                            <div>
                                                <div className="font-medium text-blue-200 mb-1">Model Explanation</div>
                                                <p className="text-sm text-blue-100 leading-relaxed">{fusion.explanation}</p>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <ErrorState 
                                    message="No fusion data available." 
                                    onRetry={() => queryClient.invalidateQueries({ queryKey: ["fusion", selectedPair] })}
                                />
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* LSTM Tab */}
                <TabsContent value="lstm" className="mt-4">
                    <Card className="border-indigo-800 shadow-lg shadow-indigo-900/20 bg-slate-900">
                        <CardHeader className="bg-gradient-to-r from-indigo-900 to-purple-900 border-b border-indigo-800">
                            <CardTitle className="flex items-center gap-2 text-indigo-100">
                                <Cpu className="w-5 h-5 text-indigo-600" />
                                LSTM Technical Agent
                                <Badge variant="outline" className="ml-auto text-xs bg-indigo-900 text-indigo-100 border-indigo-700">
                                    Deep Learning
                                </Badge>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6 pt-6">
                            {lstmLoading ? (
                                <LoadingSkeleton />
                            ) : lstmError ? (
                                <ErrorState 
                                    message="Failed to load LSTM signal." 
                                    onRetry={() => queryClient.invalidateQueries({ queryKey: ["lstm", selectedPair] })}
                                />
                            ) : lstm?.success ? (
                                <>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <div className={`p-4 rounded-2xl ${getDirectionBg(lstm.direction)} border shadow-inner`}>
                                                <Activity className={`w-10 h-10 ${
                                                    lstm.direction === 'BUY' ? 'text-green-600' :
                                                    lstm.direction === 'SELL' ? 'text-red-600' :
                                                    'text-gray-600'
                                                }`} />
                                            </div>
                                            <div>
                                                <div className="text-3xl font-bold tracking-tight">{lstm.direction}</div>
                                                <div className="text-sm text-muted-foreground flex items-center gap-1">
                                                    <TrendingUp className="w-3 h-3" />
                                                    Predicted Return: {(lstm.predicted_return * 100).toFixed(2)}%
                                                </div>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <Badge className={`${getDirectionColor(lstm.direction)} text-lg px-3 py-1`}>
                                                {(lstm.confidence * 100).toFixed(1)}%
                                            </Badge>
                                            <div className="text-xs text-muted-foreground mt-1">
                                                Uncertainty: {(lstm.model_uncertainty * 100).toFixed(1)}%
                                            </div>
                                        </div>
                                    </div>

                                    <Separator />

                                    <div className="grid grid-cols-3 gap-4">
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-emerald-900 to-emerald-950 border border-emerald-700 text-center">
                                            <div className="text-xs text-emerald-300 mb-1 flex items-center justify-center gap-1">
                                                <TrendingUp className="w-3 h-3" />
                                                P(Up)
                                            </div>
                                            <div className="text-2xl font-bold text-emerald-400">{(lstm.probability_up * 100).toFixed(1)}%</div>
                                        </div>
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-rose-900 to-rose-950 border border-rose-700 text-center">
                                            <div className="text-xs text-rose-300 mb-1 flex items-center justify-center gap-1">
                                                <TrendingUp className="w-3 h-3 rotate-180" />
                                                P(Down)
                                            </div>
                                            <div className="text-2xl font-bold text-rose-400">{(lstm.probability_down * 100).toFixed(1)}%</div>
                                        </div>
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 text-center">
                                            <div className="text-xs text-slate-300 mb-1">Uncertainty</div>
                                            <div className="text-2xl font-bold text-slate-100">{(lstm.model_uncertainty * 100).toFixed(1)}%</div>
                                        </div>
                                    </div>

                                    {/* Risk Margin for LSTM */}
                                    {(() => {
                                        const margin = getRiskMargin(lstm);
                                        return (
                                            <div className="p-4 rounded-xl bg-gradient-to-r from-slate-800 to-slate-900 border border-slate-700">
                                                <div className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
                                                    <Shield className="w-4 h-4" />
                                                    Risk Margin ({lstm.direction})
                                                </div>
                                                <div className="grid grid-cols-5 gap-3">
                                                    <div className="text-center">
                                                        <div className="text-xs text-slate-400 mb-1">Margin</div>
                                                        <div className="text-lg font-bold text-yellow-400">{margin.margin}%</div>
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-xs text-slate-400 mb-1">Stop Loss</div>
                                                        <div className={`text-lg font-bold ${lstm.direction === 'BUY' ? 'text-red-400' : 'text-orange-400'}`}>{margin.stopLoss}</div>
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-xs text-slate-400 mb-1">Take Profit</div>
                                                        <div className="text-lg font-bold text-green-400">{margin.takeProfit}</div>
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-xs text-slate-400 mb-1">R:R</div>
                                                        <div className="text-lg font-bold text-blue-400">{margin.riskReward}</div>
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-xs text-slate-400 mb-1">Leverage</div>
                                                        <div className="text-lg font-bold text-purple-400">{margin.leverage}x</div>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })()}

                                    <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-900 to-purple-900 border border-indigo-700">
                                        <div className="flex items-start gap-2">
                                            <Brain className="w-5 h-5 text-indigo-400 mt-0.5 flex-shrink-0" />
                                            <div>
                                                <div className="font-medium text-indigo-200 mb-1">LSTM Analysis</div>
                                                <p className="text-sm text-indigo-100 leading-relaxed">{lstm.explanation}</p>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <ErrorState 
                                    message="No LSTM data available." 
                                    onRetry={() => queryClient.invalidateQueries({ queryKey: ["lstm", selectedPair] })}
                                />
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* XGBoost Macro Tab */}
                <TabsContent value="macro" className="mt-4">
                    <Card className="border-emerald-800 shadow-lg shadow-emerald-900/20 bg-slate-900">
                        <CardHeader className="bg-gradient-to-r from-emerald-900 to-green-900 border-b border-emerald-800">
                            <CardTitle className="flex items-center gap-2 text-emerald-100">
                                <BarChart3 className="w-5 h-5 text-green-600" />
                                XGBoost Macro Agent
                                <Badge variant="outline" className="ml-auto text-xs bg-emerald-900 text-emerald-100 border-emerald-700">
                                    Gradient Boosting
                                </Badge>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6 pt-6">
                            {macroLoading ? (
                                <LoadingSkeleton />
                            ) : macroError ? (
                                <ErrorState 
                                    message="Failed to load macro signal. The model may need training." 
                                    onRetry={() => queryClient.invalidateQueries({ queryKey: ["xgboost-macro", selectedPair] })}
                                />
                            ) : macro?.success ? (
                                <>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <div className={`p-4 rounded-2xl ${getDirectionBg(macro.direction)} border shadow-inner`}>
                                                <BarChart3 className={`w-10 h-10 ${
                                                    macro.direction === 'BUY' ? 'text-green-600' :
                                                    macro.direction === 'SELL' ? 'text-red-600' :
                                                    'text-gray-600'
                                                }`} />
                                            </div>
                                            <div>
                                                <div className="text-3xl font-bold tracking-tight">{macro.direction}</div>
                                                <div className="text-sm text-muted-foreground flex items-center gap-1">
                                                    <Target className="w-3 h-3" />
                                                    Expected Return: {(macro.expected_return * 100).toFixed(2)}%
                                                </div>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <Badge className={`${getDirectionColor(macro.direction)} text-lg px-3 py-1`}>
                                                {(macro.confidence * 100).toFixed(1)}%
                                            </Badge>
                                        </div>
                                    </div>

                                    <Separator />

                                    <div className="space-y-3">
                                        <div className="flex items-center gap-2 text-sm font-medium text-green-900">
                                            <LineChart className="w-4 h-4" />
                                            Macro Factors
                                        </div>
                                        <div className="grid grid-cols-2 gap-3">
                                            {Object.entries(macro.macro_factors || {}).map(([factor, value]) => (
                                                <div key={factor} className="flex justify-between items-center text-sm p-3 rounded-xl bg-gradient-to-r from-slate-800 to-slate-900 border border-slate-700">
                                                    <span className="capitalize text-slate-300">{factor.replace(/_/g, ' ')}</span>
                                                    <span className="font-mono font-semibold text-slate-100">
                                                        {typeof value === 'number' ? value.toFixed(2) : value}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 p-3 rounded-xl bg-gradient-to-r from-emerald-900 to-green-900 border border-emerald-700">
                                        <CheckCircle className="w-5 h-5 text-emerald-400" />
                                        <span className="text-sm text-emerald-100">
                                            Data Quality: <strong>{(macro.data_quality_score * 100).toFixed(0)}%</strong>
                                        </span>
                                    </div>

                                    {/* Risk Margin for Macro */}
                                    {(() => {
                                        const margin = getRiskMargin(macro);
                                        return (
                                            <div className="p-4 rounded-xl bg-gradient-to-r from-slate-800 to-slate-900 border border-slate-700">
                                                <div className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
                                                    <Shield className="w-4 h-4" />
                                                    Risk Margin ({macro.direction})
                                                </div>
                                                <div className="grid grid-cols-5 gap-3">
                                                    <div className="text-center">
                                                        <div className="text-xs text-slate-400 mb-1">Margin</div>
                                                        <div className="text-lg font-bold text-yellow-400">{margin.margin}%</div>
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-xs text-slate-400 mb-1">Stop Loss</div>
                                                        <div className={`text-lg font-bold ${macro.direction === 'BUY' ? 'text-red-400' : 'text-orange-400'}`}>{margin.stopLoss}</div>
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-xs text-slate-400 mb-1">Take Profit</div>
                                                        <div className="text-lg font-bold text-green-400">{margin.takeProfit}</div>
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-xs text-slate-400 mb-1">R:R</div>
                                                        <div className="text-lg font-bold text-blue-400">{margin.riskReward}</div>
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-xs text-slate-400 mb-1">Leverage</div>
                                                        <div className="text-lg font-bold text-purple-400">{margin.leverage}x</div>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })()}

                                    <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-900 to-green-900 border border-emerald-700">
                                        <div className="flex items-start gap-2">
                                            <Zap className="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0" />
                                            <div>
                                                <div className="font-medium text-emerald-200 mb-1">XGBoost Analysis</div>
                                                <p className="text-sm text-emerald-100 leading-relaxed">{macro.explanation}</p>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <ErrorState 
                                    message="No macro data available." 
                                    onRetry={() => queryClient.invalidateQueries({ queryKey: ["xgboost-macro", selectedPair] })}
                                />
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Risk Tab */}
                <TabsContent value="risk" className="mt-4">
                    <Card className="border-rose-800 shadow-lg shadow-rose-900/20 bg-slate-900">
                        <CardHeader className="bg-gradient-to-r from-rose-900 to-orange-900 border-b border-rose-800">
                            <CardTitle className="flex items-center gap-2 text-rose-100">
                                <Shield className="w-5 h-5 text-red-600" />
                                Risk Metrics (VaR)
                                <Badge variant="outline" className="ml-auto text-xs bg-rose-900 text-rose-100 border-rose-700">
                                    Portfolio Risk
                                </Badge>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6 pt-6">
                            {riskLoading ? (
                                <LoadingSkeleton />
                            ) : riskError ? (
                                <ErrorState 
                                    message="Failed to load risk metrics." 
                                    onRetry={() => queryClient.invalidateQueries({ queryKey: ["risk", selectedPair] })}
                                />
                            ) : risk?.success ? (
                                <>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <div className={`p-4 rounded-2xl ${
                                                risk.risk_level === 'EXTREME' ? 'bg-rose-900 border-rose-700' :
                                                risk.risk_level === 'HIGH' ? 'bg-orange-900 border-orange-700' :
                                                risk.risk_level === 'MODERATE' ? 'bg-amber-900 border-amber-700' :
                                                'bg-emerald-900 border-emerald-700'
                                            } shadow-inner border`}>
                                                <Shield className={`w-10 h-10 ${getRiskColor(risk.risk_level)}`} />
                                            </div>
                                            <div>
                                                <div className={`text-2xl font-bold ${getRiskColor(risk.risk_level)}`}>
                                                    {risk.risk_level}
                                                </div>
                                                <div className="text-sm text-muted-foreground">
                                                    Risk Level
                                                </div>
                                            </div>
                                        </div>
                                        <div className="text-right p-4 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700">
                                            <div className="text-sm text-slate-300 mb-1">Position Size</div>
                                            <div className="text-2xl font-bold text-slate-100">{(risk.position_size_mult * 100).toFixed(0)}%</div>
                                            <div className="text-xs text-slate-400">recommended</div>
                                        </div>
                                    </div>

                                    <Separator />

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-rose-900 to-red-950 border border-rose-700">
                                            <div className="flex items-center gap-2 text-sm text-rose-300 mb-1">
                                                <AlertTriangle className="w-4 h-4" />
                                                VaR 95%
                                            </div>
                                            <div className="text-2xl font-bold text-rose-400">-${risk.var_95.toFixed(0)}</div>
                                            <div className="text-xs text-rose-400/70">max loss at 95% confidence</div>
                                        </div>
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-orange-900 to-amber-950 border border-orange-700">
                                            <div className="flex items-center gap-2 text-sm text-orange-300 mb-1">
                                                <AlertTriangle className="w-4 h-4" />
                                                CVaR 95%
                                            </div>
                                            <div className="text-2xl font-bold text-orange-400">-${risk.cvar_95.toFixed(0)}</div>
                                            <div className="text-xs text-orange-400/70">expected shortfall</div>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-blue-900 to-slate-900 border border-blue-700">
                                            <div className="text-sm text-blue-300 mb-1 flex items-center gap-1">
                                                <Activity className="w-4 h-4" />
                                                Realized Vol
                                            </div>
                                            <div className="text-2xl font-bold text-blue-400">{(risk.realized_vol * 100).toFixed(1)}%</div>
                                        </div>
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-purple-900 to-violet-950 border border-purple-700">
                                            <div className="text-sm text-purple-300 mb-1 flex items-center gap-1">
                                                <LineChart className="w-4 h-4" />
                                                EWMA Vol
                                            </div>
                                            <div className="text-2xl font-bold text-purple-400">{(risk.ewma_vol * 100).toFixed(1)}%</div>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700">
                                            <div className="text-sm text-slate-300 mb-1">Current Drawdown</div>
                                            <div className={`text-2xl font-bold ${risk.current_drawdown < -0.05 ? 'text-red-400' : 'text-slate-100'}`}>
                                                {(risk.current_drawdown * 100).toFixed(1)}%
                                            </div>
                                        </div>
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700">
                                            <div className="text-sm text-slate-300 mb-1">Max Drawdown</div>
                                            <div className="text-2xl font-bold text-slate-100">
                                                {(risk.max_drawdown * 100).toFixed(1)}%
                                            </div>
                                        </div>
                                    </div>

                                    <div className={`p-4 rounded-xl text-sm ${
                                        risk.risk_level === 'EXTREME' ? 'bg-rose-900 border border-rose-700 text-rose-100' :
                                        risk.risk_level === 'HIGH' ? 'bg-orange-900 border border-orange-700 text-orange-100' :
                                        risk.risk_level === 'MODERATE' ? 'bg-amber-900 border border-amber-700 text-amber-100' :
                                        'bg-emerald-900 border border-emerald-700 text-emerald-100'
                                    }`}>
                                        <div className="flex items-start gap-2">
                                            <Info className="w-5 h-5 mt-0.5 flex-shrink-0" />
                                            <div>
                                                <div className="font-semibold mb-1">Risk Recommendation</div>
                                                <p className="leading-relaxed">{risk.recommendation}</p>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <ErrorState 
                                    message="No risk data available." 
                                    onRetry={() => queryClient.invalidateQueries({ queryKey: ["risk", selectedPair] })}
                                />
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
