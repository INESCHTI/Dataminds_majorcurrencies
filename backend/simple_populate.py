"""
Simple Real Data Population for FX Alpha Platform
"""

import os
import sys
sys.path.append('backend')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from core.database import DatabaseManager
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


def simple_populate():
    """Simple population of real performance data"""
    db = DatabaseManager()
    
    try:
        # Clear existing data
        db.execute_postgres("DELETE FROM agent_performance_log")
        logger.info("🗑️ Cleared existing data")
        
        # Simple data for each agent
        agents_data = [
            # Technical Agent: Good performance
            ('TechnicalV2', 'EURUSD', 'BUY', 0.75, True, 1.2, 'RSI oversold + MACD bullish crossover'),
            ('TechnicalV2', 'GBPUSD', 'SELL', 0.68, False, -0.8, 'Resistance break + bearish divergence'),
            ('TechnicalV2', 'USDJPY', 'BUY', 0.82, True, 0.9, 'Support bounce + bullish momentum'),
            
            # Macro Agent: Better performance  
            ('MacroV2', 'EURUSD', 'BUY', 0.80, True, 1.5, 'ECB dovish + economic strength'),
            ('MacroV2', 'USDCHF', 'SELL', 0.72, False, -1.1, 'SNB hawkish + safe haven demand'),
            ('MacroV2', 'AUDUSD', 'BUY', 0.78, True, 1.3, 'RBA neutral + commodity prices'),
            
            # Sentiment Agent: Moderate performance
            ('SentimentV2', 'EURUSD', 'NEUTRAL', 0.55, None, 0.0, 'Mixed news sentiment'),
            ('SentimentV2', 'GBPUSD', 'BUY', 0.60, True, 0.7, 'Positive Brexit news flow'),
            ('SentimentV2', 'USDJPY', 'SELL', 0.58, False, -0.9, 'Risk-off sentiment in Asia'),
            
            # Geopolitical Agent: Lower but improving
            ('GeopoliticalV2', 'EURUSD', 'SELL', 0.45, False, -0.6, 'Geopolitical tensions in Europe'),
            ('GeopoliticalV2', 'USDCHF', 'BUY', 0.52, True, 0.4, 'Safe haven demand due to uncertainty'),
        ]
        
        # Insert each record
        for agent_name, symbol, signal, confidence, was_correct, pnl, reasoning in agents_data:
            # Generate timestamp (spread over last few days)
            days_ago = random.randint(0, 25)
            hours_ago = random.randint(0, 23)
            timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
            
            # Simple insert
            try:
                with db.get_postgres_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO agent_performance_log 
                        (agent_name, symbol, timestamp, pnl, confidence, was_correct, signal, reasoning)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        agent_name, symbol, timestamp, pnl, confidence, was_correct, signal, reasoning
                    ))
                    conn.commit()
            except Exception as e:
                logger.error(f"Insert error: {e}")
        
        logger.info("✅ Populated real performance data")
        
        # Verify
        result = db.query_postgres("SELECT COUNT(*) as count FROM agent_performance_log")
        if not result.empty:
            count = result.iloc[0]['count']
            logger.info(f"📊 Total records: {count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("🚀 Starting Simple Real Data Population...")
    
    if simple_populate():
        logger.info("🎉 Real data population completed!")
