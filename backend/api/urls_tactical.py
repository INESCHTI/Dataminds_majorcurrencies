"""
URLs for Tactical Analysis endpoints - Test version
"""
from django.urls import path
from .views_tactical_test import mt5_status_test

urlpatterns = [
    path('mt5_status/', mt5_status_test, name='mt5_status_test'),
]
