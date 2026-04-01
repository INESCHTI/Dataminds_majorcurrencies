#!/usr/bin/env python3
"""
Database Setup Script for FX Alpha Platform
Starts and configures all required databases
"""

import os
import sys
import subprocess
import time
import psycopg2
from influxdb_client import InfluxDBClient
import redis

def check_postgres_connection():
    """Test PostgreSQL connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', '5433')),
            database=os.getenv('POSTGRES_DB', 'forex_metadata'),
            user=os.getenv('POSTGRES_USER', 'forex_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'forex_pass')
        )
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ PostgreSQL connected: {version[0]}")
            
            # Create required tables if they don't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading_signals_log (
                    id SERIAL PRIMARY KEY,
                    pair VARCHAR(10) NOT NULL,
                    direction VARCHAR(10) NOT NULL,
                    confidence FLOAT NOT NULL,
                    agent_votes JSONB,
                    reasoning TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_performance_log (
                    id SERIAL PRIMARY KEY,
                    agent_name VARCHAR(50) NOT NULL,
                    pair VARCHAR(10) NOT NULL,
                    signal_direction VARCHAR(10) NOT NULL,
                    confidence FLOAT NOT NULL,
                    was_correct BOOLEAN,
                    pnl FLOAT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_articles (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT,
                    source VARCHAR(100),
                    url VARCHAR(500),
                    published_at TIMESTAMP,
                    sentiment_score FLOAT,
                    currencies TEXT[],
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS macro_indicators (
                    id SERIAL PRIMARY KEY,
                    indicator_name VARCHAR(100) NOT NULL,
                    currency VARCHAR(3) NOT NULL,
                    value FLOAT NOT NULL,
                    date DATE NOT NULL,
                    source VARCHAR(100),
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

def check_influx_connection():
    """Test InfluxDB connection"""
    try:
        client = InfluxDBClient(
            url=os.getenv('INFLUX_URL', 'http://localhost:8088'),
            token=os.getenv('INFLUX_TOKEN', 'my-super-secret-token'),
            org=os.getenv('INFLUX_ORG', 'forex_org')
        )
        
        health = client.health()
        if health.status == "pass":
            print(f"✅ InfluxDB connected: {health.message}")
            
            # Create bucket if it doesn't exist
            buckets_api = client.buckets_api()
            bucket_name = os.getenv('INFLUX_BUCKET', 'forex_data')
            
            try:
                bucket = buckets_api.find_bucket_by_name(bucket_name)
                if bucket:
                    print(f"✅ Bucket '{bucket_name}' exists")
                else:
                    print(f"⚠️  Bucket '{bucket_name}' not found, creating...")
                    # Bucket creation would require admin permissions
                    print("   Please create bucket manually in InfluxDB UI")
            except:
                print(f"⚠️  Could not verify bucket '{bucket_name}'")
            
            client.close()
            return True
        else:
            print(f"❌ InfluxDB health check failed: {health.message}")
            return False
            
    except Exception as e:
        print(f"❌ InfluxDB connection failed: {e}")
        return False

def check_redis_connection():
    """Test Redis connection"""
    try:
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6380')),
            decode_responses=True
        )
        
        r.ping()
        info = r.info()
        print(f"✅ Redis connected: v{info['redis_version']}")
        
        # Test basic operations
        r.set('test_key', 'test_value', ex=10)
        value = r.get('test_key')
        if value == 'test_value':
            print("✅ Redis read/write test passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def start_docker_services():
    """Start Docker services"""
    print("🐳 Starting Docker services...")
    try:
        subprocess.run(['docker-compose', 'up', '-d'], check=True)
        print("✅ Docker services started")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Docker services: {e}")
        return False
    except FileNotFoundError:
        print("❌ Docker not found. Please install Docker and Docker Compose")
        return False

def main():
    """Main setup function"""
    print("🚀 FX Alpha Platform - Database Setup")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Step 1: Start Docker services
    if not start_docker_services():
        print("\n❌ Cannot proceed without Docker services")
        sys.exit(1)
    
    # Wait for services to be ready
    print("\n⏳ Waiting for services to start...")
    time.sleep(10)
    
    # Step 2: Test connections
    print("\n🔍 Testing database connections...")
    
    postgres_ok = check_postgres_connection()
    influx_ok = check_influx_connection()
    redis_ok = check_redis_connection()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Setup Summary:")
    print(f"PostgreSQL: {'✅' if postgres_ok else '❌'}")
    print(f"InfluxDB:   {'✅' if influx_ok else '❌'}")
    print(f"Redis:      {'✅' if redis_ok else '❌'}")
    
    if all([postgres_ok, influx_ok, redis_ok]):
        print("\n🎉 All databases are ready!")
        print("You can now start the Django backend:")
        print("   cd backend && python manage.py runserver")
    else:
        print("\n⚠️  Some services are not ready. Check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
