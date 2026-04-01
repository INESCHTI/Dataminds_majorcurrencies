"""
Live Data API Views
REST API endpoints for managing live data integration and real-time metrics
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import json
import logging

from data_layer.live_data_manager import create_live_data_manager, LiveDataConfig
from risk_management.position_sizer import create_position_sizer, PositionSizingMethod
from analytics.backtesting_engine import BacktestingEngine
from performance.performance_tracker import get_performance_tracker

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class LiveDataViewSet(APIView):
    """API endpoints for live data management"""
    
    def __init__(self):
        self.live_data_manager = create_live_data_manager()
        self.performance_tracker = get_performance_tracker()
    
    def get(self, request, *args, **kwargs):
        """Handle different GET endpoints based on URL parameters"""
        endpoint = kwargs.get('endpoint', 'status')
        
        if endpoint == 'provider_status':
            return self.provider_status(request)
        elif endpoint == 'statistics':
            return self.statistics(request)
        elif endpoint == 'start_provider':
            return self.start_provider(request)
        elif endpoint == 'stop_provider':
            return self.stop_provider(request)
        elif endpoint == 'refresh_data':
            return self.refresh_data(request)
        elif endpoint == 'latest_prices':
            return self.latest_prices(request)
        else:
            return self.status(request)
    
    def post(self, request, *args, **kwargs):
        """Handle POST endpoints"""
        endpoint = kwargs.get('endpoint', 'status')
        
        if endpoint == 'start_provider':
            return self.start_provider(request)
        elif endpoint == 'stop_provider':
            return self.stop_provider(request)
        elif endpoint == 'refresh_data':
            return self.refresh_data(request)
        else:
            return Response({'error': 'Invalid endpoint'}, status=status.HTTP_400_BAD_REQUEST)
    
    def status(self, request):
        """Get overall live data status"""
        try:
            provider_status = self.live_data_manager.get_provider_status()
            statistics = self.live_data_manager.get_statistics()
            
            return Response({
                'success': True,
                'provider_status': provider_status,
                'statistics': statistics,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting live data status: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def provider_status(self, request):
        """Get status of all data providers"""
        try:
            provider_status = self.live_data_manager.get_provider_status()
            statistics = self.live_data_manager.get_statistics()
            
            return Response({
                'success': True,
                'provider_status': provider_status,
                'statistics': statistics,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting provider status: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def start_live_data(self, request):
        """Start live data streaming"""
        try:
            data = json.loads(request.body)
            symbols = data.get('symbols', ['EURUSD', 'GBPUSD', 'USDJPY'])
            
            self.live_data_manager.start(symbols)
            
            return Response({
                'success': True,
                'message': f'Live data started for symbols: {symbols}',
                'active_providers': self.live_data_manager.active_providers
            })
        except Exception as e:
            logger.error(f"Error starting live data: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def stop_live_data(self, request):
        """Stop live data streaming"""
        try:
            self.live_data_manager.stop()
            
            return Response({
                'success': True,
                'message': 'Live data streaming stopped'
            })
        except Exception as e:
            logger.error(f"Error stopping live data: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def latest_prices(self, request):
        """Get latest prices for all symbols"""
        try:
            symbols = request.GET.getlist('symbols', ['EURUSD', 'GBPUSD', 'USDJPY'])
            prices = {}
            
            for symbol in symbols:
                price = self.live_data_manager.get_latest_price(symbol)
                if price:
                    prices[symbol] = price
            
            return Response({
                'success': True,
                'prices': prices,
                'timestamp': self.live_data_manager.stats.get('last_update')
            })
        except Exception as e:
            logger.error(f"Error getting latest prices: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class RiskManagementViewSet:
    """API endpoints for risk management and position sizing"""
    
    def __init__(self):
        self.position_sizer = create_position_sizer()
    
    @action(detail=False, methods=['post'])
    def calculate_position_size(self, request):
        """Calculate optimal position size"""
        try:
            data = json.loads(request.body)
            
            symbol = data.get('symbol')
            direction = data.get('direction')
            entry_price = float(data.get('entry_price'))
            stop_loss = float(data.get('stop_loss'))
            method = data.get('method', 'percentage')
            confidence = float(data.get('confidence', 0.5))
            volatility = float(data.get('volatility', 0.01))
            
            # Convert method string to enum
            method_enum = PositionSizingMethod(method.lower())
            
            # Calculate position size
            position_size, details = self.position_sizer.calculate_position_size(
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                stop_loss=stop_loss,
                method=method_enum,
                confidence=confidence,
                volatility=volatility
            )
            
            return Response({
                'success': True,
                'position_size': position_size,
                'details': details,
                'risk_metrics': {
                    'account_balance': self.position_sizer.account_balance,
                    'total_risk': self.position_sizer.total_risk,
                    'risk_utilization': (self.position_sizer.total_risk / self.position_sizer.account_balance) * 100
                }
            })
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def portfolio_summary(self, request):
        """Get current portfolio summary"""
        try:
            summary = self.position_sizer.get_portfolio_summary()
            
            return Response({
                'success': True,
                'portfolio': summary
            })
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def risk_validation(self, request):
        """Validate current positions against risk limits"""
        try:
            validation = self.position_sizer.validate_risk_limits()
            
            return Response({
                'success': True,
                'validation': validation
            })
        except Exception as e:
            logger.error(f"Error validating risk limits: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def update_account_balance(self, request):
        """Update account balance"""
        try:
            data = json.loads(request.body)
            new_balance = float(data.get('balance'))
            
            self.position_sizer.update_account_balance(new_balance)
            
            return Response({
                'success': True,
                'new_balance': new_balance
            })
        except Exception as e:
            logger.error(f"Error updating account balance: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class BacktestingViewSet:
    """API endpoints for backtesting functionality"""
    
    def __init__(self):
        self.backtest_engine = BacktestingEngine()
    
    @action(detail=False, methods=['post'])
    def run_backtest(self, request):
        """Run backtest on historical data"""
        try:
            data = json.loads(request.body)
            
            # Parse parameters
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
            symbols = data.get('symbols', ['EURUSD', 'GBPUSD', 'USDJPY'])
            initial_balance = float(data.get('initial_balance', 100000))
            
            # Convert dates
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
            
            # Initialize backtest engine
            self.backtest_engine = BacktestingEngine(initial_balance)
            
            # Load historical data
            historical_data = self.backtest_engine.load_historical_data(start_date, end_date, symbols)
            
            # Create signal generator (using multi-agent system)
            from signal_layer.coordinator_agent_v2_enhanced import CoordinatorAgentV2Enhanced
            coordinator = CoordinatorAgentV2Enhanced()
            signal_generator = self.backtest_engine.create_multi_agent_signal_generator(coordinator)
            
            # Run backtest
            results = self.backtest_engine.run_backtest(
                historical_data=historical_data,
                signal_generator=signal_generator,
                start_date=start_date,
                end_date=end_date
            )
            
            # Generate report
            report = self.backtest_engine.generate_report(results)
            
            return Response({
                'success': True,
                'results': results,
                'report': report
            })
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def backtest_status(self, request):
        """Get backtest engine status"""
        try:
            return Response({
                'success': True,
                'status': {
                    'initial_balance': self.backtest_engine.initial_balance,
                    'current_balance': self.backtest_engine.current_balance,
                    'total_trades': len(self.backtest_engine.trades),
                    'open_positions': len(self.backtest_engine.current_positions),
                    'equity_curve_length': len(self.backtest_engine.equity_curve)
                }
            })
        except Exception as e:
            logger.error(f"Error getting backtest status: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class PerformanceMetricsViewSet:
    """API endpoints for real-time performance metrics"""
    
    def __init__(self):
        self.performance_tracker = get_performance_tracker()
    
    @action(detail=False, methods=['get'])
    def current_metrics(self, request):
        """Get current performance metrics"""
        try:
            metrics = self.performance_tracker.get_current_metrics()
            
            return Response({
                'success': True,
                'metrics': metrics,
                'timestamp': self.performance_tracker._cache_timestamp.isoformat() if self.performance_tracker._cache_timestamp else None
            })
        except Exception as e:
            logger.error(f"Error getting current metrics: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def performance_summary(self, request):
        """Get comprehensive performance summary"""
        try:
            summary = self.performance_tracker.get_performance_summary()
            
            return Response({
                'success': True,
                'summary': summary
            })
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def equity_curve(self, request):
        """Get equity curve data"""
        try:
            days = int(request.GET.get('days', 30))
            equity_data = self.performance_tracker.get_equity_curve_data(days)
            
            return Response({
                'success': True,
                'equity_curve': equity_data
            })
        except Exception as e:
            logger.error(f"Error getting equity curve: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def trade_history(self, request):
        """Get recent trade history"""
        try:
            limit = int(request.GET.get('limit', 100))
            trades = self.performance_tracker.get_trade_history(limit)
            
            return Response({
                'success': True,
                'trades': trades
            })
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def add_trade(self, request):
        """Add a completed trade"""
        try:
            data = json.loads(request.body)
            
            self.performance_tracker.add_trade(data)
            
            return Response({
                'success': True,
                'message': 'Trade added successfully'
            })
        except Exception as e:
            logger.error(f"Error adding trade: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def update_balance(self, request):
        """Update account balance"""
        try:
            data = json.loads(request.body)
            new_balance = float(data.get('balance'))
            
            self.performance_tracker.update_balance(new_balance)
            
            return Response({
                'success': True,
                'new_balance': new_balance
            })
        except Exception as e:
            logger.error(f"Error updating balance: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Import for datetime handling
from datetime import datetime
