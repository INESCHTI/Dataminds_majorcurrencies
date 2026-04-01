"""
Test endpoint for debugging MCP issues
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone


@csrf_exempt
@require_http_methods(["GET", "POST"])
def test_endpoint(request):
    """Test endpoint for debugging MCP issues"""
    if request.method == "POST":
        return JsonResponse({
            'success': True,
            'message': 'POST request received successfully',
            'method': 'POST',
            'timestamp': timezone.now().isoformat()
        })
    else:
        return JsonResponse({
            'success': True,
            'message': 'GET request received successfully',
            'method': 'GET',
            'timestamp': timezone.now().isoformat()
        })
