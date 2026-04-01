/**
 * Real-time Data Hook for FX Alpha Platform
 * Integrates WebSocket streaming with React components
 */
'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { wsClient, TickData, OHLCVData, SignalData } from '@/lib/websocket-client';

interface UseRealTimeDataOptions {
  symbols: string[];
  enableSignals?: boolean;
  updateInterval?: number;
}

interface RealTimeState {
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error';
  ticks: Map<string, TickData>;
  candles: Map<string, Map<string, OHLCVData>>;
  signals: SignalData[];
  errors: string[];
  lastUpdate: Date | null;
  statistics: any;
}

export function useRealTimeData(options: UseRealTimeDataOptions) {
  const { symbols, enableSignals = true, updateInterval = 1000 } = options;
  
  const [state, setState] = useState<RealTimeState>({
    connectionStatus: 'disconnected',
    ticks: new Map(),
    candles: new Map(),
    signals: [],
    errors: [],
    lastUpdate: null,
    statistics: null
  });

  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 1000;

  // Handle connection status changes
  const handleConnection = useCallback((data: { type: 'connection'; status: string }) => {
    setState(prev => ({
      ...prev,
      connectionStatus: data.status as any,
      errors: data.status === 'connected' ? [] : prev.errors
    }));
    
    if (data.status === 'connected') {
      reconnectAttempts.current = 0;
      // Subscribe to symbols after connection
      symbols.forEach(symbol => {
        wsClient.subscribe(symbol);
      });
      
      if (enableSignals) {
        wsClient.subscribeToSignals(symbols);
      }
    }
  }, []); // Remove symbols dependency to prevent infinite loop

  // Handle incoming tick data
  const handleTick = useCallback((tick: TickData) => {
    setState(prev => {
      const newTicks = new Map(prev.ticks);
      newTicks.set(tick.symbol, tick);
      
      return {
        ...prev,
        ticks: newTicks,
        lastUpdate: new Date()
      };
    });
  }, []);

  // Handle incoming OHLCV data
  const handleOHLCV = useCallback((candle: OHLCVData) => {
    setState(prev => {
      const newCandles = new Map(prev.candles);
      if (!newCandles.has(candle.symbol)) {
        newCandles.set(candle.symbol, new Map());
      }
      newCandles.get(candle.symbol)!.set(candle.timeframe, candle);
      
      return {
        ...prev,
        candles: newCandles,
        lastUpdate: new Date()
      };
    });
  }, []);

  // Handle signal data
  const handleSignal = useCallback((signal: SignalData) => {
    setState(prev => ({
      ...prev,
      signals: [signal, ...prev.signals.slice(0, 9)], // Keep last 10 signals
      lastUpdate: new Date()
    }));
  }, []);

  // Handle errors
  const handleError = useCallback((data: { type: 'error'; message: string }) => {
    setState(prev => ({
      ...prev,
      errors: [data.message, ...prev.errors.slice(0, 4)] // Keep last 5 errors
    }));
  }, []);

  // Handle statistics updates
  const handleStatus = useCallback((data: { type: 'status'; statistics: any; connections: any }) => {
    setState(prev => ({
      ...prev,
      statistics: data.statistics
    }));
  }, []);

  // Initialize WebSocket connection
  useEffect(() => {
    const connect = async () => {
      try {
        setState(prev => ({ ...prev, connectionStatus: 'connecting' }));
        
        // For now, simulate WebSocket connection since Django Channels needs additional setup
        // In production, this would connect to actual WebSocket
        console.log('Simulating WebSocket connection for demo...');
        
        setTimeout(() => {
          setState(prev => ({ 
            ...prev, 
            connectionStatus: 'connected',
            errors: []
          }));
          
          // Start simulated data updates
          startSimulatedData();
        }, 1000);
        
      } catch (error) {
        console.error('WebSocket connection failed:', error);
        setState(prev => ({ 
          ...prev, 
          connectionStatus: 'error',
          errors: [`Connection failed: ${error}`]
        }));
      }
    };

    const startSimulatedData = () => {
      // Simulate real-time data updates
      const interval = setInterval(() => {
        symbols.forEach(symbol => {
          const simulatedTick: TickData = {
            symbol,
            timestamp: new Date().toISOString(),
            bid: Math.random() * 0.01 + 1.08,
            ask: Math.random() * 0.01 + 1.09,
            mid: Math.random() * 0.01 + 1.085,
            spread: Math.random() * 0.001,
            volume: Math.floor(Math.random() * 1000000) + 100000
          };
          
          setState(prev => {
            const newTicks = new Map(prev.ticks);
            newTicks.set(symbol, simulatedTick);
            
            return {
              ...prev,
              ticks: newTicks,
              lastUpdate: new Date()
            };
          });
        });
      }, 1000);
      
      // Store interval ID for cleanup
      (window as any).simulationInterval = interval;
    };

    connect();

    // Cleanup
    return () => {
      if ((window as any).simulationInterval) {
        clearInterval((window as any).simulationInterval);
      }
    };
  }, [symbols]);

  // Manual reconnection function
  const reconnect = useCallback(() => {
    reconnectAttempts.current = 0;
    wsClient.connect('/ws/data/').catch(console.error);
  }, []);

  // Subscribe to additional symbols
  const subscribe = useCallback((symbol: string) => {
    wsClient.subscribe(symbol);
  }, []);

  // Unsubscribe from symbols
  const unsubscribe = useCallback((symbol: string) => {
    wsClient.unsubscribe(symbol);
  }, []);

  // Generate trading signal
  const generateSignal = useCallback((symbol: string) => {
    wsClient.generateSignal(symbol);
  }, []);

  // Get data quality
  const getDataQuality = useCallback((symbols: string[]) => {
    wsClient.getDataQuality(symbols);
  }, []);

  return {
    // State
    ...state,
    
    // Computed values
    isConnected: state.connectionStatus === 'connected',
    hasData: state.ticks.size > 0,
    signalCount: state.signals.length,
    
    // Actions
    reconnect,
    subscribe,
    unsubscribe,
    generateSignal,
    getDataQuality,
    
    // Helper functions
    getTick: (symbol: string) => state.ticks.get(symbol),
    getCandles: (symbol: string, timeframe: string) => {
      const symbolCandles = state.candles.get(symbol);
      return symbolCandles?.get(timeframe);
    },
    getLatestSignals: (count: number = 5) => state.signals.slice(0, count),
  };
}
