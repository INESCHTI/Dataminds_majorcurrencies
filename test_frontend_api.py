"""
Test Frontend API Connection
"""

import requests
import json

def test_frontend_api_endpoints():
    """Test all frontend API endpoints"""
    print("🔍 Testing Frontend API Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api"
    
    endpoints = [
        ("/monitoring/health_check/", "Health Check"),
        ("/monitoring/freshness_health/?target_minutes=240", "Freshness Health"),
        ("/monitoring/drift_detection/", "Drift Detection"),
        ("/monitoring/agent_performance/", "Agent Performance"),
    ]
    
    for endpoint, name in endpoints:
        try:
            print(f"\n📡 Testing {name}...")
            response = requests.get(f"{base_url}{endpoint}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {name}: {response.status_code}")
                print(f"   Keys: {list(data.keys())}")
                
                # Check for specific fields
                if 'freshness' in endpoint:
                    freshness = data.get('freshness', {})
                    print(f"   Status: {freshness.get('status', 'Unknown')}")
                    print(f"   Age: {freshness.get('age_minutes', 'Unknown')} minutes")
                
            else:
                print(f"❌ {name}: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
    
    # Test signal generation (POST)
    print(f"\n📡 Testing Signal Generation...")
    try:
        response = requests.post(f"{base_url}/v2-signals/generate_signal/", 
                                json={"pair": "EURUSD"})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Signal Generation: {response.status_code}")
            print(f"   Success: {data.get('success', False)}")
            print(f"   Signal: {data.get('signal', {}).get('direction', 'Unknown')}")
        else:
            print(f"❌ Signal Generation: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Signal Generation: Error - {e}")

def test_cors_headers():
    """Test CORS headers"""
    print(f"\n🌐 Testing CORS Headers...")
    
    try:
        # Test with Origin header (like browser would send)
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type',
        }
        
        response = requests.options('http://localhost:8000/api/monitoring/freshness_health/', headers=headers)
        
        print(f"✅ OPTIONS Response: {response.status_code}")
        print(f"   Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'Not set')}")
        print(f"   Access-Control-Allow-Methods: {response.headers.get('Access-Control-Allow-Methods', 'Not set')}")
        print(f"   Access-Control-Allow-Headers: {response.headers.get('Access-Control-Allow-Headers', 'Not set')}")
        
        # Test actual GET with Origin
        headers = {'Origin': 'http://localhost:3000'}
        response = requests.get('http://localhost:8000/api/monitoring/freshness_health/', headers=headers)
        
        print(f"✅ GET Response: {response.status_code}")
        print(f"   Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'Not set')}")
        
    except Exception as e:
        print(f"❌ CORS Test Error: {e}")

if __name__ == "__main__":
    print("🚀 Frontend API Connection Test")
    print("Testing all endpoints that the frontend uses")
    print()
    
    test_frontend_api_endpoints()
    test_cors_headers()
    
    print("\n📋 Summary:")
    print("If all endpoints return 200 OK, the issue might be:")
    print("1. Frontend JavaScript error")
    print("2. Network connectivity issue")
    print("3. Browser cache/CORS issue")
    print("4. TypeScript type mismatch")
    print()
    print("🔧 Troubleshooting:")
    print("1. Check browser developer console for errors")
    print("2. Clear browser cache and reload")
    print("3. Check Network tab for failed requests")
    print("4. Verify frontend is running on http://localhost:3000")
