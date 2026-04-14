"use client";

import { useForecast } from "@/hooks/useFastAPI";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, TrendingDown, Minus, AlertTriangle, LucideIcon } from "lucide-react";
import type { ForecastResponse } from "@/types/fastapi";

interface EnsembleForecastPanelProps {
    pair: string;
    periods?: number;
}

interface DirectionConfig {
    icon: LucideIcon;
    color: string;
    text: string;
    label: string;
}

type DirectionType = 'UPTREND' | 'DOWNTREND' | 'SIDEWAYS';

const directionConfig: Record<DirectionType, DirectionConfig> = {
    UPTREND: { icon: TrendingUp, color: "bg-green-500", text: "text-green-600", label: "Uptrend" },
    DOWNTREND: { icon: TrendingDown, color: "bg-red-500", text: "text-red-600", label: "Downtrend" },
    SIDEWAYS: { icon: Minus, color: "bg-gray-500", text: "text-gray-600", label: "Sideways" },
};

export function EnsembleForecastPanel({ pair, periods = 24 }: EnsembleForecastPanelProps) {
    const { data: forecast, isLoading, error } = useForecast(pair, periods);

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">Ensemble Forecast</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                </CardContent>
            </Card>
        );
    }

    if (error || !forecast) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">Ensemble Forecast</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-2 text-red-500">
                        <AlertTriangle className="w-5 h-5" />
                        <span>Failed to load forecast</span>
                    </div>
                </CardContent>
            </Card>
        );
    }

    const safeDirection = (forecast.direction as DirectionType) || 'SIDEWAYS';
    const config = directionConfig[safeDirection] || directionConfig['SIDEWAYS'];
    const Icon = config?.icon || Minus;

    return (
        <Card>
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-semibold">Ensemble Forecast</CardTitle>
                    <Badge variant="outline" className="text-xs">
                        Prophet + Kats
                    </Badge>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Main Direction */}
                <div className="flex items-center gap-4">
                    <div className={`p-3 rounded-full ${config?.color || 'bg-gray-500'} bg-opacity-20`}>
                        <Icon className={`w-8 h-8 ${config?.text || 'text-gray-600'}`} />
                    </div>
                    <div>
                        <div className={`text-2xl font-bold ${config?.text || 'text-gray-600'}`}>
                            {config?.label || 'Unknown'}
                        </div>
                        <div className="text-sm text-muted-foreground">
                            {forecast.forecast_horizon}h forecast horizon
                        </div>
                    </div>
                </div>

                {/* Confidence Bar */}
                <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Confidence</span>
                        <span className="font-medium">{(forecast.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                            className={`h-full ${config?.color || 'bg-gray-500'} transition-all duration-500`}
                            style={{ width: `${forecast.confidence * 100}%` }}
                        />
                    </div>
                </div>

                {/* Model Consensus */}
                {forecast.individual_forecasts && (
                    <div className="space-y-2 pt-2 border-t">
                        <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                            Model Consensus
                        </div>
                        <div className="grid grid-cols-3 gap-2">
                            {Object.entries(forecast.individual_forecasts as Record<string, { direction: string }>).map(([model, modelData]) => (
                                <div
                                    key={model}
                                    className="text-center p-2 rounded-lg bg-gray-50"
                                >
                                    <div className="text-xs text-muted-foreground capitalize">
                                        {model.replace('_', ' ')}
                                    </div>
                                    <div className={`text-sm font-medium ${
                                        modelData.direction === 'UPTREND' ? 'text-green-600' :
                                        modelData.direction === 'DOWNTREND' ? 'text-red-600' :
                                        'text-gray-600'
                                    }`}>
                                        {modelData.direction === 'UPTREND' ? '↑' :
                                         modelData.direction === 'DOWNTREND' ? '↓' : '→'}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Anomaly Warning */}
                {forecast.anomalies_detected && (
                    <div className="flex items-center gap-2 p-2 rounded-lg bg-yellow-50 border border-yellow-200">
                        <AlertTriangle className="w-4 h-4 text-yellow-600" />
                        <span className="text-sm text-yellow-700">Anomalies detected in forecast</span>
                    </div>
                )}

                {/* Timestamp */}
                <div className="text-xs text-muted-foreground text-right">
                    Updated: {new Date(forecast.timestamp).toLocaleTimeString()}
                </div>
            </CardContent>
        </Card>
    );
}
