"""
URL patterns for MCP Agent System API endpoints
"""
from django.urls import path
from . import mcp_views
from . import mcp_test_views

app_name = 'mcp'

urlpatterns = [
    # Test endpoint for debugging
    path('mcp/test/', mcp_test_views.test_endpoint, name='test_endpoint'),
    
    # System control endpoints
    path('mcp/ensure_running/', mcp_views.ensure_mcp_running, name='ensure_mcp_running'),
    
    # MCP Agent Collecteur endpoints
    path('mcp/collecteur/start/', mcp_views.start_collecteur, name='start_collecteur'),
    path('mcp/collecteur/stop/', mcp_views.stop_collecteur, name='stop_collecteur'),
    path('mcp/collecteur/status/', mcp_views.get_collecteur_status, name='get_collecteur_status'),
    path('mcp/collecteur/context/', mcp_views.get_collecteur_context, name='get_collecteur_context'),
    path('mcp/collecteur/tools/', mcp_views.get_collecteur_tools, name='get_collecteur_tools'),
    
    # MCP Agent Feeder endpoints
    path('mcp/feeder/start/', mcp_views.start_feeder, name='start_feeder'),
    path('mcp/feeder/stop/', mcp_views.stop_feeder, name='stop_feeder'),
    path('mcp/feeder/status/', mcp_views.get_feeder_status, name='get_feeder_status'),
    path('mcp/feeder/feeds/', mcp_views.get_feeder_feeds, name='get_feeder_feeds'),
    path('mcp/feeder/agents/', mcp_views.get_feeder_agents, name='get_feeder_agents'),
    
    # Agent-specific endpoints
    path('mcp/agents/<str:agent_name>/data/', mcp_views.get_agent_data, name='get_agent_data'),
    path('mcp/agents/signals/', mcp_views.get_agent_signals, name='get_agent_signals'),
    
    # System overview endpoints
    path('mcp/system/overview/', mcp_views.get_system_overview, name='get_system_overview'),
    path('mcp/system/realtime-stats/', mcp_views.get_realtime_stats, name='get_realtime_stats'),
]
