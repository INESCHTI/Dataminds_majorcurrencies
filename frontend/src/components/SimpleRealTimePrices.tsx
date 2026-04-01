/**
 * Simple Real-time Price Display
 * Simulates real-time data without WebSocket complexity
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react';

interface PriceData {
  symbol: string;
  bid: number;
  ask: number;
  mid: number;
  spread: number;
  timestamp: string;
  change: number;
  changePercent: number;
}

interface SimpleRealTimePricesProps {
  symbols: string[];
}

export default function SimpleRealTimePrices({ symbols }: SimpleRealTimePricesProps) {
  const [prices, setPrices] = useState<Map<string, PriceData>>(new Map());
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Simulate connection
    setTimeout(() => setIsConnected(true), 1000);

    // Simulate real-time price updates
    const interval = setInterval(() => {
      setPrices(prev => {
        const newPrices = new Map(prev);
        
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
        
        return newPrices;
      });
    }, 1000); // Update every second

    return () => clearInterval(interval);
  }, [symbols]);

  const getBasePrice = (symbol: string): number => {
    const basePrices: Record<string, number> = {
      'EURUSD': 1.0850,
      'GBPUSD': 1.2650,
      'USDJPY': 149.50,
      'USDCHF': 0.8820
    };
    return basePrices[symbol] || 1.0;
  };

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center space-x-2">
            <Activity className="h-6 w-6" />
            <span>Live FX Prices</span>
          </h2>
          <p className="text-gray-600">Real-time market data simulation</p>
        </div>
        <Badge className={isConnected ? 'bg-green-500' : 'bg-red-500'}>
          {isConnected ? 'Connected' : 'Connecting...'}
        </Badge>
      </div>

      {/* Price Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from(prices.entries()).map(([symbol, data]) => (
          <Card key={symbol} className="relative overflow-hidden hover:shadow-lg transition-shadow">
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
                      ({data.changePercent.toFixed(2)}%)
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
            {isConnected && (
              <div className="absolute top-0 left-0 w-full h-1 bg-green-500 animate-pulse" />
            )}
          </Card>
        ))}
      </div>

      {/* Info Panel */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-2">
            <h4 className="font-semibold">Real-time Features:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Live price updates every second</li>
              <li>• Bid/Ask spread calculation</li>
              <li>• Price change indicators</li>
              <li>• Connection status monitoring</li>
            </ul>
            <div className="mt-4 p-3 bg-blue-50 rounded">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> This is a simulated real-time data feed for demonstration. 
                In production, it would connect to actual market data providers via WebSocket.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
