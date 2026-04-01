"""
Advanced Features API Views
LLM Integration, Pattern Recognition, RL Optimization, Multi-Timezone
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import json
import logging
from datetime import datetime, timedelta

from ai_layer.llm_central_bank_analyzer import create_llm_analyzer
from ai_layer.chart_pattern_recognition import create_pattern_recognizer
from ai_layer.rl_weight_optimizer import create_advanced_optimizer
from ai_layer.timezone_optimizer import create_timezone_optimizer

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class LLMAnalysisViewSet:
    """API endpoints for LLM-powered central bank analysis"""
    
    def __init__(self):
        self.llm_analyzer = create_llm_analyzer()
    
    @action(detail=False, methods=['get'])
    def sample_statements(self, request):
        """Get sample central bank statements for testing"""
        try:
            statements = self.llm_analyzer.create_sample_statements()
            
            serialized_statements = []
            for stmt in statements:
                serialized_statements.append({
                    'bank': stmt.bank,
                    'timestamp': stmt.timestamp.isoformat(),
                    'statement': stmt.statement,
                    'source': stmt.source,
                    'statement_type': stmt.statement_type,
                    'officials': stmt.officials
                })
            
            return Response({
                'success': True,
                'statements': serialized_statements
            })
        except Exception as e:
            logger.error(f"Error getting sample statements: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def analyze_statement(self, request):
        """Analyze a central bank statement using LLM"""
        try:
            data = json.loads(request.body)
            
            from ai_layer.llm_central_bank_analyzer import CentralBankStatement
            statement = CentralBankStatement(
                bank=data.get('bank'),
                timestamp=datetime.fromisoformat(data.get('timestamp')),
                statement=data.get('statement'),
                source=data.get('source', 'Unknown'),
                statement_type=data.get('statement_type', 'statement'),
                officials=data.get('officials', [])
            )
            
            result = self.llm_analyzer.analyze_statement(statement)
            
            if result:
                return Response({
                    'success': True,
                    'analysis': {
                        'bank': result.bank,
                        'timestamp': result.timestamp.isoformat(),
                        'policy_bias': result.policy_bias,
                        'confidence': result.confidence,
                        'key_points': result.key_points,
                        'rate_outlook': result.rate_outlook,
                        'inflation_outlook': result.inflation_outlook,
                        'economic_outlook': result.economic_outlook,
                        'market_impact': result.market_impact,
                        'reasoning': result.reasoning
                    }
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Failed to analyze statement'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error analyzing statement: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def analyze_multiple_statements(self, request):
        """Analyze multiple central bank statements"""
        try:
            data = json.loads(request.body)
            statements_data = data.get('statements', [])
            
            from ai_layer.llm_central_bank_analyzer import CentralBankStatement
            statements = []
            
            for stmt_data in statements_data:
                statement = CentralBankStatement(
                    bank=stmt_data.get('bank'),
                    timestamp=datetime.fromisoformat(stmt_data.get('timestamp')),
                    statement=stmt_data.get('statement'),
                    source=stmt_data.get('source', 'Unknown'),
                    statement_type=stmt_data.get('statement_type', 'statement'),
                    officials=stmt_data.get('officials', [])
                )
                statements.append(statement)
            
            results = self.llm_analyzer.analyze_multiple_statements(statements)
            currency_impacts = self.llm_analyzer.get_currency_impact(results)
            
            # Serialize results
            serialized_results = []
            for result in results:
                serialized_results.append({
                    'bank': result.bank,
                    'timestamp': result.timestamp.isoformat(),
                    'policy_bias': result.policy_bias,
                    'confidence': result.confidence,
                    'key_points': result.key_points,
                    'rate_outlook': result.rate_outlook,
                    'inflation_outlook': result.inflation_outlook,
                    'economic_outlook': result.economic_outlook,
                    'market_impact': result.market_impact,
                    'reasoning': result.reasoning
                })
            
            return Response({
                'success': True,
                'analyses': serialized_results,
                'currency_impacts': currency_impacts
            })
            
        except Exception as e:
            logger.error(f"Error analyzing multiple statements: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class PatternRecognitionViewSet:
    """API endpoints for chart pattern recognition"""
    
    def __init__(self):
        self.pattern_recognizer = create_pattern_recognizer()
    
    @action(detail=False, methods=['post'])
    def analyze_chart(self, request):
        """Analyze chart for patterns"""
        try:
            data = json.loads(request.body)
            
            # Convert data to DataFrame
            import pandas as pd
            from datetime import datetime
            
            chart_data = data.get('data', [])
            symbol = data.get('symbol', 'EURUSD')
            timeframe = data.get('timeframe', '1H')
            
            df_data = []
            for candle in chart_data:
                df_data.append({
                    'timestamp': datetime.fromisoformat(candle['timestamp']),
                    'open': candle['open'],
                    'high': candle['high'],
                    'low': candle['low'],
                    'close': candle['close'],
                    'volume': candle.get('volume', 0)
                })
            
            df = pd.DataFrame(df_data)
            df = df.sort_values('timestamp')
            
            # Analyze chart
            result = self.pattern_recognizer.analyze_chart(symbol, df, timeframe)
            
            # Serialize patterns
            serialized_patterns = []
            for pattern in result.patterns:
                serialized_patterns.append({
                    'pattern_type': pattern.pattern_type,
                    'confidence': pattern.confidence,
                    'start_time': pattern.start_time.isoformat(),
                    'end_time': pattern.end_time.isoformat(),
                    'price_level': pattern.price_level,
                    'direction': pattern.direction,
                    'description': pattern.description,
                    'key_points': [(t.isoformat(), p) for t, p in pattern.key_points],
                    'pattern_data': pattern.pattern_data
                })
            
            return Response({
                'success': True,
                'analysis': {
                    'symbol': result.symbol,
                    'timeframe': result.timeframe,
                    'timestamp': result.timestamp.isoformat(),
                    'patterns': serialized_patterns,
                    'overall_sentiment': result.overall_sentiment,
                    'confidence': result.confidence,
                    'chart_image': result.chart_image,
                    'analysis_summary': result.analysis_summary
                }
            })
            
        except Exception as e:
            logger.error(f"Error analyzing chart: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def analyze_with_sample_data(self, request):
        """Analyze chart with generated sample data"""
        try:
            data = json.loads(request.body)
            symbol = data.get('symbol', 'EURUSD')
            timeframe = data.get('timeframe', '1H')
            
            # Generate sample data
            import pandas as pd
            import numpy as np
            from datetime import datetime, timedelta
            
            # Generate 200 candles of sample data
            start_time = datetime.now() - timedelta(hours=200)
            times = [start_time + timedelta(hours=i) for i in range(200)]
            
            # Generate realistic price movements
            np.random.seed(42)
            base_price = 1.0850 if symbol == 'EURUSD' else 1.2650
            returns = np.random.normal(0, 0.001, 200)  # 0.1% hourly volatility
            
            prices = [base_price]
            for ret in returns:
                prices.append(prices[-1] * (1 + ret))
            
            prices = prices[1:]  # Remove initial price
            
            # Create OHLC data
            ohlc_data = []
            for i in range(len(prices)):
                intraday_vol = np.random.normal(0, 0.0002, 4)
                
                high = prices[i] * (1 + abs(intraday_vol[0]))
                low = prices[i] * (1 - abs(intraday_vol[1]))
                
                ohlc_data.append({
                    'timestamp': times[i],
                    'open': prices[i],
                    'high': high,
                    'low': low,
                    'close': prices[i],
                    'volume': np.random.randint(1000000, 10000000)
                })
            
            df = pd.DataFrame(ohlc_data)
            
            # Analyze chart
            result = self.pattern_recognizer.analyze_chart(symbol, df, timeframe)
            
            # Serialize patterns
            serialized_patterns = []
            for pattern in result.patterns:
                serialized_patterns.append({
                    'pattern_type': pattern.pattern_type,
                    'confidence': pattern.confidence,
                    'start_time': pattern.start_time.isoformat(),
                    'end_time': pattern.end_time.isoformat(),
                    'price_level': pattern.price_level,
                    'direction': pattern.direction,
                    'description': pattern.description,
                    'key_points': [(t.isoformat(), p) for t, p in pattern.key_points],
                    'pattern_data': pattern.pattern_data
                })
            
            return Response({
                'success': True,
                'analysis': {
                    'symbol': result.symbol,
                    'timeframe': result.timeframe,
                    'timestamp': result.timestamp.isoformat(),
                    'patterns': serialized_patterns,
                    'overall_sentiment': result.overall_sentiment,
                    'confidence': result.confidence,
                    'chart_image': result.chart_image,
                    'analysis_summary': result.analysis_summary
                }
            })
            
        except Exception as e:
            logger.error(f"Error analyzing sample chart: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class RLOptimizationViewSet:
    """API endpoints for RL-based weight optimization"""
    
    def __init__(self):
        self.advanced_optimizer = create_advanced_optimizer()
    
    @action(detail=False, methods=['post'])
    def update_agent_performance(self, request):
        """Update individual agent performance"""
        try:
            data = json.loads(request.body)
            
            agent_name = data.get('agent_name')
            performance = float(data.get('performance', 0.0))
            confidence = float(data.get('confidence', 0.5))
            
            self.advanced_optimizer.rl_optimizer.update_agent_performance(agent_name, performance, confidence)
            
            return Response({
                'success': True,
                'message': f'Updated performance for {agent_name}'
            })
            
        except Exception as e:
            logger.error(f"Error updating agent performance: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def optimize_weights(self, request):
        """Optimize agent weights using RL"""
        try:
            data = json.loads(request.body)
            
            strategy = data.get('strategy', 'rl')
            portfolio_return = float(data.get('portfolio_return', 0.0))
            sharpe_ratio = float(data.get('sharpe_ratio', 0.0))
            max_drawdown = float(data.get('max_drawdown', 0.0))
            win_rate = float(data.get('win_rate', 0.0))
            
            weights = self.advanced_optimizer.optimize_weights(
                strategy=strategy,
                portfolio_return=portfolio_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate
            )
            
            return Response({
                'success': True,
                'weights': weights,
                'strategy_used': strategy
            })
            
        except Exception as e:
            logger.error(f"Error optimizing weights: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def get_optimization_stats(self, request):
        """Get optimization statistics"""
        try:
            stats = self.advanced_optimizer.get_optimizer_stats()
            
            return Response({
                'success': True,
                'stats': stats
            })
            
        except Exception as e:
            logger.error(f"Error getting optimization stats: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def reset_optimization(self, request):
        """Reset optimization state"""
        try:
            self.advanced_optimizer.rl_optimizer.reset_optimization()
            
            return Response({
                'success': True,
                'message': 'Optimization reset successfully'
            })
            
        except Exception as e:
            logger.error(f"Error resetting optimization: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class MultiTimezoneViewSet:
    """API endpoints for multi-timezone optimization"""
    
    def __init__(self):
        self.timezone_optimizer = create_timezone_optimizer()
    
    @action(detail=False, methods=['get'])
    def get_current_session(self, request):
        """Get current trading sessions"""
        try:
            current_sessions = self.timezone_optimizer.get_current_session()
            overlap = self.timezone_optimizer.get_session_overlap()
            
            return Response({
                'success': True,
                'current_sessions': current_sessions,
                'session_overlap': overlap,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting current session: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def update_session_performance(self, request):
        """Update session performance for currency pair"""
        try:
            data = json.loads(request.body)
            
            currency_pair = data.get('currency_pair')
            session_name = data.get('session_name')
            return_pct = float(data.get('return_pct', 0.0))
            sharpe_ratio = float(data.get('sharpe_ratio', 0.0))
            max_drawdown = float(data.get('max_drawdown', 0.0))
            volatility = float(data.get('volatility', 0.0))
            
            self.timezone_optimizer.update_session_performance(
                currency_pair, session_name, return_pct, sharpe_ratio, max_drawdown, volatility
            )
            
            return Response({
                'success': True,
                'message': f'Updated performance for {currency_pair} in {session_name}'
            })
            
        except Exception as e:
            logger.error(f"Error updating session performance: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def get_session_recommendations(self, request):
        """Get session-based trading recommendations"""
        try:
            data = json.loads(request.body)
            currency_pair = data.get('currency_pair', 'EURUSD')
            
            recommendations = self.timezone_optimizer.get_session_recommendations(currency_pair)
            
            return Response({
                'success': True,
                'recommendations': recommendations
            })
            
        except Exception as e:
            logger.error(f"Error getting session recommendations: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def optimize_session_weights(self, request):
        """Optimize session weights for currency pair"""
        try:
            data = json.loads(request.body)
            currency_pair = data.get('currency_pair', 'EURUSD')
            
            weights = self.timezone_optimizer.optimize_session_weights(currency_pair)
            
            return Response({
                'success': True,
                'weights': weights,
                'currency_pair': currency_pair
            })
            
        except Exception as e:
            logger.error(f"Error optimizing session weights: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def get_session_statistics(self, request):
        """Get comprehensive session statistics"""
        try:
            stats = self.timezone_optimizer.get_session_statistics()
            
            return Response({
                'success': True,
                'statistics': stats
            })
            
        except Exception as e:
            logger.error(f"Error getting session statistics: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def create_session_schedule(self, request):
        """Create trading schedule for currency pair"""
        try:
            data = json.loads(request.body)
            currency_pair = data.get('currency_pair', 'EURUSD')
            days = int(data.get('days', 7))
            
            schedule_df = self.timezone_optimizer.create_session_schedule(currency_pair, days)
            
            # Convert DataFrame to JSON
            schedule_data = schedule_df.to_dict('records')
            
            return Response({
                'success': True,
                'schedule': schedule_data,
                'currency_pair': currency_pair,
                'days': days
            })
            
        except Exception as e:
            logger.error(f"Error creating session schedule: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Import datetime
from datetime import datetime
