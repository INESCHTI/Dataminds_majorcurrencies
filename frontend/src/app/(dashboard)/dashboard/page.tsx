'use client';

import DashboardNavigation from '@/components/DashboardNavigation';
import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import {
    TrendingUp,
    Activity,
    Bot,
    Zap,
    LineChart,
    ArrowRight,
    Shield,
    Target,
    Globe,
    Brain,
    Database,
    Clock,
    CheckCircle,
    AlertCircle,
    BarChart3,
    PieChart,
    Sparkles,
    Rocket,
    TrendingDown,
    Minus,
    MapPin,
    Newspaper,
    Globe2,
    Users,
    Cpu,
    Signal,
    Timer,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { HealthCheckV2 } from "@/types";

const pairs = [
    { symbol: "EURUSD", name: "EUR/USD", description: "Euro vs US Dollar", trend: "up", session: "London/New York" },
    { symbol: "USDJPY", name: "USD/JPY", description: "US Dollar vs Japanese Yen", trend: "neutral", session: "Tokyo/London" },
    { symbol: "GBPUSD", name: "GBP/USD", description: "British Pound vs US Dollar", trend: "down", session: "London/New York" },
    { symbol: "USDCHF", name: "USD/CHF", description: "US Dollar vs Swiss Franc", trend: "up", session: "Zurich/London" },
];

export default function DashboardPage() {
    const router = useRouter();
    const [health, setHealth] = useState<HealthCheckV2 | null>(null);
    const [loading, setLoading] = useState(true);
    const [latestSignal, setLatestSignal] = useState<any>(null);
    const [signalLoading, setSignalLoading] = useState(false);

    useEffect(() => {
        const loadHealth = async () => {
            try {
                const data = await api.v2.healthCheck() as HealthCheckV2;
                setHealth(data);
            } catch (error) {
                console.error("Failed to load health:", error);
            }
            setLoading(false);
        };
        loadHealth();
        const interval = setInterval(loadHealth, 30000);
        return () => clearInterval(interval);
    }, []);

    const avgWinRate = health
        ? (
              (Object.values(health.agent_performances).reduce((sum, p) => sum + p.win_rate, 0) /
                  Object.values(health.agent_performances).length) *
              100
          ).toFixed(1)
        : 0;

    const totalSignals = health
        ? Object.values(health.agent_performances).reduce((sum, p) => sum + p.total_signals, 0)
        : 0;

    const generateQuickSignal = async (pair: string) => {
        setSignalLoading(true);
        try {
            const signal = await api.v2.generateSignal(pair);
            setLatestSignal(signal);
        } catch (error) {
            console.error("Failed to generate signal:", error);
        }
        setSignalLoading(false);
    };

    const getTrendIcon = (trend: string) => {
        switch (trend) {
            case "up": return <TrendingUp className="size-4 text-green-500" />;
            case "down": return <TrendingDown className="size-4 text-red-500" />;
            default: return <Minus className="size-4 text-yellow-500" />;
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900">
            <SidebarTrigger />
            <div className="container mx-auto p-6 space-y-8">
                <DashboardNavigation />

                <div className="flex-1 overflow-auto p-6 lg:p-8 space-y-8">
                    {/* Hero Section - Enhanced Modern Dark Theme */}
                    <Card className="border-0 bg-gradient-to-br from-purple-900/50 via-blue-900/50 to-slate-900/50 backdrop-blur-xl shadow-2xl relative overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 via-blue-500/10 to-emerald-500/10 animate-pulse"></div>
                        <CardContent className="p-8 lg:p-12 relative z-10">
                            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8">
                                <div className="flex-1 space-y-6">
                                    <div className="flex items-center gap-3">
                                        <Badge className="bg-gradient-to-r from-purple-500 to-blue-500 text-white border-0 px-4 py-2 shadow-lg">
                                            <Sparkles className="size-4 mr-2" />
                                            AI-Powered Trading
                                        </Badge>
                                        <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 px-4 py-2">
                                            <CheckCircle className="size-4 mr-2" />
                                            Production Ready
                                        </Badge>
                                        <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 px-4 py-2">
                                            <Globe2 className="size-4 mr-2" />
                                            Multi-Agent System
                                        </Badge>
                                    </div>
                                    
                                    <div className="space-y-4">
                                        <h1 className="text-4xl lg:text-6xl font-bold bg-gradient-to-r from-white via-purple-200 to-blue-200 bg-clip-text text-transparent">
                                            FX Alpha Platform
                                        </h1>
                                        <p className="text-xl text-purple-100 leading-relaxed max-w-3xl">
                                            Advanced multi-agent system combining real-time technical analysis, 
                                            macroeconomic data, sentiment analysis, and geopolitical insights 
                                            for institutional-grade FX trading signals with 4 specialized AI agents.
                                        </p>
                                    </div>
                                    
                                    <div className="flex flex-wrap gap-4">
                                        <Button
                                            onClick={() => router.push("/realtime-dashboard")}
                                            size="lg"
                                            className="bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white border-0 shadow-lg transform hover:scale-105 transition-all"
                                        >
                                            <Zap className="size-5 mr-2" />
                                            Live Trading Dashboard
                                            <ArrowRight className="size-5 ml-2" />
                                        </Button>
                                        <Button
                                            onClick={() => router.push("/agents")}
                                            size="lg"
                                            variant="outline"
                                            className="border-purple-500/50 text-purple-200 hover:bg-purple-500/20 hover:border-purple-400 transform hover:scale-105 transition-all"
                                        >
                                            <Brain className="size-5 mr-2" />
                                            View AI Agents
                                        </Button>
                                        <Button
                                            onClick={() => router.push("/monitoring")}
                                            size="lg"
                                            variant="outline"
                                            className="border-emerald-500/50 text-emerald-200 hover:bg-emerald-500/20 hover:border-emerald-400 transform hover:scale-105 transition-all"
                                        >
                                            <Activity className="size-5 mr-2" />
                                            System Monitor
                                        </Button>
                                    </div>
                                </div>
                                
                                <div className="hidden lg:flex items-center justify-center">
                                    <div className="relative">
                                        <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-blue-500 blur-3xl rounded-full opacity-50 animate-pulse"></div>
                                        <div className="relative bg-gradient-to-br from-purple-600/20 to-blue-600/20 p-8 rounded-2xl border border-purple-500/30">
                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="p-3 rounded-lg bg-purple-500/20 border border-purple-500/30">
                                                    <Bot className="size-8 text-purple-300" />
                                                </div>
                                                <div className="p-3 rounded-lg bg-blue-500/20 border border-blue-500/30">
                                                    <Globe className="size-8 text-blue-300" />
                                                </div>
                                                <div className="p-3 rounded-lg bg-emerald-500/20 border border-emerald-500/30">
                                                    <Newspaper className="size-8 text-emerald-300" />
                                                </div>
                                                <div className="p-3 rounded-lg bg-amber-500/20 border border-amber-500/30">
                                                    <Shield className="size-8 text-amber-300" />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Live Signal Generator - Enhanced */}
                    <Card className="border-0 bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-xl shadow-xl">
                        <CardHeader>
                            <CardTitle className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-gradient-to-r from-green-500 to-emerald-500">
                                        <Zap className="size-6 text-white" />
                                    </div>
                                    <div>
                                        <h2 className="text-2xl font-bold text-white">Live Signal Generator</h2>
                                        <p className="text-purple-200">Generate real trading signals with 4 AI agents</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                                        <Activity className="size-3 mr-2" />
                                        Real-Time
                                    </Badge>
                                    <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                                        <Timer className="size-3 mr-2" />
                                        15s Generation
                                    </Badge>
                                </div>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {pairs.map((pair) => (
                                    <div
                                        key={pair.symbol}
                                        className="p-6 rounded-xl border border-purple-500/30 bg-gradient-to-br from-purple-900/20 to-blue-900/20 hover:from-purple-900/30 hover:to-blue-900/30 transition-all group"
                                    >
                                        <div className="flex items-center justify-between mb-4">
                                            <div className="flex items-center gap-3">
                                                <div>
                                                    <div className="text-xl font-bold text-white">{pair.name}</div>
                                                    <div className="text-sm text-purple-200">{pair.description}</div>
                                                    <div className="flex items-center gap-2 mt-1">
                                                        <MapPin className="size-3 text-purple-400" />
                                                        <span className="text-xs text-purple-300">{pair.session}</span>
                                                    </div>
                                                </div>
                                                {getTrendIcon(pair.trend)}
                                            </div>
                                        </div>
                                        <Button
                                            onClick={() => generateQuickSignal(pair.symbol)}
                                            disabled={signalLoading}
                                            className="w-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white border-0 shadow-lg transform hover:scale-105 transition-all"
                                        >
                                            {signalLoading ? (
                                                <>
                                                    <Activity className="size-4 mr-2 animate-spin" />
                                                    Generating...
                                                </>
                                            ) : (
                                                <>
                                                    <Zap className="size-4 mr-2" />
                                                    Generate Signal
                                                </>
                                            )}
                                        </Button>
                                    </div>
                                ))}
                            </div>
                            
                            {latestSignal && (
                                <Card className="border-green-500/30 bg-gradient-to-br from-green-900/20 to-emerald-900/20 animate-pulse">
                                    <CardContent className="p-6">
                                        <div className="flex items-center gap-3 mb-4">
                                            <CheckCircle className="size-6 text-green-400" />
                                            <h3 className="text-xl font-bold text-white">Latest Signal Generated</h3>
                                            <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                                                <Signal className="size-3 mr-2" />
                                                {latestSignal.signal?.signal_id?.split('_')[0] || 'EURUSD'}
                                            </Badge>
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                            <div>
                                                <div className="text-sm text-purple-200 mb-1">Signal Direction</div>
                                                <div className="text-2xl font-bold text-white">
                                                    {latestSignal.signal?.direction || 'NEUTRAL'}
                                                </div>
                                            </div>
                                            <div>
                                                <div className="text-sm text-purple-200 mb-1">Confidence</div>
                                                <div className="text-2xl font-bold text-green-400">
                                                    {((latestSignal.signal?.confidence || 0) * 100).toFixed(1)}%
                                                </div>
                                            </div>
                                            <div>
                                                <div className="text-sm text-purple-200 mb-1">Market Regime</div>
                                                <div className="text-lg font-bold text-blue-400 capitalize">
                                                    {latestSignal.signal?.market_regime || 'normal'}
                                                </div>
                                            </div>
                                            <div>
                                                <div className="text-sm text-purple-200 mb-1">Execution Time</div>
                                                <div className="text-lg font-bold text-amber-400">
                                                    {latestSignal.metadata?.execution_time_ms || 0}ms
                                                </div>
                                            </div>
                                        </div>
                                        <div className="mt-4 p-3 rounded-lg bg-purple-900/20 border border-purple-500/30">
                                            <div className="text-xs text-purple-300 mb-1">Signal ID</div>
                                            <div className="text-sm font-mono text-purple-200">
                                                {latestSignal.signal?.signal_id || 'N/A'}
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            )}
                        </CardContent>
                    </Card>

                    {/* System Performance Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <Card className="border-0 bg-gradient-to-br from-emerald-900/50 to-slate-900/50 backdrop-blur-xl">
                            <CardContent className="p-6">
                                <div className="flex items-center gap-4 mb-4">
                                    <div className="p-3 rounded-xl bg-emerald-500/20">
                                        <Activity className="size-6 text-emerald-400" />
                                    </div>
                                    <div>
                                        <div className="text-sm text-purple-200">System Status</div>
                                        <div className="text-2xl font-bold text-white">
                                            {health?.status === "operational" ? "ONLINE" : "OFFLINE"}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="size-2 rounded-full bg-emerald-400 animate-pulse"></div>
                                    <span className="text-xs text-emerald-400">All Systems Operational</span>
                                </div>
                            </CardContent>
                        </Card>

                        <Card className="border-0 bg-gradient-to-br from-blue-900/50 to-slate-900/50 backdrop-blur-xl">
                            <CardContent className="p-6">
                                <div className="flex items-center gap-4 mb-4">
                                    <div className="p-3 rounded-xl bg-blue-500/20">
                                        <Bot className="size-6 text-blue-400" />
                                    </div>
                                    <div>
                                        <div className="text-sm text-purple-200">AI Agents</div>
                                        <div className="text-2xl font-bold text-white">
                                            {health ? Object.keys(health.agent_performances).length : 4}
                                        </div>
                                    </div>
                                </div>
                                <div className="text-xs text-blue-400">Technical • Macro • Sentiment • Geopolitical</div>
                            </CardContent>
                        </Card>

                        <Card className="border-0 bg-gradient-to-br from-purple-900/50 to-slate-900/50 backdrop-blur-xl">
                            <CardContent className="p-6">
                                <div className="flex items-center gap-4 mb-4">
                                    <div className="p-3 rounded-xl bg-purple-500/20">
                                        <Zap className="size-6 text-purple-400" />
                                    </div>
                                    <div>
                                        <div className="text-sm text-purple-200">Signals</div>
                                        <div className="text-2xl font-bold text-white">{totalSignals}</div>
                                    </div>
                                </div>
                                <div className="text-xs text-purple-400">Generated this month</div>
                            </CardContent>
                        </Card>

                        <Card className="border-0 bg-gradient-to-br from-amber-900/50 to-slate-900/50 backdrop-blur-xl">
                            <CardContent className="p-6">
                                <div className="flex items-center gap-4 mb-4">
                                    <div className="p-3 rounded-xl bg-amber-500/20">
                                        <Target className="size-6 text-amber-400" />
                                    </div>
                                    <div>
                                        <div className="text-sm text-purple-200">Win Rate</div>
                                        <div className="text-2xl font-bold text-white">{avgWinRate}%</div>
                                    </div>
                                </div>
                                <div className="text-xs text-amber-400">Across all agents</div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* AI Agent Capabilities - Enhanced with Geopolitical */}
                    <Card className="border-0 bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-xl">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-3 text-2xl text-white">
                                <Brain className="size-6 text-purple-400" />
                                AI Agent Capabilities
                                <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30">
                                    <Cpu className="size-3 mr-2" />
                                    4 Agents
                                </Badge>
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                <div className="space-y-4">
                                    <div className="p-4 rounded-xl border border-purple-500/30 bg-gradient-to-br from-purple-900/20 to-slate-900/20 hover:border-purple-400/50 transition-all group">
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className="p-2 rounded-lg bg-purple-500/20 group-hover:bg-purple-500/30 transition-all">
                                                <BarChart3 className="size-5 text-purple-400" />
                                            </div>
                                            <h3 className="font-bold text-white">Technical Analysis</h3>
                                        </div>
                                        <p className="text-sm text-purple-200 mb-3">
                                            Real-time price action, indicators, and pattern recognition
                                        </p>
                                        <div className="space-y-2">
                                            <div className="flex items-center gap-2">
                                                <div className="size-2 rounded-full bg-purple-400"></div>
                                                <span className="text-xs text-purple-300">RSI, MACD, Bollinger Bands</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="size-2 rounded-full bg-purple-400"></div>
                                                <span className="text-xs text-purple-300">ADX, Ichimoku, ATR</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="size-2 rounded-full bg-purple-400"></div>
                                                <span className="text-xs text-purple-300">85+ Technical Indicators</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div className="space-y-4">
                                    <div className="p-4 rounded-xl border border-blue-500/30 bg-gradient-to-br from-blue-900/20 to-slate-900/20 hover:border-blue-400/50 transition-all group">
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className="p-2 rounded-lg bg-blue-500/20 group-hover:bg-blue-500/30 transition-all">
                                                <Globe className="size-5 text-blue-400" />
                                            </div>
                                            <h3 className="font-bold text-white">Macroeconomic</h3>
                                        </div>
                                        <p className="text-sm text-purple-200 mb-3">
                                            Interest rates, GDP, inflation, and economic indicators
                                        </p>
                                        <div className="space-y-2">
                                            <div className="flex items-center gap-2">
                                                <div className="size-2 rounded-full bg-blue-400"></div>
                                                <span className="text-xs text-purple-300">Central Bank Policies</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="size-2 rounded-full bg-blue-400"></div>
                                                <span className="text-xs text-purple-300">Rate Differentials</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="size-2 rounded-full bg-blue-400"></div>
                                                <span className="text-xs text-purple-300">FRED Economic Data</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div className="space-y-4">
                                    <div className="p-4 rounded-xl border border-emerald-500/30 bg-gradient-to-br from-emerald-900/20 to-slate-900/20 hover:border-emerald-400/50 transition-all group">
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className="p-2 rounded-lg bg-emerald-500/20 group-hover:bg-emerald-500/30 transition-all">
                                                <Newspaper className="size-5 text-emerald-400" />
                                            </div>
                                            <h3 className="font-bold text-white">Sentiment Analysis</h3>
                                        </div>
                                        <p className="text-sm text-purple-200 mb-3">
                                            News sentiment, social media, market psychology
                                        </p>
                                        <div className="space-y-2">
                                            <div className="flex items-center gap-2">
                                                <div className="size-2 rounded-full bg-emerald-400"></div>
                                                <span className="text-xs text-purple-300">NLP Classification</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="size-2 rounded-full bg-emerald-400"></div>
                                                <span className="text-xs text-purple-300">Financial News Feed</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="size-2 rounded-full bg-emerald-400"></div>
                                                <span className="text-xs text-purple-300">Market Psychology</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div className="space-y-4">
                                    <div className="p-4 rounded-xl border border-amber-500/30 bg-gradient-to-br from-amber-900/20 to-slate-900/20 hover:border-amber-400/50 transition-all group">
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className="p-2 rounded-lg bg-amber-500/20 group-hover:bg-amber-500/30 transition-all">
                                                <Shield className="size-5 text-amber-400" />
                                            </div>
                                            <h3 className="font-bold text-white">Geopolitical</h3>
                                        </div>
                                        <p className="text-sm text-purple-200 mb-3">
                                            Political events, trade policies, regional risks
                                        </p>
                                        <div className="space-y-2">
                                            <div className="flex items-center gap-2">
                                                <div className="size-2 rounded-full bg-amber-400"></div>
                                                <span className="text-xs text-purple-300">Political Stability</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="size-2 rounded-full bg-amber-400"></div>
                                                <span className="text-xs text-purple-300">Trade Agreements</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="size-2 rounded-full bg-amber-400"></div>
                                                <span className="text-xs text-purple-300">Regional Risk Analysis</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            {/* Agent Coordination Section */}
                            <div className="mt-8 p-6 rounded-xl border border-purple-500/30 bg-gradient-to-br from-purple-900/10 to-blue-900/10">
                                <div className="flex items-center gap-3 mb-4">
                                    <Users className="size-6 text-purple-400" />
                                    <h3 className="text-xl font-bold text-white">Multi-Agent Coordination</h3>
                                    <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30">
                                        <Brain className="size-3 mr-2" />
                                        Smart Weighting
                                    </Badge>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div className="p-4 rounded-lg bg-purple-900/20 border border-purple-500/30">
                                        <div className="text-sm text-purple-200 mb-1">Dynamic Weighting</div>
                                        <div className="text-lg font-bold text-purple-300">Performance-Based</div>
                                        <div className="text-xs text-purple-400 mt-1">30-day rolling Sharpe ratio</div>
                                    </div>
                                    <div className="p-4 rounded-lg bg-blue-900/20 border border-blue-500/30">
                                        <div className="text-sm text-purple-200 mb-1">Conflict Detection</div>
                                        <div className="text-lg font-bold text-blue-300">Smart Resolution</div>
                                        <div className="text-xs text-purple-400 mt-1">Identifies opposing signals</div>
                                    </div>
                                    <div className="p-4 rounded-lg bg-emerald-900/20 border border-emerald-500/30">
                                        <div className="text-sm text-purple-200 mb-1">Market Regime</div>
                                        <div className="text-lg font-bold text-emerald-300">Adaptive Analysis</div>
                                        <div className="text-xs text-purple-400 mt-1">Trending, ranging, volatile</div>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Quick Actions - Enhanced */}
                    <Card className="border-0 bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-xl">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-3 text-xl text-white">
                                <Zap className="size-5 text-purple-400" />
                                Quick Actions
                                <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30">
                                    <Rocket className="size-3 mr-2" />
                                    Navigate
                                </Badge>
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                <Button
                                    onClick={() => router.push("/monitoring")}
                                    className="bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white border-0 shadow-lg transform hover:scale-105 transition-all"
                                >
                                    <Activity className="size-4 mr-2" />
                                    System Monitoring
                                </Button>
                                <Button
                                    onClick={() => router.push("/agents")}
                                    variant="outline"
                                    className="border-purple-500/50 text-purple-200 hover:bg-purple-500/20 transform hover:scale-105 transition-all"
                                >
                                    <Bot className="size-4 mr-2" />
                                    Agent Details
                                </Button>
                                <Button
                                    onClick={() => router.push("/backtesting")}
                                    variant="outline"
                                    className="border-blue-500/50 text-blue-200 hover:bg-blue-500/20 transform hover:scale-105 transition-all"
                                >
                                    <BarChart3 className="size-4 mr-2" />
                                    Backtesting
                                </Button>
                                <Button
                                    onClick={() => router.push("/api-test-page")}
                                    variant="outline"
                                    className="border-emerald-500/50 text-emerald-200 hover:bg-emerald-500/20 transform hover:scale-105 transition-all"
                                >
                                    <Database className="size-4 mr-2" />
                                    API Testing
                                </Button>
                            </div>
                        </CardContent>
                    </Card>

                    {/* System Status Banner */}
                    <Card className="border-0 bg-gradient-to-r from-emerald-900/30 to-blue-900/30 backdrop-blur-xl">
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="p-3 rounded-xl bg-emerald-500/20 border border-emerald-500/30">
                                        <CheckCircle className="size-6 text-emerald-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-white">System Operational</h3>
                                        <p className="text-sm text-purple-200">All 4 AI agents running with real data processing</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                                        <Signal className="size-3 mr-2" />
                                        Live
                                    </Badge>
                                    <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                                        <Database className="size-3 mr-2" />
                                        Real Data
                                    </Badge>
                                    <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30">
                                        <Cpu className="size-3 mr-2" />
                                        Multi-Agent
                                    </Badge>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}


