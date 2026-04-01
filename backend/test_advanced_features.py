#!/usr/bin/env python
"""
Test script for Advanced Features
LLM Integration, Pattern Recognition, RL Optimization, Multi-Timezone
"""
import os
import sys
import numpy as np
from datetime import datetime, timedelta

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

def test_llm_integration():
    """Test LLM Central Bank Analysis"""
    print("🤖 Testing LLM Central Bank Analysis")
    print("=" * 50)
    
    from ai_layer.llm_central_bank_analyzer import create_llm_analyzer
    
    # Create analyzer
    analyzer = create_llm_analyzer()
    
    print(f"🔧 LLM Analyzer created")
    print(f"   Model: {analyzer.model}")
    print(f"   API Key configured: {'Yes' if analyzer.api_key else 'No (using mock)'}")
    
    # Create sample statements
    statements = analyzer.create_sample_statements()
    print(f"\n📝 Sample Statements: {len(statements)}")
    
    for i, stmt in enumerate(statements, 1):
        print(f"   {i}. {stmt.bank} - {stmt.statement_type}")
    
    # Analyze statements
    print(f"\n🧠 Analyzing Statements...")
    results = analyzer.analyze_multiple_statements(statements)
    
    print(f"📊 Analysis Results:")
    for result in results:
        print(f"   {result.bank}: {result.policy_bias} ({result.confidence:.1%})")
        print(f"      Rate Outlook: {result.rate_outlook}")
        print(f"      Market Impact: {result.market_impact}")
        print(f"      Key Points: {len(result.key_points)}")
    
    # Get currency impacts
    currency_impacts = analyzer.get_currency_impact(results)
    print(f"\n💰 Currency Impacts:")
    for currency, impact in currency_impacts.items():
        print(f"   {currency}: {impact['overall_bias']} ({impact['confidence']:.1%})")
        print(f"      Market Impact: {impact['market_impact']}")
        print(f"      Rate Outlook: {impact['rate_outlook']}")
    
    print(f"\n✅ LLM Integration Test Completed!")

def test_pattern_recognition():
    """Test Chart Pattern Recognition"""
    print("\n📈 Testing Chart Pattern Recognition")
    print("=" * 50)
    
    from ai_layer.chart_pattern_recognition import create_pattern_recognizer
    import pandas as pd
    import numpy as np
    
    # Create recognizer
    recognizer = create_pattern_recognizer()
    print(f"🔧 Pattern Recognizer created")
    print(f"   Pattern detectors: {len(recognizer.pattern_detectors)}")
    
    # Generate sample data
    print(f"\n📊 Generating Sample Chart Data...")
    
    # Create 200 candles
    timestamps = [datetime.now() - timedelta(hours=i) for i in range(200, 0, -1)]
    
    # Generate price data with patterns
    base_price = 1.0850
    prices = [base_price]
    
    for i in range(199):
        # Add some trend and noise
        trend = 0.0001 * np.sin(i / 20)  # Sinusoidal trend
        noise = np.random.normal(0, 0.001)
        price_change = trend + noise
        prices.append(prices[-1] * (1 + price_change))
    
    # Create OHLC data
    ohlc_data = []
    for i in range(len(prices)):
        intraday_vol = np.random.normal(0, 0.0002, 4)
        
        high = prices[i] * (1 + abs(intraday_vol[0]))
        low = prices[i] * (1 - abs(intraday_vol[1]))
        
        ohlc_data.append({
            'timestamp': timestamps[i],
            'open': prices[i],
            'high': high,
            'low': low,
            'close': prices[i],
            'volume': np.random.randint(1000000, 10000000)
        })
    
    df = pd.DataFrame(ohlc_data)
    print(f"   Data points: {len(df)}")
    print(f"   Price range: {df['close'].min():.5f} - {df['close'].max():.5f}")
    
    # Analyze patterns
    print(f"\n🔍 Analyzing Patterns...")
    result = recognizer.analyze_chart('EURUSD', df, '1H')
    
    print(f"📈 Pattern Recognition Results:")
    print(f"   Overall Sentiment: {result.overall_sentiment}")
    print(f"   Confidence: {result.confidence:.1%}")
    print(f"   Patterns Detected: {len(result.patterns)}")
    
    for pattern in result.patterns:
        print(f"   {pattern.pattern_type}: {pattern.direction} ({pattern.confidence:.1%})")
        print(f"      Description: {pattern.description}")
        print(f"      Price Level: {pattern.price_level:.5f}")
    
    print(f"   Analysis Summary: {result.analysis_summary}")
    print(f"   Chart Image Generated: {'Yes' if result.chart_image else 'No'}")
    
    print(f"\n✅ Pattern Recognition Test Completed!")

