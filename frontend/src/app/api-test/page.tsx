/**
 * API Test Page
 * Test backend API connectivity
 */
import ApiTest from '@/components/ApiTest';

export default function ApiTestPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 p-6">
      <div className="container mx-auto">
        <h1 className="text-3xl font-bold mb-6">API Test Page</h1>
        <ApiTest />
      </div>
    </div>
  );
}
