"""
URL configuration for Simple Live Data API endpoints
"""
from django.urls import path
from . import views_v2_live_data_simple

urlpatterns = [
    path('data/status/', views_v2_live_data_simple.live_data_status),
    path('data/statistics/', views_v2_live_data_simple.live_data_statistics),
]
