"use client";

import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { 
  Play, 
  Square, 
  RefreshCw, 
  Database, 
  Network, 
  CheckCircle, 
  XCircle,
  AlertTriangle,
  Power,
  Settings
} from "lucide-react";

interface SystemStatus {
  collecteur_running: boolean;
  feeder_running: boolean;
  collecteur_stats: any;
  feeder_stats: any;
}

export function MCPControlPanel() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    collecteur_running: false,
    feeder_running: false,
    collecteur_stats: null,
    feeder_stats: null
  });
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    checkSystemStatus();
    if (autoRefresh) {
      const interval = setInterval(checkSystemStatus, 3000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const checkSystemStatus = async () => {
    try {
      const [collecteurRes, feederRes] = await Promise.all([
        api.mcp.getCollecteurStatus(),
        api.mcp.getFeederStatus()
      ]);

      setSystemStatus({
        collecteur_running: (collecteurRes as any).data.is_running,
        feeder_running: (feederRes as any).data.is_running,
        collecteur_stats: (collecteurRes as any).data.stats,
        feeder_stats: (feederRes as any).data.stats
      });
    } catch (error) {
      console.error('Failed to check system status:', error);
    }
  };

  const startCollecteur = async () => {
    setLoading(true);
    try {
      await api.mcp.startCollecteur();
      setTimeout(checkSystemStatus, 1000);
    } catch (error) {
      console.error('Failed to start collecteur:', error);
    } finally {
      setLoading(false);
    }
  };

  const stopCollecteur = async () => {
    setLoading(true);
    try {
      await api.mcp.stopCollecteur();
      setTimeout(checkSystemStatus, 1000);
    } catch (error) {
      console.error('Failed to stop collecteur:', error);
    } finally {
      setLoading(false);
    }
  };

  const startFeeder = async () => {
    setLoading(true);
    try {
      await api.mcp.startFeeder();
      setTimeout(checkSystemStatus, 1000);
    } catch (error) {
      console.error('Failed to start feeder:', error);
    } finally {
      setLoading(false);
    }
  };

  const stopFeeder = async () => {
    setLoading(true);
    try {
      await api.mcp.stopFeeder();
      setTimeout(checkSystemStatus, 1000);
    } catch (error) {
      console.error('Failed to stop feeder:', error);
    } finally {
      setLoading(false);
    }
  };

  const startAll = async () => {
    setLoading(true);
    try {
      await Promise.all([
        api.mcp.startCollecteur(),
        api.mcp.startFeeder()
      ]);
      setTimeout(checkSystemStatus, 2000);
    } catch (error) {
      console.error('Failed to start all:', error);
    } finally {
      setLoading(false);
    }
  };

  const stopAll = async () => {
    setLoading(true);
    try {
      await Promise.all([
        api.mcp.stopCollecteur(),
        api.mcp.stopFeeder()
      ]);
      setTimeout(checkSystemStatus, 2000);
    } catch (error) {
      console.error('Failed to stop all:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (running: boolean) => {
    return running ? (
      <CheckCircle className="h-4 w-4 text-green-500" />
    ) : (
      <XCircle className="h-4 w-4 text-red-500" />
    );
  };

  const getStatusBadge = (running: boolean) => {
    return running ? (
      <Badge className="bg-green-100 text-green-800">Running</Badge>
    ) : (
      <Badge variant="secondary">Stopped</Badge>
    );
  };

  return (
    <div className="space-y-6">
      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            MCP System Control
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Auto Refresh Toggle */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <RefreshCw className={`h-4 w-4 ${autoRefresh ? 'animate-spin' : ''}`} />
              <span className="text-sm font-medium">Auto Refresh</span>
            </div>
            <Button
              variant={autoRefresh ? "default" : "outline"}
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              {autoRefresh ? "On" : "Off"}
            </Button>
          </div>

          {/* System Controls */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4" />
                  <span className="font-medium">Collecteur</span>
                  {getStatusIcon(systemStatus.collecteur_running)}
                </div>
                {getStatusBadge(systemStatus.collecteur_running)}
              </div>
              <div className="flex gap-2">
                {systemStatus.collecteur_running ? (
                  <Button 
                    onClick={stopCollecteur} 
                    variant="destructive" 
                    size="sm"
                    disabled={loading}
                  >
                    <Square className="h-4 w-4 mr-2" />
                    Stop
                  </Button>
                ) : (
                  <Button 
                    onClick={startCollecteur} 
                    size="sm"
                    disabled={loading}
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Start
                  </Button>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Network className="h-4 w-4" />
                  <span className="font-medium">Feeder</span>
                  {getStatusIcon(systemStatus.feeder_running)}
                </div>
                {getStatusBadge(systemStatus.feeder_running)}
              </div>
              <div className="flex gap-2">
                {systemStatus.feeder_running ? (
                  <Button 
                    onClick={stopFeeder} 
                    variant="destructive" 
                    size="sm"
                    disabled={loading}
                  >
                    <Square className="h-4 w-4 mr-2" />
                    Stop
                  </Button>
                ) : (
                  <Button 
                    onClick={startFeeder} 
                    size="sm"
                    disabled={loading}
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Start
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Master Controls */}
          <div className="pt-4 border-t">
            <div className="flex items-center justify-between mb-3">
              <span className="font-medium">Master Controls</span>
              <Power className="h-4 w-4" />
            </div>
            <div className="flex gap-2">
              <Button 
                onClick={startAll} 
                variant="default"
                disabled={loading || (systemStatus.collecteur_running && systemStatus.feeder_running)}
              >
                <Play className="h-4 w-4 mr-2" />
                Start All
              </Button>
              <Button 
                onClick={stopAll} 
                variant="destructive"
                disabled={loading || (!systemStatus.collecteur_running && !systemStatus.feeder_running)}
              >
                <Square className="h-4 w-4 mr-2" />
                Stop All
              </Button>
              <Button 
                onClick={checkSystemStatus} 
                variant="outline"
                disabled={loading}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh Status
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Status Summary */}
      <Card>
        <CardHeader>
          <CardTitle>System Status Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Collecteur Status */}
            <div className="space-y-3">
              <h4 className="font-semibold flex items-center gap-2">
                <Database className="h-4 w-4" />
                Collecteur Status
              </h4>
              {systemStatus.collecteur_stats ? (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Total Collections:</span>
                    <span>{systemStatus.collecteur_stats.total_collections}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Success Rate:</span>
                    <span className="text-green-600">
                      {systemStatus.collecteur_stats.total_collections > 0 
                        ? ((systemStatus.collecteur_stats.successful_collections / systemStatus.collecteur_stats.total_collections) * 100).toFixed(1)
                        : 0}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Data Points:</span>
                    <span>{systemStatus.collecteur_stats.data_points_collected.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Last Activity:</span>
                    <span>
                      {systemStatus.collecteur_stats.last_activity 
                        ? new Date(systemStatus.collecteur_stats.last_activity).toLocaleTimeString()
                        : 'Never'}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-gray-500">No data available</div>
              )}
            </div>

            {/* Feeder Status */}
            <div className="space-y-3">
              <h4 className="font-semibold flex items-center gap-2">
                <Network className="h-4 w-4" />
                Feeder Status
              </h4>
              {systemStatus.feeder_stats ? (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Total Feeds:</span>
                    <span>{systemStatus.feeder_stats.total_feeds}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Success Rate:</span>
                    <span className="text-green-600">
                      {systemStatus.feeder_stats.total_feeds > 0 
                        ? ((systemStatus.feeder_stats.successful_feeds / systemStatus.feeder_stats.total_feeds) * 100).toFixed(1)
                        : 0}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Data Points:</span>
                    <span>{systemStatus.feeder_stats.data_points_processed.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Agent Updates:</span>
                    <span>
                      {Object.values(systemStatus.feeder_stats.agent_updates || {}).reduce((sum: number, count: any) => sum + (count as number || 0), 0)}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-gray-500">No data available</div>
              )}
            </div>
          </div>

          {/* System Health */}
          <div className="pt-4 border-t">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold">System Health</h4>
              <div className="flex items-center gap-2">
                {systemStatus.collecteur_running && systemStatus.feeder_running ? (
                  <>
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span className="text-green-600">All Systems Operational</span>
                  </>
                ) : systemStatus.collecteur_running || systemStatus.feeder_running ? (
                  <>
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    <span className="text-yellow-600">Partial Operation</span>
                  </>
                ) : (
                  <>
                    <XCircle className="h-4 w-4 text-red-500" />
                    <span className="text-red-600">All Systems Stopped</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
