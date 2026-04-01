"""
Test URL configuration
"""
from django.urls import path
from . import views_v2_advanced_simple_test

urlpatterns = [
    path('test/', views_v2_advanced_simple_test.test_view),
]
