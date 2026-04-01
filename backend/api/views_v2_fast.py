"""
Fast Signal Generation View - For Frontend Testing
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from datetime import datetime
import random
import json

@api_view(['POST'])
@permission_classes([AllowAny])
def generate_signal_fast(request):
    """
    Fast signal generation for frontend testing
    Bypasses heavy processing to return quick responses
    """
    try:
        pair = request.data.get('pair', 'EURUSD')
        
        # Generate quick mock signal
        directions = ['BUY', 'SELL', 'NEUTRAL']
        direction = random.choice(directions)
        confidence = random.uniform(0.4, 0.9)
        
        # Quick mock reasoning
        reasoning_templates = {
            'BUY': f"Technical analysis indicates bullish momentum for {pair}. Multiple indicators align for potential upward movement.",
            'SELL': f"Technical analysis indicates bearish momentum for {pair}. Multiple indicators suggest potential downward movement.",
            'NEUTRAL': f"Mixed signals for {pair}. Waiting for clearer directional bias before taking position."
        }
        
        signal_id = f"{pair}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        response_data = {
            'success': True,
            'signal': {
                'direction': direction,
                'confidence': confidence,
                'weighted_score': confidence if direction != 'NEUTRAL' else 0.0,
                'reasoning': reasoning_templates[direction],
                'agent_votes': {
                    'technical': {
                        'signal': direction,
                        'confidence': confidence,
                        'reasoning': f"Fast technical analysis for {pair}"
                    },
                    'macro': {
                        'signal': 'NEUTRAL',
                        'confidence': 0.5,
                        'reasoning': "Fast macro analysis - neutral stance"
                    },
                    'sentiment': {
                        'signal': direction if confidence > 0.6 else 'NEUTRAL',
                        'confidence': confidence * 0.8,
                        'reasoning': "Fast sentiment analysis"
                    },
                    'geopolitical': {
                        'signal': 'NEUTRAL',
                        'confidence': 0.4,
                        'reasoning': "Fast geopolitical analysis - stable"
                    }
                },
                'weights': {
                    'technical': 0.30,
                    'macro': 0.25,
                    'sentiment': 0.20,
                    'geopolitical': 0.25
                },
                'market_regime': 'normal',
                'conflicts': [],
                'timestamp': datetime.now().isoformat(),
                'signal_id': signal_id
            },
            'metadata': {
                'execution_time_ms': 100,  # Fast execution
                'data_timestamps': {
                    'ohlcv': datetime.now().isoformat(),
                    'macro': datetime.now().isoformat(),
                    'news': datetime.now().isoformat()
                }
            }
        }
        
        return Response(response_data)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Fast signal generation failed: {str(e)}'
        }, status=500)
