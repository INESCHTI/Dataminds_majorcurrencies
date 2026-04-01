/**
 * Integration Test Page
 * Tests all components of the FX Alpha Platform
 */
'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  RefreshCw,
  Wifi,
  Database,
  Bot,
  TrendingUp
} from 'lucide-react';
import { api } from '@/lib/api';
import { webSocketService } from '@/lib/websocket-service';

interface TestResult {
  name: string;
  status: 'pending' | 'success' | 'error';
  message: string;
  details?: any;
}

export default function IntegrationTestPage() {
  const [tests, setTests] = useState<TestResult[]>([
    { name: 'Backend API Health Check', status: 'pending', message: 'Testing...' },
    { name: 'Multi-Agent Signal Generation', status: 'pending', message: 'Testing...' },
    { name: 'WebSocket Service Status', status: 'pending', message: 'Testing...' },
    { name: 'Real-time Data API', status: 'pending', message: 'Testing...' },
    { name: 'Database Connection', status: 'pending', message: 'Testing...' },
    { name: 'Agent Performance Tracking', status: 'pending', message: 'Testing...' }
  ]);

  const [isRunning, setIsRunning] = useState(false);

  const runTests = async () => {
    setIsRunning(true);
    const newTests = [...tests];

    // Test 1: Backend API Health Check
    try {
      const health = await api.v2.healthCheck();
      newTests[0] = {
        name: 'Backend API Health Check',
        status: 'success',
        message: 'API is operational',
        details: health
      };
    } catch (error) {
      newTests[0] = {
        name: 'Backend API Health Check',
        status: 'error',
        message: `API Error: ${error}`
      };
    }

    // Test 2: Multi-Agent Signal Generation
    try {
      const signal = await api.v2.generateSignal({ pair: 'EURUSD' });
      newTests[1] = {
        name: 'Multi-Agent Signal Generation',
        status: 'success',
        message: `Signal: ${signal.signal.direction} (${(signal.signal.confidence * 100).toFixed(0)}% confidence)`,
        details: signal
      };
    } catch (error) {
      newTests[1] = {
        name: 'Multi-Agent Signal Generation',
        status: 'error',
        message: `Signal generation failed: ${error}`
      };
    }

    // Test 3: WebSocket Service Status
    try {
      const wsInfo = await webSocketService.getInfo();
      newTests[2] = {
        name: 'WebSocket Service Status',
        status: 'success',
        message: `Active: ${wsInfo.connection_info.active_connections} connections`,
        details: wsInfo
      };
    } catch (error) {
      newTests[2] = {
        name: 'WebSocket Service Status',
        status: 'error',
        message: `WebSocket service error: ${error}`
      };
    }

    // Test 4: Real-time Data API
    try {
      const data = await webSocketService.getData({ symbol: 'EURUSD', type: 'tick', count: 5 });
      newTests[3] = {
        name: 'Real-time Data API',
        status: 'success',
        message: `Retrieved ${data.count} data points`,
        details: data
      };
    } catch (error) {
      newTests[3] = {
        name: 'Real-time Data API',
        status: 'error',
        message: `Real-time data error: ${error}`
      };
    }

    // Test 5: Database Connection (via agent performance)
    try {
      const performance = await api.v2.getAgentPerformance();
      newTests[4] = {
        name: 'Database Connection',
        status: 'success',
        message: 'Database connected and responding',
        details: performance
      };
    } catch (error) {
      newTests[4] = {
        name: 'Database Connection',
        status: 'error',
        message: `Database connection error: ${error}`
      };
    }

    // Test 6: Agent Performance Tracking
    try {
      const health = await api.v2.healthCheck();
      const agentCount = Object.keys(health.agent_performances).length;
      newTests[5] = {
        name: 'Agent Performance Tracking',
        status: 'success',
        message: `${agentCount} agents tracked successfully`,
        details: health.agent_performances
      };
    } catch (error) {
      newTests[5] = {
        name: 'Agent Performance Tracking',
        status: 'error',
        message: `Performance tracking error: ${error}`
      };
    }

    setTests(newTests);
    setIsRunning(false);
  };

  useEffect(() => {
    runTests();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error': return <XCircle className="h-5 w-5 text-red-500" />;
      default: return <RefreshCw className="h-5 w-5 text-gray-500 animate-spin" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      success: 'bg-green-500',
      error: 'bg-red-500',
      pending: 'bg-yellow-500'
    };
    return <Badge className={variants[status as keyof typeof variants]}>{status}</Badge>;
  };

  const successCount = tests.filter(t => t.status === 'success').length;
  const errorCount = tests.filter(t => t.status === 'error').length;
  const pendingCount = tests.filter(t => t.status === 'pending').length;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">FX Alpha Platform - Integration Test</h1>
          <p className="text-gray-600">Comprehensive system integration verification</p>
        </div>
        <Button onClick={runTests} disabled={isRunning} className="flex items-center space-x-2">
          <RefreshCw className={`h-4 w-4 ${isRunning ? 'animate-spin' : ''}`} />
          <span>Run Tests</span>
        </Button>
      </div>

      {/* Summary */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="p-4 bg-green-50 rounded-lg">
              <CheckCircle className="h-8 w-8 text-green-500 mx-auto mb-2" />
              <div className="text-2xl font-bold text-green-600">{successCount}</div>
              <div className="text-sm text-green-700">Passed</div>
            </div>
            <div className="p-4 bg-red-50 rounded-lg">
              <XCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
              <div className="text-2xl font-bold text-red-600">{errorCount}</div>
              <div className="text-sm text-red-700">Failed</div>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg">
              <AlertCircle className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
              <div className="text-2xl font-bold text-yellow-600">{pendingCount}</div>
              <div className="text-sm text-yellow-700">Pending</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Test Results */}
      <div className="space-y-4">
        {tests.map((test, index) => (
          <Card key={index}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(test.status)}
                  <div>
                    <h3 className="font-semibold">{test.name}</h3>
                    <p className="text-sm text-gray-600">{test.message}</p>
                  </div>
                </div>
                {getStatusBadge(test.status)}
              </div>
              
              {test.details && (
                <div className="mt-4 p-3 bg-gray-50 rounded">
                  <details>
                    <summary className="text-sm font-medium cursor-pointer">View Details</summary>
                    <pre className="mt-2 text-xs overflow-auto">
                      {JSON.stringify(test.details, null, 2)}
                    </pre>
                  </details>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* System Architecture Overview */}
      <Card>
        <CardHeader>
          <CardTitle>System Architecture Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 border rounded">
              <Database className="h-8 w-8 text-blue-500 mx-auto mb-2" />
              <h4 className="font-semibold">Backend Services</h4>
              <p className="text-sm text-gray-600">Django API + Multi-Agent System</p>
            </div>
            <div className="text-center p-4 border rounded">
              <Wifi className="h-8 w-8 text-green-500 mx-auto mb-2" />
              <h4 className="font-semibold">Real-time Data</h4>
              <p className="text-sm text-gray-600">WebSocket Streaming + Live Prices</p>
            </div>
            <div className="text-center p-4 border rounded">
              <Bot className="h-8 w-8 text-purple-500 mx-auto mb-2" />
              <h4 className="font-semibold">Multi-Agent AI</h4>
              <p className="text-sm text-gray-600">4 Specialized Trading Agents</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Navigation */}
      <Card>
        <CardContent className="pt-6">
          <div className="text-center space-y-4">
            <h3 className="font-semibold">Navigate to Dashboards</h3>
            <div className="flex justify-center space-x-4">
              <Button variant="outline" onClick={() => window.location.href = '/dashboard'}>
                Original Dashboard
              </Button>
              <Button onClick={() => window.location.href = '/realtime'}>
                Real-time Dashboard
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
