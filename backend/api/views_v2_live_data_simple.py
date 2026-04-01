"""
Simple Live Data API Views
Basic endpoints for live data status
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@api_view(['GET'])
def live_data_status(request):
    """Get live data status"""
    try:
        # Mock data for now
        return Response({
            'success': True,
            'provider_status': {
                'oanda': {
                    'enabled': False,
                    'active': False,
                    'status': 'disabled'
                },
                'fxcm': {
                    'enabled': False,
                    'active': False,
                    'status': 'disabled'
                },
                'simulation': {
                    'enabled': True,
                    'active': True,
                    'status': 'active'
                }
            },
            'statistics': {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'last_update': None,
                'is_running': True
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting live data status: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def live_data_statistics(request):
    """Get live data statistics"""
    try:
        # Mock data for now
        return Response({
            'success': True,
            'statistics': {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'last_update': None,
                'is_running': True
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting live data statistics: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
