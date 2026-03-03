"""
Fundamental Agent (DSO1.1)
Analyzes macroeconomic indicators to determine forex market direction
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import subprocess
import io
from .base_agent import BaseAgent, Signal


class FundamentalAgent(BaseAgent):
    """
    Fundamental Analysis Agent
    Analyzes economic indicators: CPI, Fed Funds Rate, Unemployment, GDP, etc.
    """
    
    def __init__(self, 
                 name: str = "Fundamental Agent",
                 weight: float = 1.0,
                 cpi_weight: float = 0.3,
                 interest_rate_weight: float = 0.4,
                 unemployment_weight: float = 0.2,
                 gdp_weight: float = 0.1):
        """
        Initialize Fundamental Agent
        
        Args:
            name: Agent name
            weight: Agent weight in ensemble
            cpi_weight: Weight for CPI indicator
            interest_rate_weight: Weight for interest rate
            unemployment_weight: Weight for unemployment rate
            gdp_weight: Weight for GDP growth
        """
        super().__init__(name, weight)
        self.cpi_weight = cpi_weight
        self.interest_rate_weight = interest_rate_weight
        self.unemployment_weight = unemployment_weight
        self.gdp_weight = gdp_weight
        
        # Normalization parameters (will be updated with real data)
        self.normalization_params = {
            'cpi': {'mean': 3.0, 'std': 1.5},
            'interest_rate': {'mean': 4.0, 'std': 2.0},
            'unemployment': {'mean': 4.0, 'std': 1.0},
            'gdp_growth': {'mean': 2.5, 'std': 1.5}
        }
    
    def get_required_data(self) -> List[str]:
        """Required economic indicator columns"""
        return ['date', 'indicator_name', 'value']
    
    def fetch_economic_data(self) -> pd.DataFrame:
        """
        Fetch economic indicators from PostgreSQL via Docker
        
        Returns:
            DataFrame with economic indicators
        """
        try:
            result = subprocess.run(
                ['docker', 'exec', 'forex-postgres', 'psql', '-U', 'forex_user', 
                 '-d', 'forex_metadata',
                 '-c', 'COPY (SELECT * FROM economic_indicators ORDER BY date DESC LIMIT 100) TO STDOUT WITH CSV HEADER'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                df = pd.read_csv(io.StringIO(result.stdout))
                df['date'] = pd.to_datetime(df['date'])
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching economic data: {e}")
            return pd.DataFrame()
    
    def normalize_indicator(self, value: float, indicator_name: str) -> float:
        """
        Normalize indicator value to standard scale
        
        Args:
            value: Raw indicator value
            indicator_name: Name of indicator
            
        Returns:
            Normalized value (z-score)
        """
        if indicator_name.lower() not in self.normalization_params:
            return 0.0
        
        params = self.normalization_params[indicator_name.lower()]
        return (value - params['mean']) / params['std']
    
    def calculate_cpi_impact(self, current_cpi: float, previous_cpi: float) -> float:
        """
        Calculate CPI impact on currency
        Higher CPI (inflation) typically strengthens currency (hawkish policy)
        
        Returns:
            Score from -1 (very bearish) to +1 (very bullish)
        """
        cpi_change = current_cpi - previous_cpi
        
        if cpi_change > 0.3:  # High inflation acceleration
            return 0.8  # Bullish - likely rate hikes
        elif cpi_change > 0.1:
            return 0.4
        elif cpi_change > -0.1:
            return 0.0  # Neutral
        elif cpi_change > -0.3:
            return -0.4
        else:
            return -0.8  # Bearish - deflationary pressures
    
    def calculate_interest_rate_impact(self, current_rate: float, previous_rate: float) -> float:
        """
        Calculate interest rate impact on currency
        Higher rates attract foreign capital (bullish)
        
        Returns:
            Score from -1 to +1
        """
        rate_change = current_rate - previous_rate
        
        if rate_change > 0.25:  # Rate hike
            return 1.0  # Very bullish
        elif rate_change > 0:
            return 0.6
        elif rate_change == 0:
            # Check absolute level
            if current_rate > 5.0:
                return 0.5  # High rates are bullish
            elif current_rate < 2.0:
                return -0.5  # Low rates are bearish
            return 0.0
        elif rate_change > -0.25:
            return -0.6
        else:
            return -1.0  # Rate cut - bearish
    
    def calculate_unemployment_impact(self, current_unemp: float, previous_unemp: float) -> float:
        """
        Calculate unemployment impact on currency
        Lower unemployment = stronger economy = bullish
        
        Returns:
            Score from -1 to +1
        """
        unemp_change = current_unemp - previous_unemp
        
        if unemp_change < -0.5:  # Strong job growth
            return 0.8
        elif unemp_change < -0.2:
            return 0.4
        elif unemp_change < 0.2:
            return 0.0
        elif unemp_change < 0.5:
            return -0.4
        else:
            return -0.8  # Rising unemployment - bearish
    
    def analyze(self, symbol: str, data: Optional[pd.DataFrame] = None, **kwargs) -> Signal:
        """
        Analyze economic indicators and generate fundamental signal
        
        Args:
            symbol: Currency pair (e.g., 'EURUSD')
            data: Optional economic data DataFrame. If None, fetches from database
            
        Returns:
            Signal with BUY/SELL/HOLD recommendation
        """
        # Fetch data if not provided
        if data is None or data.empty:
            data = self.fetch_economic_data()
        
        if data.empty:
            return Signal(
                timestamp=datetime.now(),
                symbol=symbol,
                direction='HOLD',
                confidence=0.0,
                agent_name=self.name,
                reasoning="No economic data available",
                indicators={}
            )
        
        # Extract currency from symbol (first 3 chars for base currency)
        base_currency = symbol[:3] if len(symbol) >= 6 else 'USD'
        
        # Filter for most recent data
        recent_date = data['date'].max()
        cutoff_date = recent_date - timedelta(days=60)
        recent_data = data[data['date'] >= cutoff_date]
        
        # Pivot data for easier analysis
        pivot_data = recent_data.pivot_table(
            index='date',
            columns='indicator_name',
            values='value',
            aggfunc='first'
        ).sort_index(ascending=False)
        
        if len(pivot_data) < 2:
            return Signal(
                timestamp=datetime.now(),
                symbol=symbol,
                direction='HOLD',
                confidence=0.3,
                agent_name=self.name,
                reasoning="Insufficient historical economic data",
                indicators={}
            )
        
        # Get current and previous values
        current_row = pivot_data.iloc[0]
        previous_row = pivot_data.iloc[1]
        
        # Calculate individual impacts
        impacts = []
        reasoning_parts = []
        indicator_values = {}
        
        # CPI Analysis
        if 'CPI' in current_row and 'CPI' in previous_row:
            cpi_impact = self.calculate_cpi_impact(
                current_row['CPI'], 
                previous_row['CPI']
            ) * self.cpi_weight
            impacts.append(cpi_impact)
            indicator_values['cpi_current'] = float(current_row['CPI'])
            indicator_values['cpi_previous'] = float(previous_row['CPI'])
            indicator_values['cpi_change'] = float(current_row['CPI'] - previous_row['CPI'])
            
            if abs(cpi_impact) > 0.1:
                direction_str = "rising" if cpi_impact > 0 else "falling"
                reasoning_parts.append(f"CPI {direction_str} ({current_row['CPI']:.2f}%)")
        
        # Interest Rate Analysis
        if 'Fed Funds Rate' in current_row and 'Fed Funds Rate' in previous_row:
            rate_impact = self.calculate_interest_rate_impact(
                current_row['Fed Funds Rate'],
                previous_row['Fed Funds Rate']
            ) * self.interest_rate_weight
            impacts.append(rate_impact)
            indicator_values['interest_rate_current'] = float(current_row['Fed Funds Rate'])
            indicator_values['interest_rate_previous'] = float(previous_row['Fed Funds Rate'])
            indicator_values['interest_rate_change'] = float(
                current_row['Fed Funds Rate'] - previous_row['Fed Funds Rate']
            )
            
            if abs(rate_impact) > 0.15:
                direction_str = "hawkish" if rate_impact > 0 else "dovish"
                reasoning_parts.append(
                    f"Interest rate {direction_str} ({current_row['Fed Funds Rate']:.2f}%)"
                )
        
        # Unemployment Analysis
        if 'Unemployment Rate' in current_row and 'Unemployment Rate' in previous_row:
            unemp_impact = self.calculate_unemployment_impact(
                current_row['Unemployment Rate'],
                previous_row['Unemployment Rate']
            ) * self.unemployment_weight
            impacts.append(unemp_impact)
            indicator_values['unemployment_current'] = float(current_row['Unemployment Rate'])
            indicator_values['unemployment_previous'] = float(previous_row['Unemployment Rate'])
            indicator_values['unemployment_change'] = float(
                current_row['Unemployment Rate'] - previous_row['Unemployment Rate']
            )
            
            if abs(unemp_impact) > 0.08:
                direction_str = "improving" if unemp_impact > 0 else "deteriorating"
                reasoning_parts.append(
                    f"Employment {direction_str} ({current_row['Unemployment Rate']:.1f}%)"
                )
        
        # Aggregate impacts
        if not impacts:
            return Signal(
                timestamp=datetime.now(),
                symbol=symbol,
                direction='HOLD',
                confidence=0.2,
                agent_name=self.name,
                reasoning="Insufficient indicator coverage",
                indicators=indicator_values
            )
        
        total_impact = sum(impacts)
        avg_impact = total_impact / len(impacts)
        
        # Determine signal
        if avg_impact > 0.15:
            direction = 'BUY'
            confidence = min(abs(avg_impact), 1.0)
            reasoning = f"Fundamental outlook bullish for {base_currency}: " + ", ".join(reasoning_parts)
        elif avg_impact < -0.15:
            direction = 'SELL'
            confidence = min(abs(avg_impact), 1.0)
            reasoning = f"Fundamental outlook bearish for {base_currency}: " + ", ".join(reasoning_parts)
        else:
            direction = 'HOLD'
            confidence = 0.5 - abs(avg_impact)
            reasoning = f"Fundamental outlook neutral for {base_currency}: " + ", ".join(reasoning_parts)
        
        indicator_values['aggregate_score'] = float(avg_impact)
        indicator_values['num_indicators'] = len(impacts)
        
        signal = Signal(
            timestamp=datetime.now(),
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            agent_name=self.name,
            reasoning=reasoning,
            indicators=indicator_values
        )
        
        self.record_signal(signal)
        return signal
