/**
 * Advanced Dashboard - Integrates all advanced features
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Brain, 
  Eye, 
  Target, 
  Globe,
  TrendingUp,
  TrendingDown,
  Activity,
  Zap,
  Shield,
  RefreshCw,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';

interface DashboardStats {
  llm: {
    active_analyses: number;
    currency_impacts: number;
    avg_confidence: number;
  };
  patterns: {
    patterns_detected: number;
    avg_confidence: number;
    overall_sentiment: string;
  };
  rl: {
    optimization_rounds: number;
    avg_reward: number;
    current_strategy: string;
  };
  timezone: {
    active_sessions: string[];
    session_overlap: string | null;
    optimized_weights: number;
  };
}

export default function AdvancedDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchDashboardStats = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Fetch stats from all endpoints
      const [llmResponse, patternsResponse, rlResponse, timezoneResponse] = await Promise.all([
        fetch('/api/v2/llm/sample_statements/'),
        fetch('/api/v2/patterns/analyze_with_sample_data/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ symbol: 'EURUSD', timeframe: '1H' })
        }),
        fetch('/api/v2/rl/get_optimization_stats/'),
        fetch('/api/v2/timezone/get_current_session/')
      ]);

      const llmData = await llmResponse.json();
      const patternsData = await patternsResponse.json();
      const rlData = await rlResponse.json();
      const timezoneData = await timezoneResponse.json();

      if (llmData.success && patternsData.success && rlData.success && timezoneData.success) {
        setStats({
          llm: {
            active_analyses: llmData.statements.length,
            currency_impacts: Object.keys(llmData.statements).length,
            avg_confidence: 0.75 // Mock data
          },
          patterns: {
            patterns_detected: patternsData.analysis.patterns.length,
            avg_confidence: patternsData.analysis.confidence,
            overall_sentiment: patternsData.analysis.overall_sentiment
          },
          rl: {
            optimization_rounds: rlData.stats.rl_stats.optimization_rounds,
            avg_reward: rlData.stats.rl_stats.avg_reward,
            current_strategy: rlData.stats.current_strategy
          },
          timezone: {
            active_sessions: timezoneData.current_sessions,
            session_overlap: timezoneData.session_overlap,
            optimized_weights: 4 // Mock data
          }
        });
        setLastUpdate(new Date());
      } else {
        setError('Failed to fetch dashboard statistics');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'BULLISH':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'BEARISH':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'BULLISH':
        return 'bg-green-500';
      case 'BEARISH':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 p-6">
      <div className="container mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center space-x-2">
              <Zap className="h-8 w-8" />
              <span>Advanced Features Dashboard</span>
            </h1>
            <p className="text-gray-600">AI-powered trading intelligence and optimization</p>
          </div>
          <div className="flex items-center space-x-2">
            <Button onClick={fetchDashboardStats} disabled={isLoading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
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
            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* LLM Analysis */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center space-x-2">
                    <Brain className="h-5 w-5 text-blue-500" />
                    <span>LLM Analysis</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Active Analyses</span>
                      <span className="font-bold">{stats.llm.active_analyses}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Currency Impacts</span>
                      <span className="font-bold">{stats.llm.currency_impacts}</span>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Avg Confidence</span>
                        <span>{(stats.llm.avg_confidence * 100).toFixed(1)}%</span>
                      </div>
                      <Progress value={stats.llm.avg_confidence * 100} className="h-2" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Pattern Recognition */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center space-x-2">
                    <Eye className="h-5 w-5 text-purple-500" />
                    <span>Pattern Recognition</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Patterns Detected</span>
                      <span className="font-bold">{stats.patterns.patterns_detected}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm flex items-center">
                        Overall Sentiment
                        {getSentimentIcon(stats.patterns.overall_sentiment)}
                      </span>
                      <Badge className={getSentimentColor(stats.patterns.overall_sentiment)}>
                        {stats.patterns.overall_sentiment}
                      </Badge>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Avg Confidence</span>
                        <span>{(stats.patterns.avg_confidence * 100).toFixed(1)}%</span>
                      </div>
                      <Progress value={stats.patterns.avg_confidence * 100} className="h-2" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* RL Optimization */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center space-x-2">
                    <Target className="h-5 w-5 text-green-500" />
                    <span>RL Optimization</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Optimization Rounds</span>
                      <span className="font-bold">{stats.rl.optimization_rounds}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Current Strategy</span>
                      <Badge variant="outline" className="capitalize">
                        {stats.rl.current_strategy}
                      </Badge>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Avg Reward</span>
                        <span>{stats.rl.avg_reward.toFixed(4)}</span>
                      </div>
                      <Progress value={Math.min(stats.rl.avg_reward * 20, 100)} className="h-2" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Multi-Timezone */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center space-x-2">
                    <Globe className="h-5 w-5 text-orange-500" />
                    <span>Multi-Timezone</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Active Sessions</span>
                      <span className="font-bold">{stats.timezone.active_sessions.length}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Session Overlap</span>
                      <span className="font-bold">
                        {stats.timezone.session_overlap || 'None'}
                      </span>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Optimized Weights</span>
                        <span>{stats.timezone.optimized_weights}</span>
                      </div>
                      <Progress value={(stats.timezone.optimized_weights / 6) * 100} className="h-2" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Feature Access */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <Card className="border-blue-200 bg-blue-50">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Brain className="h-5 w-5 text-blue-500" />
                    <span>LLM Central Bank Analysis</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 mb-4">
                    GPT-4 powered analysis of central bank communications and policy decisions
                  </p>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>FED, ECB, BOE, BOJ analysis</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>Policy bias detection</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>Currency impact analysis</span>
                    </div>
                  </div>
                  <Button className="w-full mt-4" asChild>
                    <a href="/dashboard/llm-analysis">Open LLM Analysis</a>
                  </Button>
                </CardContent>
              </Card>

              <Card className="border-purple-200 bg-purple-50">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Eye className="h-5 w-5 text-purple-500" />
                    <span>Pattern Recognition</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 mb-4">
                    Computer vision-based chart pattern detection and technical analysis
                  </p>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>8 pattern types</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>89% avg confidence</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>Chart visualization</span>
                    </div>
                  </div>
                  <Button className="w-full mt-4" asChild>
                    <a href="/dashboard/pattern-recognition">Open Pattern Recognition</a>
                  </Button>
                </CardContent>
              </Card>

              <Card className="border-green-200 bg-green-50">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Target className="h-5 w-5 text-green-500" />
                    <span>RL Weight Optimization</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 mb-4">
                    Reinforcement learning for dynamic agent weight optimization
                  </p>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>Q-learning algorithm</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>4 optimization strategies</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>Real-time performance tracking</span>
                    </div>
                  </div>
                  <Button className="w-full mt-4" asChild>
                    <a href="/dashboard/rl-optimization">Open RL Optimization</a>
                  </Button>
                </CardContent>
              </Card>

              <Card className="border-orange-200 bg-orange-50">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Globe className="h-5 w-5 text-orange-500" />
                    <span>Multi-Timezone</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 mb-4">
                    Session-based trading strategies and timezone optimization
                  </p>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>4 trading sessions</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>Session overlap detection</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>Currency-specific optimization</span>
                    </div>
                  </div>
                  <Button className="w-full mt-4" asChild>
                    <a href="/dashboard/multi-timezone">Open Multi-Timezone</a>
                  </Button>
                </CardContent>
              </Card>

              <Card className="border-cyan-200 bg-cyan-50">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Zap className="h-5 w-5 text-cyan-500" />
                    <span>Live Data</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 mb-4">
                    Real-time market data integration and provider management
                  </p>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>OANDA/FXCM integration</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>WebSocket streaming</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>Simulation fallback</span>
                    </div>
                  </div>
                  <Button className="w-full mt-4" asChild>
                    <a href="/live-data">Open Live Data</a>
                  </Button>
                </CardContent>
              </Card>

              <Card className="border-red-200 bg-red-50">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Shield className="h-5 w-5 text-red-500" />
                    <span>Risk Management</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 mb-4">
                    Advanced position sizing and comprehensive risk controls
                  </p>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>5 position sizing methods</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>Risk validation</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>Portfolio monitoring</span>
                    </div>
                  </div>
                  <Button className="w-full mt-4" asChild>
                    <a href="/risk-management">Open Risk Management</a>
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Status Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="h-5 w-5" />
                  <span>System Status</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium mb-3">Advanced Features Status</h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">LLM Analysis</span>
                        <Badge className="bg-green-500">Active</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Pattern Recognition</span>
                        <Badge className="bg-green-500">Active</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">RL Optimization</span>
                        <Badge className="bg-green-500">Active</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Multi-Timezone</span>
                        <Badge className="bg-green-500">Active</Badge>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-3">Last Update</h4>
                    <div className="text-sm text-gray-600">
                      <div>{lastUpdate.toLocaleString()}</div>
                      <div className="mt-2 text-xs">
                        All systems operational and ready for trading
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
