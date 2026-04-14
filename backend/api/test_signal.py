"""
Test Signal Generation Endpoint
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
import json

from signal_layer.coordinator_agent_v2 import CoordinatorAgentV2


@api_view(['GET', 'POST'])
def test_generate_signal(request):
    """
    Test signal generation endpoint
    
    GET /api/test/generate_signal/
    POST /api/test/generate_signal/
    """
    try:
        if request.method == 'GET':
            return Response({
                'success': True,
                'message': 'Signal generation endpoint is working',
                'method': 'GET',
                'timestamp': datetime.now().isoformat()
            })
        
        elif request.method == 'POST':
            # Parse request body
            try:
                if isinstance(request.body, bytes):
                    body_data = json.loads(request.body.decode('utf-8'))
                else:
                    body_data = request.data
            except:
                body_data = {}
            
            pair = body_data.get('pair', 'EURUSD')
            
            # Generate signal
            coordinator = CoordinatorAgentV2()
            result = coordinator.generate_and_record_signal(pair)
            
            return Response({
                'success': True,
                'data': result,
                'pair': pair,
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
