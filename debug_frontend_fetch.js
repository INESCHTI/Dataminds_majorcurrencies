// Debug script to test frontend fetch - run in browser console
// Copy and paste this into browser developer console on http://localhost:3000

async function testFetch() {
    console.log('🔍 Testing frontend fetch...');
    
    const API_BASE = "http://localhost:8000/api";
    
    // Test 1: Basic fetch
    try {
        console.log('📡 Testing basic fetch...');
        const response = await fetch(`${API_BASE}/monitoring/health_check/`);
        console.log('✅ Basic fetch status:', response.status);
        console.log('✅ Basic fetch headers:', response.headers.get('content-type'));
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Basic fetch data:', data);
        } else {
            console.error('❌ Basic fetch failed:', response.statusText);
        }
    } catch (error) {
        console.error('❌ Basic fetch error:', error);
    }
    
    // Test 2: Freshness health (the failing endpoint)
    try {
        console.log('📡 Testing freshness health fetch...');
        const response = await fetch(`${API_BASE}/monitoring/freshness_health/?target_minutes=240`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000'
            }
        });
        console.log('✅ Freshness status:', response.status);
        console.log('✅ Freshness headers:', response.headers.get('content-type'));
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Freshness data:', data);
            console.log('✅ Freshness data keys:', Object.keys(data));
            console.log('✅ Freshness freshness:', data.freshness);
        } else {
            console.error('❌ Freshness failed:', response.statusText);
            console.error('❌ Freshness error text:', await response.text());
        }
    } catch (error) {
        console.error('❌ Freshness error:', error);
        console.error('❌ Error name:', error.name);
        console.error('❌ Error message:', error.message);
    }
    
    // Test 3: With timeout (like frontend does)
    try {
        console.log('📡 Testing with timeout...');
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000);
        
        const response = await fetch(`${API_BASE}/monitoring/freshness_health/?target_minutes=240`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Timeout fetch data:', data);
        } else {
            console.error('❌ Timeout fetch failed:', response.statusText);
        }
    } catch (error) {
        console.error('❌ Timeout fetch error:', error);
        if (error.name === 'AbortError') {
            console.error('❌ Request was aborted (timeout)');
        }
    }
    
    // Test 4: Check CORS
    try {
        console.log('📡 Testing CORS preflight...');
        const response = await fetch(`${API_BASE}/monitoring/freshness_health/?target_minutes=240`, {
            method: 'OPTIONS',
            headers: {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
        });
        console.log('✅ CORS status:', response.status);
        console.log('✅ CORS headers:', {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        });
    } catch (error) {
        console.error('❌ CORS error:', error);
    }
}

// Run the test
testFetch().then(() => {
    console.log('🎉 Debug test complete!');
}).catch((error) => {
    console.error('💥 Debug test failed:', error);
});

console.log('📋 Instructions:');
console.log('1. Open browser developer tools (F12)');
console.log('2. Go to Console tab');
console.log('3. Copy and paste this entire script');
console.log('4. Press Enter to run');
console.log('5. Check the output for errors');
