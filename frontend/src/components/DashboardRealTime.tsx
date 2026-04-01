/**
 * Enhanced Dashboard with Real-time Integration
 * Combines multi-agent signals with live market data
 */
'use client';

import DashboardNavigation from '@/components/DashboardNavigation';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Signal, 
  RefreshCw,
  Wifi,
  WifiOff
} from 'lucide-react';
import SimpleRealTimePrices from '@/components/SimpleRealTimePrices';
import { api } from '@/lib/api';

interface AgentSignal {
  technical: { signal: string; confidence: number };
  macro: { signal: string; confidence: number };
  sentiment: { signal: string; confidence: number };
  geopolitical: { signal: string; confidence: number };
}

export default function DashboardRealTime() {
  const [selectedSymbol, setSelectedSymbol] = useState('EURUSD');
  const [agentSignals, setAgentSignals] = useState<AgentSignal | null>(null);
  const [isGeneratingSignal, setIsGeneratingSignal] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [errors, setErrors] = useState<string[]>([]);
  const [ticks, setTicks] = useState<any[]>([]);
  const [signals, setSignals] = useState<any[]>([]);
  const [currentTick, setCurrentTick] = useState<any>(null);
  const [currentCandle, setCurrentCandle] = useState<any>(null);
  const [hasData, setHasData] = useState(false);
  
  const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'];

  // Helper functions
  const getSignalIcon = (signal: string) => {
    return signal === 'BUY' ? TrendingUp : signal === 'SELL' ? TrendingDown : Activity;
  };

  const getSignalColor = (signal: string) => {
    return signal === 'BUY' ? 'text-green-600' : signal === 'SELL' ? 'text-red-600' : 'text-gray-600';
  };

  // Generate multi-agent signal
  const handleGenerateSignal = async () => {
    setIsGeneratingSignal(true);
    setErrors([]);
    try {
      const response = await api.generateSignal(selectedSymbol);
      if (response.success && response.signal) {
        setAgentSignals(response.signal.agent_votes);
      } else {
        setErrors(['Signal generation failed: Invalid response format']);
      }
    } catch (error: any) {
      console.error('Signal generation failed:', error);
      setErrors([error.message || 'Signal generation failed']);
    } finally {
      setIsGeneratingSignal(false);
    }
  };

  const getConnectionIcon = () => {
    return <Wifi className="h-4 w-4" />;
  };

  const formatPrice = (price: number, symbol: string) => {
    if (symbol === 'USDJPY') {
      return price.toFixed(2);
    }
    return price.toFixed(5);
  };

  const formatSpread = (bid: number, ask: number) => {
    return ((ask - bid) * 10000).toFixed(1); // Convert to pips
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      <DashboardNavigation />
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">FX Alpha Platform - Real-time</h1>
          <p className="text-gray-600">Multi-agent trading signals with live market data</p>
        </div>
        <div className="flex items-center space-x-4">
          <Badge className={isConnected ? 'bg-green-500' : 'bg-red-500'}>
            {getConnectionIcon()}
            <span className="ml-2">{connectionStatus}</span>
          </Badge>
          <Button 
            onClick={handleGenerateSignal} 
            disabled={isGeneratingSignal || !isConnected}
            className="flex items-center space-x-2"
          >
            {isGeneratingSignal ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Signal className="h-4 w-4" />
            )}
            <span>Generate Signal</span>
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {errors.length > 0 && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="space-y-2">
              <h4 className="font-semibold text-red-800">Connection Errors:</h4>
              {errors.map((error, index) => (
                <p key={index} className="text-sm text-red-600">{error}</p>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Symbol Selector */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center space-x-4">
            <span className="font-semibold">Select Symbol:</span>
            <div className="flex space-x-2">
              {symbols.map(symbol => (
                <Button
                  key={symbol}
                  variant={selectedSymbol === symbol ? 'default' : 'outline'}
                  onClick={() => setSelectedSymbol(symbol)}
                  className="flex items-center space-x-2"
                >
                  <span>{symbol}</span>
                  {ticks.has(symbol) && (
                    <div className="w-2 h-2 bg-green-500 rounded-full" />
                  )}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Dashboard */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Price Panel */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Live Price - {selectedSymbol}</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {currentTick ? (
              <div className="space-y-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">
                    {formatPrice(currentTick.mid, selectedSymbol)}
                  </div>
                  <div className="text-sm text-gray-500">
                    {new Date(currentTick.timestamp).toLocaleTimeString()}
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-blue-50 rounded">
                    <div className="text-sm text-blue-600 font-medium">Bid</div>
                    <div className="text-lg font-bold text-blue-800">
                      {formatPrice(currentTick.bid, selectedSymbol)}
                    </div>
                  </div>
                  <div className="text-center p-3 bg-red-50 rounded">
                    <div className="text-sm text-red-600 font-medium">Ask</div>
                    <div className="text-lg font-bold text-red-800">
                      {formatPrice(currentTick.ask, selectedSymbol)}
                    </div>
                  </div>
                </div>
                
                <div className="text-center text-sm text-gray-600">
                  Spread: {formatSpread(currentTick.bid, currentTick.ask)} pips
                </div>
                
                {currentCandle && (
                  <div className="text-center text-sm text-gray-600">
                    <div>M1 Candle: O {formatPrice(currentCandle.open, selectedSymbol)} | 
                    H {formatPrice(currentCandle.high, selectedSymbol)} | 
                    L {formatPrice(currentCandle.low, selectedSymbol)} | 
                    C {formatPrice(currentCandle.close, selectedSymbol)}</div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                {isConnected ? 'Waiting for data...' : 'Connect to see live prices'}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Multi-Agent Signals */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Signal className="h-5 w-5" />
              <span>Multi-Agent Analysis - {selectedSymbol}</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {agentSignals ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(agentSignals).map(([agent, data]) => (
                    <div key={agent} className="text-center p-4 border rounded">
                      <div className="flex items-center justify-center mb-2">
                        {getSignalIcon(data.signal)}
                      </div>
                      <div className="font-semibold capitalize">{agent}</div>
                      <div className={`text-sm font-medium px-2 py-1 rounded ${getSignalColor(data.signal)}`}>
                        {data.signal}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {(data.confidence * 100).toFixed(0)}% confidence
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="text-center text-sm text-gray-600">
                  <div>Real-time analysis powered by 4 specialized agents</div>
                  <div>Technical (30%) | Macro (25%) | Sentiment (20%) | Geopolitical (25%)</div>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <Signal className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>Click "Generate Signal" to see multi-agent analysis</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Signals */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Trading Signals</CardTitle>
        </CardHeader>
        <CardContent>
          {signals.length > 0 ? (
            <div className="space-y-3">
              {signals.slice(0, 5).map((signal, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded">
                  <div className="flex items-center space-x-4">
                    {getSignalIcon(signal.direction)}
                    <div>
                      <div className="font-semibold">{signal.symbol}</div>
                      <div className="text-sm text-gray-500">{signal.direction}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">
                      {(signal.confidence * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(signal.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              No recent signals available
            </div>
          )}
        </CardContent>
      </Card>

      {/* System Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Connection Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span>WebSocket:</span>
                <Badge className={isConnected ? 'bg-green-500' : 'bg-red-500'}>
                  {connectionStatus}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Data Streams:</span>
                <Badge className={hasData ? 'bg-green-500' : 'bg-gray-500'}>
                  {ticks.size > 0 ? 'Active' : 'Inactive'}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Market Data</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span>Active Symbols:</span>
                <span className="font-medium">{ticks.size}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Price Updates:</span>
                <span className="font-medium">Real-time</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Multi-Agent System</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span>Active Agents:</span>
                <span className="font-medium">4/4</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Last Signal:</span>
                <span className="font-medium">
                  {signals.length > 0 ? 
                    new Date(signals[0].timestamp).toLocaleTimeString() : 
                    'None'
                  }
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
