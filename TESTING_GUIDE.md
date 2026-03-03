# 🧪 Agent Testing Guide

Complete guide to testing the multi-agent forex trading system.

---

## Quick Start

```bash
# Run full test suite
python test_agents.py

# Run quick interactive example
python quick_test_example.py
```

---

## 1. Command Line Testing

### Full Test Suite

```bash
python test_agents.py
```

**What it tests:**
- ✅ Technical Agent with RSI, MACD, Bollinger Bands, MA
- ✅ Fundamental Agent with economic indicators
- ✅ Sentiment Agent with news NLP
- ✅ Ensemble system with EURUSD, GBPUSD, USDJPY
- ✅ Conflict resolution (weighted vs majority)
- ✅ Performance metrics

**Expected output:**
```
🔵 TECHNICAL AGENT TEST
📈 Technical Agent Signal:
   Direction: BUY
   Confidence: 20.00%
   Reasoning: MACD histogram positive...
```

---

## 2. Python Interactive Testing

### Method A: Quick Script

```bash
python quick_test_example.py
```

### Method B: Python REPL

```python
from agents import EnsembleAgent
import pandas as pd

# Create ensemble
ensemble = EnsembleAgent(voting_method='weighted')

# Analyze (with your forex data)
signal = ensemble.analyze(symbol='EURUSD', forex_data=df)

# View results
print(f"{signal['direction']}: {signal['confidence']:.1%}")
```

### Method C: Test Individual Agents

```python
from agents import TechnicalAgent, FundamentalAgent, SentimentAgent

# Technical only
tech = TechnicalAgent(rsi_period=14)
tech_signal = tech.analyze(symbol='EURUSD', forex_data=df)

# Fundamental only
fund = FundamentalAgent()
fund_signal = fund.analyze(symbol='EURUSD', forex_data=df)

# Sentiment only
sent = SentimentAgent(lookback_days=7)
sent_signal = sent.analyze(symbol='EURUSD', forex_data=df)
```

---

## 3. Notebook Testing

### Add to Jupyter Notebook

```python
# Cell 1: Setup
import sys
sys.path.append('.')
from agents import EnsembleAgent
from influxdb_client import InfluxDBClient
import os
from dotenv import load_dotenv

load_dotenv()

# Cell 2: Fetch data
client = InfluxDBClient(
    url=os.getenv('INFLUXDB_URL'),
    token=os.getenv('INFLUXDB_TOKEN'),
    org=os.getenv('INFLUXDB_ORG')
)

query = f'''
from(bucket: "{os.getenv('INFLUXDB_BUCKET')}")
  |> range(start: -90d)
  |> filter(fn: (r) => r["_measurement"] == "forex")
  |> filter(fn: (r) => r["symbol"] == "EURUSD")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
'''

df = client.query_api().query_data_frame(query)
df = df.rename(columns={'_time': 'timestamp'})

# Cell 3: Test ensemble
ensemble = EnsembleAgent(voting_method='weighted')
signal = ensemble.analyze(symbol='EURUSD', forex_data=df)

print(f"📊 Signal: {signal['direction']}")
print(f"🎯 Confidence: {signal['confidence']:.1%}")
print(f"💡 Reasoning: {signal['reasoning']}")

# Cell 4: Visualize performance
perf = ensemble.get_ensemble_performance()
print(f"Agreement Rate: {perf['agreement_rate']:.1%}")
print(f"Avg Confidence: {perf['average_confidence']:.1%}")
```

---

## 4. Streamlit Dashboard Testing

### Add Agent Testing Tab

Create a new page in your Streamlit dashboard:

