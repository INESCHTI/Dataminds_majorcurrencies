"""
URL patterns for Forex Alpha API
"""

from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.HealthView.as_view(), name='health'),
    path('symbols/', views.SymbolsView.as_view(), name='symbols'),
    path('timeframes/', views.TimeframesView.as_view(), name='timeframes'),
    path('forex-data/', views.ForexDataView.as_view(), name='forex-data'),
    path('economic-indicators/', views.EconomicIndicatorsView.as_view(), name='economic-indicators'),
    path('signals/', views.SignalsView.as_view(), name='signals'),
    path('signals/history/', views.SignalHistoryView.as_view(), name='signal-history'),
    path('signals/train-rl/', views.TrainRLView.as_view(), name='train-rl'),
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('chat/explain/', views.ChatExplainView.as_view(), name='chat-explain'),
]
