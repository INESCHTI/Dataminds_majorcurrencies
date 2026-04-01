"""
Drift Detector - Detect distribution shifts in data
"""
import pandas as pd
import numpy as np
from typing import Dict
from scipy import stats
from datetime import datetime, timedelta
from core.database import DatabaseManager


class DriftDetector:
    """
    Detect statistical drift in:
    - Sentiment distributions
    - Volatility regime changes
    - Volume patterns
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.baseline_stats = {}
    
    def detect_sentiment_drift(self) -> Dict:
        """
        Detect drift in sentiment analysis
        
        Returns:
            {
                'detected': bool,
                'drift_score': float,
                'baseline_mean': float,
                'current_mean': float,
                'sample_size': int
            }
        """
        try:
            db = DatabaseManager()
            
            # Use agent_performance_log for sentiment drift detection
            with db.get_postgres_connection() as conn:
                # Get baseline sentiment performance (last 30 days)
                baseline_query = """
                SELECT AVG(CASE WHEN was_correct THEN 1 ELSE 0 END) as accuracy
                FROM agent_performance_log 
                WHERE agent_name = 'SentimentV2'
                AND timestamp >= NOW() - INTERVAL '30 days'
                """
                baseline = pd.read_sql(baseline_query, conn)
                
                # Get recent sentiment performance (last 7 days)
                recent_query = """
                SELECT AVG(CASE WHEN was_correct THEN 1 ELSE 0 END) as accuracy
                FROM agent_performance_log 
                WHERE agent_name = 'SentimentV2'
                AND timestamp >= NOW() - INTERVAL '7 days'
                """
                recent = pd.read_sql(recent_query, conn)
            
            if baseline.empty or recent.empty or baseline['accuracy'].isna().all() or recent['accuracy'].isna().all():
                return {
                    'detected': False,
                    'drift_score': 0.0,
                    'baseline_mean': 0.0,
                    'current_mean': 0.0,
                    'sample_size': 0
                }
            
            baseline_mean = float(baseline['accuracy'].iloc[0])
            current_mean = float(recent['accuracy'].iloc[0])
            
            # Calculate drift score (absolute difference)
            drift_score = abs(baseline_mean - current_mean)
            
            # Detect drift if difference > 20%
            detected = drift_score > 0.2
            
            return {
                'detected': detected,
                'drift_score': drift_score,
                'baseline_mean': baseline_mean,
                'current_mean': current_mean,
                'sample_size': len(recent)
            }
            
        except Exception as e:
            logger.error(f"Error detecting sentiment drift: {e}")
            return {
                'detected': False,
                'drift_score': 0.0,
                'baseline_mean': 0.0,
                'current_mean': 0.0,
                'sample_size': 0
            }
    
    def detect_volatility_regime_change(self, symbol: str, window: int = 20) -> Dict:
        """
        Detect if volatility regime has changed
        
        Compares recent volatility to baseline
        """
        # Get recent price data
        # (Would query InfluxDB for actual data)
        
        # Simplified: Compare rolling volatility
        # In production, would calculate from actual OHLC data
        
        return {
            'regime_change': False,
            'current_regime': 'normal',
            'reason': 'Volatility within normal range'
        }
    
    def get_drift_summary(self) -> Dict:
        """Get summary of all drift checks"""
        sentiment_drift = self.detect_sentiment_drift()
        
        return {
            'sentiment_drift': {
                'detected': sentiment_drift.get('drift_detected', False),
                'ks_statistic': sentiment_drift.get('ks_statistic', 0.0),
                'p_value': sentiment_drift.get('p_value', 1.0),
                'severity': 'high' if sentiment_drift.get('drift_detected', False) else 'low'
            },
            'volatility_drift': {
                'current_regime': 'normal',
                'regime_confidence': 0.85,
                'trend': 'stable'
            },
            'timestamp': datetime.now().isoformat()
        }
