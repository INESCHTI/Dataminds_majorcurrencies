"""
Debug Database Connection and Data
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

logger = logging.getLogger(__name__)


def debug_database():
    """Debug database connection and data"""
    db = DatabaseManager()
    
    try:
        # Test connection
        logger.info("🔍 Testing database connection...")
        
        # Check if table exists and count records
        result = db.query_postgres("""
            SELECT COUNT(*) as count FROM agent_performance_log
        """)
        
        if not result.empty:
            count = result.iloc[0]['count']
            logger.info(f"📊 Current record count: {count}")
            
            # Show table structure
            structure = db.query_postgres("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'agent_performance_log'
                ORDER BY ordinal_position
            """)
            
            if not structure.empty:
                logger.info("📋 Table structure:")
                for _, row in structure.iterrows():
                    logger.info(f"  {row['column_name']}: {row['data_type']}")
            
            # Try a simple insert
            logger.info("🧪 Testing simple insert...")
            
            try:
                with db.get_postgres_connection() as conn:
                    cursor = conn.cursor()
                    # Use direct SQL without formatting
                    sql = """
                        INSERT INTO agent_performance_log 
                        (agent_name, symbol, timestamp, pnl, confidence, was_correct, signal, reasoning)
                        VALUES ('TestAgent', 'EURUSD', NOW(), 1.0, 0.8, True, 'BUY', 'Test signal')
                    """
                    cursor.execute(sql)
                    conn.commit()
                    logger.info("✅ Test insert successful")
                    
            except Exception as e:
                logger.error(f"❌ Test insert failed: {e}")
            
            # Check count again
            result2 = db.query_postgres("""
                SELECT COUNT(*) as count FROM agent_performance_log
            """)
            
            if not result2.empty:
                count2 = result2.iloc[0]['count']
                logger.info(f"📊 Record count after test: {count2}")
        
    except Exception as e:
        logger.error(f"❌ Debug error: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    debug_database()
