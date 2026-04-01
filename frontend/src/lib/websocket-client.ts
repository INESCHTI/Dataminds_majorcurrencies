/**
 * WebSocket Client for Real-time FX Data
 * Handles connection management and data streaming
 */
'use client';

import { useState, useEffect } from 'react';

export interface TickData {
  symbol: string;
  timestamp: string;
  bid: number;
  ask: number;
  mid: number;
  spread: number;
  volume: number;
}

export interface OHLCVData {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timeframe: string;
}

export interface SignalData {
  symbol: string;
  direction: 'BUY' | 'SELL' | 'NEUTRAL';
  confidence: number;
  reasoning: string;
  timestamp: string;
}

export type WebSocketMessage = 
  | { type: 'tick'; } & TickData
  | { type: 'ohlcv'; } & OHLCVData
  | { type: 'signal_generated'; } & SignalData
  | { type: 'connection'; status: string; }
  | { type: 'error'; message: string }
  | { type: 'pong'; timestamp: string }
  | { type: 'status'; statistics: any; connections: any };

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;
  private subscribers = new Map<string, Set<(data: any) => void>>();
  private pingInterval: NodeJS.Timeout | null = null;

  constructor(baseUrl: string = 'ws://localhost:8000') {
    this.url = baseUrl;
  }

  /**
   * Connect to WebSocket server
   */
  async connect(endpoint: string = '/ws/data/'): Promise<void> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.isConnecting = true;

    try {
      // For demo purposes, simulate connection instead of actual WebSocket
      // In production, this would be: const wsUrl = `${this.url}${endpoint}`;
      console.log('Simulating WebSocket connection to:', endpoint);
      
      // Simulate successful connection after delay
      setTimeout(() => {
        this.isConnecting = false;
        this.emit('connection', { type: 'connection', status: 'connected' });
        this.startPingInterval();
      }, 500);
      
      return;
      
      // Actual WebSocket connection (commented out for demo)
      /*
      const wsUrl = `${this.url}${endpoint}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.startPingInterval();
        this.emit('connection', { type: 'connection', status: 'connected' });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.isConnecting = false;
        this.stopPingInterval();
        this.emit('connection', { type: 'connection', status: 'disconnected' });
        
        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', { type: 'error', message: 'WebSocket connection error' });
      };
      */

    } catch (error) {
      this.isConnecting = false;
      console.error('Failed to connect WebSocket:', error);
      throw error;
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.stopPingInterval();
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  /**
   * Subscribe to real-time data for a symbol
   */
  subscribe(symbol: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        symbol: symbol
      }));
    }
  }

  /**
   * Unsubscribe from real-time data for a symbol
   */
  unsubscribe(symbol: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe',
        symbol: symbol
      }));
    }
  }

  /**
   * Subscribe to real-time signals
   */
  subscribeToSignals(symbols: string[]): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe_signals',
        symbols: symbols
      }));
    }
  }

  /**
   * Generate a trading signal
   */
  generateSignal(symbol: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'generate_signal',
        symbol: symbol
      }));
    }
  }

  /**
   * Get system status
   */
  getStatus(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'get_status'
      }));
    }
  }

  /**
   * Get data quality for symbols
   */
  getDataQuality(symbols: string[]): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'get_quality',
        symbols: symbols
      }));
    }
  }

  /**
   * Add event listener
   */
  on(event: string, callback: (data: any) => void): void {
    if (!this.subscribers.has(event)) {
      this.subscribers.set(event, new Set());
    }
    this.subscribers.get(event)!.add(callback);
  }

  /**
   * Remove event listener
   */
  off(event: string, callback: (data: any) => void): void {
    const callbacks = this.subscribers.get(event);
    if (callbacks) {
      callbacks.delete(callback);
    }
  }

  /**
   * Get connection status
   */
  get connectionStatus(): string {
    if (!this.ws) return 'disconnected';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting';
      case WebSocket.OPEN: return 'connected';
      case WebSocket.CLOSING: return 'closing';
      case WebSocket.CLOSED: return 'disconnected';
      default: return 'unknown';
    }
  }

  private handleMessage(data: WebSocketMessage): void {
    // Emit to specific subscribers
    this.emit(data.type, data);
    
    // Also emit to general message subscribers
    this.emit('message', data);
  }

  private emit(event: string, data: any): void {
    const callbacks = this.subscribers.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in WebSocket callback for ${event}:`, error);
        }
      });
    }
  }

  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // Ping every 30 seconds
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      this.connect().catch(error => {
        console.error('Reconnect failed:', error);
      });
    }, delay);
  }
}

// Create singleton instance
export const wsClient = new WebSocketClient();

// React hook for WebSocket
export function useWebSocket() {
  const [connectionStatus, setConnectionStatus] = useState<string>('disconnected');
  const [latestData, setLatestData] = useState<Map<string, TickData>>(new Map());
  const [latestCandles, setLatestCandles] = useState<Map<string, Map<string, OHLCVData>>>(new Map());
  const [signals, setSignals] = useState<SignalData[]>([]);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    // Connection status handler
    const handleConnection = (data: { type: 'connection'; status: string }) => {
      setConnectionStatus(data.status);
    };

    // Tick data handler
    const handleTick = (data: TickData) => {
      setLatestData(prev => {
        const newMap = new Map(prev);
        newMap.set(data.symbol, data);
        return newMap;
      });
    };

    // OHLCV data handler
    const handleOHLCV = (data: OHLCVData) => {
      setLatestCandles(prev => {
        const newMap = new Map(prev);
        if (!newMap.has(data.symbol)) {
          newMap.set(data.symbol, new Map());
        }
        newMap.get(data.symbol)!.set(data.timeframe, data);
        return newMap;
      });
    };

    // Signal handler
    const handleSignal = (data: SignalData) => {
      setSignals(prev => [data, ...prev.slice(0, 9)]); // Keep last 10 signals
    };

    // Error handler
    const handleError = (data: { type: 'error'; message: string }) => {
      setErrors(prev => [data.message, ...prev.slice(0, 4)]); // Keep last 5 errors
    };

    // Register event listeners
    wsClient.on('connection', handleConnection);
    wsClient.on('tick', handleTick);
    wsClient.on('ohlcv', handleOHLCV);
    wsClient.on('signal_generated', handleSignal);
    wsClient.on('error', handleError);

    // Connect on mount
    wsClient.connect().catch(console.error);

    // Cleanup on unmount
    return () => {
      wsClient.off('connection', handleConnection);
      wsClient.off('tick', handleTick);
      wsClient.off('ohlcv', handleOHLCV);
      wsClient.off('signal_generated', handleSignal);
      wsClient.off('error', handleError);
      wsClient.disconnect();
    };
  }, []);

  return {
    connectionStatus,
    latestData,
    latestCandles,
    signals,
    errors,
    subscribe: wsClient.subscribe.bind(wsClient),
    unsubscribe: wsClient.unsubscribe.bind(wsClient),
    subscribeToSignals: wsClient.subscribeToSignals.bind(wsClient),
    generateSignal: wsClient.generateSignal.bind(wsClient),
    getStatus: wsClient.getStatus.bind(wsClient),
    getDataQuality: wsClient.getDataQuality.bind(wsClient)
  };
}
