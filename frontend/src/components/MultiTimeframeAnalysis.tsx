"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { TrendingUp, TrendingDown, Minus, Clock, Activity } from 'lucide-react';

interface TimeframeSignal {
  timeframe: string;
  signal: number;
  confidence: number;
  reasoning: string;
  indicators: any;
}

interface MultiTimeframeData {
  signal: number;
  confidence: number;
  timeframe_signals: Record<string, any>;
  reasoning: string;
  agent: string;
  features_used: any;
}

interface MultiTimeframeAnalysisProps {
  symbol: string;
  onSignalGenerated?: (signal: MultiTimeframeData) => void;
}

export function MultiTimeframeAnalysis({ symbol, onSignalGenerated }: MultiTimeframeAnalysisProps) {
  const [data, setData] = useState<MultiTimeframeData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateSignal = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.tactical.multitimeframeSignal(symbol);
      setData(response.signal as MultiTimeframeData);
      onSignalGenerated?.(response.signal as MultiTimeframeData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la génération du signal');
    } finally {
      setLoading(false);
    }
  };

  const getSignalIcon = (signal: number) => {
    switch (signal) {
      case 1:
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case -1:
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Minus className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getSignalColor = (signal: number) => {
    switch (signal) {
      case 1:
        return 'bg-green-100 text-green-800 border-green-200';
      case -1:
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    }
  };

  const getSignalText = (signal: number) => {
    switch (signal) {
      case 1:
        return 'ACHAT';
      case -1:
        return 'VENTE';
      default:
        return 'NEUTRE';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-500';
    if (confidence >= 0.6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const formatTimeframeCategory = (category: string) => {
    switch (category) {
      case 'tactique':
        return 'Court Terme (Tactique)';
      case 'strategique':
        return 'Moyen Terme (Stratégique)';
      case 'positionnel':
        return 'Long Terme (Positionnel)';
      default:
        return category;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Analyse Multi-Timeframe - {symbol}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Bouton de génération */}
        <div className="flex justify-center">
          <Button 
            onClick={generateSignal}
            disabled={loading}
            className="w-full max-w-md"
          >
            {loading ? (
              <>
                <Clock className="mr-2 h-4 w-4 animate-spin" />
                Analyse en cours...
              </>
            ) : (
              'Générer Signal Multi-Timeframe'
            )}
          </Button>
        </div>

        {/* Erreur */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            <strong>Erreur:</strong> {error}
          </div>
        )}

        {/* Signal principal */}
        {data && (
          <div className="text-center space-y-3">
            <div className={`inline-flex items-center gap-3 px-6 py-4 rounded-lg border-2 ${getSignalColor(data.signal)}`}>
              {getSignalIcon(data.signal)}
              <span className="text-2xl font-bold">
                {getSignalText(data.signal)}
              </span>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-center gap-2">
                <span className="text-sm text-gray-600">Confiance:</span>
                <div className="flex items-center gap-2">
                  <div className={`w-24 h-2 rounded-full ${getConfidenceColor(data.confidence)}`} />
                  <span className="text-sm font-medium">
                    {(data.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Signaux par timeframe */}
        {data?.timeframe_signals && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-center">Analyse par Timeframe</h3>
            
            {Object.entries(data.timeframe_signals).map(([category, categoryData]) => (
              <Card key={category} className="border-l-4 border-l-blue-500">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">
                    {formatTimeframeCategory(category)}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {/* Signal agrégé de la catégorie */}
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <span className="font-medium">Signal Catégorie:</span>
                    <div className="flex items-center gap-2">
                      {getSignalIcon(categoryData.signal)}
                      <span className="font-bold">
                        {getSignalText(categoryData.signal)}
                      </span>
                      <Badge variant="outline">
                        {(categoryData.confidence * 100).toFixed(1)}%
                      </Badge>
                    </div>
                  </div>

                  {/* Signaux individuels */}
                  {categoryData.individual_signals && categoryData.individual_signals.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium text-gray-700">Signaux Individuels:</h4>
                      {categoryData.individual_signals.map((signal: any, index: number) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-white border rounded">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium">{signal.timeframe}</span>
                            {getSignalIcon(signal.signal)}
                            <span className="text-sm">{getSignalText(signal.signal)}</span>
                          </div>
                          <Badge variant="outline" className="text-xs">
                            {(signal.confidence * 100).toFixed(1)}%
                          </Badge>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Raisonnement */}
                  {categoryData.reasoning && (
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded">
                      <h4 className="text-sm font-medium text-blue-800 mb-1">Raisonnement:</h4>
                      <p className="text-sm text-blue-700">{categoryData.reasoning}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Raisonnement principal */}
        {data?.reasoning && (
          <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <h3 className="font-semibold text-gray-800 mb-2">Raisonnement Global:</h3>
            <p className="text-sm text-gray-700 whitespace-pre-line">{data.reasoning}</p>
          </div>
        )}

        {/* Features utilisées */}
        {data?.features_used && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="font-semibold text-blue-800 mb-2">Paramètres d'Analyse:</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              {Object.entries(data.features_used).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="font-medium text-blue-700 capitalize">{key}:</span>
                  <span className="text-blue-600">{(value as number).toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
