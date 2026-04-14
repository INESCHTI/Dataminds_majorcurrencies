"""
PHASE 6: API URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse
from api.views import (
    SignalViewSet, AgentExplanationViewSet, BacktestViewSet,
    HealthViewSet, FeatureViewSet
)

router = DefaultRouter()
router.register(r'signals', SignalViewSet, basename='signals')
router.register(r'agent', AgentExplanationViewSet, basename='agent')
router.register(r'backtest', BacktestViewSet, basename='backtest')

from . import urls_v2
from . import urls_websocket
from . import urls_v2_live_data_simple
from . import urls_mcp
from . import urls_tactical

urlpatterns = [
    path('', include(router.urls)),
    path('ws/', include(urls_websocket)),
    path('v2/', include(urls_v2_live_data_simple)),  # Live data endpoints
]

# V2 API endpoints
urlpatterns += [
    path('v2/', include('api.urls_v2')),
    path('v2-signals/', include('api.urls_v2')),
    path('monitoring/', include('api.urls_v2')),
    path('explain/', include('api.urls_v2')),
    path('backtesting/', include('api.urls_v2')),
    path('correlations/', include('api.urls_v2')),
    path('validation/', include('api.urls_v2')),
    path('data/', include('api.urls_v2')),
]

# MCP Agent System endpoints
urlpatterns += [
    path('mcp/', include('api.urls_mcp')),
    path('tactical/', include('api.urls_tactical')),
]
