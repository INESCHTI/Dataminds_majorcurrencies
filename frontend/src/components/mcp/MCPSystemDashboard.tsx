"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import { 
  Play, 
  Square, 
  Activity, 
  Database, 
  Network, 
  Settings, 
  BarChart3,
  Zap,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle
} from "lucide-react";

interface MCPCollecteurStatus {
  is_running: boolean;
  session_id: string;
  stats: {
    total_collections: number;
    successful_collections: number;
    failed_collections: number;
    data_points_collected: number;
    start_time: string;
    last_activity: string | null;
  };
  data_sources: Record<string, any>;
}

interface MCPFeederStatus {
  is_running: boolean;
  stats: {
    total_feeds: number;
    successful_feeds: number;
    failed_feeds: number;
    data_points_processed: number;
    agent_updates: Record<string, number>;
  };
  agent_feeds: Record<string, any>;
}

interface AgentSignal {
  signal: number;
  confidence: number;
  reasoning?: string;
  error?: string;
}

export function MCPSystemDashboard() {
  const [collecteurStatus, setCollecteurStatus] = useState<MCPCollecteurStatus | null>(null);
  const [feederStatus, setFeederStatus] = useState<MCPFeederStatus | null>(null);
  const [agentSignals, setAgentSignals] = useState<Record<string, AgentSignal>>({});
  const [systemOverview, setSystemOverview] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data on component mount
  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [collecteurRes, feederRes, signalsRes, overviewRes] = await Promise.all([
        api.mcp.getCollecteurStatus(),
        api.mcp.getFeederStatus(),
        api.mcp.getAgentSignals(),
        api.mcp.getSystemOverview()
      ]);

      if (collecteurRes.success) {
        setCollecteurStatus(collecteurRes.data);
      }
      if (feederRes.success) {
        setFeederStatus(feederRes.data);
      }
      if (signalsRes.success) {
        setAgentSignals(signalsRes.data.signals);
      }
      if (overviewRes.success) {
        setSystemOverview(overviewRes.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch MCP data');
    } finally {
      setLoading(false);
    }
  };

  const startCollecteur = async () => {
    try {
      const response = await api.mcp.startCollecteur();
      if (response.success) {
        setTimeout(fetchAllData, 1000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start collecteur');
    }
  };

  const stopCollecteur = async () => {
    try {
      const response = await api.mcp.stopCollecteur();
      if (response.success) {
        setTimeout(fetchAllData, 1000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop collecteur');
    }
  };

  const startFeeder = async () => {
    try {
      const response = await api.mcp.startFeeder();
      if (response.success) {
        setTimeout(fetchAllData, 1000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start feeder');
    }
  };

  const stopFeeder = async () => {
    try {
      const response = await api.mcp.stopFeeder();
      if (response.success) {
        setTimeout(fetchAllData, 1000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop feeder');
    }
  };

  const getSignalIcon = (signal: number) => {
    switch (signal) {
      case 1: return <CheckCircle className="h-4 w-4 text-green-500" />;
      case -1: return <XCircle className="h-4 w-4 text-red-500" />;
      case 0: return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default: return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getSignalText = (signal: number) => {
    switch (signal) {
      case 1: return 'BUY';
      case -1: return 'SELL';
      case 0: return 'NEUTRAL';
      default: return 'UNKNOWN';
    }
  };

  if (loading && !collecteurStatus && !feederStatus) {
    return (
      <div className="flex items-center justify-center h-64">
        <Activity className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-2">Loading MCP System...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">MCP Agent System</h2>
          <p className="text-gray-600">Model Context Protocol - Real-time Data Collection & Distribution</p>
        </div>
        {error && (
          <Badge variant="destructive" className="ml-4">
            Error: {error}
          </Badge>
        )}
      </div>

      {/* System Overview */}
      {systemOverview && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              System Overview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {systemOverview.system.total_data_points.toLocaleString()}
                </div>
                <div className="text-sm text-gray-600">Total Data Points</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {(systemOverview.system.success_rate * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">Success Rate</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {Math.floor(systemOverview.system.uptime_seconds / 3600)}h
                </div>
                <div className="text-sm text-gray-600">Uptime</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {systemOverview.feeder.active_feeds}
                </div>
                <div className="text-sm text-gray-600">Active Feeds</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* MCP Collecteur */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              MCP Agent Collecteur
              <Badge variant={collecteurStatus?.is_running ? "default" : "secondary"}>
                {collecteurStatus?.is_running ? "Running" : "Stopped"}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              {collecteurStatus?.is_running ? (
                <Button onClick={stopCollecteur} variant="destructive" size="sm">
                  <Square className="h-4 w-4 mr-2" />
                  Stop Collecteur
                </Button>
              ) : (
                <Button onClick={startCollecteur} size="sm">
                  <Play className="h-4 w-4 mr-2" />
                  Start Collecteur
                </Button>
              )}
              <Button onClick={fetchAllData} variant="outline" size="sm">
                <Activity className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>

            {collecteurStatus && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Session ID:</span>
                  <span className="font-mono">{collecteurStatus.session_id}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Total Collections:</span>
                  <span>{collecteurStatus.stats.total_collections}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Success Rate:</span>
                  <span>{((collecteurStatus.stats.successful_collections / Math.max(collecteurStatus.stats.total_collections, 1)) * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Data Points:</span>
                  <span>{collecteurStatus.stats.data_points_collected.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Last Activity:</span>
                  <span>{collecteurStatus.stats.last_activity ? new Date(collecteurStatus.stats.last_activity).toLocaleTimeString() : 'Never'}</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* MCP Feeder */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Network className="h-5 w-5" />
              MCP Agent Feeder
              <Badge variant={feederStatus?.is_running ? "default" : "secondary"}>
                {feederStatus?.is_running ? "Running" : "Stopped"}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              {feederStatus?.is_running ? (
                <Button onClick={stopFeeder} variant="destructive" size="sm">
                  <Square className="h-4 w-4 mr-2" />
                  Stop Feeder
                </Button>
              ) : (
                <Button onClick={startFeeder} size="sm">
                  <Play className="h-4 w-4 mr-2" />
                  Start Feeder
                </Button>
              )}
              <Button onClick={fetchAllData} variant="outline" size="sm">
                <Activity className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>

            {feederStatus && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Total Feeds:</span>
                  <span>{feederStatus.stats.total_feeds}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Success Rate:</span>
                  <span>{((feederStatus.stats.successful_feeds / Math.max(feederStatus.stats.total_feeds, 1)) * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Data Points:</span>
                  <span>{feederStatus.stats.data_points_processed.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Active Feeds:</span>
                  <span>{Object.values(feederStatus.agent_feeds).filter((feed: any) => feed.is_active).length}</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Agent Signals */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Agent Signals
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {Object.entries(agentSignals).map(([agentName, signal]) => (
              <div key={agentName} className="text-center p-4 border rounded-lg">
                <div className="font-semibold capitalize">{agentName}</div>
                <div className="flex items-center justify-center gap-2 mt-2">
                  {getSignalIcon(signal.signal)}
                  <span className={`font-bold ${
                    signal.signal === 1 ? 'text-green-600' : 
                    signal.signal === -1 ? 'text-red-600' : 
                    'text-yellow-600'
                  }`}>
                    {getSignalText(signal.signal)}
                  </span>
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  Confidence: {(signal.confidence * 100).toFixed(1)}%
                </div>
                {signal.error && (
                  <div className="text-xs text-red-500 mt-1">
                    Error: {signal.error}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Detailed Tabs */}
      <Tabs defaultValue="feeds" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="feeds">Data Feeds</TabsTrigger>
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="tools">MCP Tools</TabsTrigger>
          <TabsTrigger value="realtime">Real-time Stats</TabsTrigger>
        </TabsList>

        <TabsContent value="feeds" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Specialized Data Feeds</CardTitle>
            </CardHeader>
            <CardContent>
              {feederStatus?.agent_feeds && (
                <div className="space-y-4">
                  {Object.entries(feederStatus.agent_feeds).map(([agentName, feed]) => (
                    <div key={agentName} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold capitalize">{agentName} Agent</h4>
                        <Badge variant={feed.is_active ? "default" : "secondary"}>
                          {feed.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                        <div>
                          <span className="text-gray-600">Frequency:</span>
                          <span className="ml-2">{feed.update_frequency}s</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Data Types:</span>
                          <span className="ml-2">{feed.data_types.length}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Cache Size:</span>
                          <span className="ml-2">{feed.cache_size}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Last Update:</span>
                          <span className="ml-2">{feed.last_update ? new Date(feed.last_update).toLocaleTimeString() : 'Never'}</span>
                        </div>
                      </div>
                      <div className="mt-2">
                        <div className="text-sm text-gray-600">Data Types:</div>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {feed.data_types.map((type: string) => (
                            <Badge key={type} variant="outline" className="text-xs">
                              {type}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="agents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Connected Agents</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(agentSignals).map(([agentName, signal]) => (
                  <div key={agentName} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold capitalize">{agentName}</h4>
                      {getSignalIcon(signal.signal)}
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Signal:</span>
                        <span className={`font-bold ${
                          signal.signal === 1 ? 'text-green-600' : 
                          signal.signal === -1 ? 'text-red-600' : 
                          'text-yellow-600'
                        }`}>
                          {getSignalText(signal.signal)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Confidence:</span>
                        <span>{(signal.confidence * 100).toFixed(1)}%</span>
                      </div>
                      {signal.reasoning && (
                        <div className="mt-2">
                          <span className="text-gray-600">Reasoning:</span>
                          <p className="text-xs mt-1">{signal.reasoning}</p>
                        </div>
                      )}
                      {signal.error && (
                        <div className="mt-2">
                          <span className="text-red-600">Error:</span>
                          <p className="text-xs mt-1">{signal.error}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tools" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>MCP Tools</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold mb-2">Data Collection Tools</h4>
                  <div className="space-y-1 text-sm">
                    <div>• collect_mt5_data - Real-time price data</div>
                    <div>• collect_rss_news - News articles</div>
                    <div>• collect_fred_data - Economic indicators</div>
                  </div>
                </div>
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold mb-2">Data Storage Tools</h4>
                  <div className="space-y-1 text-sm">
                    <div>• store_influxdb - Time-series storage</div>
                    <div>• store_postgresql - Relational storage</div>
                  </div>
                </div>
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold mb-2">Analysis Tools</h4>
                  <div className="space-y-1 text-sm">
                    <div>• analyze_data_quality - Quality assessment</div>
                    <div>• optimize_collection - Performance tuning</div>
                  </div>
                </div>
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold mb-2">MCP Features</h4>
                  <div className="space-y-1 text-sm">
                    <div>• Model Context Protocol</div>
                    <div>• Tool-based architecture</div>
                    <div>• Real-time processing</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="realtime" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Real-time Statistics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {collecteurStatus && (
                  <div>
                    <h4 className="font-semibold mb-4">Collecteur Stats</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>Total Collections:</span>
                        <span>{collecteurStatus.stats.total_collections}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Successful:</span>
                        <span className="text-green-600">{collecteurStatus.stats.successful_collections}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Failed:</span>
                        <span className="text-red-600">{collecteurStatus.stats.failed_collections}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Data Points:</span>
                        <span>{collecteurStatus.stats.data_points_collected.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                )}
                {feederStatus && (
                  <div>
                    <h4 className="font-semibold mb-4">Feeder Stats</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>Total Feeds:</span>
                        <span>{feederStatus.stats.total_feeds}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Successful:</span>
                        <span className="text-green-600">{feederStatus.stats.successful_feeds}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Failed:</span>
                        <span className="text-red-600">{feederStatus.stats.failed_feeds}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Data Points:</span>
                        <span>{feederStatus.stats.data_points_processed.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
