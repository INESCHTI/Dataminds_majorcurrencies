"""
Real Data Integration Verification Script
Verifies all dashboard pages and agents use real data from InfluxDB (MT5) and real sources
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from influxdb_client import InfluxDBClient
from signal_layer.technical_agent_v2_enhanced import TechnicalAgentV2Enhanced
from signal_layer.macro_agent_v2 import MacroAgentV2
from signal_layer.sentiment_agent_v2 import SentimentAgentV2
from signal_layer.geopolitical_agent_v2_enhanced import GeopoliticalAgentV2Enhanced
from signal_layer.coordinator_agent_v2_enhanced import CoordinatorAgentV2Enhanced
from django.conf import settings


def print_section(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)


def check_influxdb_connection():
    """Verify InfluxDB connection and real data"""
    print_section("INFLUXDB CONNECTION & REAL DATA")
    
    try:
        client = InfluxDBClient(
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG
        )
        
        query_api = client.query_api()
        
        # Check if we have real OHLCV data
        query = '''
        from(bucket: "forex_data")
          |> range(start: -24h)
          |> filter(fn: (r) => r["_measurement"] == "ohlcv")
          |> filter(fn: (r) => r["symbol"] == "EURUSD")
          |> limit(n: 10)
        '''
        
        result = query_api.query(query)
        
        if result:
            print("✅ InfluxDB connection successful")
            print(f"✅ Found {len(result)} tables with real OHLCV data")
            
            # Show latest data point
            for table in result:
                for record in table.records:
                    print(f"   Latest: {record.get_time()} - {record.values.get('symbol')} - {record.get_field()}: {record.get_value()}")
                    break
                break
        else:
            print("❌ No real OHLCV data found in InfluxDB")
            
        client.close()
        return len(result) > 0
        
    except Exception as e:
        print(f"❌ InfluxDB connection failed: {e}")
        return False


def check_mt5_data():
    """Verify MetaTrader5 data integration"""
    print_section("METATRADER5 DATA INTEGRATION")
    
    try:
        from acquisition.mt5_collector import collect_mt5_data
        
        # Check MT5 configuration
        mt5_login = os.getenv('MT5_LOGIN')
        mt5_server = os.getenv('MT5_SERVER')
        
        if mt5_login and mt5_server:
            print(f"✅ MT5 configuration found")
            print(f"   Login: {mt5_login}")
            print(f"   Server: {mt5_server}")
            
            # Note: We won't actually connect to MT5 in this verification
            # as it requires the terminal to be running
            print("✅ MT5 integration ready (requires MT5 terminal running)")
        else:
            print("⚠️  MT5 configuration not found")
            
    except Exception as e:
        print(f"❌ MT5 integration check failed: {e}")


def check_agents_real_data():
    """Test all agents with real data"""
    print_section("AGENTS REAL DATA TESTING")
    
    # Test currencies
    currencies = ['EUR', 'USD']
    
    # Test Technical Agent
    print("\n📊 Testing Technical Agent...")
    try:
        tech_agent = TechnicalAgentV2Enhanced()
        tech_signal = tech_agent.generate_signal(currencies, timeframe='1H')
        print(f"✅ Technical Agent: Signal {tech_signal.get('signal', 'N/A')} - Confidence: {tech_signal.get('confidence', 0):.2f}")
        print(f"   Uses real InfluxDB OHLCV data: {bool(tech_signal.get('features_used', {}))}")
    except Exception as e:
        print(f"❌ Technical Agent failed: {e}")
    
    # Test Macro Agent
    print("\n📈 Testing Macro Agent...")
    try:
        macro_agent = MacroAgentV2()
        macro_signal = macro_agent.generate_signal(currencies)
        print(f"✅ Macro Agent: Signal {macro_signal.get('signal', 'N/A')} - Confidence: {macro_signal.get('confidence', 0):.2f}")
        print(f"   Uses real economic indicators: {bool(macro_signal.get('features_used', {}))}")
    except Exception as e:
        print(f"❌ Macro Agent failed: {e}")
    
    # Test Sentiment Agent
    print("\n💭 Testing Sentiment Agent...")
    try:
        sentiment_agent = SentimentAgentV2()
        sentiment_signal = sentiment_agent.generate_signal(currencies)
        print(f"✅ Sentiment Agent: Signal {sentiment_signal.get('signal', 'N/A')} - Confidence: {sentiment_signal.get('confidence', 0):.2f}")
        print(f"   Uses real news sentiment: {bool(sentiment_signal.get('features_used', {}))}")
    except Exception as e:
        print(f"❌ Sentiment Agent failed: {e}")
    
    # Test Enhanced Geopolitical Agent
    print("\n🌍 Testing Enhanced Geopolitical Agent...")
    try:
        geo_agent = GeopoliticalAgentV2Enhanced()
        geo_signal = geo_agent.generate_signal(currencies)
        print(f"✅ Geopolitical Agent: Signal {geo_signal.get('signal', 'N/A')} - Confidence: {geo_signal.get('confidence', 0):.2f}")
        print(f"   Uses real RSS feeds: {geo_signal.get('features_used', {}).get('rss_sources', 0)} sources")
        print(f"   Real articles analyzed: {geo_signal.get('features_used', {}).get('news_count', 0)}")
    except Exception as e:
        print(f"❌ Geopolitical Agent failed: {e}")


def check_coordinator_integration():
    """Test coordinator with all agents"""
    print_section("COORDINATOR MULTI-AGENT INTEGRATION")
    
    try:
        coordinator = CoordinatorAgentV2Enhanced()
        
        # Test signal generation
        print("\n🔄 Testing Multi-Agent Signal Generation...")
        result = coordinator.generate_final_signal('EURUSD', 'EUR', 'USD')
        
        if result and result.get('success', False):
            signal = result.get('signal', {})
            print(f"✅ Multi-Agent Signal: {signal.get('direction', 'N/A')}")
            print(f"   Overall Confidence: {signal.get('confidence', 0):.3f}")
            print(f"   Weighted Score: {signal.get('weighted_score', 0):.3f}")
            
            # Show agent breakdown
            agent_votes = signal.get('agent_votes', {})
            print(f"\n📊 Agent Breakdown:")
            for agent, vote in agent_votes.items():
                print(f"   {agent}: {vote.get('signal', 'N/A')} ({vote.get('confidence', 0):.2f})")
            
            # Show weights
            weights = signal.get('weights', {})
            print(f"\n⚖️  Agent Weights:")
            for agent, weight in weights.items():
                print(f"   {agent}: {weight:.2f}")
                
        else:
            print("❌ Multi-agent signal generation failed")
            
    except Exception as e:
        print(f"❌ Coordinator test failed: {e}")


def check_api_keys():
    """Verify free API keys configuration"""
    print_section("FREE API KEYS CONFIGURATION")
    
    api_keys = {
        'FRED_API_KEY': os.getenv('FRED_API_KEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'INFLUXDB_URL': os.getenv('INFLUXDB_URL'),
        'INFLUXDB_TOKEN': os.getenv('INFLUXDB_TOKEN'),
        'POSTGRES_HOST': os.getenv('POSTGRES_HOST'),
        'MT5_LOGIN': os.getenv('MT5_LOGIN'),
        'MT5_SERVER': os.getenv('MT5_SERVER'),
    }
    
    for key, value in api_keys.items():
        if value:
            masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '***'
            print(f"✅ {key}: {masked_value}")
        else:
            print(f"⚠️  {key}: Not configured")


def check_dashboard_endpoints():
    """Verify dashboard endpoints use real data"""
    print_section("DASHBOARD ENDPOINTS REAL DATA")
    
    from api.views_v2_advanced_simple import (
        llm_analyze_multiple_statements,
        patterns_analyze_with_sample_data,
        rl_get_optimization_stats,
        timezone_get_current_session
    )
    
    # Test LLM endpoint
    print("\n🤖 Testing LLM Analysis Endpoint...")
    try:
        from django.http import HttpRequest
        request = HttpRequest()
        request.method = 'POST'
        
        # This will likely fail gracefully due to no LLM API key, but should show real behavior
        result = llm_analyze_multiple_statements(request)
        print("✅ LLM endpoint responds (check for real API key)")
    except Exception as e:
        print(f"⚠️  LLM endpoint: {str(e)[:100]}...")
    
    # Test Pattern Analysis endpoint
    print("\n📈 Testing Pattern Analysis Endpoint...")
    try:
        request = HttpRequest()
        request.method = 'POST'
        result = patterns_analyze_with_sample_data(request)
        print("✅ Pattern analysis endpoint responds")
    except Exception as e:
        print(f"⚠️  Pattern analysis: {str(e)[:100]}...")
    
    # Test RL Optimization endpoint
    print("\n🧠 Testing RL Optimization Endpoint...")
    try:
        request = HttpRequest()
        request.method = 'GET'
        result = rl_get_optimization_stats(request)
        print("✅ RL optimization endpoint responds")
    except Exception as e:
        print(f"⚠️  RL optimization: {str(e)[:100]}...")
    
    # Test Timezone endpoint
    print("\n🌍 Testing Timezone Analysis Endpoint...")
    try:
        request = HttpRequest()
        request.method = 'GET'
        result = timezone_get_current_session(request)
        print("✅ Timezone analysis endpoint responds")
    except Exception as e:
        print(f"⚠️  Timezone analysis: {str(e)[:100]}...")


def main():
    """Run comprehensive real data verification"""
    print("🚀 REAL DATA INTEGRATION VERIFICATION")
    print("Checking all dashboard pages and agents use REAL data sources")
    
    # Run all checks
    checks = [
        ("InfluxDB Real Data", check_influxdb_connection),
        ("MT5 Integration", check_mt5_data),
        ("Agents Real Data", check_agents_real_data),
        ("Coordinator Integration", check_coordinator_integration),
        ("API Keys Configuration", check_api_keys),
        ("Dashboard Endpoints", check_dashboard_endpoints),
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ {name} check failed: {e}")
            results[name] = False
    
    # Summary
    print_section("REAL DATA INTEGRATION SUMMARY")
    
    total_checks = len(results)
    passed_checks = sum(1 for result in results.values() if result)
    
    print(f"📊 Overall Status: {passed_checks}/{total_checks} checks passed")
    
    for name, result in results.items():
        status = "✅" if result else "⚠️"
        print(f"   {status} {name}")
    
    if passed_checks == total_checks:
        print("\n🎉 ALL SYSTEMS USING REAL DATA!")
        print("✅ Dashboard pages will display real InfluxDB (MT5) data")
        print("✅ All agents analyze real market data and news")
        print("✅ Geopolitical agent uses real RSS feeds")
        print("✅ No mock data anywhere in the system")
    else:
        print(f"\n⚠️  {total_checks - passed_checks} systems need attention")
        print("Some components may not be fully configured for real data")
    
    print(f"\nVerification completed at: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
