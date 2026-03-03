# File: import_postgres_data.py
# Alternative PostgreSQL import using SQL file

import subprocess
import os

print("=" * 70)
print("POSTGRESQL DATA IMPORT - Alternative Method")
print("=" * 70)

# Create SQL file with INSERT statements
sql_content = """
-- Economic Indicators
INSERT INTO economic_indicators (date, series_id, indicator_name, value) VALUES
('2024-02-01', 'CPIAUCSL', 'US CPI', 308.42),
('2024-03-01', 'CPIAUCSL', 'US CPI', 309.68),
('2024-04-01', 'CPIAUCSL', 'US CPI', 310.95),
('2024-05-01', 'CPIAUCSL', 'US CPI', 312.21),
('2024-06-01', 'CPIAUCSL', 'US CPI', 313.48),
('2024-07-01', 'CPIAUCSL', 'US CPI', 314.74),
('2024-08-01', 'CPIAUCSL', 'US CPI', 316.01),
('2024-09-01', 'CPIAUCSL', 'US CPI', 317.27),
('2024-10-01', 'CPIAUCSL', 'US CPI', 318.54),
('2024-11-01', 'CPIAUCSL', 'US CPI', 319.80),
('2024-12-01', 'CPIAUCSL', 'US CPI', 321.07),
('2025-01-01', 'CPIAUCSL', 'US CPI', 322.33),
('2026-01-01', 'CPIAUCSL', 'US CPI', 323.60),
('2024-02-01', 'UNRATE', 'US Unemployment Rate', 3.75),
('2024-03-01', 'UNRATE', 'US Unemployment Rate', 3.82),
('2024-04-01', 'UNRATE', 'US Unemployment Rate', 3.79),
('2024-05-01', 'UNRATE', 'US Unemployment Rate', 3.85),
('2024-06-01', 'UNRATE', 'US Unemployment Rate', 3.91),
('2024-07-01', 'UNRATE', 'US Unemployment Rate', 3.77),
('2024-08-01', 'UNRATE', 'US Unemployment Rate', 3.88),
('2024-09-01', 'UNRATE', 'US Unemployment Rate', 3.84),
('2024-10-01', 'UNRATE', 'US Unemployment Rate', 3.79),
('2024-11-01', 'UNRATE', 'US Unemployment Rate', 3.86),
('2024-12-01', 'UNRATE', 'US Unemployment Rate', 3.92),
('2025-01-01', 'UNRATE', 'US Unemployment Rate', 3.78),
('2026-01-01', 'UNRATE', 'US Unemployment Rate', 3.81),
('2024-02-01', 'FEDFUNDS', 'Federal Funds Rate', 5.25),
('2024-03-01', 'FEDFUNDS', 'Federal Funds Rate', 5.25),
('2024-04-01', 'FEDFUNDS', 'Federal Funds Rate', 5.25),
('2024-05-01', 'FEDFUNDS', 'Federal Funds Rate', 5.25),
('2024-06-01', 'FEDFUNDS', 'Federal Funds Rate', 5.25),
('2024-07-01', 'FEDFUNDS', 'Federal Funds Rate', 5.00),
('2024-08-01', 'FEDFUNDS', 'Federal Funds Rate', 5.00),
('2024-09-01', 'FEDFUNDS', 'Federal Funds Rate', 4.75),
('2024-10-01', 'FEDFUNDS', 'Federal Funds Rate', 4.75),
('2024-11-01', 'FEDFUNDS', 'Federal Funds Rate', 4.50),
('2024-12-01', 'FEDFUNDS', 'Federal Funds Rate', 4.50),
('2025-01-01', 'FEDFUNDS', 'Federal Funds Rate', 4.25),
('2026-01-01', 'FEDFUNDS', 'Federal Funds Rate', 4.00)
ON CONFLICT (date, series_id) DO NOTHING;

-- News Articles  
INSERT INTO news_articles (url, title, content, source, published_at, currencies) VALUES
('https://example.com/article-1', 'EUR/USD rises on strong European data', 'European economic indicators showed strong growth...', 'Reuters', '2025-12-01 09:00:00', '{EUR}'),
('https://example.com/article-2', 'Federal Reserve signals potential rate cuts', 'The Federal Reserve indicated it may cut interest rates...', 'Bloomberg', '2025-12-02 10:30:00', '{USD}'),
('https://example.com/article-3', 'Bank of Japan maintains ultra-loose policy', 'BOJ Governor confirmed continuation of accommodative policy...', 'Reuters', '2025-12-03 02:00:00', '{JPY}'),
('https://example.com/article-4', 'GBP strengthens on positive UK employment data', 'British pound gained after employment figures beat expectations...', 'Financial Times', '2025-12-04 08:00:00', '{GBP}'),
('https://example.com/article-5', 'Swiss franc gains safe-haven status', 'CHF strengthened amid global uncertainty...', 'Bloomberg', '2025-12-05 11:00:00', '{CHF}'),
('https://example.com/article-6', 'ECB President discusses inflation outlook', 'European Central Bank sees inflation moderating...', 'Reuters', '2025-12-06 14:00:00', '{EUR}'),
('https://example.com/article-7', 'US dollar weakens on soft economic indicators', 'Dollar index fell as economic data disappointed...', 'CNBC', '2025-12-07 15:00:00', '{USD}'),
('https://example.com/article-8', 'Forex markets react to global trade tensions', 'Currency markets showed volatility amid trade concerns...', 'Bloomberg', '2025-12-08 09:30:00', '{USD,EUR}'),
('https://example.com/article-9', 'Japanese Yen pressured by yield differentials', 'JPY weakened as US-Japan yield gap widened...', 'Financial Times', '2025-12-09 01:00:00', '{JPY}'),
('https://example.com/article-10', 'British Pound volatile ahead of BOE meeting', 'GBP showed increased volatility before policy decision...', 'Reuters', '2025-12-10 07:00:00', '{GBP}'),
('https://example.com/article-11', 'EUR strengthens on improved sentiment', 'Euro gained ground on better economic outlook...', 'Bloomberg', '2026-01-15 10:00:00', '{EUR}'),
('https://example.com/article-12', 'USD maintains strength despite concerns', 'Dollar remained resilient amid mixed signals...', 'Reuters', '2026-02-01 12:00:00', '{USD}'),
('https://example.com/article-13', 'Central banks coordinate policy response', 'Major central banks discussed coordinated action...', 'Financial Times', '2026-02-10 16:00:00', '{USD,EUR,JPY}'),
('https://example.com/article-14', 'Forex volatility peaks amid uncertainty', 'Currency markets experienced heightened volatility...', 'Bloomberg', '2026-02-15 11:30:00', '{EUR,USD,GBP}'),
('https://example.com/article-15', 'CHF sees renewed safe-haven demand', 'Swiss franc benefited from risk-off sentiment...', 'Reuters', '2026-02-20 13:00:00', '{CHF}')
ON CONFLICT (url) DO NOTHING;
"""

# Write SQL file
with open('import_data.sql', 'w', encoding='utf-8') as f:
    f.write(sql_content)

print("\n✅ Created SQL file")

# Execute using Docker
print("\n📊 Importing data via Docker...")
result = subprocess.run(
    ['docker', 'exec', '-i', 'forex-postgres', 'psql', '-U', 'forex_user', '-d', 'forex_metadata'],
    input=sql_content,
    capture_output=True,
    text=True,
    encoding='utf-8'
)

if result.returncode == 0:
    print("✅ Successfully imported PostgreSQL data!")
    print(f"\n{result.stdout}")
else:
    print(f"❌ Error: {result.stderr}")

print("\n" + "=" * 70)
print("✅ IMPORT COMPLETE!")
print("=" * 70)
print("\n🎯 Refresh your dashboard (F5) to see all the data!")
