"use client";

import { MCPSystemDashboard } from "@/components/mcp/MCPSystemDashboard";
import { MCPControlPanel } from "@/components/mcp/MCPControlPanel";

export default function MCPPage() {
  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">MCP Agent System</h1>
          <p className="text-gray-600">Model Context Protocol - Real-time Data Collection & Distribution</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <MCPControlPanel />
        </div>
        <div className="lg:col-span-2">
          <MCPSystemDashboard />
        </div>
      </div>
    </div>
  );
}
