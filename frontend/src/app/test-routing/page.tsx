/**
 * Test Routing Page
 */
export default function TestRoutingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-50 p-6">
      <div className="container mx-auto">
        <h1 className="text-3xl font-bold mb-4">Test Routing Page</h1>
        <p className="text-gray-600 mb-4">This page tests if routing works correctly.</p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-lg border">
            <h2 className="font-semibold">LLM Analysis</h2>
            <p className="text-sm text-gray-600">Route: /llm-analysis</p>
          </div>
          
          <div className="bg-white p-4 rounded-lg border">
            <h2 className="font-semibold">Pattern Recognition</h2>
            <p className="text-sm text-gray-600">Route: /pattern-recognition</p>
          </div>
          
          <div className="bg-white p-4 rounded-lg border">
            <h2 className="font-semibold">RL Optimization</h2>
            <p className="text-sm text-gray-600">Route: /rl-optimization</p>
          </div>
          
          <div className="bg-white p-4 rounded-lg border">
            <h2 className="font-semibold">Multi-Timezone</h2>
            <p className="text-sm text-gray-600">Route: /multi-timezone</p>
          </div>
          
          <div className="bg-white p-4 rounded-lg border">
            <h2 className="font-semibold">Live Data</h2>
            <p className="text-sm text-gray-600">Route: /live-data</p>
          </div>
          
          <div className="bg-white p-4 rounded-lg border">
            <h2 className="font-semibold">Risk Management</h2>
            <p className="text-sm text-gray-600">Route: /risk-management</p>
          </div>
        </div>
      </div>
    </div>
  );
}
