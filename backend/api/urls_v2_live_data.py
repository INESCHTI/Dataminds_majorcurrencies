"""
URL configuration for Live Data API endpoints
"""
from django.urls import path
from . import views_v2_live_data

urlpatterns = [
    # Live Data Management
    path('live-data/provider_status/', views_v2_live_data.LiveDataViewSet().provider_status),
    path('live-data/start_live_data/', views_v2_live_data.LiveDataViewSet().start_live_data),
    path('live-data/stop_live_data/', views_v2_live_data.LiveDataViewSet().stop_live_data),
    path('live-data/latest_prices/', views_v2_live_data.LiveDataViewSet().latest_prices),
    
    # Risk Management
    path('risk-management/calculate_position_size/', views_v2_live_data.RiskManagementViewSet().calculate_position_size),
    path('risk-management/portfolio_summary/', views_v2_live_data.RiskManagementViewSet().portfolio_summary),
    path('risk-management/risk_validation/', views_v2_live_data.RiskManagementViewSet().risk_validation),
    path('risk-management/update_account_balance/', views_v2_live_data.RiskManagementViewSet().update_account_balance),
    
    # Backtesting
    path('backtesting/run_backtest/', views_v2_live_data.BacktestingViewSet().run_backtest),
    path('backtesting/backtest_status/', views_v2_live_data.BacktestingViewSet().backtest_status),
    
    # Performance Metrics
    path('performance/current_metrics/', views_v2_live_data.PerformanceMetricsViewSet().current_metrics),
    path('performance/performance_summary/', views_v2_live_data.PerformanceMetricsViewSet().performance_summary),
    path('performance/equity_curve/', views_v2_live_data.PerformanceMetricsViewSet().equity_curve),
    path('performance/trade_history/', views_v2_live_data.PerformanceMetricsViewSet().trade_history),
    path('performance/add_trade/', views_v2_live_data.PerformanceMetricsViewSet().add_trade),
    path('performance/update_balance/', views_v2_live_data.PerformanceMetricsViewSet().update_balance),
]
