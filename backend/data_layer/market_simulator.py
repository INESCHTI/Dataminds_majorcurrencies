"""
Market Data Simulator for FX Alpha Platform
Provides realistic price movements for signal testing
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Dict, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
import time
import threading
from data_layer.signal_recorder import update_market_data

logger = logging.getLogger(__name__)


class MarketSimulator:
    """
    Simulates realistic forex market movements
    """
    
    def __init__(self):
        self.running = False
        self.base_prices = {
            'EURUSD': 1.0850,
            'GBPUSD': 1.2650,
            'USDJPY': 149.50,
            'USDCHF': 0.8820,
            'AUDUSD': 0.6520,
            'USDCAD': 1.3580
        }
        
        self.current_prices = self.base_prices.copy()
        
        # Market characteristics
        self.volatility = {
            'EURUSD': 0.008,  # 0.8% daily volatility
            'GBPUSD': 0.010,  # 1.0% daily volatility
            'USDJPY': 0.012,  # 1.2% daily volatility
            'USDCHF': 0.006,  # 0.6% daily volatility
            'AUDUSD': 0.015,  # 1.5% daily volatility
            'USDCAD': 0.009   # 0.9% daily volatility
        }
        
        # Correlation matrix (simplified)
        self.correlations = {
            ('EURUSD', 'GBPUSD'): 0.7,
            ('EURUSD', 'USDJPY'): 0.3,
            ('EURUSD', 'USDCHF'): 0.5,
            ('GBPUSD', 'USDJPY'): 0.6,
            ('GBPUSD', 'EURUSD'): 0.7,
            # Add more correlations as needed
        }
        
        # Market sessions
        self.sessions = {
            'asian': {'start': 0, 'end': 9},    # 00:00-09:00 UTC
            'london': {'start': 7, 'end': 16},   # 07:00-16:00 UTC
            'ny': {'start': 12, 'end': 21}     # 12:00-21:00 UTC
        }
    
    def start_simulation(self):
        """MARKET SIMULATION DISABLED - Using REAL DATA ONLY"""
        logger.warning("🚫 Market simulation is DISABLED - configure real data sources (MT5, Alpha Vantage)")
        return  # Do not start simulation
    
    def stop_simulation(self):
        """Stop the market simulation"""
        self.running = False
        logger.info("📉 Market simulation stopped")
    
    def _run_simulation(self):
        """Main simulation loop"""
        while self.running:
            try:
                # Get current UTC hour
                current_hour = datetime.now().hour
                
                # Determine market session
                session_multiplier = self._get_session_multiplier(current_hour)
                
                # Update prices for each pair
                price_updates = {}
                
                for pair in self.current_prices.keys():
                    # Base price movement with session influence
                    base_movement = np.random.normal(0, self.volatility[pair] * session_multiplier)
                    
                    # Add correlated movement from other pairs
                    correlation_adjustment = self._calculate_correlation_adjustment(pair, base_movement)
                    
                    # Calculate new price
                    old_price = self.current_prices[pair]
                    price_change_pct = (base_movement + correlation_adjustment)
                    new_price = old_price * (1 + price_change_pct)
                    
                    # Ensure prices stay within reasonable bounds
                    max_change = 0.02  # Maximum 2% change per update
                    if abs(price_change_pct) > max_change:
                        price_change_pct = max_change if price_change_pct > 0 else -max_change
                        new_price = old_price * (1 + price_change_pct)
                    
                    price_updates[pair] = new_price
                
                # Update market data
                update_market_data(price_updates)
                
                # Log summary
                self._log_market_update(price_updates)
                
                # Wait for next update (30 seconds)
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Simulation error: {e}")
                time.sleep(5)
    
    def _get_session_multiplier(self, hour: int) -> float:
        """Get volatility multiplier based on market session"""
        if self.sessions['asian']['start'] <= hour < self.sessions['asian']['end']:
            return 0.5  # Lower volatility in Asian session
        elif self.sessions['london']['start'] <= hour < self.sessions['london']['end']:
            return 1.2  # Higher volatility in London session
        elif self.sessions['ny']['start'] <= hour < self.sessions['ny']['end']:
            return 1.5  # Highest volatility in NY session
        else:
            return 0.8  # Normal volatility
    
    def _calculate_correlation_adjustment(self, pair: str, base_movement: float) -> float:
        """Calculate price adjustment based on correlations with other pairs"""
        adjustment = 0.0
        
        for (other_pair, correlation) in self.correlations.items():
            if pair in other_pair:
                # Get recent movement of correlated pair
                # This is simplified - in production, would use actual price history
                other_movement = np.random.normal(0, self.volatility.get(other_pair.replace(pair, ''), 0.01))
                adjustment += correlation * other_movement * 0.3  # 30% influence
        
        return adjustment
    
    def _log_market_update(self, price_updates: Dict[str, float]):
        """Log market price updates"""
        changes = []
        for pair, new_price in price_updates.items():
            old_price = self.current_prices[pair]
            change_pct = ((new_price - old_price) / old_price) * 100
            changes.append(f"{pair}: {old_price:.5f} → {new_price:.5f} ({change_pct:+.2f}%)")
        
        logger.info(f"📈 Price updates: {' | '.join(changes)}")
        
        # Update current prices
        self.current_prices.update(price_updates)
    
    def get_current_prices(self) -> Dict[str, float]:
        """Get current market prices"""
        return self.current_prices.copy()
    
    def inject_market_event(self, event_type: str, pairs: List[str], impact: float):
        """
        Inject a market event (news, economic data, etc.)
        """
        logger.info(f"📰 Market event: {event_type} affecting {pairs} with impact {impact}")
        
        # Apply immediate price shock to affected pairs
        for pair in pairs:
            if pair in self.current_prices:
                if event_type == 'positive':
                    price_change = abs(impact) * 0.01  # Positive event
                elif event_type == 'negative':
                    price_change = -abs(impact) * 0.01  # Negative event
                else:
                    price_change = np.random.normal(0, 0.005)  # Random movement
                
                old_price = self.current_prices[pair]
                new_price = old_price * (1 + price_change)
                
                update_market_data({pair: new_price})
                logger.info(f"📰 Event impact on {pair}: {old_price:.5f} → {new_price:.5f}")


# Global market simulator instance
market_simulator = MarketSimulator()


def start_market_simulation():
    """Start the market simulation"""
    market_simulator.start_simulation()


def stop_market_simulation():
    """Stop the market simulation"""
    market_simulator.stop_simulation()


def get_current_market_prices():
    """Get current market prices"""
    return market_simulator.get_current_prices()


def inject_market_event(event_type: str, pairs: List[str], impact: float):
    """Inject a market event"""
    market_simulator.inject_market_event(event_type, pairs, impact)


if __name__ == "__main__":
    # Test the simulator
    start_market_simulation()
    
    try:
        while True:
            print(f"Current prices: {get_current_market_prices()}")
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nStopping simulation...")
        stop_market_simulation()
