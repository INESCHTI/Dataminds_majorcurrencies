/**
 * Real-time Price Display Component
 * Shows live FX prices with WebSocket integration
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface PriceData {
  symbol: string;
  bid: number;
  ask: number;
  mid: number;
  spread: number;
  timestamp: string;
  change?: number;
  changePercent?: number;
}

export default function RealTimePrices() {
  const [prices, setPrices] = useState<Map<string, PriceData>>(new Map());
  const [connectionStatus, setConnectionStatus] = useState<string>('disconnected');
  const [errors, setErrors] = useState<string[]>([]);

  // Simulated WebSocket connection for demo
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    const connectWebSocket = () => {
      setConnectionStatus('connecting');
      
      // Simulate connection
      setTimeout(() => {
        setConnectionStatus('connected');
        setErrors([]);
        
        // Start price updates
        interval = setInterval(() => {
          updatePrices();
        }, 1000); // Update every second
      }, 1000);
    };
    
    const updatePrices = () => {
      const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'];
      const newPrices = new Map(prices);
      
      symbols.forEach(symbol => {
        const currentPrice = newPrices.get(symbol);
        const basePrice = getBasePrice(symbol);
        const variation = (Math.random() - 0.5) * 0.001; // ±0.1% variation
        const newMid = basePrice * (1 + variation);
        const spread = basePrice * 0.0001; // 1 pip spread
        
        const newPriceData: PriceData = {
          symbol,
          bid: newMid - spread / 2,
          ask: newMid + spread / 2,
          mid: newMid,
          spread,
          timestamp: new Date().toISOString(),
          change: currentPrice ? newMid - currentPrice.mid : 0,
          changePercent: currentPrice ? ((newMid - currentPrice.mid) / currentPrice.mid) * 100 : 0
        };
        
        newPrices.set(symbol, newPriceData);
      });
      
      setPrices(newPrices);
    };
    
    const getBasePrice = (symbol: string): number => {
      const basePrices: Record<string, number> = {
        'EURUSD': 1.0850,
        'GBPUSD': 1.2650,
        'USDJPY': 149.50,
        'USDCHF': 0.8820
      };
      return basePrices[symbol] || 1.0;
    };
    
    connectWebSocket();
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [prices]);

  const getPriceIcon = (change: number = 0) => {
    if (change > 0) return <TrendingUp className="h-4 w-4 text-green-500" />;
    if (change < 0) return <TrendingDown className="h-4 w-4 text-red-500" />;
    return <Minus className="h-4 w-4 text-gray-500" />;
  };

  const getPriceColor = (change: number = 0) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const formatPrice = (price: number, symbol: string) => {
    if (symbol === 'USDJPY') {
      return price.toFixed(2);
    }
    return price.toFixed(5);
  };

  const formatSpread = (spread: number) => {
    return (spread * 10000).toFixed(1); // Convert to pips
  };

  const getConnectionBadge = () => {
    const colors = {
      connected: 'bg-green-500',
      connecting: 'bg-yellow-500',
      disconnected: 'bg-red-500'
    };
    
    return (
      <Badge className={colors[connectionStatus as keyof typeof colors] || 'bg-gray-500'}>
        {connectionStatus}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Real-time FX Prices</h2>
          <p className="text-gray-600">Live market data with WebSocket streaming</p>
        </div>
        {getConnectionBadge()}
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

      {/* Price Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from(prices.entries()).map(([symbol, data]) => (
          <Card key={symbol} className="relative overflow-hidden">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg font-semibold">{symbol}</CardTitle>
                {getPriceIcon(data.change)}
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {/* Mid Price */}
                <div className="text-center">
                  <div className={`text-2xl font-bold ${getPriceColor(data.change)}`}>
                    {formatPrice(data.mid, symbol)}
                  </div>
                  {data.change !== 0 && (
                    <div className={`text-sm ${getPriceColor(data.change)}`}>
                      {data.change > 0 ? '+' : ''}{formatPrice(data.change, symbol)} 
                      ({data.changePercent?.toFixed(2)}%)
                    </div>
                  )}
                </div>
                
                {/* Bid/Ask */}
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="text-center p-2 bg-blue-50 rounded">
                    <div className="text-blue-600 font-medium">Bid</div>
                    <div className="text-blue-800">{formatPrice(data.bid, symbol)}</div>
                  </div>
                  <div className="text-center p-2 bg-red-50 rounded">
                    <div className="text-red-600 font-medium">Ask</div>
                    <div className="text-red-800">{formatPrice(data.ask, symbol)}</div>
                  </div>
                </div>
                
                {/* Spread */}
                <div className="text-center text-sm text-gray-600">
                  Spread: {formatSpread(data.spread)} pips
                </div>
                
                {/* Timestamp */}
                <div className="text-center text-xs text-gray-500">
                  {new Date(data.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </CardContent>
            
            {/* Animated border effect for live data */}
            {connectionStatus === 'connected' && (
              <div className="absolute top-0 left-0 w-full h-1 bg-green-500 animate-pulse" />
            )}
          </Card>
        ))}
      </div>

      {/* Instructions */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-2">
            <h4 className="font-semibold">Real-time Features:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Live price updates every second</li>
              <li>• Bid/Ask spread calculation</li>
              <li>• Price change indicators</li>
              <li>• Connection status monitoring</li>
              <li>• Error handling and reconnection</li>
            </ul>
            <div className="mt-4 p-3 bg-blue-50 rounded">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> This is a simulated WebSocket connection for demonstration. 
                In production, it would connect to the actual WebSocket service running at 
                ws://localhost:8000/ws/data/
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
