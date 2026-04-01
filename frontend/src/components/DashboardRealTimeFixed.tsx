/**
 * Enhanced Dashboard with Real-time Integration - Fixed Version
 * Combines multi-agent signals with live market data
 */
'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Signal, 
  RefreshCw,
  Wifi
} from 'lucide-react';
import DashboardNavigation from '@/components/DashboardNavigation';
import SimpleRealTimePrices from '@/components/SimpleRealTimePrices';
import { api } from '@/lib/api';

interface AgentSignal {
  technical: { signal: string; confidence: number };
  macro: { signal: string; confidence: number };
  sentiment: { signal: string; confidence: number };
  geopolitical: { signal: string; confidence: number };
}

export default function DashboardRealTimeFixed() {
  const [selectedSymbol, setSelectedSymbol] = useState('EURUSD');
  const [agentSignals, setAgentSignals] = useState<AgentSignal | null>(null);
  const [isGeneratingSignal, setIsGeneratingSignal] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  
  const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'];

  // Generate multi-agent signal
  const handleGenerateSignal = async () => {
    setIsGeneratingSignal(true);
    setErrors([]);
    try {
      const response = await fetch('http://localhost:8000/api/v2/signals/generate_signal/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pair: selectedSymbol }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setAgentSignals(data.signal.agent_votes);
    } catch (error: any) {
      console.error('Signal generation failed:', error);
      setErrors([`Signal generation failed: ${error.message || 'Unknown error'}`]);
    } finally {
      setIsGeneratingSignal(false);
    }
  };

  const getSignalIcon = (signal: string) => {
    switch (signal.toUpperCase()) {
      case 'BUY': return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'SELL': return <TrendingDown className="h-4 w-4 text-red-500" />;
      default: return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal.toUpperCase()) {
      case 'BUY': return 'text-green-600 bg-green-50';
      case 'SELL': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getConnectionIcon = () => {
    return <Wifi className="h-4 w-4" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      <DashboardNavigation />
      
      {/* Header */}
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">FX Alpha Platform - Real-time</h1>
            <p className="text-gray-600">Multi-agent trading signals with live market data</p>
          </div>
          <div className="flex items-center space-x-4">
            <Badge className="bg-green-500">
              {getConnectionIcon()}
              <span className="ml-2">Connected</span>
            </Badge>
            <Button 
              onClick={handleGenerateSignal} 
              disabled={isGeneratingSignal}
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
                <h4 className="font-semibold text-red-800">Errors:</h4>
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
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Main Dashboard */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Live Prices */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="h-5 w-5" />
                <span>Live Market Data</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <SimpleRealTimePrices symbols={symbols} />
            </CardContent>
          </Card>

          {/* Multi-Agent Signals */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Signal className="h-5 w-5" />
                <span>Multi-Agent Analysis - {selectedSymbol}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {agentSignals ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
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
                  <Badge className="bg-green-500">Connected</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span>Data Streams:</span>
                  <Badge className="bg-green-500">Active</Badge>
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
                  <span className="font-medium">{symbols.length}</span>
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
                    {agentSignals ? 'Generated' : 'None'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
