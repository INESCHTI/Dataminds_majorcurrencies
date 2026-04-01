"""
API Views for MCP Agent System Integration
Provides REST endpoints for frontend to control and monitor MCP system
"""
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
import traceback

from mcp_agent_collecteur import get_mcp_agent_collecteur
from mcp_agent_feeder import get_mcp_agent_feeder


@csrf_exempt
@require_http_methods(["POST"])
def start_collecteur(request):
    """Start MCP Agent Collecteur"""
    try:
        collecteur = get_mcp_agent_collecteur()
        collecteur.start_collection()
        
        return JsonResponse({
            'success': True,
            'message': 'MCP Agent Collecteur started successfully',
            'session_id': collecteur.session_id,
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def stop_collecteur(request):
    """Stop MCP Agent Collecteur"""
    try:
        collecteur = get_mcp_agent_collecteur()
        collecteur.stop_collection()
        
        return JsonResponse({
            'success': True,
            'message': 'MCP Agent Collecteur stopped successfully',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
def get_collecteur_status(request):
    """Get MCP Agent Collecteur status"""
    try:
        collecteur = get_mcp_agent_collecteur()
        stats = collecteur.get_statistics()
        
        return JsonResponse({
            'success': True,
            'data': {
                'is_running': collecteur.is_running,
                'session_id': collecteur.session_id,
                'stats': stats,
                'data_sources': collecteur.data_sources,
                'timestamp': timezone.now().isoformat()
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
def get_collecteur_context(request):
    """Get MCP Agent Collecteur context"""
    try:
        collecteur = get_mcp_agent_collecteur()
        context = collecteur.get_mcp_context()
        
        return JsonResponse({
            'success': True,
            'data': context,
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
def get_collecteur_tools(request):
    """Get MCP Agent Collecteur tools"""
    try:
        collecteur = get_mcp_agent_collecteur()
        tools = []
        
        for tool in collecteur.tools:
            tools.append({
                'name': tool.name,
                'description': tool.description,
                'parameters': tool.parameters
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'tools': tools,
                'count': len(tools),
                'timestamp': timezone.now().isoformat()
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def start_feeder(request):
    """Start MCP Agent Feeder"""
    try:
        feeder = get_mcp_agent_feeder()
        feeder.start_feeding()
        
        return JsonResponse({
            'success': True,
            'message': 'MCP Agent Feeder started successfully',
            'connected_agents': list(feeder.agents.keys()),
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def stop_feeder(request):
    """Stop MCP Agent Feeder"""
    try:
        feeder = get_mcp_agent_feeder()
        feeder.stop_feeding()
        
        return JsonResponse({
            'success': True,
            'message': 'MCP Agent Feeder stopped successfully',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
def get_feeder_status(request):
    """Get MCP Agent Feeder status"""
    try:
        feeder = get_mcp_agent_feeder()
        stats = feeder.get_feeding_statistics()
        
        return JsonResponse({
            'success': True,
            'data': {
                'is_running': feeder.is_running,
                'stats': stats,
                'agent_feeds': stats.get('agent_feeds', {}),
                'timestamp': timezone.now().isoformat()
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
def get_feeder_feeds(request):
    """Get detailed feed configurations"""
    try:
        feeder = get_mcp_agent_feeder()
        feeds = {}
        
        for agent_name, feed in feeder.agent_feeds.items():
            feeds[agent_name] = {
                'agent_name': feed.agent_name,
                'data_types': feed.data_types,
                'update_frequency': feed.update_frequency,
                'filters': feed.filters,
                'is_active': feed.is_active,
                'last_update': feed.last_update.isoformat() if feed.last_update else None,
                'cache_size': len(feed.data_cache)
            }
        
        return JsonResponse({
            'success': True,
            'data': {
                'feeds': feeds,
                'count': len(feeds),
                'timestamp': timezone.now().isoformat()
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
def get_feeder_agents(request):
    """Get connected agents information"""
    try:
        feeder = get_mcp_agent_feeder()
        agents = {}
        
        for agent_name, agent in feeder.agents.items():
            agents[agent_name] = {
                'name': agent_name,
                'class': agent.__class__.__name__,
                'feed_active': feeder.agent_feeds[agent_name].is_active,
                'last_update': feeder.agent_feeds[agent_name].last_update.isoformat() if feeder.agent_feeds[agent_name].last_update else None,
                'update_frequency': feeder.agent_feeds[agent_name].update_frequency,
                'data_types': feeder.agent_feeds[agent_name].data_types
            }
        
        return JsonResponse({
            'success': True,
            'data': {
                'agents': agents,
                'count': len(agents),
                'timestamp': timezone.now().isoformat()
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
def get_agent_data(request, agent_name):
    """Get specialized data for a specific agent"""
    try:
        feeder = get_mcp_agent_feeder()
        
        if agent_name not in feeder.agents:
            return JsonResponse({
                'success': False,
                'error': f'Agent {agent_name} not found',
                'timestamp': timezone.now().isoformat()
            }, status=404)
        
        feed = feeder.agent_feeds[agent_name]
        
        return JsonResponse({
            'success': True,
            'data': {
                'agent_name': agent_name,
                'data_cache': feed.data_cache,
                'last_update': feed.last_update.isoformat() if feed.last_update else None,
                'is_active': feed.is_active,
                'data_types': feed.data_types,
                'filters': feed.filters,
                'timestamp': timezone.now().isoformat()
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
def get_agent_signals(request):
    """Get current signals from all agents"""
    try:
        feeder = get_mcp_agent_feeder()
        signals = {}
        
        for agent_name, agent in feeder.agents.items():
            try:
                # Generate signal for each agent
                if agent_name == 'technical':
                    signal = agent.generate_signal('EURUSD', 'EUR', 'USD')
                elif agent_name == 'macro':
                    signal = agent.generate_signal(['EUR', 'USD'])
                elif agent_name == 'sentiment':
                    signal = agent.generate_signal(['EUR', 'USD'])
                elif agent_name == 'geopolitical':
                    signal = agent.generate_signal(['EUR', 'USD'])
                elif agent_name == 'coordinator':
                    signal = agent.generate_final_signal('EURUSD', 'EUR', 'USD')
                
                signals[agent_name] = signal
                
            except Exception as e:
                signals[agent_name] = {
                    'error': str(e),
                    'timestamp': timezone.now().isoformat()
                }
        
        return JsonResponse({
            'success': True,
            'data': {
                'signals': signals,
                'count': len(signals),
                'timestamp': timezone.now().isoformat()
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
def get_system_overview(request):
    """Get complete system overview"""
    try:
        collecteur = get_mcp_agent_collecteur()
        feeder = get_mcp_agent_feeder()
        
        collecteur_stats = collecteur.get_statistics()
        feeder_stats = feeder.get_feeding_statistics()
        
        overview = {
            'collecteur': {
                'is_running': collecteur.is_running,
                'session_id': collecteur.session_id,
                'stats': collecteur_stats,
                'data_sources': collecteur.data_sources
            },
            'feeder': {
                'is_running': feeder.is_running,
                'stats': feeder_stats,
                'connected_agents': list(feeder.agents.keys()),
                'active_feeds': sum(1 for feed in feeder.agent_feeds.values() if feed.is_active)
            },
            'system': {
                'total_data_points': collecteur_stats.get('data_points_collected', 0) + feeder_stats.get('data_points_processed', 0),
                'success_rate': (collecteur_stats.get('success_rate', 0) + feeder_stats.get('success_rate', 0)) / 2,
                'uptime_seconds': max(collecteur_stats.get('uptime_seconds', 0), feeder_stats.get('uptime_seconds', 0))
            },
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse({
            'success': True,
            'data': overview
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
def get_realtime_stats(request):
    """Get real-time system statistics"""
    try:
        collecteur = get_mcp_agent_collecteur()
        feeder = get_mcp_agent_feeder()
        
        # Get latest stats
        collecteur_stats = collecteur.get_statistics()
        feeder_stats = feeder.get_feeding_statistics()
        
        realtime_stats = {
            'collecteur': {
                'total_collections': collecteur_stats.get('total_collections', 0),
                'successful_collections': collecteur_stats.get('successful_collections', 0),
                'data_points_collected': collecteur_stats.get('data_points_collected', 0),
                'last_activity': collecteur_stats.get('last_activity'),
                'is_running': collecteur.is_running
            },
            'feeder': {
                'total_feeds': feeder_stats.get('total_feeds', 0),
                'successful_feeds': feeder_stats.get('successful_feeds', 0),
                'data_points_processed': feeder_stats.get('data_points_processed', 0),
                'agent_updates': feeder_stats.get('agent_updates', {}),
                'is_running': feeder.is_running
            },
            'performance': {
                'collecteur_success_rate': collecteur_stats.get('success_rate', 0),
                'feeder_success_rate': feeder_stats.get('success_rate', 0),
                'data_points_per_hour': feeder_stats.get('data_points_per_hour', 0),
                'active_feeds': sum(1 for feed in feeder.agent_feeds.values() if feed.is_active)
            },
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse({
            'success': True,
            'data': realtime_stats
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)
