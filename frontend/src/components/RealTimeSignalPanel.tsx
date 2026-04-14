'use client';

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
    TrendingUp,
    TrendingDown,
    Minus,
    Bot,
    Activity,
    Zap,
    RefreshCw,
    Play,
    StopCircle,
} from "lucide-react";
import { api } from "@/lib/api";

interface SignalData {
    success: boolean;
    signal: {
        direction: string;
        confidence: number;
        weighted_score: number;
        reasoning: string;
        agent_votes: Record<string, any>;
        weights: Record<string, number>;
        market_regime: string;
        conflicts: string[];
        timestamp: string;
        signal_id: string;
    };
    metadata: {
        execution_time_ms: number;
        data_timestamps: Record<string, string>;
    };
}

interface HealthData {
    status: string;
    agent_performances: Record<string, {
        agent_type: string;
        total_signals: number;
        win_rate: number;
        sharpe_ratio: number;
        max_drawdown: number;
    }>;
}

export default function RealTimeSignalPanel() {
    const [health, setHealth] = useState<HealthData | null>(null);
    const [latestSignal, setLatestSignal] = useState<SignalData | null>(null);
    const [loading, setLoading] = useState(false);
    const [autoGenerate, setAutoGenerate] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Load health data
    useEffect(() => {
        const loadHealth = async () => {
            try {
                const data = await api.v2.healthCheck() as HealthData;
                setHealth(data);
            } catch (err) {
                setError("Failed to load health data");
            }
        };
        loadHealth();
        const interval = setInterval(loadHealth, 10000); // Update every 10 seconds
        return () => clearInterval(interval);
    }, []);

    // Auto-generate signals
    useEffect(() => {
        if (!autoGenerate) return;

        const generateSignal = async () => {
            try {
                const signal = await api.v2.generateSignal("EURUSD") as SignalData;
                setLatestSignal(signal);
                setError(null);
            } catch (err) {
                setError("Failed to generate signal");
            }
        };

        generateSignal();
        const interval = setInterval(generateSignal, 30000); // Every 30 seconds
        return () => clearInterval(interval);
    }, [autoGenerate]);

    const handleGenerateSignal = async (pair: string = "EURUSD") => {
        setLoading(true);
        setError(null);
        try {
            const signal = await api.v2.generateSignal(pair) as SignalData;
            setLatestSignal(signal);
        } catch (err) {
            setError("Failed to generate signal");
        } finally {
            setLoading(false);
        }
    };

    const getSignalIcon = (direction: string) => {
        switch (direction) {
            case "BUY":
                return <TrendingUp className="size-5 text-green-500" />;
            case "SELL":
                return <TrendingDown className="size-5 text-red-500" />;
            default:
                return <Minus className="size-5 text-yellow-500" />;
        }
    };

    const getSignalColor = (direction: string) => {
        switch (direction) {
            case "BUY":
                return "bg-green-500/10 text-green-600 border-green-500/20";
            case "SELL":
                return "bg-red-500/10 text-red-600 border-red-500/20";
            default:
                return "bg-yellow-500/10 text-yellow-600 border-yellow-500/20";
        }
    };

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

    return (
        <div className="space-y-6">
            {/* System Status */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Activity className="size-5" />
                        System Status
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="text-center">
                            <div className="text-2xl font-bold text-green-600">
                                {health?.status || "Unknown"}
                            </div>
                            <div className="text-sm text-muted-foreground">Status</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold">
                                {Object.keys(health?.agent_performances || {}).length}
                            </div>
                            <div className="text-sm text-muted-foreground">Active Agents</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold">{totalSignals}</div>
                            <div className="text-sm text-muted-foreground">Total Signals</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold">{avgWinRate}%</div>
                            <div className="text-sm text-muted-foreground">Avg Win Rate</div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Signal Generation */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Zap className="size-5" />
                            Signal Generation
                        </div>
                        <div className="flex items-center gap-2">
                            <Button
                                variant={autoGenerate ? "default" : "outline"}
                                size="sm"
                                onClick={() => setAutoGenerate(!autoGenerate)}
                            >
                                {autoGenerate ? <StopCircle className="size-4 mr-2" /> : <Play className="size-4 mr-2" />}
                                Auto {autoGenerate ? "Stop" : "Start"}
                            </Button>
                            <Button
                                onClick={() => handleGenerateSignal()}
                                disabled={loading}
                                size="sm"
                            >
                                <RefreshCw className={`size-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                                Generate
                            </Button>
                        </div>
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {error && (
                        <div className="mb-4 p-3 bg-red-500/10 text-red-600 rounded-md">
                            {error}
                        </div>
                    )}

                    {latestSignal && (
                        <div className="space-y-4">
                            {/* Signal Summary */}
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    {getSignalIcon(latestSignal.direction)}
                                    <div>
                                        <div className="font-semibold">{latestSignal.direction}</div>
                                        <div className="text-sm text-muted-foreground">
                                            Confidence: {(latestSignal.confidence * 100).toFixed(1)}%
                                        </div>
                                    </div>
                                </div>
                                <Badge className={getSignalColor(latestSignal.direction)}>
                                    ID: {latestSignal.signal_id}
                                </Badge>
                            </div>

                            <Separator />

                            {/* Agent Breakdown */}
                            <div>
                                <h4 className="font-semibold mb-3">Agent Votes</h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {Object.entries(latestSignal.signal.agent_votes).map(([agent, vote]) => (
                                        <div key={agent} className="flex items-center justify-between p-3 bg-muted/50 rounded-md">
                                            <div className="flex items-center gap-2">
                                                <Bot className="size-4" />
                                                <span className="capitalize">{agent}</span>
                                            </div>
                                            <div className="text-right">
                                                <div className="font-medium">{vote.signal}</div>
                                                <div className="text-sm text-muted-foreground">
                                                    {(vote.confidence * 100).toFixed(0)}%
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <Separator />

                            {/* Market Regime */}
                            <div className="flex items-center justify-between">
                                <span className="text-muted-foreground">Market Regime:</span>
                                <Badge variant="outline">{latestSignal.signal.market_regime}</Badge>
                            </div>

                            {/* Conflicts */}
                            {latestSignal.signal.conflicts.length > 0 && (
                                <div>
                                    <h4 className="font-semibold mb-2">Conflicts</h4>
                                    <div className="space-y-1">
                                        {latestSignal.signal.conflicts.map((conflict, index) => (
                                            <div key={index} className="text-sm text-orange-600">
                                                ⚠️ {conflict}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Reasoning */}
                            <div>
                                <h4 className="font-semibold mb-2">Reasoning</h4>
                                <div className="text-sm text-muted-foreground whitespace-pre-wrap">
                                    {latestSignal.signal.reasoning}
                                </div>
                            </div>
                        </div>
                    )}

                    {!latestSignal && !loading && (
                        <div className="text-center py-8 text-muted-foreground">
                            Click "Generate" to create a new signal
                        </div>
                    )}

                    {loading && (
                        <div className="text-center py-8">
                            <RefreshCw className="size-8 animate-spin mx-auto mb-2" />
                            <div className="text-muted-foreground">Generating signal...</div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Agent Performance */}
            {health && (
                <Card>
                    <CardHeader>
                        <CardTitle>Agent Performance</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            {Object.entries(health.agent_performances).map(([agent, perf]) => (
                                <div key={agent} className="p-4 bg-muted/50 rounded-md">
                                    <h4 className="font-semibold capitalize mb-2">{agent}</h4>
                                    <div className="space-y-1 text-sm">
                                        <div className="flex justify-between">
                                            <span>Signals:</span>
                                            <span>{perf.total_signals}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Win Rate:</span>
                                            <span>{(perf.win_rate * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Sharpe:</span>
                                            <span>{perf.sharpe_ratio.toFixed(2)}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Max DD:</span>
                                            <span>{perf.max_drawdown.toFixed(1)}%</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
