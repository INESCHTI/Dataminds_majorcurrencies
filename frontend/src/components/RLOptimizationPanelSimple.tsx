/**
 * Simple RL Optimization Panel for testing
 */
'use client';

import React from 'react';

export default function RLOptimizationPanelSimple() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">RL Optimization</h2>
        <p className="text-gray-600">Reinforcement learning agent weight optimization</p>
      </div>
      
      <div className="bg-white p-6 rounded-lg border">
        <h3 className="font-semibold mb-4">Agent Weight Optimization</h3>
        <p>RL Optimization component is working!</p>
      </div>
    </div>
  );
}
