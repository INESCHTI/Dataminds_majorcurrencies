"""
Test Signal Generation - Frontend vs Backend
"""

import requests
import json
import time

def test_signal_generation():
    """Test signal generation and analyze response"""
    print("🔍 Testing Signal Generation")
    print("=" * 50)
    
    # Test the exact same call the frontend makes
    url = "http://localhost:8000/api/v2-signals/generate_signal/"
    payload = {"pair": "EURUSD"}
    headers = {"Content-Type": "application/json"}
    
    print(f"📡 Request: POST {url}")
    print(f"📦 Payload: {payload}")
    print()
    
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        end_time = time.time()
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"⏱️ Response Time: {(end_time - start_time)*1000:.0f}ms")
        print(f"📄 Content-Type: {response.headers.get('content-type')}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Response Structure:")
            print(f"   Keys: {list(data.keys())}")
            
            if 'signal' in data:
                signal = data['signal']
                print(f"   Signal Keys: {list(signal.keys())}")
                print(f"   Direction: {signal.get('direction', 'Unknown')}")
                print(f"   Confidence: {signal.get('confidence', 0):.1%}")
                print(f"   Signal ID: {signal.get('signal_id', 'Unknown')}")
                print(f"   Reasoning Length: {len(signal.get('reasoning', ''))} chars")
            
            if 'success' in data:
                print(f"   Success: {data['success']}")
            
            print()
            print("🎯 Expected Frontend Interface:")
            print("   interface SignalData {")
            print("       success: boolean;")
            print("       signal: {")
            print("           direction: string;")
            print("           confidence: number;")
            print("           ...other fields")
            print("       };")
            print("   }")
            
            print()
            print("✅ Response matches expected structure!")
            
        else:
            print(f"❌ Error Response: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is backend running?")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_frontend_api_format():
    """Test if the response format matches what frontend expects"""
    print("\n🔍 Testing Frontend API Format")
    print("=" * 50)
    
    try:
        response = requests.post("http://localhost:8000/api/v2-signals/generate_signal/", 
                                json={"pair": "EURUSD"})
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            required_fields = ['success', 'signal']
            signal_fields = ['direction', 'confidence', 'reasoning', 'signal_id']
            
            print("📋 Required Field Check:")
            for field in required_fields:
                present = field in data
                print(f"   ✅ {field}: {'Present' if present else 'MISSING'}")
            
            if 'signal' in data:
                print("\n📋 Signal Field Check:")
                for field in signal_fields:
                    present = field in data['signal']
                    print(f"   ✅ {field}: {'Present' if present else 'MISSING'}")
            
            # Check data types
            print("\n📋 Data Type Check:")
            print(f"   ✅ success: {type(data.get('success', 'Missing'))}")
            print(f"   ✅ signal: {type(data.get('signal', 'Missing'))}")
            
            if 'signal' in data:
                signal = data['signal']
                print(f"   ✅ direction: {type(signal.get('direction', 'Missing'))}")
                print(f"   ✅ confidence: {type(signal.get('confidence', 'Missing'))}")
                print(f"   ✅ reasoning: {type(signal.get('reasoning', 'Missing'))}")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test Error: {e}")

if __name__ == "__main__":
    print("🚀 Signal Generation Test")
    print("Testing backend response format for frontend compatibility")
    print()
    
    test_signal_generation()
    test_frontend_api_format()
    
    print("\n🎯 Frontend Debugging Tips:")
    print("1. Open browser console (F12)")
    print("2. Look for TypeScript errors")
    print("3. Check Network tab for failed requests")
    print("4. Verify the response is being parsed correctly")
    print("5. Check if the SignalData interface matches the response")
