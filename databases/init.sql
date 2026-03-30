CREATE TABLE IF NOT EXISTS economic_indicators (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    series_id VARCHAR(50) NOT NULL,
    indicator_name VARCHAR(100),
    value DECIMAL(15,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(date, series_id)
);

CREATE INDEX idx_indicators_date ON economic_indicators(date DESC);

CREATE TABLE IF NOT EXISTS news_articles (
    article_id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    source VARCHAR(100),
    published_at TIMESTAMPTZ,
    currencies VARCHAR(3)[],
    scraped_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_articles_published ON news_articles(published_at DESC);

CREATE TABLE IF NOT EXISTS economic_events (
    event_id SERIAL PRIMARY KEY,
    event_date TIMESTAMPTZ NOT NULL,
    currency VARCHAR(3) NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    importance VARCHAR(10),
    forecast DECIMAL(15,4),
    actual DECIMAL(15,4),
    previous DECIMAL(15,4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_date ON economic_events(event_date DESC);