'use client';

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

export default function ApiTestPage() {
    const [results, setResults] = useState<Record<string, any>>({});
    const [loading, setLoading] = useState<Record<string, boolean>>({});
    const [errors, setErrors] = useState<Record<string, string>>({});

    const testEndpoint = async (name: string, endpoint: () => Promise<any>) => {
        setLoading(prev => ({ ...prev, [name]: true }));
        setErrors(prev => ({ ...prev, [name]: '' }));
        
        try {
            const result = await endpoint();
            setResults(prev => ({ ...prev, [name]: result }));
            console.log(`✅ ${name}:`, result);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            setErrors(prev => ({ ...prev, [name]: errorMessage }));
            console.error(`❌ ${name}:`, error);
        } finally {
            setLoading(prev => ({ ...prev, [name]: false }));
        }
    };

    const endpoints = [
        {
            name: 'Health Check',
            endpoint: () => api.v2.healthCheck(),
            description: 'Check system health and agent status'
        },
        {
            name: 'Freshness Health',
            endpoint: () => api.v2.healthCheck(),
            description: 'Check system health and agent status'
        },
        {
            name: 'Drift Detection',
            endpoint: () => api.v2.healthCheck(),
            description: 'Check system health and agent status'
        },
        {
            name: 'Signal Generation',
            endpoint: () => api.v2.generateSignal('EURUSD'),
            description: 'Generate trading signal'
        }
    ];

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 p-8">
            <div className="max-w-4xl mx-auto space-y-8">
                <div className="text-center">
                    <h1 className="text-3xl font-bold mb-2">API Test Page</h1>
                    <p className="text-muted-foreground">
                        Test all frontend API endpoints to diagnose connection issues
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {endpoints.map(({ name, endpoint, description }) => (
                        <Card key={name}>
                            <CardHeader>
                                <CardTitle className="flex items-center justify-between">
                                    {name}
                                    <Badge variant={errors[name] ? "destructive" : results[name] ? "default" : "secondary"}>
                                        {errors[name] ? "Error" : results[name] ? "Success" : "Pending"}
                                    </Badge>
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-sm text-muted-foreground mb-4">
                                    {description}
                                </p>
                                
                                <Button
                                    onClick={() => testEndpoint(name, endpoint)}
                                    disabled={loading[name]}
                                    className="w-full"
                                >
                                    {loading[name] ? "Testing..." : `Test ${name}`}
                                </Button>

                                {errors[name] && (
                                    <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                                        <p className="text-sm text-red-600">{errors[name]}</p>
                                    </div>
                                )}

                                {results[name] && (
                                    <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
                                        <p className="text-sm text-green-600 font-medium mb-2">Response:</p>
                                        <pre className="text-xs text-green-700 overflow-auto max-h-40">
                                            {JSON.stringify(results[name], null, 2)}
                                        </pre>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    ))}
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>Troubleshooting Tips</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2 text-sm">
                            <p>• Check browser console (F12) for detailed error messages</p>
                            <p>• Verify backend is running on http://localhost:8000</p>
                            <p>• Clear browser cache and reload the page</p>
                            <p>• Check Network tab in developer tools for failed requests</p>
                            <p>• Ensure CORS is properly configured in backend</p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
