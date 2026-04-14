"""
Test ultra-simple pour les endpoints tactiques
"""
from django.http import JsonResponse

def mt5_status_test(request):
    """Test endpoint pour MT5 status"""
    return JsonResponse({
        'success': True,
        'message': 'Test endpoint MT5 status',
        'stats': {'is_connected': False, 'is_streaming': False},
        'health': {'status': 'test', 'issues': []}
    })
