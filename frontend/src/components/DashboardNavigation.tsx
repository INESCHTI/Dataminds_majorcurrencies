/**
 * Navigation component for dashboard switching
 */
'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Activity, BarChart3, TrendingUp, Zap } from 'lucide-react';

export default function DashboardNavigation() {
  return (
    <Card className="mb-6">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">FX Alpha Platform</h2>
            <p className="text-gray-600">Advanced Multi-Agent Forex Trading System</p>
          </div>
          <div className="flex space-x-4">
            <Link href="/dashboard">
              <Button variant="outline" className="flex items-center space-x-2">
                <BarChart3 className="h-4 w-4" />
                <span>Original Dashboard</span>
              </Button>
            </Link>
            <Link href="/realtime-dashboard">
              <Button className="flex items-center space-x-2">
                <Zap className="h-4 w-4" />
                <span>Real-Time Dashboard</span>
              </Button>
            </Link>
          </div>
        </div>
        
        <div className="mt-4 p-4 bg-green-50 rounded-lg">
          <div className="flex items-start space-x-3">
            <Zap className="h-5 w-5 text-green-600 mt-0.5" />
            <div>
              <h4 className="font-semibold text-green-800">Real Data Integration Active!</h4>
              <p className="text-sm text-green-700">
                The real-time dashboard now connects to the actual PostgreSQL database with 
                18 real signal records from 4 active agents. Generate live signals and track 
                real performance metrics with win rates, Sharpe ratios, and P&L data.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
