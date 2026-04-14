"use client";

import { useState } from "react";
import { EnsembleForecastPanel } from "@/components/EnsembleForecastPanel";
import { COTPanel } from "@/components/COTPanel";
import { SentimentAnalysisPanel } from "@/components/SentimentAnalysisPanel";
import { MetaLearningPanel } from "@/components/MetaLearningPanel";
import { RegimePanel } from "@/components/RegimePanel";
import { useDashboardData, useFastApiHealth } from "@/hooks/useFastAPI";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertCircle, CheckCircle, RefreshCw, Activity, Brain, TrendingUp, MessageSquare, Users } from "lucide-react";

const CURRENCY_PAIRS = [
    { value: "EURUSD", label: "EUR/USD" },
    { value: "GBPUSD", label: "GBP/USD" },
    { value: "USDJPY", label: "USD/JPY" },
    { value: "USDCHF", label: "USD/CHF" },
    { value: "AUDUSD", label: "AUD/USD" },
    { value: "NZDUSD", label: "NZD/USD" },
    { value: "USDCAD", label: "USD/CAD" },
];

export default function AdvancedFeaturesPage() {
    const [selectedPair, setSelectedPair] = useState("EURUSD");
    const health = useFastApiHealth();
    const { 
        signal, 
        forecast, 
        patterns, 
        cot, 
        prices, 
        agentStatus,
        wsSignal,
        wsConnected,
        isLoading,
        error,
        refetch 
    } = useDashboardData(selectedPair);

    return (
        <div className="container mx-auto p-6 space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <Activity className="w-8 h-8" />
                        Advanced Features Dashboard
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Ensemble forecasting, COT positioning, FinBERT sentiment, and Meta-Learning
                    </p>
                </div>

                <div className="flex items-center gap-4">
                    {/* Pair Selector */}
                    <select
                        value={selectedPair}
                        onChange={(e) => setSelectedPair(e.target.value)}
                        className="px-4 py-2 border rounded-md bg-background"
                    >
                        {CURRENCY_PAIRS.map((pair) => (
                            <option key={pair.value} value={pair.value}>
                                {pair.label}
                            </option>
                        ))}
                    </select>

                    {/* Refresh Button */}
                    <Button onClick={() => refetch()} variant="outline" size="icon">
                        <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                    </Button>

                    {/* FastAPI Status */}
                    <div className="flex items-center gap-2">
                        {health.data ? (
                            <Badge variant="default" className="bg-green-500">
                                <CheckCircle className="w-3 h-3 mr-1" />
                                FastAPI
                            </Badge>
                        ) : (
                            <Badge variant="destructive">
                                <AlertCircle className="w-3 h-3 mr-1" />
                                FastAPI
                            </Badge>
                        )}
                        {wsConnected && (
                            <Badge variant="outline" className="border-green-500 text-green-600">
                                WS Live
                            </Badge>
                        )}
                    </div>
                </div>
            </div>

            {/* Error Display */}
            {error && (
                <Card className="border-red-200 bg-red-50">
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-2 text-red-600">
                            <AlertCircle className="w-5 h-5" />
                            <span>Error loading data. Some features may be unavailable.</span>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Column */}
                <div className="space-y-6">
                    {/* Regime Classification */}
                    <RegimePanel pair={selectedPair} />

                    {/* Signal Card */}
                    <Card>
                        <CardHeader className="pb-3">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                                    <Activity className="w-5 h-5" />
                                    Trading Signal
                                </CardTitle>
                                <Badge variant="outline">{selectedPair}</Badge>
                            </div>
                        </CardHeader>
                        <CardContent>
                            {signal ? (
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <span className="text-3xl font-bold">
                                            {signal.direction}
                                        </span>
                                        <Badge 
                                            className={
                                                signal.direction === 'BUY' ? 'bg-green-500' :
                                                signal.direction === 'SELL' ? 'bg-red-500' :
                                                'bg-gray-500'
                                            }
                                        >
                                            {(signal.confidence * 100).toFixed(1)}% confidence
                                        </Badge>
                                    </div>
                                    {wsSignal && (
                                        <div className="text-sm text-muted-foreground flex items-center gap-2">
                                            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                            Real-time: {wsSignal.signal} ({(wsSignal.confidence * 100).toFixed(0)}%)
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="text-muted-foreground">Loading signal...</div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Ensemble Forecast */}
                    <EnsembleForecastPanel pair={selectedPair} periods={24} />

                    {/* COT Positioning */}
                    <COTPanel pair={selectedPair} />
                </div>

                {/* Right Column */}
                <div className="space-y-6">
                    {/* Tabs for different features */}
                    <Tabs defaultValue="sentiment" className="w-full">
                        <TabsList className="grid w-full grid-cols-3">
                            <TabsTrigger value="sentiment" className="flex items-center gap-2">
                                <MessageSquare className="w-4 h-4" />
                                Sentiment
                            </TabsTrigger>
                            <TabsTrigger value="meta" className="flex items-center gap-2">
                                <Brain className="w-4 h-4" />
                                Meta-Learn
                            </TabsTrigger>
                            <TabsTrigger value="patterns" className="flex items-center gap-2">
                                <TrendingUp className="w-4 h-4" />
                                Patterns
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="sentiment" className="mt-4">
                            <SentimentAnalysisPanel />
                        </TabsContent>

                        <TabsContent value="meta" className="mt-4">
                            <MetaLearningPanel />
                        </TabsContent>

                        <TabsContent value="patterns" className="mt-4">
                            <Card>
                                <CardHeader>
                                    <CardTitle>Pattern Recognition</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    {patterns ? (
                                        <div className="space-y-2">
                                            <div className="flex justify-between text-sm">
                                                <span>CNN Patterns</span>
                                                <Badge variant="outline">{patterns.cnn_count}</Badge>
                                            </div>
                                            <div className="flex justify-between text-sm">
                                                <span>Traditional Patterns</span>
                                                <Badge variant="outline">{patterns.traditional_count}</Badge>
                                            </div>
                                            <div className="flex justify-between text-sm">
                                                <span>Hybrid Confidence</span>
                                                <span className="font-medium">{(patterns.hybrid_confidence * 100).toFixed(1)}%</span>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="text-muted-foreground">Patterns panel uses existing component</div>
                                    )}
                                </CardContent>
                            </Card>
                        </TabsContent>
                    </Tabs>

                    {/* Agent Status */}
                    <Card>
                        <CardHeader className="pb-3">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                                    <Users className="w-5 h-5" />
                                    Agent Status
                                </CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent>
                            {agentStatus ? (
                                <div className="grid grid-cols-2 gap-2">
                                    {Object.entries(agentStatus.agents as Record<string, { status: string; weight: number }>).map(([name, agentData]) => (
                                        <div key={name} className="flex items-center justify-between p-2 rounded bg-gray-50">
                                            <span className="text-sm capitalize">{name}</span>
                                            <Badge 
                                                variant={agentData.status === 'active' ? 'default' : 'destructive'}
                                                className="text-xs"
                                            >
                                                {(agentData.weight * 100).toFixed(0)}%
                                            </Badge>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-muted-foreground">Loading agent status...</div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Summary Card */}
                    <Card className="bg-gradient-to-br from-blue-50 to-indigo-50">
                        <CardHeader>
                            <CardTitle>Integration Summary</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2 text-sm">
                            <div className="flex items-center gap-2">
                                <CheckCircle className="w-4 h-4 text-green-500" />
                                <span>Regime Classification (HMM)</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <CheckCircle className="w-4 h-4 text-green-500" />
                                <span>Ensemble Forecasting (Prophet + Kats)</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <CheckCircle className="w-4 h-4 text-green-500" />
                                <span>COT Positioning (Institutional Data)</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <CheckCircle className="w-4 h-4 text-green-500" />
                                <span>FinBERT Sentiment Analysis</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <CheckCircle className="w-4 h-4 text-green-500" />
                                <span>Meta-Learning Ensemble</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <CheckCircle className="w-4 h-4 text-green-500" />
                                <span>FastAPI Async Endpoints</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <CheckCircle className="w-4 h-4 text-green-500" />
                                <span>WebSocket Real-time Updates</span>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
