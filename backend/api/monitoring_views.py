"""
Enhanced API Views for Monitoring and System Health
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime
import json

from monitoring.enhanced_monitoring import get_enhanced_monitoring
from monitoring.performance_tracker import PerformanceTracker


class MonitoringViewSet(viewsets.ViewSet):
    """
    API endpoints for system monitoring and health checks
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.monitoring = get_enhanced_monitoring()
        self.performance_tracker = PerformanceTracker()
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """
        Get overall system health status
        
        GET /api/monitoring/health/
        """
        try:
            health_status = self.monitoring.get_health_status()
            
            return Response({
                'success': True,
                'data': health_status,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
                'status': 'ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """
        Get Prometheus-style metrics
        
        GET /api/monitoring/metrics/
        """
        try:
            prometheus_metrics = self.monitoring.export_prometheus_metrics()
            
            return Response(
                prometheus_metrics,
                content_type='text/plain; version=0.0.4; charset=utf-8'
            )
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def agents(self, request):
        """
        Get detailed agent performance metrics
        
        GET /api/monitoring/agents/
        """
        try:
            agent_names = ['technical', 'macro', 'sentiment', 'geopolitical']
            agent_metrics = {}
            
            for agent_name in agent_names:
                agent_metrics[agent_name] = self.monitoring.get_agent_performance(agent_name)
            
            return Response({
                'success': True,
                'data': agent_metrics,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def system(self, request):
        """
        Get system resource metrics
        
        GET /api/monitoring/system/
        """
        try:
            system_metrics = self.monitoring.collect_system_metrics()
            
            return Response({
                'success': True,
                'data': {
                    'cpu_usage': system_metrics.cpu_usage,
                    'memory_usage': system_metrics.memory_usage,
                    'disk_usage': system_metrics.disk_usage,
                    'active_connections': system_metrics.active_connections,
                    'timestamp': system_metrics.timestamp.isoformat()
                }
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def performance(self, request):
        """
        Get detailed performance analytics
        
        GET /api/monitoring/performance/
        """
        try:
            # Get performance data from tracker
            performance_data = self.performance_tracker.get_performance_summary()
            
            return Response({
                'success': True,
                'data': performance_data,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