def test_rl_optimization():
    """Test RL Weight Optimization"""
    print("\n🎮 Testing RL Weight Optimization")
    print("=" * 50)
    
    from ai_layer.rl_weight_optimizer import create_advanced_optimizer
    
    # Create optimizer
    optimizer = create_advanced_optimizer()
    print(f"🔧 Advanced Optimizer created")
    print(f"   Available strategies: {list(optimizer.optimization_strategies.keys())}")
    
    # Simulate agent performance updates
    print(f"\n📊 Updating Agent Performance...")
    
    agents = ['technical', 'macro', 'sentiment', 'geopolitical']
    
    for round_num in range(1, 6):
        print(f"   Round {round_num}:")
        
        # Simulate performance data
        for agent in agents:
            # Random performance between -0.1 and 0.1
            performance = np.random.uniform(-0.1, 0.1)
            confidence = np.random.uniform(0.5, 0.9)
            
            optimizer.rl_optimizer.update_agent_performance(agent, performance, confidence)
            
            # Get current performance
            if agent in optimizer.rl_optimizer.agents:
                perf = optimizer.rl_optimizer.agents[agent]
                print(f"     {agent}: {performance:+.3f} (conf: {confidence:.2f})")
        
        # Simulate portfolio metrics
        portfolio_return = np.random.uniform(-0.02, 0.03)
        sharpe_ratio = np.random.uniform(-0.5, 2.0)
        max_drawdown = np.random.uniform(0.0, 0.05)
        win_rate = np.random.uniform(0.3, 0.8)
        
        # Optimize weights
        weights = optimizer.optimize_weights(
            strategy='rl',
            portfolio_return=portfolio_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate
        )
        
        print(f"   Optimized Weights: {weights}")
        print(f"   Portfolio Return: {portfolio_return:+.3f}")
    
    # Get optimization stats
    print(f"\n📈 Optimization Statistics:")
    stats = optimizer.get_optimizer_stats()
    
    print(f"   Current Strategy: {stats['current_strategy']}")
    print(f"   Optimization Rounds: {stats['rl_stats']['optimization_rounds']}")
    print(f"   Average Reward: {stats['rl_stats']['avg_reward']:.4f}")
    print(f"   Best Reward: {stats['rl_stats']['best_reward']:.4f}")
    print(f"   Performance Trend: {stats['rl_stats']['performance_trend']}")
    
    print(f"   Strategy Performance:")
    for strategy, perf in stats['strategy_performance'].items():
        print(f"     {strategy}: {perf['avg_performance']:.4f} (samples: {perf['sample_size']})")
    
    print(f"   Agent Performances:")
    for agent, perf in stats['rl_stats']['agent_performances'].items():
        print(f"     {agent}:")
        print(f"       Success Rate: {perf['success_rate']:.1%}")
        print(f"       Avg Confidence: {perf['avg_confidence']:.2f}")
        print(f"       Current Weight: {perf['current_weight']:.3f}")
    
    print(f"\n✅ RL Optimization Test Completed!")