```python
# In app.py or new file pages/4_🤖_Agent_Testing.py

import streamlit as st
from agents import EnsembleAgent, TechnicalAgent, FundamentalAgent, SentimentAgent
from influxdb_client import InfluxDBClient
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

st.title("🤖 Multi-Agent Trading System")
st.markdown("Test and monitor trading agents in real-time")

# Sidebar configuration
st.sidebar.header("Agent Configuration")

voting_method = st.sidebar.selectbox(
    "Voting Method",
    ["weighted", "majority"],
    help="How to combine agent signals"
)

conflict_resolution = st.sidebar.selectbox(
    "Conflict Resolution",
    ["confidence", "priority"],
    help="How to resolve disagreements"
)

min_confidence = st.sidebar.slider(
    "Min Confidence Threshold",
    0.0, 1.0, 0.3,
    help="Minimum confidence to act"
)

# Currency pair selection
symbol = st.selectbox(
    "Currency Pair",
    ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
)

# Fetch data button
if st.button("🔍 Analyze", type="primary"):
    with st.spinner("Fetching forex data..."):
        # Connect to InfluxDB
        client = InfluxDBClient(
            url=os.getenv('INFLUXDB_URL', 'http://localhost:8086'),
            token=os.getenv('INFLUXDB_TOKEN'),
            org=os.getenv('INFLUXDB_ORG')
        )
        
        query = f'''
        from(bucket: "{os.getenv('INFLUXDB_BUCKET')}")
          |> range(start: -90d)
          |> filter(fn: (r) => r["_measurement"] == "forex")
          |> filter(fn: (r) => r["symbol"] == "{symbol}")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        
        forex_data = client.query_api().query_data_frame(query)
        
        if not forex_data.empty:
            forex_data = forex_data.rename(columns={'_time': 'timestamp'})
            
            # Test individual agents
            st.subheader("Individual Agent Signals")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 🔵 Technical")
                tech = TechnicalAgent()
                tech_signal = tech.analyze(symbol=symbol, forex_data=forex_data)
                
                direction_emoji = {"BUY": "📈", "SELL": "📉", "HOLD": "⏸️"}
                st.metric(
                    "Direction",
                    tech_signal['direction'],
                    delta=f"{tech_signal['confidence']:.1%}"
                )
                st.caption(tech_signal['reasoning'][:100] + "...")
            
            with col2:
                st.markdown("#### 🟢 Fundamental")
                fund = FundamentalAgent()
                fund_signal = fund.analyze(symbol=symbol, forex_data=forex_data)
                
                st.metric(
                    "Direction",
                    fund_signal['direction'],
                    delta=f"{fund_signal['confidence']:.1%}"
                )
                st.caption(fund_signal['reasoning'][:100] + "...")
            
            with col3:
                st.markdown("#### 🟡 Sentiment")
                sent = SentimentAgent()
                sent_signal = sent.analyze(symbol=symbol, forex_data=forex_data)
                
                st.metric(
                    "Direction",
                    sent_signal['direction'],
                    delta=f"{sent_signal['confidence']:.1%}"
                )
                st.caption(sent_signal['reasoning'][:100] + "...")
            
            # Ensemble decision
            st.divider()
            st.subheader("🎯 Ensemble Decision")
            
            ensemble = EnsembleAgent(
                voting_method=voting_method,
                conflict_resolution=conflict_resolution,
                min_confidence_threshold=min_confidence
            )
            
            ensemble_signal = ensemble.analyze(symbol=symbol, forex_data=forex_data)
            
            # Big decision display
            col1, col2 = st.columns([2, 1])
            
            with col1:
                direction = ensemble_signal['direction']
                confidence = ensemble_signal['confidence']
                
                if direction == "BUY":
                    st.success(f"📈 {direction}")
                elif direction == "SELL":
                    st.error(f"📉 {direction}")
                else:
                    st.info(f"⏸️ {direction}")
                
                st.markdown(f"**Confidence:** {confidence:.1%}")
                st.markdown(f"**Voting Method:** {voting_method}")
                st.markdown(f"**Reasoning:** {ensemble_signal['reasoning']}")
            
            with col2:
                # Performance metrics
                st.markdown("**Performance**")
                perf = ensemble.get_ensemble_performance()
                st.metric("Agreement", f"{perf['agreement_rate']:.0%}")
                st.metric("Avg Confidence", f"{perf['average_confidence']:.0%}")
            
            # Voting breakdown
            st.divider()
            st.subheader("⚖️ Voting Breakdown")
            
            voting_data = pd.DataFrame({
                'Agent': ['Technical', 'Fundamental', 'Sentiment'],
                'Direction': [
                    tech_signal['direction'],
                    fund_signal['direction'],
                    sent_signal['direction']
                ],
                'Confidence': [
                    tech_signal['confidence'],
                    fund_signal['confidence'],
                    sent_signal['confidence']
                ],
                'Weight': [0.4, 0.4, 0.2]
            })
            
            st.dataframe(
                voting_data,
                use_container_width=True,
                hide_index=True
            )
            
        else:
            st.error(f"❌ No data found for {symbol}")
        
        client.close()
```

To add this to your Streamlit app:

1. Create `pages/4_🤖_Agent_Testing.py` with the code above
2. Restart Streamlit: `streamlit run app.py`
3. New "Agent Testing" page will appear in sidebar

---

## 5. Automated Testing (CI/CD)

### pytest Integration

```bash
pip install pytest pytest-cov
```

Create `tests/test_agents_pytest.py`:

