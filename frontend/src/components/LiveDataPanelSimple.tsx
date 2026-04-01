/**
 * Simple Live Data Panel for testing
 */
'use client';

import React from 'react';

export default function LiveDataPanelSimple() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Live Data</h2>
        <p className="text-gray-600">Real-time market data integration</p>
      </div>
      
      <div className="bg-white p-6 rounded-lg border">
        <h3 className="font-semibold mb-4">Live Data Management</h3>
        <p>Live Data component is working!</p>
      </div>
    </div>
  );
}
