"""
Monitoring API URLs - Simple Version
"""
from django.urls import path
from api import monitoring_simple, test_signal, mcp_status

urlpatterns = [
    path('monitoring/health', monitoring_simple.health_check, name='health_check'),
    path('monitoring/system', monitoring_simple.system_metrics, name='system_metrics'),
    path('monitoring/metrics', monitoring_simple.prometheus_metrics, name='prometheus_metrics'),
    path('test/generate_signal', test_signal.test_generate_signal, name='test_generate_signal'),
    path('mcp/status', mcp_status.mcp_status, name='mcp_status'),
    path('mcp/ensure_running', mcp_status.ensure_mcp_running, name='ensure_mcp_running'),
]
