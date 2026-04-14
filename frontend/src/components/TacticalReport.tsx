"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { api } from '@/lib/api';
import { 
  FileText, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle,
  Clock,
  Activity,
  DollarSign,
  Shield
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

interface TacticalReport {
  report_id: string;
  generated_at: string;
  positions: TacticalPosition[];
  market_overview: any;
  risk_assessment: any;
  performance_summary: any;
  recommendations: string[];
}

interface TacticalReportProps {
  onPositionsUpdate?: (positions: TacticalPosition[]) => void;
}

export function TacticalReport({ onPositionsUpdate }: TacticalReportProps) {
  const [report, setReport] = useState<TacticalReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateReport = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.tactical.generateTacticalReport(true);
      setReport(response.report as TacticalReport);
      onPositionsUpdate?.(response.report.positions as TacticalPosition[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la génération du rapport');
    } finally {
      setLoading(false);
    }
  };

  const getDirectionIcon = (direction: string) => {
    switch (direction) {
      case 'BUY':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'SELL':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getDirectionColor = (direction: string) => {
    switch (direction) {
      case 'BUY':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'SELL':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low':
        return 'bg-green-100 text-green-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'high':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getConfidenceWidth = (confidence: number) => {
    return `${(confidence * 100)}%`;
  };

  const formatCurrency = (value: number) => {
    return value.toFixed(5);
  };

  const downloadReport = () => {
    if (!report) return;
    
    const dataStr = JSON.stringify(report, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `tactical_report_${report.report_id}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* En-tête et génération */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Rapport Tactique Forex
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
            <div className="text-sm text-gray-600">
              Générez une analyse tactique complète des 4 paires majeures
            </div>
            <Button 
              onClick={generateReport}
              disabled={loading}
              className="w-full sm:w-auto"
            >
              {loading ? (
                <>
                  <Clock className="mr-2 h-4 w-4 animate-spin" />
                  Génération en cours...
                </>
              ) : (
                <>
                  <FileText className="mr-2 h-4 w-4" />
                  Générer Rapport Tactique
                </>
              )}
            </Button>
          </div>

          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              <strong>Erreur:</strong> {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Rapport généré */}
      {report && (
        <Tabs defaultValue="positions" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="positions">Positions</TabsTrigger>
            <TabsTrigger value="market">Marché</TabsTrigger>
            <TabsTrigger value="risks">Risques</TabsTrigger>
            <TabsTrigger value="recommendations">Recommandations</TabsTrigger>
          </TabsList>

          {/* Onglet Positions */}
          <TabsContent value="positions" className="space-y-4">
            <div className="grid gap-4">
              {report.positions.map((position, index) => (
                <Card key={index} className="border-l-4 border-l-blue-500">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <DollarSign className="h-5 w-5" />
                        {position.symbol}
                      </CardTitle>
                      <div className="flex items-center gap-2">
                        <Badge className={getDirectionColor(position.direction)}>
                          {position.direction}
                        </Badge>
                        <Badge variant="outline">
                          {(position.confidence * 100).toFixed(1)}%
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Zone d'entrée et niveaux */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <h4 className="font-medium text-gray-700">Zone d'Entrée</h4>
                        <div className="p-3 bg-blue-50 border border-blue-200 rounded">
                          <div className="text-sm space-y-1">
                            <div className="flex justify-between">
                              <span>Optimal:</span>
                              <span className="font-medium">
                                {formatCurrency(position.entry_zone.optimal || 0)}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span>Borne inf:</span>
                              <span>{formatCurrency(position.entry_zone.lower || 0)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Borne sup:</span>
                              <span>{formatCurrency(position.entry_zone.upper || 0)}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <h4 className="font-medium text-gray-700">Gestion Risque</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between items-center p-2 bg-red-50 rounded">
                            <span className="text-sm">Stop Loss:</span>
                            <span className="font-medium text-red-700">
                              {formatCurrency(position.stop_loss)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center p-2 bg-green-50 rounded">
                            <span className="text-sm">Take Profit:</span>
                            <span className="font-medium text-green-700">
                              {formatCurrency(position.take_profit)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center p-2 bg-purple-50 rounded">
                            <span className="text-sm">R/R:</span>
                            <span className="font-medium text-purple-700">
                              {position.risk_reward.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Confiance */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm font-medium text-gray-700">Confiance:</span>
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: getConfidenceWidth(position.confidence) }}
                          />
                        </div>
                        <span className="text-sm font-medium">
                          {(position.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    {/* Catalyseurs */}
                    {position.catalysts && position.catalysts.length > 0 && (
                      <div>
                        <h4 className="font-medium text-gray-700 mb-2 flex items-center gap-2">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          Catalyseurs
                        </h4>
                        <div className="space-y-1">
                          {position.catalysts.map((catalyst, idx) => (
                            <Badge key={idx} variant="outline" className="mr-2">
                              {catalyst}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Risques */}
                    {position.risks && position.risks.length > 0 && (
                      <div>
                        <h4 className="font-medium text-gray-700 mb-2 flex items-center gap-2">
                          <AlertTriangle className="h-4 w-4 text-yellow-500" />
                          Risques Identifiés
                        </h4>
                        <div className="space-y-1">
                          {position.risks.map((risk, idx) => (
                            <div key={idx} className="p-2 bg-yellow-50 border border-yellow-200 rounded text-sm">
                              {risk}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Raisonnement */}
                    {position.reasoning && (
                      <div className="p-3 bg-gray-50 border border-gray-200 rounded">
                        <h4 className="font-medium text-gray-800 mb-1">Raisonnement:</h4>
                        <p className="text-sm text-gray-700">{position.reasoning}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Onglet Marché */}
          <TabsContent value="market" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Vue d'ensemble */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Vue d'Ensemble</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span>Session Actuelle:</span>
                    <Badge>{report.market_overview.market_session?.session || 'N/A'}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Régime Volatilité:</span>
                    <Badge className={getRiskColor(report.market_overview.volatility_regime?.regime)}>
                      {report.market_overview.volatility_regime?.regime || 'N/A'}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Dernière MAJ:</span>
                    <span className="text-sm text-gray-600">
                      {new Date(report.market_overview.timestamp).toLocaleString()}
                    </span>
                  </div>
                </CardContent>
              </Card>

              {/* Sentiment */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Sentiment Marché</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span>Statut:</span>
                    <Badge>{report.market_overview.sentiment_summary?.overall || 'N/A'}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Articles 24h:</span>
                    <span>{report.market_overview.sentiment_summary?.articles_last_24h || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Score Fraîcheur:</span>
                    <span>{report.market_overview.sentiment_summary?.freshness_score?.toFixed(1) || 0}%</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Onglet Risques */}
          <TabsContent value="risks" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Évaluation des Risques
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className={`p-4 rounded-lg ${getRiskColor(report.risk_assessment.overall_risk_level)}`}>
                    <h4 className="font-semibold mb-2">Niveau de Risque Global</h4>
                    <div className="text-2xl font-bold capitalize">
                      {report.risk_assessment.overall_risk_level}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="font-medium">Facteurs de Risque</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Risque Volatilité:</span>
                        <Badge className={getRiskColor(report.risk_assessment.volatility_risk)}>
                          {report.risk_assessment.volatility_risk}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span>Risque Corrélation:</span>
                        <Badge className={getRiskColor(report.risk_assessment.correlation_risk)}>
                          {report.risk_assessment.correlation_risk}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Risques géopolitiques */}
                {report.risk_assessment.geopolitical_risks && (
                  <div>
                    <h4 className="font-medium mb-2">Risques Géopolitiques</h4>
                    <div className="space-y-1">
                      {report.risk_assessment.geopolitical_risks.map((risk: string, idx: number) => (
                        <div key={idx} className="p-2 bg-orange-50 border border-orange-200 rounded text-sm">
                          {risk}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Risques économiques */}
                {report.risk_assessment.economic_risks && (
                  <div>
                    <h4 className="font-medium mb-2">Risques Économiques</h4>
                    <div className="space-y-1">
                      {report.risk_assessment.economic_risks.map((risk: string, idx: number) => (
                        <div key={idx} className="p-2 bg-blue-50 border border-blue-200 rounded text-sm">
                          {risk}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Onglet Recommandations */}
          <TabsContent value="recommendations" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  Recommandations Actionnables
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {report.recommendations.map((recommendation, index) => (
                    <div key={index} className="p-3 bg-green-50 border border-green-200 rounded">
                      <p className="text-sm text-green-800">{recommendation}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {/* Actions du rapport */}
      {report && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
              <div className="text-sm text-gray-600">
                Rapport généré le: {new Date(report.generated_at).toLocaleString()}
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={downloadReport}>
                  <FileText className="mr-2 h-4 w-4" />
                  Télécharger JSON
                </Button>
                <Button onClick={generateReport}>
                  <Clock className="mr-2 h-4 w-4" />
                  Actualiser
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
