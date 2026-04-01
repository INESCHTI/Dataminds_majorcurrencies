/**
 * Auth Test Page
 * Test NextAuth functionality
 */
import AuthTest from '@/components/AuthTest';

export default function AuthTestPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 p-6">
      <div className="container mx-auto">
        <h1 className="text-3xl font-bold mb-6">Authentication Test</h1>
        <AuthTest />
      </div>
    </div>
  );
}
