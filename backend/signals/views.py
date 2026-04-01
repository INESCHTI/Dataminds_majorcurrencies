"""Serializers and views for signals app."""
from rest_framework import serializers, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import TradingSignal


class TradingSignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradingSignal
        fields = "__all__"


class TradingSignalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TradingSignal.objects.all()
    serializer_class = TradingSignalSerializer


@api_view(["GET"])
def latest_signals(request):
    """Get the latest active signal for each pair."""
    pairs = ["EURUSD", "USDJPY", "USDCHF", "GBPUSD"]
    result = []
    for pair in pairs:
        signal = TradingSignal.objects.filter(pair=pair).first()
        if signal:
            result.append(TradingSignalSerializer(signal).data)
        else:
            # NO MOCK SIGNALS - Return proper error for real data requirements
            return Response({
                'error': f'No real trading signal available for {pair}. Please generate real signals using the multi-agent system.',
                'pair': pair
            }, status=status.HTTP_404_NOT_FOUND)
    return Response(result)
