"""
MCP Status API - Check if MCP System is running
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
import json

from mcp_agent_collecteur import get_mcp_agent_collecteur
from mcp_agent_feeder import get_mcp_agent_feeder


@api_view(['GET'])
def mcp_status(request):
    """
    Get MCP System status
    
    GET /api/mcp/status
    """
    try:
        collecteur = get_mcp_agent_collecteur()
        feeder = get_mcp_agent_feeder()
        
        # Get data sources status
        data_sources = collecteur.data_sources if hasattr(collecteur, 'data_sources') else {}
        
        return Response({
            'success': True,
            'data': {
                'collecteur': {
                    'is_running': collecteur.is_running,
                    'session_id': collecteur.session_id,
                    'stats': getattr(collecteur, 'stats', {}),
                    'data_sources': data_sources
                },
                'feeder': {
                    'is_running': feeder.is_running,
                    'agent_feeds': len(getattr(feeder, 'agent_feeds', {})),
                    'agents': list(getattr(feeder, 'agents', {}).keys())
                },
                'last_check': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def ensure_mcp_running(request):
    """
    Ensure MCP System is running - starts if not
    
    POST /api/mcp/ensure_running
    """
    try:
        collecteur = get_mcp_agent_collecteur()
        feeder = get_mcp_agent_feeder()
        
        actions_taken = []
        
        # Start collecteur if not running
        if not collecteur.is_running:
            collecteur.start_collection()
            actions_taken.append('Started MCP Collecteur')
        
        # Start feeder if not running  
        if not feeder.is_running:
            feeder.start_feeding()
            actions_taken.append('Started MCP Feeder')
        
        return Response({
            'success': True,
            'data': {
                'collecteur_running': collecteur.is_running,
                'feeder_running': feeder.is_running,
                'actions_taken': actions_taken,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
