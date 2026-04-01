/**
 * Auth Test Component
 * Tests NextAuth functionality
 */
'use client';

import React, { useState } from 'react';
import { signIn, signOut, useSession } from 'next-auth/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, XCircle, User, LogIn, LogOut } from 'lucide-react';

export default function AuthTest() {
  const { data: session, status } = useSession();
  const [testResult, setTestResult] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const testSignIn = async () => {
    setIsLoading(true);
    setTestResult('');
    
    try {
      const result = await signIn('credentials', {
        email: 'demo@example.com',
        password: 'demo',
        redirect: false,
      });
      
      console.log('Sign in result:', result);
      setTestResult(result?.ok ? 'Sign in successful!' : `Sign in failed: ${result?.error}`);
    } catch (error: any) {
      console.error('Sign in error:', error);
      setTestResult(`Sign in error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const testSignOut = async () => {
    setIsLoading(true);
    setTestResult('');
    
    try {
      await signOut();
      setTestResult('Sign out successful!');
    } catch (error: any) {
      console.error('Sign out error:', error);
      setTestResult(`Sign out error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <User className="h-5 w-5" />
          <span>NextAuth Test</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Session Status */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
            <div>
              <span className="font-medium">Session Status: </span>
              <Badge className={status === 'authenticated' ? 'bg-green-500' : 'bg-gray-500'}>
                {status}
              </Badge>
            </div>
            {session && (
              <div className="text-sm text-gray-600">
                User: {session.user?.email}
              </div>
            )}
          </div>

          {/* Auth Actions */}
          <div className="flex space-x-4">
            {status === 'authenticated' ? (
              <Button onClick={testSignOut} disabled={isLoading} className="flex items-center space-x-2">
                <LogOut className="h-4 w-4" />
                <span>{isLoading ? 'Signing out...' : 'Sign Out'}</span>
              </Button>
            ) : (
              <Button onClick={testSignIn} disabled={isLoading} className="flex items-center space-x-2">
                <LogIn className="h-4 w-4" />
                <span>{isLoading ? 'Signing in...' : 'Sign In (Demo)'}</span>
              </Button>
            )}
          </div>

          {/* Test Results */}
          {testResult && (
            <div className={`p-4 rounded-lg ${
              testResult.includes('successful') ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
            } border`}>
              <div className="flex items-center space-x-2">
                {testResult.includes('successful') ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500" />
                )}
                <span className={`font-medium ${
                  testResult.includes('successful') ? 'text-green-800' : 'text-red-800'
                }`}>
                  Result:
                </span>
              </div>
              <p className={`mt-2 text-sm ${
                testResult.includes('successful') ? 'text-green-700' : 'text-red-700'
              }`}>
                {testResult}
              </p>
            </div>
          )}

          {/* Session Info */}
          {session && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="font-semibold text-blue-800 mb-2">Session Info:</h4>
              <pre className="text-xs text-blue-700 whitespace-pre-wrap">
                {JSON.stringify(session, null, 2)}
              </pre>
            </div>
          )}

          {/* Instructions */}
          <div className="text-xs text-gray-500 space-y-1">
            <p><strong>Demo Credentials:</strong></p>
            <p>Email: demo@example.com</p>
            <p>Password: demo</p>
            <p>• Click "Sign In (Demo)" to test authentication</p>
            <p>• Uses simplified auth without database</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
