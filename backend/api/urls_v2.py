"""
URL configuration for V2 API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_v2 import (
    TradingSignalV2ViewSet,
    PerformanceMonitoringViewSet,
    ExplainabilityViewSet,
    BacktestingViewSet,
    CorrelationViewSet,
    ValidationViewSet,
    DataRefreshViewSet,
)
from .views_v2_advanced_simple import (
    llm_sample_statements,
    llm_analyze_multiple_statements,
    patterns_analyze_with_sample_data,
    rl_get_optimization_stats,
    timezone_get_current_session,
    timezone_get_session_recommendations,
    timezone_get_session_statistics,
    timezone_optimize_session_weights,
)
from .views_v2_fast import generate_signal_fast

router = DefaultRouter()
router.register(r'v2-signals', TradingSignalV2ViewSet, basename='trading-signal-v2')
router.register(r'monitoring', PerformanceMonitoringViewSet, basename='monitoring-v2')
router.register(r'explain', ExplainabilityViewSet, basename='explain-v2')
router.register(r'backtesting', BacktestingViewSet, basename='backtesting-v2')
router.register(r'correlations', CorrelationViewSet, basename='correlations-v2')
router.register(r'validation', ValidationViewSet, basename='validation-v2')
router.register(r'data', DataRefreshViewSet, basename='data-v2')

urlpatterns = [
    path('', include(router.urls)),
    # Fast signal generation endpoint
    path('v2-signals-fast/generate_signal/', generate_signal_fast, name='generate-signal-fast'),
    # Orchestrated signal generation (LLM as Judge)
    path('v2-signals/generate_orchestrated_signal/', TradingSignalV2ViewSet.as_view({'post': 'generate_orchestrated_signal'}), name='generate-orchestrated-signal'),
    # Advanced features endpoints
    path('llm/sample_statements/', llm_sample_statements),
    path('llm/analyze_multiple_statements/', llm_analyze_multiple_statements),
    path('patterns/analyze_with_sample_data/', patterns_analyze_with_sample_data),
    path('rl/get_optimization_stats/', rl_get_optimization_stats),
    path('timezone/get_current_session/', timezone_get_current_session),
    path('timezone/get_session_recommendations/', timezone_get_session_recommendations),
    path('timezone/get_session_statistics/', timezone_get_session_statistics),
    path('timezone/optimize_session_weights/', timezone_optimize_session_weights),
]
