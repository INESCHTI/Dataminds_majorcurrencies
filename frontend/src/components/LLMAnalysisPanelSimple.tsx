/**
 * Simple LLM Analysis Panel for testing
 */
'use client';

import React from 'react';

export default function LLMAnalysisPanelSimple() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">LLM Analysis</h2>
        <p className="text-gray-600">GPT-4 powered central bank analysis</p>
      </div>
      
      <div className="bg-white p-6 rounded-lg border">
        <h3 className="font-semibold mb-4">Central Bank Analysis</h3>
        <p>LLM Analysis component is working!</p>
      </div>
    </div>
  );
}
