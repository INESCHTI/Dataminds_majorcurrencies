"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { 
  Activity, 
  Clock, 
  TrendingUp, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Play,
  Square,
  RefreshCw
} from 'lucide-react';

interface MT5Stats {
  connection_time: string | null;
  ticks_received: number;
  errors_count: number;
  last_tick_time: string | null;
  symbols_active: string[];
  uptime_seconds: number | null;
  is_connected: boolean;
  is_streaming: boolean;
  symbols_configured: number;
  connection_info: {
    server: string;
    login: string;
  };
}

interface MT5Health {
  status: string;
  issues: string[];
  timestamp: string;
}

export function MT5Monitor() {
  const [stats, setStats] = useState<MT5Stats | null>(null);
  const [health, setHealth] = useState<MT5Health | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const response = await api.tactical.mt5Status();
      setStats(response.stats as MT5Stats);
      setHealth(response.health as MT5Health);
    } catch (err) {
      console.error('Erreur récupération statut MT5:', err);
    } finally {
      setLoading(false);
    }
  };

  const startService = async () => {
    try {
      await api.tactical.startMt5Service();
      setTimeout(fetchStatus, 2000); // Attendre 2s avant de vérifier
    } catch (err) {
      console.error('Erreur démarrage MT5:', err);
    }
  };

  const stopService = async () => {
    try {
      await api.tactical.stopMt5Service();
      setTimeout(fetchStatus, 2000); // Attendre 2s avant de vérifier
    } catch (err) {
      console.error('Erreur arrêt MT5:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); // Actualiser toutes les 10s
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800';
      case 'unhealthy':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'degraded':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'unhealthy':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const formatUptime = (seconds: number | null) => {
    if (!seconds) return 'N/A';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    return `${hours}h ${minutes}m ${secs}s`;
  };

  const formatTime = (timeStr: string | null) => {
    if (!timeStr) return 'N/A';
    return new Date(timeStr).toLocaleTimeString();
  };

  return (
    <div className="space-y-6">
      {/* En-tête avec contrôles */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Monitoring MT5 - Connexion Temps Réel
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm"
                onClick={fetchStatus}
                disabled={loading}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                Actualiser
              </Button>
              {stats?.is_connected ? (
                <Button 
                  variant="destructive" 
                  size="sm"
                  onClick={stopService}
                >
                  <Square className="mr-2 h-4 w-4" />
                  Arrêter
                </Button>
              ) : (
                <Button 
                  variant="default" 
                  size="sm"
                  onClick={startService}
                >
                  <Play className="mr-2 h-4 w-4" />
                  Démarrer
                </Button>
              )}
            </div>
          </CardTitle>
        </CardHeader>
      </Card>

      {/* Statut de santé */}
      {health && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {getStatusIcon(health.status)}
              État de Santé: {health.status.toUpperCase()}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`p-4 rounded-lg ${getStatusColor(health.status)}`}>
              <div className="text-lg font-semibold mb-2">
                {health.status === 'healthy' && '✅ Système MT5 opérationnel'}
                {health.status === 'degraded' && '⚠️ Système MT5 dégradé'}
                {health.status === 'unhealthy' && '❌ Système MT5 hors service'}
              </div>
              
              {health.issues && health.issues.length > 0 && (
                <div className="space-y-1">
                  <h4 className="font-medium">Issues détectées:</h4>
                  {health.issues.map((issue, index) => (
                    <div key={index} className="text-sm">
                      • {issue}
                    </div>
                  ))}
                </div>
              )}
              
              <div className="text-sm text-gray-600 mt-2">
                Dernière vérification: {new Date(health.timestamp).toLocaleString()}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Statistiques de connexion */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Connexion</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span>Statut:</span>
                  <Badge className={stats.is_connected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                    {stats.is_connected ? 'Connecté' : 'Déconnecté'}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span>Streaming:</span>
                  <Badge className={stats.is_streaming ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}>
                    {stats.is_streaming ? 'Actif' : 'Inactif'}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span>Serveur:</span>
                  <span className="text-sm font-mono">{stats.connection_info.server}</span>
                </div>
                <div className="flex justify-between">
                  <span>Login:</span>
                  <span className="text-sm font-mono">{stats.connection_info.login}</span>
                </div>
                {stats.connection_time && (
                  <div className="flex justify-between">
                    <span>Connecté depuis:</span>
                    <span className="text-sm">
                      {formatTime(stats.connection_time)}
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span>Uptime:</span>
                  <span className="font-medium">
                    {formatUptime(stats.uptime_seconds)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Ticks reçus:</span>
                  <span className="font-medium">
                    {stats.ticks_received.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Erreurs:</span>
                  <span className={`font-medium ${stats.errors_count > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {stats.errors_count}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Dernier tick:</span>
                  <span className="text-sm">
                    {formatTime(stats.last_tick_time)}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Symboles</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span>Symboles actifs:</span>
                  <Badge className="bg-blue-100 text-blue-800">
                    {stats.symbols_active.length}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span>Symboles configurés:</span>
                  <Badge className="bg-green-100 text-green-800">
                    {stats.symbols_configured}
                  </Badge>
                </div>
                
                {stats.symbols_active.length > 0 && (
                  <div className="mt-3">
                    <h4 className="text-sm font-medium mb-2">Symboles surveillés:</h4>
                    <div className="grid grid-cols-2 gap-2">
                      {stats.symbols_active.map((symbol, index) => (
                        <Badge key={index} variant="outline" className="justify-center">
                          {symbol}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Graphique de performance en temps réel */}
      {stats && stats.is_connected && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Performance en Temps Réel
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
              <div className="p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {stats.ticks_received.toLocaleString()}
                </div>
                <div className="text-sm text-green-700">Ticks Total</div>
              </div>
              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {stats.errors_count === 0 ? '0' : stats.errors_count}
                </div>
                <div className="text-sm text-blue-700">Erreurs</div>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {stats.uptime_seconds ? Math.round(stats.ticks_received / (stats.uptime_seconds / 60)) : 0}
                </div>
                <div className="text-sm text-purple-700">Ticks/Min</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
