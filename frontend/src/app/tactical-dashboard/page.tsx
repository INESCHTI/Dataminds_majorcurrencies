"use client";

import React, { useState } from 'react';
import { MultiTimeframeAnalysis } from '@/components/MultiTimeframeAnalysis';
import { TacticalReport } from '@/components/TacticalReport';
import { MT5Monitor } from '@/components/MT5Monitor';
import { FreshnessHealthCard } from '@/components/freshness-health-card';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { 
  BarChart3, 
  FileText, 
  Activity, 
  TrendingUp,
  Shield,
  Globe,
  Clock
} from 'lucide-react';

interface TacticalPosition {
  symbol: string;
  direction: string;
  confidence: number;
  timeframe: string;
  entry_zone: Record<string, number>;
  stop_loss: number;
  take_profit: number;
  risk_reward: number;
  reasoning: string;
  market_regime: string;
  catalysts: string[];
  risks: string[];
}

export default function TacticalDashboard() {
  const [activePositions, setActivePositions] = useState<TacticalPosition[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState('EURUSD');

  const handlePositionsUpdate = (positions: TacticalPosition[]) => {
    setActivePositions(positions);
  };

  const getActivePositionsCount = () => {
    return activePositions.filter(p => p.confidence > 0.7).length;
  };

  const getHighConfidencePositions = () => {
    return activePositions.filter(p => p.confidence > 0.8);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      {/* En-tête */}
      <div className="mb-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-2xl">
              <BarChart3 className="h-8 w-8 text-blue-600" />
              Tableau de Bord Tactique Forex
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {getActivePositionsCount()}
                </div>
                <div className="text-sm text-blue-700">Positions Actives</div>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {getHighConfidencePositions().length}
                </div>
                <div className="text-sm text-green-700">Haute Confiance</div>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">4</div>
                <div className="text-sm text-purple-700">Paires Majeures</div>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">24/7</div>
                <div className="text-sm text-orange-700">Monitoring</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tableau de bord principal */}
      <Tabs defaultValue="monitoring" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="monitoring" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Monitoring MT5
          </TabsTrigger>
          <TabsTrigger value="analysis" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Analyse Multi-TF
          </TabsTrigger>
          <TabsTrigger value="reports" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Rapports Tactiques
          </TabsTrigger>
          <TabsTrigger value="freshness" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Fraîcheur Données
          </TabsTrigger>
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Globe className="h-4 w-4" />
            Vue d'Ensemble
          </TabsTrigger>
        </TabsList>

        {/* Onglet Monitoring MT5 */}
        <TabsContent value="monitoring" className="space-y-6">
          <MT5Monitor />
        </TabsContent>

        {/* Onglet Analyse Multi-Timeframe */}
        <TabsContent value="analysis" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Sélection de la Paire</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'].map((symbol) => (
                  <button
                    key={symbol}
                    onClick={() => setSelectedSymbol(symbol)}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      selectedSymbol === symbol
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium">{symbol}</div>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          <MultiTimeframeAnalysis 
            symbol={selectedSymbol}
            onSignalGenerated={(signal) => {
              console.log('Signal généré:', signal);
            }}
          />
        </TabsContent>

        {/* Onglet Rapports Tactiques */}
        <TabsContent value="reports" className="space-y-6">
          <TacticalReport 
            onPositionsUpdate={handlePositionsUpdate}
          />
        </TabsContent>

        {/* Onglet Fraîcheur Données */}
        <TabsContent value="freshness" className="space-y-6">
          <FreshnessHealthCard />
        </TabsContent>

        {/* Onglet Vue d'Ensemble */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Résumé des positions */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Résumé des Positions
                </CardTitle>
              </CardHeader>
              <CardContent>
                {activePositions.length > 0 ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 gap-3">
                      {activePositions.slice(0, 5).map((position, index) => (
                        <div key={index} className="p-3 border rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium">{position.symbol}</span>
                            <Badge className={
                              position.direction === 'BUY' 
                                ? 'bg-green-100 text-green-800'
                                : position.direction === 'SELL'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-yellow-100 text-yellow-800'
                            }>
                              {position.direction}
                            </Badge>
                          </div>
                          <div className="text-sm text-gray-600">
                            <div>Confiance: {(position.confidence * 100).toFixed(1)}%</div>
                            <div>R/R: {position.risk_reward.toFixed(2)}</div>
                            <div>Timeframe: {position.timeframe}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    {activePositions.length > 5 && (
                      <div className="text-center text-sm text-gray-600">
                        ... et {activePositions.length - 5} autres positions
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    <Shield className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <div>Aucune position active</div>
                    <div className="text-sm">Générez un rapport tactique pour voir les positions</div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Statistiques du système */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  État du Système
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">✅</div>
                      <div className="text-sm text-green-700">Backend Actif</div>
                    </div>
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">4</div>
                      <div className="text-sm text-blue-700">Agents Actifs</div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">MCP</div>
                      <div className="text-sm text-purple-700">Protocole Actif</div>
                    </div>
                    <div className="text-center p-4 bg-orange-50 rounded-lg">
                      <div className="text-2xl font-bold text-orange-600">100%</div>
                      <div className="text-sm text-orange-700">Données Gratuites</div>
                    </div>
                  </div>

                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-medium mb-2">Architecture Multi-Agents:</h4>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                        <span>Technical Agent</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                        <span>Macro Agent</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                        <span>Sentiment Agent</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                        <span>Geopolitical Agent</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                        <span>Multi-Timeframe Agent</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                        <span>MT5 Connector</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
