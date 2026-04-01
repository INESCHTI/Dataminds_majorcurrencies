/**
 * RL Weight Optimization Panel Component
 * Displays reinforcement learning agent weight optimization
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Brain, 
  TrendingUp, 
  TrendingDown, 
  Settings,
  RefreshCw,
  BarChart3,
  Target,
  Zap,
  AlertTriangle,
  CheckCircle,
  Activity
} from 'lucide-react';
import { api } from '@/lib/api';

interface AgentPerformance {
  agent_name: string;
  success_rate: number;
  avg_confidence: number;
  current_weight: number;
  volatility: number;
}

interface OptimizationStats {
  current_strategy: string;
  strategy_performance: Record<string, {
    avg_performance: number;
    recent_performance: number;
    sample_size: number;
  }>;
  rl_stats: {
    optimization_rounds: number;
    avg_reward: number;
    best_reward: number;
    current_weights: Record<string, number>;
    performance_trend: string;
    agent_performances: Record<string, AgentPerformance>;
  };
  available_strategies: string[];
}

interface RLOptimizationPanelProps {
  className?: string;
}

export default function RLOptimizationPanel({ className }: RLOptimizationPanelProps) {
  const [stats, setStats] = useState<OptimizationStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState('rl');
  const [portfolioMetrics, setPortfolioMetrics] = useState({
    portfolio_return: 0.0,
    sharpe_ratio: 0.0,
    max_drawdown: 0.0,
    win_rate: 0.0
  });

  const fetchStats = async () => {
    try {
      const data = await api.advanced.rl.getOptimizationStats() as any;
      setStats(data);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const updateAgentPerformance = async (agentName: string, performance: number, confidence: number) => {
    try {
      const data = await api.advanced.rl.optimizeWeights({
        agent_name: agentName,
        performance: performance,
        confidence: confidence
      }) as any;
      
      if (!data.success) {
        setError(data.error);
      } else {
        await fetchStats(); // Refresh stats
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const optimizeWeights = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await api.advanced.rl.optimizeWeights({
        optimization_rounds: 10,
        learning_rate: 0.01
      }) as any;
      
      if (!data.success) {
        setError(data.error);
      } else {
        await fetchStats(); // Refresh stats
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const resetOptimization = async () => {
    try {
      const data = await api.advanced.rl.optimizeWeights({}) as any;
      
      if (!data.success) {
        setError(data.error);
      } else {
        await fetchStats(); // Refresh stats
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'declining':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'improving':
        return 'text-green-600';
      case 'declining':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getPerformanceColor = (performance: number) => {
    if (performance > 0.05) return 'text-green-600';
    if (performance < -0.05) return 'text-red-600';
    return 'text-gray-600';
  };

  const getWeightColor = (weight: number) => {
    if (weight > 0.3) return 'text-blue-600';
    if (weight < 0.2) return 'text-orange-600';
    return 'text-gray-600';
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center space-x-2">
            <Brain className="h-6 w-6" />
            <span>RL Weight Optimization</span>
          </h2>
          <p className="text-gray-600">Reinforcement learning agent weight optimization</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button onClick={resetOptimization} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Reset
          </Button>
          <Button onClick={fetchStats}>
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

      {stats && (
        <>
          {/* Optimization Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center space-x-2">
                  <Settings className="h-5 w-5 text-blue-500" />
                  <span className="font-medium">Current Strategy</span>
                </div>
                <div className="text-2xl font-bold mt-2 capitalize">{stats.current_strategy}</div>
                <div className="text-sm text-gray-600">Optimization method</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center space-x-2">
                  <Target className="h-5 w-5 text-green-500" />
                  <span className="font-medium">Optimization Rounds</span>
                </div>
                <div className="text-2xl font-bold mt-2">{stats.rl_stats.optimization_rounds}</div>
                <div className="text-sm text-gray-600">Total iterations</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center space-x-2">
                  <Zap className="h-5 w-5 text-yellow-500" />
                  <span className="font-medium">Average Reward</span>
                </div>
                <div className="text-2xl font-bold mt-2">{stats.rl_stats.avg_reward.toFixed(4)}</div>
                <div className="text-sm text-gray-600">RL reward score</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center space-x-2">
                  <TrendingUp className="h-5 w-5 text-purple-500" />
                  <span className="font-medium">Performance Trend</span>
                </div>
                <div className="flex items-center space-x-2 mt-2">
                  {getTrendIcon(stats.rl_stats.performance_trend)}
                  <span className={`text-lg font-bold capitalize ${getTrendColor(stats.rl_stats.performance_trend)}`}>
                    {stats.rl_stats.performance_trend}
                  </span>
                </div>
                <div className="text-sm text-gray-600">Recent performance</div>
              </CardContent>
            </Card>
          </div>

          {/* Strategy Performance */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5" />
                <span>Strategy Performance</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(stats.strategy_performance).map(([strategy, perf]) => (
                  <div key={strategy} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold capitalize">{strategy}</span>
                      {strategy === stats.current_strategy && (
                        <Badge className="bg-blue-500">Active</Badge>
                      )}
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Avg Performance</span>
                        <span className={getPerformanceColor(perf.avg_performance)}>
                          {perf.avg_performance.toFixed(4)}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Recent Performance</span>
                        <span className={getPerformanceColor(perf.recent_performance)}>
                          {perf.recent_performance.toFixed(4)}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Sample Size</span>
                        <span>{perf.sample_size}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Agent Performance */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Brain className="h-5 w-5" />
                <span>Agent Performance & Weights</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(stats.rl_stats.agent_performances).map(([agent, perf]) => (
                  <div key={agent} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-semibold capitalize">{agent}</span>
                      <div className="flex items-center space-x-1">
                        <Target className="h-4 w-4" />
                        <span className={`text-sm font-bold ${getWeightColor(perf.current_weight)}`}>
                          {(perf.current_weight * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      {/* Weight Progress */}
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Weight</span>
                          <span>{(perf.current_weight * 100).toFixed(1)}%</span>
                        </div>
                        <Progress value={perf.current_weight * 100} className="h-2" />
                      </div>

                      {/* Success Rate */}
                      <div className="flex justify-between text-sm">
                        <span>Success Rate</span>
                        <span className={getPerformanceColor(perf.success_rate - 0.5)}>
                          {(perf.success_rate * 100).toFixed(1)}%
                        </span>
                      </div>

                      {/* Avg Confidence */}
                      <div className="flex justify-between text-sm">
                        <span>Avg Confidence</span>
                        <span>{perf.avg_confidence.toFixed(2)}</span>
                      </div>

                      {/* Volatility */}
                      <div className="flex justify-between text-sm">
                        <span>Volatility</span>
                        <span>{perf.volatility.toFixed(3)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Optimization Controls */}
          <Card>
            <CardHeader>
              <CardTitle>Optimization Controls</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Strategy Selection */}
                <div>
                  <label className="text-sm font-medium mb-2 block">Optimization Strategy</label>
                  <div className="flex space-x-2">
                    {stats.available_strategies.map(strategy => (
                      <Button
                        key={strategy}
                        variant={selectedStrategy === strategy ? 'default' : 'outline'}
                        onClick={() => setSelectedStrategy(strategy)}
                        className="capitalize"
                      >
                        {strategy.replace('_', ' ')}
                      </Button>
                    ))}
                  </div>
                </div>

                {/* Portfolio Metrics Input */}
                <div>
                  <label className="text-sm font-medium mb-2 block">Portfolio Metrics (for optimization)</label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <label className="text-xs text-gray-600">Portfolio Return</label>
                      <input
                        type="number"
                        step="0.001"
                        value={portfolioMetrics.portfolio_return}
                        onChange={(e) => setPortfolioMetrics(prev => ({ ...prev, portfolio_return: parseFloat(e.target.value) || 0 }))}
                        className="w-full px-2 py-1 border rounded text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-600">Sharpe Ratio</label>
                      <input
                        type="number"
                        step="0.1"
                        value={portfolioMetrics.sharpe_ratio}
                        onChange={(e) => setPortfolioMetrics(prev => ({ ...prev, sharpe_ratio: parseFloat(e.target.value) || 0 }))}
                        className="w-full px-2 py-1 border rounded text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-600">Max Drawdown</label>
                      <input
                        type="number"
                        step="0.001"
                        value={portfolioMetrics.max_drawdown}
                        onChange={(e) => setPortfolioMetrics(prev => ({ ...prev, max_drawdown: parseFloat(e.target.value) || 0 }))}
                        className="w-full px-2 py-1 border rounded text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-600">Win Rate</label>
                      <input
                        type="number"
                        step="0.01"
                        value={portfolioMetrics.win_rate}
                        onChange={(e) => setPortfolioMetrics(prev => ({ ...prev, win_rate: parseFloat(e.target.value) || 0 }))}
                        className="w-full px-2 py-1 border rounded text-sm"
                      />
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex space-x-2">
                  <Button onClick={optimizeWeights} disabled={isLoading}>
                    {isLoading ? (
                      <>
                        <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                        Optimizing...
                      </>
                    ) : (
                      'Optimize Weights'
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Current Weights Display */}
          <Card>
            <CardHeader>
              <CardTitle>Current Agent Weights</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(stats.rl_stats.current_weights).map(([agent, weight]) => (
                  <div key={agent} className="flex items-center space-x-4">
                    <div className="w-24">
                      <span className="text-sm font-medium capitalize">{agent}</span>
                    </div>
                    <div className="flex-1">
                      <Progress value={weight * 100} className="h-2" />
                    </div>
                    <div className="w-16 text-right">
                      <span className={`text-sm font-bold ${getWeightColor(weight)}`}>
                        {(weight * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Instructions */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-3">
            <h4 className="font-semibold">RL Optimization Instructions:</h4>
            <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
              <li>View current optimization statistics and agent performances</li>
              <li>Select optimization strategy (RL, Performance-based, Volatility-adjusted, Momentum-based)</li>
              <li>Input current portfolio metrics for optimization</li>
              <li>Click "Optimize Weights" to run RL optimization</li>
              <li>Monitor agent weight adjustments and performance trends</li>
              <li>Reset optimization if needed to start fresh</li>
            </ol>
            <div className="mt-4 p-3 bg-blue-50 rounded">
              <p className="text-sm text-blue-800">
                <strong>Strategies:</strong> RL uses Q-learning, Performance-based uses recent returns, Volatility-adjusted uses risk metrics, Momentum-based uses performance trends.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
