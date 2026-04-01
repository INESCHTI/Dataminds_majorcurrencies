"""
URL configuration for Simple Advanced Features API endpoints
"""
from django.urls import path
from . import views_v2_advanced_simple

urlpatterns = [
    # LLM Central Bank Analysis
    path('llm/sample_statements/', views_v2_advanced_simple.llm_sample_statements),
    path('llm/analyze_multiple_statements/', views_v2_advanced_simple.llm_analyze_multiple_statements),
    
    # Chart Pattern Recognition
    path('patterns/analyze_with_sample_data/', views_v2_advanced_simple.patterns_analyze_with_sample_data),
    
    # RL Weight Optimization
    path('rl/get_optimization_stats/', views_v2_advanced_simple.rl_get_optimization_stats),
    
    # Multi-Timezone Optimization
    path('timezone/get_current_session/', views_v2_advanced_simple.timezone_get_current_session),
    path('timezone/get_session_recommendations/', views_v2_advanced_simple.timezone_get_session_recommendations),
]
