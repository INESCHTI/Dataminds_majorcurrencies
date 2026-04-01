/**
 * WebSocket Service API
 * Manages the backend WebSocket service
 */
import { api } from './api';

export interface WebSocketServiceStatus {
  status: 'active' | 'inactive' | 'error';
  endpoints: {
    ticks: string;
    ohlcv: string;
    symbols: string;
  };
  available_symbols: string[];
  connection_info: {
    active_connections: number;
    total_subscribers: number;
  };
}

export interface WebSocketDataParams {
  symbol?: string;
  type?: 'tick' | 'ohlcv';
  count?: number;
  timeframe?: string;
}

class WebSocketService {
  /**
   * Get WebSocket service information
   */
  async getInfo(): Promise<WebSocketServiceStatus> {
    const response = await fetch('/api/websocket/info/');
    if (!response.ok) {
      throw new Error('Failed to get WebSocket service info');
    }
    return response.json();
  }

  /**
   * Start the WebSocket service
   */
  async start(symbols: string[] = ['EURUSD', 'GBPUSD', 'USDJPY']): Promise<any> {
    const response = await fetch('/api/websocket/start/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        symbols,
        providers: { forexcom: {} }
      })
    });

    if (!response.ok) {
      throw new Error('Failed to start WebSocket service');
    }
    
    return response.json();
  }

  /**
   * Stop the WebSocket service
   */
  async stop(): Promise<any> {
    const response = await fetch('/api/websocket/stop/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      throw new Error('Failed to stop WebSocket service');
    }
    
    return response.json();
  }

  /**
   * Get real-time data
   */
  async getData(params: WebSocketDataParams = {}): Promise<any> {
    const queryParams = new URLSearchParams();
    
    if (params.symbol) queryParams.append('symbol', params.symbol);
    if (params.type) queryParams.append('type', params.type);
    if (params.count) queryParams.append('count', params.count.toString());
    if (params.timeframe) queryParams.append('timeframe', params.timeframe);

    const response = await fetch(`/api/websocket/data/?${queryParams}`);
    if (!response.ok) {
      throw new Error('Failed to get real-time data');
    }
    
    return response.json();
  }

  /**
   * Get data quality metrics
   */
  async getQuality(symbol?: string): Promise<any> {
    const url = symbol ? `/api/websocket/quality/?symbol=${symbol}` : '/api/websocket/quality/';
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error('Failed to get data quality');
    }
    
    return response.json();
  }

  /**
   * Get latest prices
   */
  async getLatestPrices(symbols?: string[]): Promise<any> {
    const queryParams = symbols ? `?symbols=${symbols.join(',')}` : '';
    
    const response = await fetch(`/api/websocket/prices/${queryParams}`);
    if (!response.ok) {
      throw new Error('Failed to get latest prices');
    }
    
    return response.json();
  }
}

export const webSocketService = new WebSocketService();
