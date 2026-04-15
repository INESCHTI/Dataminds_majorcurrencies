"""
Test script for TokenFactory (Llama-3.1-70B) integration
Run this to verify the LLM connection is working
"""

import os
import sys

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.llm_factory_lightweight import TokenFactoryClient, LightweightLLMFactory, get_lightweight_llm

def test_tokenfactory_connection():
    """Test basic TokenFactory connectivity"""
    print("=" * 60)
    print("Testing TokenFactory Connection")
    print("=" * 60)
    
    client = TokenFactoryClient()
    
    if not client.enabled:
        print("❌ TokenFactory not configured")
        print("   Set TOKENFACTORY_API_KEY environment variable")
        return False
    
    print(f"✓ TokenFactory configured")
    print(f"  Base URL: {client.base_url}")
    print(f"  Model: {client.model}")
    
    # Test simple generation
    print("\nTesting simple text generation...")
    response = client.generate_text(
        prompt="What is 2+2? Answer with just the number.",
        max_tokens=50
    )
    
    if response:
        print(f"✓ Generation successful: {response.strip()}")
        return True
    else:
        print("❌ Generation failed")
        return False

def test_trading_explanation():
    """Test trading signal explanation generation"""
    print("\n" + "=" * 60)
    print("Testing Trading Explanation Generation")
    print("=" * 60)
    
    llm = get_lightweight_llm()
    
    # Sample signal data
    signal_data = {
        'pair': 'EURUSD',
        'signal': 1,  # BUY
        'confidence': 0.82,
        'agent_signals': {
            'TechnicalAgent': {'signal': 1, 'confidence': 0.85},
            'MacroAgent': {'signal': 1, 'confidence': 0.75},
            'SentimentAgent': {'signal': 0, 'confidence': 0.60}
        }
    }
    
    print("Generating explanation for EURUSD BUY signal (82% confidence)...")
    explanation = llm.generate_explanation(signal_data)
    
    print("\nGenerated Explanation:")
    print("-" * 60)
    print(explanation)
    print("-" * 60)
    
    if llm.use_llama_for_explanations:
        print("✓ Used Llama-3.1-70B via TokenFactory")
    else:
        print("⚠ Used template-based fallback")
    
    return True

def test_news_analysis():
    """Test news sentiment analysis"""
    print("\n" + "=" * 60)
    print("Testing News Analysis")
    print("=" * 60)
    
    llm = get_lightweight_llm()
    
    headline = "Fed Signals Potential Rate Cuts in 2024 Amid Cooling Inflation"
    content = "The Federal Reserve indicated it may cut interest rates next year as inflation shows signs of cooling..."
    
    print(f"Headline: {headline}")
    result = llm.analyze_news_with_llm(headline, content)
    
    print(f"\nAnalysis Result:")
    print(f"  Sentiment: {result.get('label')} ({result.get('score', 0):.2f})")
    print(f"  Impact: {result.get('impact', 'N/A')}")
    print(f"  Source: {result.get('source', 'unknown')}")
    
    insights = result.get('insights', [])
    if insights:
        print(f"  Key Insights:")
        for insight in insights:
            print(f"    - {insight}")
    
    return True

def test_tactical_report():
    """Test tactical report generation"""
    print("\n" + "=" * 60)
    print("Testing Tactical Report Generation")
    print("=" * 60)
    
    llm = get_lightweight_llm()
    
    pair = 'EURUSD'
    signals = [
        {'direction': 'BUY', 'confidence': 0.82, 'timestamp': '2024-01-15 10:00'},
        {'direction': 'BUY', 'confidence': 0.78, 'timestamp': '2024-01-15 14:00'},
        {'direction': 'NEUTRAL', 'confidence': 0.55, 'timestamp': '2024-01-15 18:00'},
    ]
    market_data = {
        'trend': 'Bullish',
        'volatility': 'Normal',
        'support': '1.0850',
        'resistance': '1.0950'
    }
    
    print(f"Generating tactical report for {pair}...")
    report = llm.generate_tactical_report(pair, signals, market_data)
    
    print("\nTactical Report:")
    print("-" * 60)
    print(report[:500] + "..." if len(report) > 500 else report)
    print("-" * 60)
    
    return True

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("TOKENFACTORY (LLAMA-3.1-70B) INTEGRATION TEST")
    print("=" * 60)
    
    # Load environment variables from .env file if exists
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        print(f"\nLoading environment from: {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key, value)
    
    results = []
    
    # Run tests
    results.append(("Connection", test_tokenfactory_connection()))
    results.append(("Trading Explanation", test_trading_explanation()))
    results.append(("News Analysis", test_news_analysis()))
    results.append(("Tactical Report", test_tactical_report()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n✓ All tests passed! TokenFactory integration is working.")
    else:
        print("\n⚠ Some tests failed. Check configuration and try again.")
        print("\nTroubleshooting:")
        print("  1. Verify TOKENFACTORY_API_KEY is set in .env file")
        print("  2. Get API key from: https://tokenfactory.esprit.tn")
        print("  3. Check your internet connection")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
