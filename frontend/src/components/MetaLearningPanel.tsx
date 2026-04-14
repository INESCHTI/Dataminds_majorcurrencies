"use client";

import { useState } from "react";
import { useMetaLearner } from "@/hooks/useFastAPI";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, TrendingDown, Minus, AlertTriangle, Brain } from "lucide-react";

interface AgentPrediction {
    agent_name: string;
    signal: number;
    confidence: number;
}

export function MetaLearningPanel() {
    const metaLearner = useMetaLearner();
    const [predictions, setPredictions] = useState<AgentPrediction[]>([
        { agent_name: "technical", signal: 1, confidence: 0.75 },
        { agent_name: "macro", signal: 0, confidence: 0.60 },
        { agent_name: "sentiment", signal: 1, confidence: 0.80 },
        { agent_name: "geopolitical", signal: -1, confidence: 0.55 },
    ]);

    const handlePredict = () => {
        metaLearner.mutate({ predictions });
    };

    const result = metaLearner.data;

    const updatePrediction = (index: number, field: keyof AgentPrediction, value: number) => {
        const newPredictions = [...predictions];
        newPredictions[index] = { ...newPredictions[index], [field]: value };
        setPredictions(newPredictions);
    };

    return (
        <Card>
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-semibold flex items-center gap-2">
                        <Brain className="w-5 h-5" />
                        Meta-Learning Ensemble
                    </CardTitle>
                    <Badge variant="outline" className="text-xs">
                        Stacking
                    </Badge>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Agent Predictions */}
                <div className="space-y-2">
                    <label className="text-sm font-medium">Agent Predictions</label>
                    {predictions.map((pred, index) => (
                        <div key={pred.agent_name} className="flex items-center gap-2 p-2 rounded-lg bg-gray-50">
                            <span className="text-sm capitalize w-24">{pred.agent_name}</span>
                            <select
                                value={pred.signal}
                                onChange={(e) => updatePrediction(index, 'signal', parseInt(e.target.value))}
                                className="px-2 py-1 border rounded text-sm"
                            >
                                <option value={1}>Buy</option>
                                <option value={0}>Neutral</option>
                                <option value={-1}>Sell</option>
                            </select>
                            <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.05"
                                value={pred.confidence}
                                onChange={(e) => updatePrediction(index, 'confidence', parseFloat(e.target.value))}
                                className="flex-1"
                            />
                            <span className="text-xs w-12 text-right">{(pred.confidence * 100).toFixed(0)}%</span>
                        </div>
                    ))}
                </div>

                <Button 
                    onClick={handlePredict} 
                    disabled={metaLearner.isPending}
                    className="w-full"
                >
                    {metaLearner.isPending ? "Computing..." : "Run Meta-Learner"}
                </Button>

                {/* Results */}
                {metaLearner.isPending && (
                    <div className="space-y-2">
                        <Skeleton className="h-8 w-full" />
                        <Skeleton className="h-4 w-3/4" />
                    </div>
                )}

                {result && (
                    <div className="space-y-3 p-3 rounded-lg bg-blue-50">
                        {/* Final Signal */}
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">Ensemble Signal</span>
                            <Badge 
                                className={
                                    result.direction === 'BUY' ? 'bg-green-500' :
                                    result.direction === 'SELL' ? 'bg-red-500' :
                                    'bg-gray-500'
                                }
                            >
                                {result.direction}
                            </Badge>
                        </div>

                        {/* Confidence */}
                        <div className="space-y-1">
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Confidence</span>
                                <span className="font-medium">{(result.confidence * 100).toFixed(1)}%</span>
                            </div>
                            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                    className={`h-full transition-all duration-500 ${
                                        result.direction === 'BUY' ? 'bg-green-500' :
                                        result.direction === 'SELL' ? 'bg-red-500' :
                                        'bg-gray-500'
                                    }`}
                                    style={{ width: `${result.confidence * 100}%` }}
                                />
                            </div>
                        </div>

                        {/* Individual Models */}
                        {result.individual_results && (
                            <div className="space-y-2 pt-2 border-t border-blue-200">
                                <span className="text-xs font-medium text-blue-800">Model Contributions</span>
                                <div className="grid grid-cols-3 gap-2">
                                    {Object.entries(result.individual_results as Record<string, { signal: number; confidence: number }>).map(([model, modelData]) => (
                                        <div key={model} className="text-center p-2 rounded bg-white">
                                            <div className="text-xs text-muted-foreground capitalize">
                                                {model.replace('_', ' ')}
                                            </div>
                                            <div className={`text-sm font-medium ${
                                                modelData.signal === 1 ? 'text-green-600' :
                                                modelData.signal === -1 ? 'text-red-600' :
                                                'text-gray-600'
                                            }`}>
                                                {modelData.signal === 1 ? '↑' : modelData.signal === -1 ? '↓' : '→'}
                                            </div>
                                            <div className="text-xs text-muted-foreground">
                                                {(modelData.confidence * 100).toFixed(0)}%
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {metaLearner.isError && (
                    <div className="flex items-center gap-2 text-red-500 text-sm">
                        <AlertTriangle className="w-4 h-4" />
                        <span>Meta-learner failed</span>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
