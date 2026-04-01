/**
 * API Test Component
 * Tests backend API connectivity
 */
'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, XCircle, RefreshCw } from 'lucide-react';

export default function ApiTest() {
  const [testResult, setTestResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const testApi = async () => {
    setIsLoading(true);
    setError('');
    setTestResult(null);

    try {
      console.log('Testing API call to:', 'http://localhost:8000/api/v2/signals/generate_signal/');
      
      const response = await fetch('http://localhost:8000/api/v2/signals/generate_signal/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pair: 'EURUSD' }),
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log('Success response:', data);
      setTestResult(data);

    } catch (err: any) {
      console.error('API test failed:', err);
      setError(err.message || 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>API Connectivity Test</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <Button onClick={testApi} disabled={isLoading} className="w-full">
            {isLoading ? 'Testing...' : 'Test Signal Generation API'}
          </Button>

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <XCircle className="h-5 w-5 text-red-500" />
                <span className="font-semibold text-red-800">Error:</span>
              </div>
              <pre className="mt-2 text-sm text-red-700 whitespace-pre-wrap">{error}</pre>
            </div>
          )}

          {testResult && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span className="font-semibold text-green-800">Success!</span>
              </div>
              <div className="mt-2 space-y-2">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium">Signal:</span>
                  <Badge className={testResult.signal?.direction === 'BUY' ? 'bg-green-500' : testResult.signal?.direction === 'SELL' ? 'bg-red-500' : 'bg-gray-500'}>
                    {testResult.signal?.direction || 'NEUTRAL'}
                  </Badge>
                </div>
                <div className="text-sm">
                  <span className="font-medium">Confidence:</span> {((testResult.signal?.confidence || 0) * 100).toFixed(1)}%
                </div>
                <div className="text-sm">
                  <span className="font-medium">Agent Votes:</span>
                  <pre className="mt-1 text-xs bg-gray-100 p-2 rounded">
                    {JSON.stringify(testResult.signal?.agent_votes, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}

          <div className="text-xs text-gray-500">
            <p>Testing endpoint: http://localhost:8000/api/v2/signals/generate_signal/</p>
            <p>Method: POST | Body: {"{ \"pair\": \"EURUSD\" }"}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
