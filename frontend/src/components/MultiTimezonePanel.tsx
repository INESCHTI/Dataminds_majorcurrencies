/**
 * Multi-Timezone Optimization Panel Component
 * Displays session-based trading strategies and timezone optimization
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Globe, 
  Clock, 
  TrendingUp,
  TrendingDown,
  Target,
  RefreshCw,
  BarChart3,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import { api } from '@/lib/api';
import { 
  Activity,
  Moon,
  Calendar,
  Sun
} from 'lucide-react';

interface SessionRecommendation {
  session: string;
  weight: number;
  characteristics: any;
  action: string;
  risk_level: string;
  optimal_strategies: string[];
}

interface SessionStatistics {
  session_overview: Record<string, {
    name: string;
    timezone: string;
    hours: string;
    major_currencies: string[];
    volatility_multiplier: number;
    volume_multiplier: number;
  }>;
  currency_performance: Record<string, Record<string, {
    total_trades: number;
    win_rate: number;
    avg_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    optimal_weight: number;
    last_updated: string;
  }>>;
  optimization_summary: {
    total_currency_pairs: number;
    total_trades_analyzed: number;
    active_sessions: string[];
    current_overlap: string | null;
    last_optimization: string;
  };
}

interface MultiTimezonePanelProps {
  className?: string;
}

export default function MultiTimezonePanel({ className }: MultiTimezonePanelProps) {
  const [currentSessions, setCurrentSessions] = useState<string[]>([]);
  const [currentOverlap, setCurrentOverlap] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [sessionWeights, setSessionWeights] = useState<Record<string, number>>({});
  const [statistics, setStatistics] = useState<SessionStatistics | null>(null);
  const [selectedCurrency, setSelectedCurrency] = useState('EURUSD');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCurrentSession = async () => {
    try {
      const data = await api.advanced.timezone.getCurrentSession() as any;
      setCurrentSessions(data.current_sessions);
      setCurrentOverlap(data.session_overlap);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const fetchRecommendations = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await api.advanced.timezone.getSessionRecommendations(selectedCurrency) as any;
      setRecommendations(data.recommendations);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const optimizeWeights = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await api.advanced.timezone.optimizeSessionWeights({
        currency_pair: selectedCurrency,
        optimization_method: 'performance_based'
      }) as any;
      
      setSessionWeights(data.weights);
      await fetchRecommendations(); // Refresh recommendations
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const data = await api.advanced.timezone.getSessionStatistics() as any;
      setStatistics(data.statistics);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const getSessionIcon = (sessionName: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      'asian': <Sun className="h-4 w-4 text-yellow-500" />,
      'london': <Globe className="h-4 w-4 text-blue-500" />,
      'new_york': <BarChart3 className="h-4 w-4 text-green-500" />,
      'sydney': <Moon className="h-4 w-4 text-purple-500" />
    };
    return iconMap[sessionName] || <Clock className="h-4 w-4" />;
  };

  const getSessionColor = (sessionName: string) => {
    const colorMap: Record<string, string> = {
      'asian': 'bg-yellow-500',
      'london': 'bg-blue-500',
      'new_york': 'bg-green-500',
      'sydney': 'bg-purple-500'
    };
    return colorMap[sessionName] || 'bg-gray-500';
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'high':
        return 'text-red-600';
      case 'medium':
        return 'text-yellow-600';
      default:
        return 'text-green-600';
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'increase_position_size':
        return 'text-green-600';
      case 'reduce_position_size_or_avoid':
        return 'text-red-600';
      default:
        return 'text-blue-600';
    }
  };

  useEffect(() => {
    fetchCurrentSession();
    fetchStatistics();
  }, []);

  useEffect(() => {
    if (selectedCurrency) {
      fetchRecommendations();
    }
  }, [selectedCurrency]);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center space-x-2">
            <Globe className="h-6 w-6" />
            <span>Multi-Timezone Optimization</span>
          </h2>
          <p className="text-gray-600">Session-based trading strategies and timezone optimization</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button onClick={fetchCurrentSession}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <span className="font-semibold text-red-800">Error:</span>
            </div>
            <p className="text-red-700 mt-1">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Current Session Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Clock className="h-5 w-5" />
            <span>Current Trading Sessions</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium mb-3">Active Sessions</h4>
              <div className="flex flex-wrap gap-2">
                {currentSessions.length > 0 ? (
                  currentSessions.map(session => (
                    <Badge key={session} className={getSessionColor(session)}>
                      <div className="flex items-center space-x-1">
                        {getSessionIcon(session)}
                        <span className="capitalize">{session.replace('_', ' ')}</span>
                      </div>
                    </Badge>
                  ))
                ) : (
                  <span className="text-gray-500">No active sessions</span>
                )}
              </div>
            </div>
            <div>
              <h4 className="font-medium mb-3">Session Overlap</h4>
              <div>
                {currentOverlap ? (
                  <Badge className="bg-orange-500">
                    <div className="flex items-center space-x-1">
                      <Activity className="h-3 w-3" />
                      <span className="capitalize">{currentOverlap.replace('_', ' ')}</span>
                    </div>
                  </Badge>
                ) : (
                  <span className="text-gray-500">No overlap</span>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Currency Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Currency Pair Selection</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium">Select Currency:</label>
            <select 
              value={selectedCurrency} 
              onChange={(e) => setSelectedCurrency(e.target.value)}
              className="px-3 py-1 border rounded"
            >
              <option value="EURUSD">EUR/USD</option>
              <option value="GBPUSD">GBP/USD</option>
              <option value="USDJPY">USD/JPY</option>
              <option value="USDCHF">USD/CHF</option>
              <option value="AUDUSD">AUD/USD</option>
              <option value="NZDUSD">NZD/USD</option>
              <option value="USDCAD">USD/CAD</option>
            </select>
            <Button onClick={optimizeWeights} disabled={isLoading}>
              {isLoading ? 'Optimizing...' : 'Optimize Weights'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Session Recommendations */}
      {recommendations && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Target className="h-5 w-5" />
              <span>Session Recommendations - {selectedCurrency}</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Session Weights */}
              <div>
                <h4 className="font-medium mb-3">Optimized Session Weights</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {sessionWeights && Object.entries(sessionWeights).map(([session, weight]) => (
                    <div key={session} className="text-center">
                      <div className="flex items-center justify-center space-x-2 mb-2">
                        {getSessionIcon(session)}
                        <span className="text-sm font-medium capitalize">{session.replace('_', ' ')}</span>
                      </div>
                      <div className="text-2xl font-bold">{(weight * 100).toFixed(1)}%</div>
                      <Progress value={weight * 100} className="h-2 mt-2" />
                    </div>
                  ))}
                </div>
              </div>

              {/* Active Session Recommendations */}
              <div>
                <h4 className="font-medium mb-3">Active Session Recommendations</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {recommendations.recommendations.map((rec: SessionRecommendation, index: number) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          {getSessionIcon(rec.session)}
                          <span className="font-semibold capitalize">{rec.session.replace('_', ' ')}</span>
                        </div>
                        <Badge variant="outline">
                          Weight: {(rec.weight * 100).toFixed(1)}%
                        </Badge>
                      </div>
                      
                      <div className="space-y-3">
                        {/* Action */}
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Recommended Action:</span>
                          <span className={`text-sm font-medium ${getActionColor(rec.action)}`}>
                            {rec.action.replace('_', ' ')}
                          </span>
                        </div>

                        {/* Risk Level */}
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Risk Level:</span>
                          <span className={`text-sm font-medium ${getRiskColor(rec.risk_level)}`}>
                            {rec.risk_level}
                          </span>
                        </div>

                        {/* Characteristics */}
                        <div>
                          <span className="text-sm font-medium">Session Characteristics:</span>
                          <div className="text-sm text-gray-600 mt-1">
                            <div>Liquidity: {rec.characteristics.liquidity}</div>
                            <div>Volatility: {rec.characteristics.volatility_multiplier}x</div>
                            <div>Volume: {rec.characteristics.volume_multiplier}x</div>
                          </div>
                        </div>

                        {/* Optimal Strategies */}
                        <div>
                          <span className="text-sm font-medium">Optimal Strategies:</span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {rec.optimal_strategies.map((strategy: string, idx: number) => (
                              <Badge key={idx} variant="secondary" className="text-xs">
                                {strategy.replace('_', ' ')}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Overlap Recommendation */}
              {recommendations.overlap_recommendation && (
                <div className="border-l-4 border-orange-500 pl-4">
                  <h4 className="font-medium mb-2">Session Overlap Active</h4>
                  <div className="text-sm space-y-1">
                    <div><strong>Overlap:</strong> {recommendations.overlap_recommendation.description}</div>
                    <div><strong>Action:</strong> {recommendations.overlap_recommendation.action.replace('_', ' ')}</div>
                    <div><strong>Volatility Multiplier:</strong> {recommendations.overlap_recommendation.volatility_multiplier}x</div>
                    <div><strong>Volume Multiplier:</strong> {recommendations.overlap_recommendation.volume_multiplier}x</div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Session Statistics */}
      {statistics && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5" />
              <span>Session Statistics</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Session Overview */}
              <div>
                <h4 className="font-medium mb-3">Trading Sessions Overview</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {statistics && statistics.session_overview && Object.entries(statistics.session_overview).map(([session, overview]) => (
                    <div key={session} className="border rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-3">
                        {getSessionIcon(session)}
                        <span className="font-semibold">{overview.name}</span>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div><strong>Timezone:</strong> {overview.timezone}</div>
                        <div><strong>Hours:</strong> {overview.hours}</div>
                        <div><strong>Major Currencies:</strong> {overview.major_currencies.join(', ')}</div>
                        <div><strong>Volatility Multiplier:</strong> {overview.volatility_multiplier}x</div>
                        <div><strong>Volume Multiplier:</strong> {overview.volume_multiplier}x</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Optimization Summary */}
              <div>
                <h4 className="font-medium mb-3">Optimization Summary</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Total Currency Pairs:</span>
                    <div>{statistics.optimization_summary.total_currency_pairs}</div>
                  </div>
                  <div>
                    <span className="font-medium">Total Trades Analyzed:</span>
                    <div>{statistics.optimization_summary.total_trades_analyzed}</div>
                  </div>
                  <div>
                    <span className="font-medium">Active Sessions:</span>
                    <div>{statistics.optimization_summary.active_sessions.join(', ')}</div>
                  </div>
                  <div>
                    <span className="font-medium">Last Optimization:</span>
                    <div>{new Date(statistics.optimization_summary.last_optimization).toLocaleString()}</div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Instructions */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-3">
            <h4 className="font-semibold">Multi-Timezone Instructions:</h4>
            <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
              <li>View current active trading sessions and overlaps</li>
              <li>Select currency pair for session-based optimization</li>
              <li>Click "Optimize Weights" to calculate optimal session weights</li>
              <li>Review session recommendations and optimal strategies</li>
              <li>Monitor session statistics and performance metrics</li>
              <li>Adjust trading strategies based on session characteristics</li>
            </ol>
            <div className="mt-4 p-3 bg-blue-50 rounded">
              <p className="text-sm text-blue-800">
                <strong>Trading Sessions:</strong> Asian (Tokyo), London (European), New York (US), Sydney (Asia-Pacific). Overlaps provide highest liquidity.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
