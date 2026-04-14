"""
Macro Data Loader - Pure data retrieval from PostgreSQL
Reads from macro_indicators table (unified schema)
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import pandas as pd
from core.database import DatabaseManager


class MacroDataLoader:
    """Load macroeconomic data from PostgreSQL macro_indicators table"""
    
    def __init__(self):
        pass
    
    def load_interest_rates(
        self,
        currencies: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Load central bank interest rates from economic_indicators
        
        Returns:
            DataFrame with columns: date, currency, rate
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now()
        
        try:
            with DatabaseManager.get_postgres_connection() as conn:
                # Map series IDs to currencies and indicator types
                series_mapping = {
                    'FEDFUNDS': 'USD',
                    'DFF': 'USD'
                }
                
                # Build query for FRED data
                currency_series = []
                for currency in currencies:
                    if currency == 'USD':
                        currency_series.extend(['FEDFUNDS', 'DFF'])
                    # Add more currency mappings as needed
                
                if not currency_series:
                    return pd.DataFrame(columns=['date', 'currency', 'rate'])
                
                query = """
                SELECT date, value as rate, series_id
                FROM economic_indicators
                WHERE series_id = ANY(%s)
                AND date BETWEEN %s AND %s
                ORDER BY date, series_id
                """
                df = pd.read_sql(query, conn, params=(currency_series, start_date, end_date))
                
                # Map series_id back to currency
                df['currency'] = df['series_id'].map(series_mapping)
                df = df.dropna(subset=['currency'])
                
                return df[['date', 'currency', 'rate']]
        except Exception as e:
            print(f"Error loading interest rates: {e}")
            return pd.DataFrame(columns=['date', 'currency', 'rate'])
    
    def load_inflation_rates(
        self,
        currencies: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Load CPI/inflation data from economic_indicators"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now()
        
        try:
            with DatabaseManager.get_postgres_connection() as conn:
                # Map series IDs to currencies and indicator types
                series_mapping = {
                    'CPIAUCSL': 'USD',
                }
                
                # Build query for FRED data
                currency_series = []
                for currency in currencies:
                    if currency == 'USD':
                        currency_series.append('CPIAUCSL')
                    # Add more currency mappings as needed
                
                if not currency_series:
                    return pd.DataFrame(columns=['date', 'currency', 'inflation_rate'])
                
                query = """
                SELECT date, value as inflation_rate, series_id
                FROM economic_indicators
                WHERE series_id = ANY(%s)
                AND date BETWEEN %s AND %s
                ORDER BY date, series_id
                """
                df = pd.read_sql(query, conn, params=(currency_series, start_date, end_date))
                
                # Map series_id back to currency
                df['currency'] = df['series_id'].map(series_mapping)
                df = df.dropna(subset=['currency'])
                
                return df[['date', 'currency', 'inflation_rate']]
        except Exception as e:
            print(f"Error loading inflation rates: {e}")
            return pd.DataFrame(columns=['date', 'currency', 'inflation_rate'])
    
    def load_gdp_data(
        self,
        currencies: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Load GDP growth data from economic_indicators"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=730)
        if end_date is None:
            end_date = datetime.now()
        
        try:
            with DatabaseManager.get_postgres_connection() as conn:
                # Map series IDs to currencies and indicator types
                series_mapping = {
                    'GDP': 'USD',
                }
                
                # Build query for FRED data
                currency_series = []
                for currency in currencies:
                    if currency == 'USD':
                        currency_series.append('GDP')
                    # Add more currency mappings as needed
                
                if not currency_series:
                    return pd.DataFrame(columns=['date', 'currency', 'gdp_growth_rate'])
                
                query = """
                SELECT date, value as gdp_growth_rate, series_id
                FROM economic_indicators
                WHERE series_id = ANY(%s)
                AND date BETWEEN %s AND %s
                ORDER BY date, series_id
                """
                df = pd.read_sql(query, conn, params=(currency_series, start_date, end_date))
                
                # Map series_id back to currency
                df['currency'] = df['series_id'].map(series_mapping)
                df = df.dropna(subset=['currency'])
                
                return df[['date', 'currency', 'gdp_growth_rate']]
        except Exception as e:
            print(f"Error loading GDP data: {e}")
            return pd.DataFrame(columns=['date', 'currency', 'gdp_growth_rate'])
