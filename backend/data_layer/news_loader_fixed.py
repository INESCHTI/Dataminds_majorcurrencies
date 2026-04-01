"""
Fixed News Data Loader - Simplified for reliable operation
Works with existing news_articles table structure
"""
from datetime import datetime, timedelta
from typing import Optional, List
import pandas as pd
from core.database import DatabaseManager


class NewsLoader:
    """Load news articles from PostgreSQL - Fixed version"""
    
    def __init__(self):
        pass
    
    def load_news(
        self,
        currencies: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Load news articles with simplified query
        """
        if start_time is None:
            start_time = datetime.now() - timedelta(days=7)
        if end_time is None:
            end_time = datetime.now()
        
        try:
            with DatabaseManager.get_postgres_connection() as conn:
                # Simplified query without JSONB operations
                query = """
                SELECT 
                    article_id as id,
                    published_at as timestamp,
                    title,
                    content,
                    source,
                    sentiment_score,
                    mentioned_currencies as currencies
                FROM news_articles
                WHERE published_at BETWEEN %s AND %s
                ORDER BY published_at DESC
                LIMIT %s
                """
                df = pd.read_sql(query, conn, params=(start_time, end_time, limit))
                
                # Filter by currencies in Python if needed
                if currencies and not df.empty:
                    mask = df['currencies'].astype(str).str.contains(
                        '|'.join(currencies), na=False
                    )
                    df = df[mask]
                
                return df
        except Exception as e:
            print(f"Error loading news: {e}")
            return pd.DataFrame(columns=['id', 'timestamp', 'title', 'content', 'source', 'currencies', 'sentiment_score'])

    def latest_timestamp(self) -> Optional[datetime]:
        """Return the most recent news publication timestamp."""
        try:
            with DatabaseManager.get_postgres_connection() as conn:
                query = "SELECT MAX(published_at) AS last_ts FROM news_articles"
                df = pd.read_sql(query, conn)
                if df.empty or df.loc[0, 'last_ts'] is None:
                    return None
                return pd.to_datetime(df.loc[0, 'last_ts']).to_pydatetime()
        except Exception as e:
            print(f"Error getting latest timestamp: {e}")
            return None

    def get_freshness_health(self, freshness_target_minutes: int = 240) -> dict:
        """Compute freshness KPIs for news ingestion."""
        try:
            with DatabaseManager.get_postgres_connection() as conn:
                now = datetime.now()
                
                # Articles in last hour
                hour_ago = now - timedelta(hours=1)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM news_articles WHERE published_at >= %s",
                    (hour_ago,)
                )
                articles_last_1h = cursor.fetchone()[0]
                
                # Articles in last 24 hours
                day_ago = now - timedelta(hours=24)
                cursor.execute(
                    "SELECT COUNT(*) FROM news_articles WHERE published_at >= %s",
                    (day_ago,)
                )
                articles_last_24h = cursor.fetchone()[0]
                
                # Latest article
                cursor.execute(
                    "SELECT MAX(published_at) FROM news_articles"
                )
                latest_ts = cursor.fetchone()[0]
                
                if latest_ts:
                    age_minutes = (now - latest_ts).total_seconds() / 60
                    if age_minutes <= freshness_target_minutes:
                        status = "PASS"
                    elif age_minutes <= freshness_target_minutes * 2:
                        status = "WARN"
                    else:
                        status = "NO_DATA"
                    freshness_score = max(0, 100 - (age_minutes / freshness_target_minutes) * 100)
                else:
                    status = "NO_DATA"
                    age_minutes = None
                    freshness_score = 0.0
                
                return {
                    'status': status,
                    'last_news_timestamp': latest_ts.isoformat() if latest_ts else None,
                    'age_minutes': age_minutes,
                    'articles_last_1h': articles_last_1h,
                    'articles_last_24h': articles_last_24h,
                    'freshness_score': freshness_score,
                    'target_max_age_minutes': freshness_target_minutes
                }
        except Exception as e:
            print(f"Error computing freshness health: {e}")
            return {
                'status': 'NO_DATA',
                'last_news_timestamp': None,
                'age_minutes': None,
                'articles_last_1h': 0,
                'articles_last_24h': 0,
                'freshness_score': 0.0,
                'target_max_age_minutes': freshness_target_minutes
            }
