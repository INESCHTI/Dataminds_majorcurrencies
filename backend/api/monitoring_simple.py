"""
Simple Monitoring API Views
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
import json

from monitoring.enhanced_monitoring import get_enhanced_monitoring


@api_view(['GET'])
def health_check(request):
    """
    Simple health check endpoint
    
    GET /api/monitoring/health
    """
    try:
        monitoring = get_enhanced_monitoring()
        health_status = monitoring.get_health_status()
        
        # Convert dataclass to dict for JSON serialization
        health_dict = {
            'status': health_status['status'],
            'health_score': health_status['health_score'],
            'uptime': health_status['uptime'],
            'agent_count': health_status['agent_count'],
            'total_signals': health_status['total_signals']
        }
        
        return Response({
            'success': True,
            'data': health_dict,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'status': 'ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def system_metrics(request):
    """
    Get system resource metrics
    
    GET /api/monitoring/system
    """
    try:
        monitoring = get_enhanced_monitoring()
        system_metrics = monitoring.collect_system_metrics()
        
        # Convert dataclass to dict for JSON serialization
        metrics_dict = {
            'cpu_usage': system_metrics.cpu_usage,
            'memory_usage': system_metrics.memory_usage,
            'disk_usage': system_metrics.disk_usage,
            'active_connections': system_metrics.active_connections,
            'timestamp': system_metrics.timestamp
        }
        
        return Response({
            'success': True,
            'data': metrics_dict
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def prometheus_metrics(request):
    """
    Get Prometheus-style metrics
    
    GET /api/monitoring/metrics
    """
    try:
        monitoring = get_enhanced_monitoring()
        prometheus_metrics = monitoring.export_prometheus_metrics()
        
        return Response(
            prometheus_metrics,
            content_type='text/plain; version=0.0.4; charset=utf-8'
        )
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
