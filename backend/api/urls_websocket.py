"""
WebSocket URL configuration
"""
from django.urls import path
from . import views_v2_websocket

urlpatterns = [
    # WebSocket service management
    path('websocket/start/', views_v2_websocket.start_websocket_service, name='start-websocket'),
    path('websocket/stop/', views_v2_websocket.stop_websocket_service, name='stop-websocket'),
    
    # WebSocket information
    path('websocket/info/', views_v2_websocket.websocket_info, name='websocket-info'),
    
    # Real-time data endpoints
    path('websocket/data/', views_v2_websocket.get_real_time_data, name='real-time-data'),
    path('websocket/quality/', views_v2_websocket.get_data_quality, name='data-quality'),
    path('websocket/prices/', views_v2_websocket.get_latest_prices, name='latest-prices'),
]
