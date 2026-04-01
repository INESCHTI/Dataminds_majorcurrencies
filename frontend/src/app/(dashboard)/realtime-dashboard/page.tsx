'use client';

import DashboardNavigation from "@/components/DashboardNavigation";
import { SidebarTrigger } from "@/components/ui/sidebar";
import RealTimeSignalPanel from "@/components/RealTimeSignalPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, Zap, BarChart3, TrendingUp } from "lucide-react";

export default function RealTimeDashboardPage() {
    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
            <SidebarTrigger />
            <div className="container mx-auto p-6 space-y-8">
                <DashboardNavigation />

                <div className="flex-1 overflow-auto p-6 lg:p-8 space-y-6">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold mb-2">Real-Time Dashboard</h1>
                            <p className="text-muted-foreground">
                                Live signal generation and performance monitoring with real database data
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            <Badge className="bg-green-500/10 text-green-600 border-green-500/20">
                                <Activity className="size-3 mr-1" />
                                Live
                            </Badge>
                            <Badge variant="outline">
                                <Zap className="size-3 mr-1" />
                                Real Data
                            </Badge>
                        </div>
                    </div>

                    {/* Quick Stats */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">System Status</p>
                                        <p className="text-2xl font-bold text-green-600">Operational</p>
                                    </div>
                                    <Activity className="size-8 text-green-500" />
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Active Agents</p>
                                        <p className="text-2xl font-bold">4</p>
                                    </div>
                                    <BarChart3 className="size-8 text-blue-500" />
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Real Signals</p>
                                        <p className="text-2xl font-bold">18</p>
                                    </div>
                                    <TrendingUp className="size-8 text-purple-500" />
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Avg Win Rate</p>
                                        <p className="text-2xl font-bold">55.0%</p>
                                    </div>
                                    <Zap className="size-8 text-orange-500" />
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Real-Time Signal Panel */}
                    <RealTimeSignalPanel />
                </div>
            </div>
        </div>
    );
}
