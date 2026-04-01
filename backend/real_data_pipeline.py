"""
Real Data Pipeline for FX Alpha Platform
Coordinates real market data, signal generation, and trade execution
"""

import os
import sys
sys.path.append('backend')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from data_layer.real_market_data import get_market_data, store_market_data
from data_layer.real_signal_recorder import generate_real_signals, execute_trade, update_trades_with_market_data
from signal_layer.coordinator_agent_v2 import CoordinatorAgentV2
import logging
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class RealDataPipeline:
    """
    Complete real data pipeline:
    1. Fetch real market data
    2. Generate real signals from agents
    3. Execute trades
    4. Track performance
    """
    
    def __init__(self):
        self.coordinator = CoordinatorAgentV2()
        self.pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD']
        self.agents = ['TechnicalV2', 'MacroV2', 'SentimentV2', 'GeopoliticalV2']
        
    def run_historical_backtest(self, days: int = 30):
        """
        Run a backtest with real historical data
        """
        logger.info(f"🚀 Starting {days}-day historical backtest...")
        
        for pair in self.pairs:
            logger.info(f"📊 Processing {pair}...")
            
            # Get historical market data
            ohlcv_df = get_market_data(pair, days)
            if ohlcv_df.empty:
                logger.warning(f"No data available for {pair}")
                continue
            
            # Store to InfluxDB
            store_market_data(ohlcv_df, pair)
            
            # Generate signals for each day
            for i in range(len(ohlcv_df) - 1):  # Exclude last day (no future data)
                day_data = ohlcv_df.iloc[:i+1]
                current_date = day_data.iloc[-1]['datetime']
                
                logger.info(f"  📈 Processing {current_date.date()} for {pair}...")
                
                # Generate signals from each agent
                for agent in self.agents:
                    signal = generate_real_signals(day_data, agent, pair)
                    
                    # Execute trade if signal is strong enough
                    if signal['confidence'] > 0.6 and signal['signal'] != 'NEUTRAL':
                        trade_id = execute_trade(signal)
                        if trade_id:
                            logger.info(f"    💼 {agent} opened {signal['signal']} trade {trade_id}")
                
                # Simulate price movement to close trades
                if i < len(ohlcv_df) - 1:
                    next_price = ohlcv_df.iloc[i+1]['close']
                    current_prices = {pair: next_price}
                    closed_trades = update_trades_with_market_data(current_prices)
                    
                    for trade in closed_trades:
                        logger.info(f"    📊 Trade closed: {trade['exit_reason']}, P&L: {trade['pnl']:+.2%}")
        
        logger.info("✅ Historical backtest completed!")
    
    def run_real_time_simulation(self, duration_minutes: int = 60):
        """
        Run real-time simulation
        """
        logger.info(f"🔄 Starting real-time simulation for {duration_minutes} minutes...")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        while datetime.now() < end_time:
            logger.info(f"📊 Processing market data at {datetime.now().strftime('%H:%M:%S')}...")
            
            current_prices = {}
            
            # Process each pair
            for pair in self.pairs:
                # Get recent market data
                ohlcv_df = get_market_data(pair, 5)  # Last 5 days
                if ohlcv_df.empty:
                    continue
                
                current_price = ohlcv_df.iloc[-1]['close']
                current_prices[pair] = current_price
                
                # Generate coordinator signal
                try:
                    signal_result = self.coordinator.generate_and_record_signal(pair)
                    
                    if signal_result.get('final_signal') != 0:  # Non-neutral signal
                        signal_direction = signal_result['final_signal']
                        confidence = signal_result['confidence']
                        
                        # Create trade signal for execution
                        trade_signal = {
                            'signal': 'BUY' if signal_direction == 1 else 'SELL',
                            'confidence': confidence,
                            'pair': pair,
                            'entry_price': current_price,
                            'agent_name': 'CoordinatorV2',
                            'reasoning': signal_result.get('deterministic_reason', 'Coordinated signal')
                        }
                        
                        trade_id = execute_trade(trade_signal)
                        if trade_id:
                            logger.info(f"💼 Opened {trade_signal['signal']} trade {trade_id} at {current_price:.5f}")
                
                except Exception as e:
                    logger.error(f"Error generating signal for {pair}: {e}")
            
            # Update existing trades
            if current_prices:
                closed_trades = update_trades_with_market_data(current_prices)
                for trade in closed_trades:
                    logger.info(f"📊 Trade closed: {trade['exit_reason']}, P&L: {trade['pnl']:+.2%}")
            
            # Wait for next update (every 5 minutes)
            time.sleep(300)
        
        logger.info("✅ Real-time simulation completed!")
    
    def generate_performance_report(self):
        """
        Generate a performance report from real data
        """
        try:
            from core.database import DatabaseManager
            
            db = DatabaseManager()
            
            # Get performance summary
            summary = db.query_postgres("""
                SELECT 
                    agent_name,
                    COUNT(*) as total_signals,
                    AVG(CASE WHEN was_correct THEN 1 ELSE 0 END)::numeric as win_rate,
                    AVG(pnl)::numeric as avg_pnl,
                    STDDEV(pnl)::numeric as pnl_std,
                    MAX(pnl)::numeric as max_pnl,
                    MIN(pnl)::numeric as min_pnl,
                    AVG(confidence)::numeric as avg_confidence
                FROM agent_performance_log
                GROUP BY agent_name
                ORDER BY agent_name
            """)
            
            if not summary.empty:
                logger.info("📈 PERFORMANCE REPORT:")
                logger.info("=" * 50)
                
                total_trades = 0
                total_pnl = 0.0
                
                for _, row in summary.iterrows():
                    agent_name = row['agent_name']
                    signals = int(row['total_signals'])
                    win_rate = row['win_rate']
                    avg_pnl = row['avg_pnl']
                    confidence = row['avg_confidence']
                    
                    total_trades += signals
                    total_pnl += avg_pnl * signals
                    
                    # Calculate Sharpe ratio (simplified)
                    pnl_std = row['pnl_std'] or 0.01
                    sharpe = (avg_pnl / pnl_std) if pnl_std > 0 else 0.0
                    
                    logger.info(f"🤖 {agent_name}:")
                    logger.info(f"   Signals: {signals}")
                    logger.info(f"   Win Rate: {win_rate:.1%}")
                    logger.info(f"   Avg P&L: {avg_pnl:+.3f}")
                    logger.info(f"   Sharpe: {sharpe:.2f}")
                    logger.info(f"   Confidence: {confidence:.2f}")
                    logger.info("")
                
                # Overall performance
                if total_trades > 0:
                    overall_win_rate = summary['was_correct'].mean()
                    overall_pnl = total_pnl / total_trades
                    
                    logger.info("📊 OVERALL PERFORMANCE:")
                    logger.info(f"   Total Trades: {total_trades}")
                    logger.info(f"   Overall Win Rate: {overall_win_rate:.1%}")
                    logger.info(f"   Overall Avg P&L: {overall_pnl:+.3f}")
                    logger.info(f"   Total P&L: {total_pnl:+.3f}")
                
            else:
                logger.warning("No performance data available")
                
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Real Data Pipeline')
    parser.add_argument('--backtest', type=int, help='Run historical backtest for N days')
    parser.add_argument('--simulate', type=int, help='Run real-time simulation for N minutes')
    parser.add_argument('--report', action='store_true', help='Generate performance report')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    pipeline = RealDataPipeline()
    
    if args.backtest:
        pipeline.run_historical_backtest(args.backtest)
        pipeline.generate_performance_report()
    
    elif args.simulate:
        pipeline.run_real_time_simulation(args.simulate)
        pipeline.generate_performance_report()
    
    elif args.report:
        pipeline.generate_performance_report()
    
    else:
        print("Usage:")
        print("  python real_data_pipeline.py --backtest 30    # 30-day historical backtest")
        print("  python real_data_pipeline.py --simulate 60    # 60-minute real-time simulation")
        print("  python real_data_pipeline.py --report         # Generate performance report")