def test_multi_timezone():
    """Test Multi-Timezone Optimization"""
    print("\n🌍 Testing Multi-Timezone Optimization")
    print("=" * 50)
    
    from ai_layer.timezone_optimizer import create_timezone_optimizer
    
    # Create optimizer
    optimizer = create_timezone_optimizer()
    print(f"🔧 Multi-Timezone Optimizer created")
    print(f"   Trading Sessions: {list(optimizer.sessions.keys())}")
    print(f"   Session Overlaps: {list(optimizer.session_overlaps.keys())}")
    
    # Get current session
    print(f"\n🕐 Current Trading Sessions:")
    current_sessions = optimizer.get_current_session()
    overlap = optimizer.get_session_overlap()
    
    print(f"   Active Sessions: {current_sessions}")
    print(f"   Session Overlap: {overlap}")
    
    # Test session characteristics
    print(f"\n📊 Session Characteristics:")
    for session_name in current_sessions:
        characteristics = optimizer.get_session_characteristics(session_name, 'EURUSD')
        print(f"   {session_name}:")
        print(f"     Liquidity: {characteristics.get('liquidity', 'unknown')}")
        print(f"     Volatility Multiplier: {characteristics.get('volatility_multiplier', 1.0)}")
        print(f"     Volume Multiplier: {characteristics.get('volume_multiplier', 1.0)}")
        print(f"     Currency Relevance: {characteristics.get('currency_relevance', 'unknown')}")
    
    # Update session performance
    print(f"\n📈 Updating Session Performance...")
    
    for session_name in optimizer.sessions.keys():
        # Simulate performance data
        return_pct = np.random.uniform(-0.01, 0.02)
        sharpe_ratio = np.random.uniform(-0.5, 1.5)
        max_drawdown = np.random.uniform(0.0, 0.03)
        volatility = np.random.uniform(0.005, 0.02)
        
        optimizer.update_session_performance(
            'EURUSD', session_name, return_pct, sharpe_ratio, max_drawdown, volatility
        )
        
        print(f"   {session_name}: {return_pct:+.3f} (Sharpe: {sharpe_ratio:.2f})")
    
    # Get session recommendations
    print(f"\n💡 Session Recommendations:")
    recommendations = optimizer.get_session_recommendations('EURUSD')
    
    print(f"   Current Time: {recommendations['current_time']}")
    print(f"   Active Sessions: {recommendations['active_sessions']}")
    print(f"   Session Weights: {recommendations['session_weights']}")
    
    for rec in recommendations['recommendations']:
        print(f"   {rec['session']}: {rec['action']} (Risk: {rec['risk_level']})")
        print(f"     Weight: {rec['weight']:.3f}")
        print(f"     Optimal Strategies: {', '.join(rec['optimal_strategies'])}")
    
    if recommendations.get('overlap_recommendation'):
        overlap_rec = recommendations['overlap_recommendation']
        print(f"   Overlap: {overlap_rec['description']}")
        print(f"     Action: {overlap_rec['action']}")
        print(f"     Risk Adjustment: {overlap_rec['risk_adjustment']}")
    
    # Optimize session weights
    print(f"\n⚖️ Optimized Session Weights:")
    weights = optimizer.optimize_session_weights('EURUSD')
    
    for session, weight in weights.items():
        print(f"   {session}: {weight:.3f}")
    
    # Get session statistics
    print(f"\n📊 Session Statistics:")
    stats = optimizer.get_session_statistics()
    
    print(f"   Total Currency Pairs: {stats['optimization_summary']['total_currency_pairs']}")
    print(f"   Total Trades Analyzed: {stats['optimization_summary']['total_trades_analyzed']}")
    print(f"   Last Optimization: {stats['optimization_summary']['last_optimization']}")
    
    print(f"\n✅ Multi-Timezone Test Completed!")

def main():
    """Run all advanced features tests"""
    print("🚀 Starting Advanced Features Tests")
    print("=" * 60)
    
    try:
        test_llm_integration()
        test_pattern_recognition()
        test_rl_optimization()
        test_multi_timezone()
        
        print("\n🎉 All Advanced Features Tests Completed Successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
