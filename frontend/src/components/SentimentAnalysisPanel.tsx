"use client";

import { useState } from "react";
import { useAnalyzeSentiment } from "@/hooks/useFastAPI";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { ChangeEvent } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, TrendingDown, Minus, AlertTriangle, MessageSquare } from "lucide-react";

export function SentimentAnalysisPanel() {
    const [text, setText] = useState("");
    const analyzeSentiment = useAnalyzeSentiment();

    const handleAnalyze = () => {
        if (text.trim()) {
            analyzeSentiment.mutate({ texts: [text] });
        }
    };

    const result = analyzeSentiment.data?.results?.[0];

    return (
        <Card>
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-semibold flex items-center gap-2">
                        <MessageSquare className="w-5 h-5" />
                        FinBERT Sentiment
                    </CardTitle>
                    <Badge variant="outline" className="text-xs">
                        AI-Powered
                    </Badge>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Input */}
                <div className="space-y-2">
                    <label className="text-sm font-medium">Enter financial text</label>
                    <textarea
                        placeholder="e.g., Fed raises interest rates by 25 basis points..."
                        value={text}
                        onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setText(e.target.value)}
                        rows={3}
                        className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <Button 
                        onClick={handleAnalyze} 
                        disabled={!text.trim() || analyzeSentiment.isPending}
                        className="w-full"
                    >
                        {analyzeSentiment.isPending ? "Analyzing..." : "Analyze Sentiment"}
                    </Button>
                </div>

                {/* Results */}
                {analyzeSentiment.isPending && (
                    <div className="space-y-2">
                        <Skeleton className="h-8 w-full" />
                        <Skeleton className="h-4 w-3/4" />
                    </div>
                )}

                {result && (
                    <div className="space-y-3 p-3 rounded-lg bg-gray-50">
                        {/* Sentiment Badge */}
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">Sentiment</span>
                            <Badge 
                                className={
                                    result.sentiment === 'bullish' ? 'bg-green-500' :
                                    result.sentiment === 'bearish' ? 'bg-red-500' :
                                    'bg-gray-500'
                                }
                            >
                                {result.sentiment.toUpperCase()}
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
                                        result.sentiment === 'bullish' ? 'bg-green-500' :
                                        result.sentiment === 'bearish' ? 'bg-red-500' :
                                        'bg-gray-500'
                                    }`}
                                    style={{ width: `${result.confidence * 100}%` }}
                                />
                            </div>
                        </div>

                        {/* Entities */}
                        {result.entities.length > 0 && (
                            <div className="space-y-1">
                                <span className="text-sm font-medium">Entities Detected</span>
                                <div className="flex flex-wrap gap-1">
                                    {result.entities.map((entity: string, i: number) => (
                                        <Badge key={i} variant="outline" className="text-xs">
                                            {entity}
                                        </Badge>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {analyzeSentiment.isError && (
                    <div className="flex items-center gap-2 text-red-500 text-sm">
                        <AlertTriangle className="w-4 h-4" />
                        <span>Failed to analyze sentiment</span>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
