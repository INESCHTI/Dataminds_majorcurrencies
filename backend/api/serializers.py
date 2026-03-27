"""
DRF Serializers for Forex Alpha API
"""

from rest_framework import serializers
from .models import SignalLog, LangChainSession


class SignalLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignalLog
        fields = '__all__'


class LangChainSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LangChainSession
        fields = '__all__'


class ForexDataRequestSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10, default='EURUSD')
    timeframe = serializers.CharField(max_length=10, default='H1')
    days_back = serializers.IntegerField(min_value=1, max_value=365, default=30)


class SignalRequestSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)
    timeframe = serializers.CharField(max_length=10, default='H1')
    days_back = serializers.IntegerField(min_value=1, max_value=90, default=14)
    include_rl = serializers.BooleanField(default=True)
    include_langchain = serializers.BooleanField(default=False)
    session_id = serializers.CharField(max_length=100, required=False, default='default')


class ChatRequestSerializer(serializers.Serializer):
    session_id = serializers.CharField(max_length=100)
    message = serializers.CharField()
    symbol = serializers.CharField(max_length=10, required=False, default='')


class TrainRLRequestSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)
    timeframe = serializers.CharField(max_length=10, default='H1')
    days_back = serializers.IntegerField(min_value=30, max_value=365, default=90)
    episodes = serializers.IntegerField(min_value=1, max_value=200, default=50)
