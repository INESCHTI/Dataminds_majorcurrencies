import requests
import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
dotenv_path = os.path.join(project_root, 'config', '.env')
load_dotenv(dotenv_path=dotenv_path, override=True)

POSTGRES_HOST     = os.getenv('POSTGRES_HOST')
POSTGRES_PORT     = os.getenv('POSTGRES_PORT')
POSTGRES_DB       = os.getenv('POSTGRES_DB')
POSTGRES_USER     = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
NEWSAPI_KEY       = os.getenv('NEWSAPI_KEY')

KEYWORDS = ['forex', 'EUR', 'USD', 'JPY', 'GBP', 'CHF', 'Federal Reserve', 'ECB', 'currency', 'exchange rate']

def scrape_newsapi():
    print(f"\n📰 Fetching from NewsAPI...")
    articles = []
    if not NEWSAPI_KEY:
        print(f"   ❌ NEWSAPI_KEY not found in .env file")
        return articles
    try:
        url = 'https://newsapi.org/v2/everything'
        params = {
            'q': 'forex currency exchange rate',
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': 30,
            'apiKey': NEWSAPI_KEY
        }
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, params=params, timeout=10, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'error':
                print(f"   ❌ NewsAPI Error: {data.get('message')}")
                return articles
            items = data.get('articles', [])
            print(f"   📄 Articles found: {len(items)}")
            for item in items:
                title       = item.get('title', '')
                item_url    = item.get('url', '')
                pub_date    = item.get('publishedAt', '')
                description = item.get('description', '')
                combined_text = f"{title} {description}".strip()
                content_lower = combined_text.lower()
                is_relevant = any(k.lower() in content_lower for k in KEYWORDS)
                if is_relevant and item_url:
                    currencies = [c for c in ['EUR', 'USD', 'JPY', 'GBP', 'CHF'] if c in combined_text.upper()]
                    articles.append({
                        'url':          item_url,
                        'title':        title[:500],
                        'content':      combined_text[:2000],
                        'source':       'NewsAPI',
                        'published_at': pub_date,
                        'currencies':   currencies,
                        'scraped_at':   datetime.now()
                    })
            print(f"   ✅ Found {len(articles)} forex-related articles")
        else:
            print(f"   ❌ Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
    return articles

def get_sample_news_articles():
    now = datetime.now()
    ts  = str(int(now.timestamp()))
    return [
        {
            'title':        'EUR/USD rises as ECB signals higher rates ahead',
            'url':          f'https://example.com/eur-usd-ecb-{ts}',
            'content':      'The EUR/USD exchange rate climbed to 1.18 as the ECB indicated potential rate hikes',
            'source':       'SampleData',
            'published_at': now.isoformat(),
            'currencies':   ['EUR', 'USD'],
            'scraped_at':   now   # ← FIXED
        },
        {
            'title':        'USD/JPY strengthens on Federal Reserve hawkish stance',
            'url':          f'https://example.com/usd-jpy-fed-{ts}',
            'content':      'USD/JPY reaches 145.50 as the Federal Reserve maintains its tight monetary policy',
            'source':       'SampleData',
            'published_at': now.isoformat(),
            'currencies':   ['USD', 'JPY'],
            'scraped_at':   now   # ← FIXED
        },
        {
            'title':        'GBP/USD volatility increases amid negotiations',
            'url':          f'https://example.com/gbp-usd-{ts}',
            'content':      'The GBP/USD pair shows increased volatility as traders await economic data',
            'source':       'SampleData',
            'published_at': now.isoformat(),
            'currencies':   ['GBP', 'USD'],
            'scraped_at':   now   # ← FIXED
        },
        {
            'title':        'Forex market awaits inflation data release',
            'url':          f'https://example.com/forex-inflation-{ts}',
            'content':      'Major currency pairs trading sideways as traders await inflation announcements',
            'source':       'SampleData',
            'published_at': now.isoformat(),
            'currencies':   ['EUR', 'USD', 'JPY'],
            'scraped_at':   now   # ← FIXED
        },
        {
            'title':        'Central banks coordinate on currency stability',
            'url':          f'https://example.com/central-banks-{ts}',
            'content':      'G7 central banks discuss forex market stability and coordinate policy',
            'source':       'SampleData',
            'published_at': now.isoformat(),
            'currencies':   ['EUR', 'USD', 'GBP', 'CHF'],
            'scraped_at':   now   # ← FIXED
        }
    ]

def write_articles_to_postgres(articles):
    if not articles:
        print("\n⚠️  No articles to write")
        return
    print(f"\n💾 Writing {len(articles)} articles to PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        inserted   = 0
        duplicates = 0
        for article in articles:
            def safe_utf8(val):
                if isinstance(val, str):
                    return val.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
                return val
            try:
                cursor.execute(
                    """
                    INSERT INTO news_articles (url, title, content, source, published_at, currencies, scraped_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                    """,
                    (
                        safe_utf8(article['url']),
                        safe_utf8(article['title']),
                        safe_utf8(article['content']),
                        safe_utf8(article['source']),
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
                print(f"   ⚠️  Row error: {e}")
        conn.commit()
        print(f"   ✅ Inserted {inserted} new articles")
        if duplicates > 0:
            print(f"   ℹ️  Skipped {duplicates} duplicates")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"   ❌ Database error: {e}")

def main():
    print("=" * 60)
    print("NEWS DATA ACQUISITION")
    print("=" * 60)
    articles = scrape_newsapi()
    if not articles:
        print("\n⚠️  No live data available, using sample data...")
        articles = get_sample_news_articles()
    write_articles_to_postgres(articles)
    print("\n" + "=" * 60)
    print("✅ NEWS DATA ACQUISITION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()