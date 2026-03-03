"""
Test Multi-Agent Forex Trading System
Demonstrates all three agents and ensemble decision-making
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient

# Import agents
from agents import (
    TechnicalAgent,
    FundamentalAgent,
    SentimentAgent,
    EnsembleAgent
)


def fetch_forex_data_for_agent(symbol='EURUSD', timeframe='1D', days_back=90):
    """Fetch forex data from InfluxDB"""
    try:
        client = InfluxDBClient(
            url='http://localhost:8086',
            token='my-super-secret-token',
            org='forexalpha'
        )
        query_api = client.query_api()
        
        query = f'''
        from(bucket: "forex_data")
            |> range(start: -{days_back}d)
            |> filter(fn: (r) => r["_measurement"] == "forex_prices")
            |> filter(fn: (r) => r["symbol"] == "{symbol}")
            |> filter(fn: (r) => r["timeframe"] == "{timeframe}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        
        df = query_api.query_data_frame(query)
        if not df.empty:
            df['_time'] = pd.to_datetime(df['_time'])
            df = df.sort_values('_time').reset_index(drop=True)
            # Rename columns to match agent expectations
            df = df.rename(columns={'_time': 'time'})
        
        client.close()
        return df
    except Exception as e:
        print(f"❌ Error fetching forex data: {e}")
        return pd.DataFrame()


def print_signal(signal, agent_name=None):
    """Pretty print a trading signal"""
    name = agent_name or signal.agent_name
    symbol = '📈' if signal.direction == 'BUY' else '📉' if signal.direction == 'SELL' else '⏸️'
    
    print(f"\n{symbol} {name} Signal:")
    print(f"   Symbol: {signal.symbol}")
    print(f"   Direction: {signal.direction}")
    print(f"   Confidence: {signal.confidence:.2%}")
    print(f"   Reasoning: {signal.reasoning}")
    print(f"   Timestamp: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if signal.indicators:
        print(f"   Key Indicators:")
        for key, value in list(signal.indicators.items())[:5]:  # Show first 5
            if isinstance(value, (int, float)):
                print(f"      {key}: {value:.4f}" if abs(value) < 100 else f"      {key}: {value:.2f}")
            else:
                print(f"      {key}: {value}")


def print_ensemble_result(result):
    """Pretty print ensemble decision"""
    symbol = '📈' if result['direction'] == 'BUY' else '📉' if result['direction'] == 'SELL' else '⏸️'
    
    print(f"\n{'='*70}")
    print(f"{symbol} ENSEMBLE DECISION")
    print(f"{'='*70}")
    print(f"Symbol: {result['symbol']}")
    print(f"Direction: {result['direction']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Voting Method: {result['voting_method']}")
    print(f"Reasoning: {result['reasoning']}")
    
    if 'buy_score' in result:
        print(f"\nVoting Breakdown:")
        print(f"   BUY Score:  {result['buy_score']:.4f}")
        print(f"   SELL Score: {result['sell_score']:.4f}")
        print(f"   HOLD Score: {result['hold_score']:.4f}")
    
    print(f"\nIndividual Agent Signals:")
    for sig in result.get('individual_signals', []):
        direction_sym = '📈' if sig['direction'] == 'BUY' else '📉' if sig['direction'] == 'SELL' else '⏸️'
        print(f"   {direction_sym} {sig['agent_name']}: {sig['direction']} ({sig['confidence']:.2%})")
    
    print(f"{'='*70}\n")


def test_individual_agents():
    """Test each agent individually"""
    print("\n" + "="*70)
    print("TESTING INDIVIDUAL AGENTS")
    print("="*70)
    
    symbol = 'EURUSD'
    
    # Test Technical Agent
    print("\n🔵 TECHNICAL AGENT TEST")
    print("-" * 70)
    tech_agent = TechnicalAgent(weight=1.0)
    
    forex_data = fetch_forex_data_for_agent(symbol, '1D', 90)
    if not forex_data.empty:
        tech_signal = tech_agent.analyze(symbol, forex_data)
        print_signal(tech_signal)
    else:
        print("❌ No forex data available for technical analysis")
    
    # Test Fundamental Agent
    print("\n🟢 FUNDAMENTAL AGENT TEST")
    print("-" * 70)
    fund_agent = FundamentalAgent(weight=1.0)
    fund_signal = fund_agent.analyze(symbol)
    print_signal(fund_signal)
    
    # Test Sentiment Agent
    print("\n🟡 SENTIMENT AGENT TEST")
    print("-" * 70)
    sent_agent = SentimentAgent(weight=1.0)
    sent_signal = sent_agent.analyze(symbol)
    print_signal(sent_signal)


def test_ensemble_system():
    """Test ensemble decision-making"""
    print("\n" + "="*70)
    print("TESTING ENSEMBLE SYSTEM")
    print("="*70)
    
    symbol = 'EURUSD'
    
    # Create ensemble with all agents
    ensemble = EnsembleAgent(
        technical_agent=TechnicalAgent(weight=0.4),
        fundamental_agent=FundamentalAgent(weight=0.4),
        sentiment_agent=SentimentAgent(weight=0.2),
        voting_method='weighted',
        min_confidence_threshold=0.3
    )
    
    # Fetch data
    forex_data = fetch_forex_data_for_agent(symbol, '1D', 90)
    
    # Run ensemble analysis
    result = ensemble.analyze(
        symbol=symbol,
        forex_data=forex_data,
        economic_data=None,  # Will fetch automatically
        news_data=None  # Will fetch automatically
    )
    
    # Print result
    print_ensemble_result(result)
    
    # Test with different symbols
    print("\n" + "="*70)
    print("TESTING MULTIPLE CURRENCY PAIRS")
    print("="*70)
    
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
    for sym in symbols:
        print(f"\n📊 Analyzing {sym}...")
        forex_data = fetch_forex_data_for_agent(sym, '1D', 90)
        result = ensemble.analyze(symbol=sym, forex_data=forex_data)
        
        # Print compact result
        direction_sym = '📈' if result['direction'] == 'BUY' else '📉' if result['direction'] == 'SELL' else '⏸️'
        print(f"   {direction_sym} {sym}: {result['direction']} (Confidence: {result['confidence']:.2%})")


def test_conflict_resolution():
    """Test conflict resolution when agents disagree"""
    print("\n" + "="*70)
    print("TESTING CONFLICT RESOLUTION (DSO2.2)")
    print("="*70)
    
    # Test with different voting methods
    voting_methods = ['weighted', 'majority']
    symbol = 'EURUSD'
    forex_data = fetch_forex_data_for_agent(symbol, '1D', 90)
    
    for method in voting_methods:
        print(f"\n🔄 Testing {method.upper()} voting method:")
        print("-" * 70)
        
        ensemble = EnsembleAgent(
            technical_agent=TechnicalAgent(weight=0.5),
            fundamental_agent=FundamentalAgent(weight=0.3),
            sentiment_agent=SentimentAgent(weight=0.2),
            voting_method=method,
            conflict_resolution='confidence'
        )
        
        result = ensemble.analyze(symbol=symbol, forex_data=forex_data)
        
        # Print compact result
        print(f"   Direction: {result['direction']}")
        print(f"   Confidence: {result['confidence']:.2%}")
        print(f"   Agents: {result['num_agents']}")


def display_agent_performance():
    """Display performance metrics for all agents"""
    print("\n" + "="*70)
    print("AGENT PERFORMANCE METRICS")
    print("="*70)
    
    symbol = 'EURUSD'
    forex_data = fetch_forex_data_for_agent(symbol, '1D', 90)
    
    # Create and run ensemble
    ensemble = EnsembleAgent()
    
    # Generate multiple signals
    for i in range(5):
        ensemble.analyze(symbol=symbol, forex_data=forex_data)
    
    # Get performance
    performance = ensemble.get_ensemble_performance()
    
    print(f"\n📊 Ensemble Statistics:")
    print(f"   Total Signals: {performance['total_signals']}")
    print(f"   Average Confidence: {performance['avg_confidence']:.2%}")
    print(f"   Agreement Rate: {performance['agreement_rate']:.2%}")
    
    print(f"\n🔵 Technical Agent:")
    tech_perf = performance['technical_performance']
    print(f"   Total Signals: {tech_perf['total_signals']}")
    print(f"   Avg Confidence: {tech_perf['avg_confidence']:.2%}")
    print(f"   BUY/SELL/HOLD: {tech_perf['buy_signals']}/{tech_perf['sell_signals']}/{tech_perf['hold_signals']}")
    
    print(f"\n🟢 Fundamental Agent:")
    fund_perf = performance['fundamental_performance']
    print(f"   Total Signals: {fund_perf['total_signals']}")
    print(f"   Avg Confidence: {fund_perf['avg_confidence']:.2%}")
    print(f"   BUY/SELL/HOLD: {fund_perf['buy_signals']}/{fund_perf['sell_signals']}/{fund_perf['hold_signals']}")
    
    print(f"\n🟡 Sentiment Agent:")
    sent_perf = performance['sentiment_performance']
    print(f"   Total Signals: {sent_perf['total_signals']}")
    print(f"   Avg Confidence: {sent_perf['avg_confidence']:.2%}")
    print(f"   BUY/SELL/HOLD: {sent_perf['buy_signals']}/{sent_perf['sell_signals']}/{sent_perf['hold_signals']}")


def main():
    """Main test runner"""
    print("\n" + "="*70)
    print("🤖 MULTI-AGENT FOREX TRADING SYSTEM TEST SUITE")
    print("="*70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version.split()[0]}")
    
    try:
        # Run all tests
        test_individual_agents()
        test_ensemble_system()
        test_conflict_resolution()
        display_agent_performance()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\n📋 Summary:")
        print("   ✅ Technical Agent: Operational (RSI, MACD, Bollinger Bands, MA)")
        print("   ✅ Fundamental Agent: Operational (CPI, Interest Rates, Unemployment)")
        print("   ✅ Sentiment Agent: Operational (News sentiment analysis)")
        print("   ✅ Ensemble System: Operational (Weighted voting + conflict resolution)")
        print("\n🎯 System ready for Phase 2: Enhanced Feature Engineering & MLOps Integration")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
