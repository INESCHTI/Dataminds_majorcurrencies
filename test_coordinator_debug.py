"""
Debug Coordinator Agent
"""

import os
import sys
sys.path.append('backend')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

def test_coordinator_directly():
    """Test coordinator directly to see the exact error"""
    try:
        import django
        django.setup()
        
        from signal_layer.coordinator_agent_v2 import CoordinatorAgentV2
        
        print("🔍 Testing Coordinator Agent Directly")
        print("=" * 50)
        
        coordinator = CoordinatorAgentV2()
        
        print("✅ Coordinator initialized")
        
        # Test signal generation
        print("📡 Testing signal generation...")
        signal = coordinator.generate_final_signal('EURUSD', 'EUR', 'USD')
        
        print("✅ Signal generated successfully!")
        print(f"   Final Signal: {signal.get('final_signal', 'Unknown')}")
        print(f"   Confidence: {signal.get('confidence', 0):.1%}")
        print(f"   Execution Time: {signal.get('execution_time', 0):.1f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Coordinator Debug Test")
    print()
    
    success = test_coordinator_directly()
    
    if success:
        print("\n✅ Coordinator working correctly!")
    else:
        print("\n❌ Coordinator has issues - see error above")
