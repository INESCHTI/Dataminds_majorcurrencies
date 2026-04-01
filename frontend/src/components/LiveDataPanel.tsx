/**
 * Live Data Panel Component
 * Displays real-time data provider status and controls
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Activity, 
  Wifi, 
  WifiOff, 
  Play, 
  Square, 
  RefreshCw,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';

interface ProviderStatus {
  enabled: boolean;
  active: boolean;
  status: string;
}

interface LiveDataStats {
  total_ticks: number;
  total_errors: number;
  provider_status: Record<string, string>;
  last_update: string | null;
  is_running: boolean;
  uptime_seconds: number;
}

interface LiveDataPanelProps {
  symbols: string[];
}

export default function LiveDataPanel({ symbols }: LiveDataPanelProps) {
  const [providerStatus, setProviderStatus] = useState<Record<string, ProviderStatus>>({});
  const [statistics, setStatistics] = useState<LiveDataStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const fetchData = async () => {
    try {
      const response = await fetch('/api/v2/live-data/provider_status/');
        const data = await response.json();
        
        if (data.success) {
          setProviderStatus(data.providers);
          setStatistics(data.statistics);
          setIsConnected(data.statistics.is_running);
        } else {
          setError(data.error);
        }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const startLiveData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v2/live-data/start_live_data/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbols }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setIsConnected(true);
        await fetchData(); // Refresh status
      } else {
        setError(data.error);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const stopLiveData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v2/live-data/stop_live_data/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      const data = await response.json();
      
      if (data.success) {
        setIsConnected(false);
        await fetchData(); // Refresh status
      } else {
        setError(data.error);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const getProviderIcon = (provider: string, status: ProviderStatus) => {
    if (!status.enabled) return <WifiOff className="h-4 w-4 text-gray-400" />;
    if (status.active && status.status === 'connected') {
      return <Wifi className="h-4 w-4 text-green-500" />;
    }
    return <WifiOff className="h-4 w-4 text-red-500" />;
  };

  const getProviderBadge = (status: ProviderStatus) => {
    if (!status.enabled) return <Badge variant="secondary">Disabled</Badge>;
    if (status.active && status.status === 'connected') {
      return <Badge className="bg-green-500">Connected</Badge>;
    }
    if (status.status.includes('error')) {
      return <Badge variant="destructive">Error</Badge>;
    }
    return <Badge variant="outline">Disconnected</Badge>;
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center space-x-2">
            <Activity className="h-6 w-6" />
            <span>Live Data Management</span>
          </h2>
          <p className="text-gray-600">Real-time market data provider status</p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge className={isConnected ? 'bg-green-500' : 'bg-red-500'}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </Badge>
          <Button
            onClick={isConnected ? stopLiveData : startLiveData}
            disabled={isLoading}
            className="flex items-center space-x-2"
          >
            {isLoading ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : isConnected ? (
              <Square className="h-4 w-4" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            <span>{isConnected ? 'Stop' : 'Start'} Live Data</span>
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

      {/* Provider Status */}
      <Card>
        <CardHeader>
          <CardTitle>Data Provider Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(providerStatus).map(([provider, status]) => (
              <div key={provider} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {getProviderIcon(provider, status)}
                    <span className="font-medium capitalize">{provider}</span>
                  </div>
                  {getProviderBadge(status)}
                </div>
                <div className="text-sm text-gray-600">
                  <div>Status: {status.status}</div>
                  <div>Enabled: {status.enabled ? 'Yes' : 'No'}</div>
                  <div>Active: {status.active ? 'Yes' : 'No'}</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Statistics */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <TrendingUp className="h-5 w-5 text-blue-500" />
                <span className="font-medium">Total Ticks</span>
              </div>
              <div className="text-2xl font-bold mt-2">{statistics.total_ticks.toLocaleString()}</div>
              <div className="text-sm text-gray-600">Since start</div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                <span className="font-medium">Total Errors</span>
              </div>
              <div className="text-2xl font-bold mt-2">{statistics.total_errors}</div>
              <div className="text-sm text-gray-600">Connection issues</div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span className="font-medium">Uptime</span>
              </div>
              <div className="text-2xl font-bold mt-2">
                {formatUptime(statistics.uptime_seconds)}
              </div>
              <div className="text-sm text-gray-600">Running time</div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <Activity className="h-5 w-5 text-purple-500" />
                <span className="font-medium">Active Providers</span>
              </div>
              <div className="text-2xl font-bold mt-2">
                {Object.values(providerStatus).filter(p => p.active).length}
              </div>
              <div className="text-sm text-gray-600">Connected providers</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Symbols Being Tracked */}
      <Card>
        <CardHeader>
          <CardTitle>Active Symbols</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {symbols.map(symbol => (
              <Badge key={symbol} variant="outline" className="px-3 py-1">
                {symbol}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Instructions */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-3">
            <h4 className="font-semibold">Live Data Setup Instructions:</h4>
            <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
              <li>Configure your OANDA API credentials in <code className="bg-gray-100 px-1">backend/.env.live</code></li>
              <li>Set <code className="bg-gray-100 px-1">OANDA_API_KEY</code> and <code className="bg-gray-100 px-1">OANDA_ACCOUNT_ID</code></li>
              <li>Choose environment: <code className="bg-gray-100 px-1">practice</code> for demo or <code className="bg-gray-100 px-1">live</code> for production</li>
              <li>Click "Start Live Data" to begin streaming real-time prices</li>
              <li>The system will automatically fallback to simulation if no providers are available</li>
            </ol>
            <div className="mt-4 p-3 bg-blue-50 rounded">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> For demo purposes, the system will use simulated data if no API credentials are configured.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
