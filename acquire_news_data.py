# File: acquire_news_data.py

import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import time

load_dotenv()

POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

# Keywords to search for
KEYWORDS = ['forex', 'EUR', 'USD', 'JPY', 'GBP', 'CHF', 'Federal Reserve', 'ECB', 'currency']

def scrape_reuters_rss():
    """Scrape Reuters RSS feed for forex news"""
    print("=" * 60)
    print("NEWS DATA ACQUISITION")  
    print("=" * 60)
    
    articles = []
    
    # Reuters Business RSS
    rss_url = "https://www.reuters.com/rssFeed/businessNews"
    
    print(f"\n📰 Fetching Reuters RSS feed...")
    
    try:
        response = requests.get(rss_url, timeout=10)
        soup = BeautifulSoup(response.content, 'xml')
        
        items = soup.find_all('item')
        print(f"   Found {len(items)} articles")
        
        for item in items:
            title = item.find('title').text if item.find('title') else ''
            link = item.find('link').text if item.find('link') else ''
            pub_date = item.find('pubDate').text if item.find('pubDate') else ''
            description = item.find('description').text if item.find('description') else ''
            
            # Check if forex-related
            content = f"{title} {description}".lower()
            is_relevant = any(keyword.lower() in content for keyword in KEYWORDS)
            
            if is_relevant and link:
                # Identify currencies mentioned
                currencies = []
                for curr in ['EUR', 'USD', 'JPY', 'GBP', 'CHF']:
                    if curr in content.upper():
                        currencies.append(curr)
                
                articles.append({
                    'url': link,
                    'title': title,
                    'content': description,
                    'source': 'Reuters',
                    'published_at': pub_date,
                    'currencies': currencies,
                    'scraped_at': datetime.now()
                })
        
        print(f"   ✅ Found {len(articles)} forex-related articles")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return articles

def write_articles_to_postgres(articles):
    """Write articles to PostgreSQL"""
    if not articles:
        print("\n⚠️  No articles to write")
        return
    
    print(f"\n💾 Writing {len(articles)} articles to PostgreSQL...")
    
    conn_string = f"host={POSTGRES_HOST} port={POSTGRES_PORT} dbname={POSTGRES_DB} user={POSTGRES_USER} password={POSTGRES_PASSWORD}"
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    
    inserted = 0
    duplicates = 0
    
    try:
        for article in articles:
            try:
                cursor.execute(
                    """
                    INSERT INTO news_articles (url, title, content, source, published_at, currencies, scraped_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                    """,
                    (
                        article['url'],
                        article['title'],
                        article['content'],
                        article['source'],
                        article['published_at'],
                        article['currencies'],
                        article['scraped_at']
                    )
                )
                
                if cursor.rowcount > 0:
                    inserted += 1
                else:
                    duplicates += 1
                    
            except Exception as e:
                print(f"   ⚠️  Error inserting article: {e}")
        
        conn.commit()
        print(f"   ✅ Inserted {inserted} new articles")
        if duplicates > 0:
            print(f"   ℹ️  Skipped {duplicates} duplicates")
        
    except Exception as e:
        conn.rollback()
        print(f"   ❌ Write failed: {e}")
    finally:
        cursor.close()
        conn.close()

def main():
    # Scrape articles
    articles = scrape_reuters_rss()
    
    # Write to database
    write_articles_to_postgres(articles)
    
    print("\n" + "=" * 60)
    print("✅ NEWS DATA ACQUISITION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