```python
import pytest
from agents import TechnicalAgent, FundamentalAgent, SentimentAgent, EnsembleAgent
import pandas as pd
import numpy as np

@pytest.fixture
def sample_forex_data():
    """Generate sample forex data for testing"""
    dates = pd.date_range(start='2026-01-01', periods=100, freq='1H')
    return pd.DataFrame({
        'timestamp': dates,
        'symbol': 'EURUSD',
        'open': np.random.uniform(1.08, 1.12, 100),
        'high': np.random.uniform(1.08, 1.12, 100),
        'low': np.random.uniform(1.08, 1.12, 100),
        'close': np.random.uniform(1.08, 1.12, 100),
        'volume': np.random.randint(1000, 10000, 100)
    })

def test_technical_agent_returns_signal(sample_forex_data):
    agent = TechnicalAgent()
    signal = agent.analyze(symbol='EURUSD', forex_data=sample_forex_data)
    
    assert signal['direction'] in ['BUY', 'SELL', 'HOLD']
    assert 0 <= signal['confidence'] <= 1
    assert 'reasoning' in signal

def test_ensemble_weighted_voting(sample_forex_data):
    ensemble = EnsembleAgent(voting_method='weighted')
    signal = ensemble.analyze(symbol='EURUSD', forex_data=sample_forex_data)
    
    assert signal['direction'] in ['BUY', 'SELL', 'HOLD']
    assert 0 <= signal['confidence'] <= 1

def test_ensemble_conflict_resolution(sample_forex_data):
    # Test both resolution methods
    confidence_ensemble = EnsembleAgent(conflict_resolution='confidence')
    priority_ensemble = EnsembleAgent(conflict_resolution='priority')
    
    sig1 = confidence_ensemble.analyze(symbol='EURUSD', forex_data=sample_forex_data)
    sig2 = priority_ensemble.analyze(symbol='EURUSD', forex_data=sample_forex_data)
    
    assert sig1['direction'] in ['BUY', 'SELL', 'HOLD']
    assert sig2['direction'] in ['BUY', 'SELL', 'HOLD']
```

Run with:
```bash
pytest tests/ -v --cov=agents
```

---

## 6. Performance Testing

### Load Testing

```python
# performance_test.py
import time
from agents import EnsembleAgent
import pandas as pd

def test_throughput():
    """Test how many signals per second"""
    ensemble = EnsembleAgent()
    
    # Generate sample data
    df = pd.DataFrame({
        'timestamp': pd.date_range('2026-01-01', periods=100, freq='1H'),
        'open': [1.10] * 100,
        'high': [1.11] * 100,
        'low': [1.09] * 100,
        'close': [1.10] * 100,
        'volume': [5000] * 100
    })
    
    # Time 100 signals
    start = time.time()
    for i in range(100):
        signal = ensemble.analyze(symbol='EURUSD', forex_data=df)
    end = time.time()
    
    throughput = 100 / (end - start)
    print(f"Throughput: {throughput:.2f} signals/second")

if __name__ == "__main__":
    test_throughput()
```

---

## 7. Debugging Failed Tests

### Enable Verbose Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from agents import EnsembleAgent

# Now all agent operations will log detailed info
ensemble = EnsembleAgent()
signal = ensemble.analyze(symbol='EURUSD', forex_data=df)
```

### Check Data Quality

```python
# Verify forex data before testing
print(f"Data shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"Missing values: {df.isnull().sum()}")
print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
```

---

## 8. Expected Test Results

### Phase 1 (Current - Bootstrap)

| Agent | Expected Signal | Confidence | Notes |
|-------|----------------|------------|-------|
| **Technical** | BUY/SELL | 10-30% | Working normally |
| **Fundamental** | HOLD | 0-30% | Needs 60 days data |
| **Sentiment** | HOLD | 0-20% | Low news volume |
| **Ensemble** | HOLD | 10-25% | Conservative |

### Phase 2 (After 60 days)

| Agent | Expected Signal | Confidence | Notes |
|-------|----------------|------------|-------|
| **Technical** | BUY/SELL | 40-70% | Full data |
| **Fundamental** | BUY/SELL | 50-80% | Trend analysis |
| **Sentiment** | BUY/SELL/HOLD | 30-60% | More news |
| **Ensemble** | BUY/SELL | 50-75% | High confidence |

---

## Troubleshooting

### ❌ "No forex data found"
**Solution:** Run data acquisition first
```bash
python acquire_mt5_data.py
```

### ❌ "Insufficient historical economic data"
**Solution:** Normal during bootstrap. Wait 60 days or backfill data

### ❌ "Connection refused" to InfluxDB/PostgreSQL
**Solution:** Start Docker containers
```bash
docker-compose up -d
```

### ❌ ImportError: No module named 'agents'
**Solution:** Run from project root directory
```bash
cd forex-alpha-data
python test_agents.py
```

---

## Best Practices

1. **Test regularly** - Run `test_agents.py` after any code changes
2. **Monitor performance** - Track confidence trends over time
3. **Compare voting methods** - Test weighted vs majority for your use case
4. **Validate with backtesting** - Coming in Phase 2
5. **Log all signals** - Keep history for analysis

---

## Next Steps

After testing Phase 1 agents, proceed to:

1. **Phase 2:** Enhanced feature engineering (ATR, Fibonacci, etc.)
2. **Phase 3:** XGBoost meta-learner training
3. **Phase 4:** MLOps integration (MLflow, Prometheus)
4. **Phase 5:** Production deployment (FastAPI, Docker)

See [PHASE1_STATUS.md](PHASE1_STATUS.md) for detailed roadmap.
