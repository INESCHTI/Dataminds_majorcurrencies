"""
Simple test view to verify URL routing works
"""
from django.http import JsonResponse

def test_view(request):
    """Simple test view"""
    return JsonResponse({
        'success': True,
        'message': 'Advanced features URLs are working!',
        'test': True
    })
