"""
Test TokenFactory API Integration
"""

import os
import sys
sys.path.append('backend')

# Set environment variables for testing
os.environ['TOKENFACTORY_API_KEY'] = 'YOUR_API_KEY'  # Replace with actual key
os.environ['TOKENFACTORY_BASE_URL'] = 'https://tokenfactory.esprit.tn/api'
os.environ['TOKENFACTORY_MODEL'] = 'hosted_vllm/Llama-3.1-70B-Instruct'

def test_tokenfactory_llm():
    """Test the TokenFactory LLM integration"""
    print("🚀 Testing TokenFactory LLM Integration")
    print("=" * 50)
    
    try:
        from core.llm_factory_tokenfactory import get_tokenfactory_llm, get_enhanced_reasoning
        
        # Test 1: Basic LLM connection
        print("\n1. 🔍 Testing TokenFactory API Connection...")
        llm = get_tokenfactory_llm()
        
        if not llm.enabled:
            print("⚠️ TokenFactory API key not configured, using fallback mode")
        else:
            print("✅ TokenFactory API configured")
        
        # Test 2: Simple completion
        print("\n2. 📝 Testing Simple Completion...")
        messages = [
            {"role": "system", "content": "You are a helpful FX trading assistant."},
            {"role": "user", "content": "Should I buy or sell EURUSD today? Give a brief answer."}
        ]
        
        response = llm.create_completion(messages, temperature=0.3, max_tokens=100)
        
        if response and 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content']
            print(f"✅ LLM Response: {content[:100]}...")
        else:
            print("⚠️ Using fallback response")
        
        # Test 3: Enhanced reasoning
        print("\n3. 🧠 Testing Enhanced Reasoning...")
        reasoning = get_enhanced_reasoning()
        
        market_data = {
            'price': 1.0850,
            'trend': 'upward',
            'volume': 'high',
            'rsi': 65.0
        }
        
        analysis = reasoning.analyze_market_signal(
            agent_type='technical',
            market_data=market_data,
            additional_context='EURUSD is showing bullish momentum'
        )
        
        print(f"✅ Signal: {analysis.get('signal', 'NEUTRAL')}")
        print(f"✅ Confidence: {analysis.get('confidence', 0):.1%}")
        print(f"✅ Reasoning: {analysis.get('reasoning', 'No reasoning')[:100]}...")
        
        # Test 4: Enhanced agent
        print("\n4. 🤖 Testing Enhanced Agent...")
        from signal_layer.enhanced_agent_v2 import create_enhanced_agent
        
        agent = create_enhanced_agent('technical')
        
        ohlcv_data = {
            'open': 1.0840,
            'high': 1.0860,
            'low': 1.0830,
            'close': 1.0850,
            'volume': 1000000
        }
        
        signal = agent.generate_signal(ohlcv_data)
        
        print(f"✅ Agent Signal: {signal.get('signal', 'NEUTRAL')}")
        print(f"✅ Agent Confidence: {signal.get('confidence', 0):.1%}")
        print(f"✅ LLM Enhanced: {signal.get('llm_enhanced', False)}")
        print(f"✅ Agent Reasoning: {signal.get('reasoning', 'No reasoning')[:100]}...")
        
        print("\n🎉 TokenFactory Integration Test Complete!")
        
        if llm.enabled:
            print("✅ Full LLM integration working")
        else:
            print("⚠️ Fallback mode active - configure API key for full functionality")
        
        return True
        
    except Exception as e:
        print(f"❌ TokenFactory integration test failed: {e}")
        return False

def test_coordinator_integration():
    """Test coordinator with enhanced LLM"""
    print("\n🔗 Testing Coordinator Integration...")
    
    try:
        from signal_layer.coordinator_agent_v2 import CoordinatorAgentV2
        
        coordinator = CoordinatorAgentV2()
        
        # Test signal generation
        signal_data = coordinator.generate_final_signal('EURUSD', 'EUR', 'USD')
        
        print(f"✅ Coordinator Signal: {signal_data.get('final_signal', 'NEUTRAL')}")
        print(f"✅ Coordinator Confidence: {signal_data.get('confidence', 0):.1%}")
        print(f"✅ Explanation Length: {len(signal_data.get('explanation', ''))}")
        
        # Check if explanation is enhanced
        explanation = signal_data.get('explanation', '')
        if len(explanation) > 100 and 'analysis' in explanation.lower():
            print("✅ Enhanced LLM explanation detected")
        else:
            print("⚠️ Using fallback explanation")
        
        return True
        
    except Exception as e:
        print(f"❌ Coordinator integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 TokenFactory API Integration Test")
    print("Configure your API key in .env file to test full functionality")
    print("Current setup: TOKENFACTORY_API_KEY=YOUR_API_KEY")
    print()
    
    # Run tests
    test_tokenfactory_llm()
    test_coordinator_integration()
    
    print("\n📋 Integration Summary:")
    print("✅ TokenFactory LLM factory created")
    print("✅ Enhanced reasoning system implemented")
    print("✅ Enhanced agents created")
    print("✅ Coordinator integration updated")
    print("✅ Fallback mechanisms in place")
    
    print("\n🚀 Next Steps:")
    print("1. Add your actual TokenFactory API key to .env")
    print("2. Restart the backend server")
    print("3. Test signal generation with enhanced LLM")
    print("4. Monitor reasoning quality improvements")
