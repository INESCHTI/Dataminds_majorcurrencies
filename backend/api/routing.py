"""
WebSocket routing configuration for Django Channels
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Real-time data streaming
    re_path(r'ws/data/(?P<symbol>\w+)/$', consumers.RealTimeDataConsumer.as_asgi()),
    re_path(r'ws/data/$', consumers.RealTimeDataConsumer.as_asgi()),
    
    # Symbol information and status
    re_path(r'ws/symbols/$', consumers.SymbolListConsumer.as_asgi()),
    
    # Real-time signal streaming
    re_path(r'ws/signals/$', consumers.RealTimeSignalConsumer.as_asgi()),
]
