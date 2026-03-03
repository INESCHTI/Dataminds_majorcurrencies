"""
Quick example: Test agents interactively
Run this in Python console or as script
"""

from agents import TechnicalAgent, FundamentalAgent, SentimentAgent, EnsembleAgent
from influxdb_client import InfluxDBClient
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to InfluxDB
client = InfluxDBClient(
    url=os.getenv('INFLUXDB_URL', 'http://localhost:8086'),
    token=os.getenv('INFLUXDB_TOKEN'),
    org=os.getenv('INFLUXDB_ORG')
)

# Fetch recent forex data
query = f'''
from(bucket: "{os.getenv('INFLUXDB_BUCKET')}")
  |> range(start: -90d)
  |> filter(fn: (r) => r["_measurement"] == "forex")
  |> filter(fn: (r) => r["symbol"] == "EURUSD")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
'''

query_api = client.query_api()
result = query_api.query_data_frame(query)

if not result.empty:
    forex_data = result.rename(columns={'_time': 'timestamp'})
    
    # Test 1: Technical Agent
    print("=" * 60)
    print("🔵 TECHNICAL AGENT")
    print("=" * 60)
    tech_agent = TechnicalAgent()
    tech_signal = tech_agent.analyze(symbol='EURUSD', forex_data=forex_data)
    print(f"Direction: {tech_signal['direction']}")
    print(f"Confidence: {tech_signal['confidence']:.2%}")
    print(f"Reasoning: {tech_signal['reasoning']}")
    
    # Test 2: Ensemble (all agents)
    print("\n" + "=" * 60)
    print("🎯 ENSEMBLE SYSTEM")
    print("=" * 60)
    ensemble = EnsembleAgent(voting_method='weighted')
    ensemble_signal = ensemble.analyze(symbol='EURUSD', forex_data=forex_data)
    print(f"Direction: {ensemble_signal['direction']}")
    print(f"Confidence: {ensemble_signal['confidence']:.2%}")
    print(f"Reasoning: {ensemble_signal['reasoning']}")
    
    # Test 3: Compare voting methods
    print("\n" + "=" * 60)
    print("⚖️ VOTING METHOD COMPARISON")
    print("=" * 60)
    
    weighted = EnsembleAgent(voting_method='weighted')
    majority = EnsembleAgent(voting_method='majority')
    
    w_signal = weighted.analyze(symbol='EURUSD', forex_data=forex_data)
    m_signal = majority.analyze(symbol='EURUSD', forex_data=forex_data)
    
    print(f"Weighted: {w_signal['direction']} ({w_signal['confidence']:.2%})")
    print(f"Majority: {m_signal['direction']} ({m_signal['confidence']:.2%})")

else:
    print("❌ No forex data found. Run acquire_mt5_data.py first.")

client.close()
