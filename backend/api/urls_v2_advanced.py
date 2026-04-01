"""
URL configuration for Advanced Features API endpoints
"""
from django.urls import path
from . import views_v2_advanced

urlpatterns = [
    # LLM Central Bank Analysis
    path('llm/sample_statements/', views_v2_advanced.LLMAnalysisViewSet().sample_statements),
    path('llm/analyze_statement/', views_v2_advanced.LLMAnalysisViewSet().analyze_statement),
    path('llm/analyze_multiple_statements/', views_v2_advanced.LLMAnalysisViewSet().analyze_multiple_statements),
    
    # Chart Pattern Recognition
    path('patterns/analyze_chart/', views_v2_advanced.PatternRecognitionViewSet().analyze_chart),
    path('patterns/analyze_with_sample_data/', views_v2_advanced.PatternRecognitionViewSet().analyze_with_sample_data),
    
    # RL Weight Optimization
    path('rl/update_agent_performance/', views_v2_advanced.RLOptimizationViewSet().update_agent_performance),
    path('rl/optimize_weights/', views_v2_advanced.RLOptimizationViewSet().optimize_weights),
    path('rl/get_optimization_stats/', views_v2_advanced.RLOptimizationViewSet().get_optimization_stats),
    path('rl/reset_optimization/', views_v2_advanced.RLOptimizationViewSet().reset_optimization),
    
    # Multi-Timezone Optimization
    path('timezone/get_current_session/', views_v2_advanced.MultiTimezoneViewSet().get_current_session),
    path('timezone/update_session_performance/', views_v2_advanced.MultiTimezoneViewSet().update_session_performance),
    path('timezone/get_session_recommendations/', views_v2_advanced.MultiTimezoneViewSet().get_session_recommendations),
    path('timezone/optimize_session_weights/', views_v2_advanced.MultiTimezoneViewSet().optimize_session_weights),
    path('timezone/get_session_statistics/', views_v2_advanced.MultiTimezoneViewSet().get_session_statistics),
    path('timezone/create_session_schedule/', views_v2_advanced.MultiTimezoneViewSet().create_session_schedule),
]
