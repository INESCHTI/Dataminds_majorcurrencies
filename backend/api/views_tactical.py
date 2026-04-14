"""
API Views pour les fonctionnalités tactiques avancées
Intègre l'agent multi-timeframe et le générateur de rapports
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
def multitimeframe_signal(request):
    """
    Génère un signal multi-timeframe
    
    POST /api/tactical/multitimeframe_signal/
    Body: {"symbol": "EURUSD"}
    """
    try:
        from signal_layer.multitimeframe_agent_v2 import MultitimeframeAgentV2
        from datetime import datetime
        
        data = json.loads(request.body)
        symbol = data.get('symbol', 'EURUSD')
        
        multitimeframe_agent = MultitimeframeAgentV2()
        signal = multitimeframe_agent.generate_signal(symbol)
        
        return Response({
            'success': True,
            'symbol': symbol,
            'signal': signal,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur signal multi-timeframe: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def generate_tactical_report(request):
    """
    Génère un rapport tactique complet
    
    POST /api/tactical/generate_tactical_report/
    Body: {"include_positions": true}
    """
    try:
        from analytics.tactical_report_generator import get_tactical_generator
        from datetime import datetime
        
        data = json.loads(request.body)
        include_positions = data.get('include_positions', True)
        
        tactical_generator = get_tactical_generator()
        report = tactical_generator.generate_tactical_report(include_positions)
        
        json_report = tactical_generator.export_report_to_json(report)
        
        return Response({
            'success': True,
            'report': json.loads(json_report),
            'report_id': report.report_id,
            'timestamp': report.generated_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur rapport tactique: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def mt5_status(request):
    """
    Vérifie le statut du connecteur MT5
    
    GET /api/tactical/mt5_status/
    """
    try:
        from acquisition.mt5_mcp_connector import get_mt5_connector
        from datetime import datetime
        
        mt5_connector = get_mt5_connector()
        stats = mt5_connector.get_stats()
        health = mt5_connector.health_check()
        
        return Response({
            'success': True,
            'stats': stats,
            'health': health,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur statut MT5: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def start_mt5_service(request):
    """
    Démarre le service MT5
    
    POST /api/tactical/start_mt5_service/
    """
    try:
        from acquisition.mt5_mcp_connector import get_mt5_connector
        from datetime import datetime
        
        mt5_connector = get_mt5_connector()
        success = mt5_connector.connect()
        if success:
            mt5_connector.start_streaming()
        
        return Response({
            'success': success,
            'message': 'Service MT5 démarré' if success else 'Échec démarrage MT5',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur démarrage MT5: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def stop_mt5_service(request):
    """
    Arrête le service MT5
    
    POST /api/tactical/stop_mt5_service/
    """
    try:
        from acquisition.mt5_mcp_connector import get_mt5_connector
        from datetime import datetime
        
        mt5_connector = get_mt5_connector()
        mt5_connector.disconnect()
        
        return Response({
            'success': True,
            'message': 'Service MT5 arrêté',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur arrêt MT5: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Import pour datetime
from datetime import datetime
