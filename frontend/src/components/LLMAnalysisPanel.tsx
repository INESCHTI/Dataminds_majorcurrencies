/**
 * LLM Central Bank Analysis Panel Component
 * Displays GPT-4 powered central bank analysis
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Brain,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Target,
  AlertTriangle,
  CheckCircle,
  FileText
} from 'lucide-react';
import { api } from '@/lib/api';

interface CentralBankStatement {
  bank: string;
  timestamp: string;
  statement: string;
  source: string;
  statement_type: string;
  officials: string[];
}

interface LLMAnalysis {
  bank: string;
  timestamp: string;
  policy_bias: string;
  confidence: number;
  key_points: string[];
  rate_outlook: string;
  inflation_outlook: string;
  economic_outlook: string;
  market_impact: string;
  reasoning: string;
}

interface CurrencyImpact {
  overall_bias: string;
  confidence: number;
  market_impact: string;
  rate_outlook: string;
  analyses: LLMAnalysis[];
  weighted_score: number;
}

interface LLMAnalysisPanelProps {
  className?: string;
}

export default function LLMAnalysisPanel({ className }: LLMAnalysisPanelProps) {
  const [statements, setStatements] = useState<CentralBankStatement[]>([]);
  const [analyses, setAnalyses] = useState<LLMAnalysis[]>([]);
  const [currencyImpacts, setCurrencyImpacts] = useState<Record<string, CurrencyImpact>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedBank, setSelectedBank] = useState<string>('all');

  const fetchSampleStatements = async () => {
    try {
      const data = await api.advanced.llm.getSampleStatements();
      setStatements(data);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const analyzeStatements = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await api.advanced.llm.analyzeStatements(statements);
      setAnalyses(data.analyses);
      setCurrencyImpacts(data.currency_impacts);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const getBiasIcon = (bias: string) => {
    switch (bias) {
      case 'HAWKISH':
        return <TrendingUp className="h-4 w-4 text-red-500" />;
      case 'DOVISH':
        return <TrendingDown className="h-4 w-4 text-green-500" />;
      default:
        return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };

  const getBiasColor = (bias: string) => {
    switch (bias) {
      case 'HAWKISH':
        return 'bg-red-500';
      case 'DOVISH':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getImpactIcon = (impact: string) => {
    switch (impact) {
      case 'BULLISH':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'BEARISH':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'BULLISH':
        return 'bg-green-500';
      case 'BEARISH':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  useEffect(() => {
    fetchSampleStatements();
  }, []);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center space-x-2">
            <Brain className="h-6 w-6" />
            <span>LLM Central Bank Analysis</span>
          </h2>
          <p className="text-gray-600">GPT-4 powered central bank communication analysis</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button onClick={fetchSampleStatements} disabled={isLoading}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={analyzeStatements} disabled={isLoading || statements.length === 0}>
            {isLoading ? 'Analyzing...' : 'Analyze Statements'}
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <span className="font-semibold text-red-800">Error:</span>
            </div>
            <p className="text-red-700 mt-1">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Sample Statements */}
      {statements.length > 0 && analyses.length === 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <MessageSquare className="h-5 w-5" />
              <span>Sample Central Bank Statements</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {statements.map((statement, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">{statement.bank}</span>
                    <Badge variant="outline">{statement.statement_type}</Badge>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{statement.statement}</p>
                  <div className="text-xs text-gray-500">
                    <span>Source: {statement.source}</span>
                    <span className="mx-2">•</span>
                    <span>{new Date(statement.timestamp).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 text-center">
              <p className="text-sm text-gray-600 mb-2">
                Click "Analyze Statements" to process with GPT-4
              </p>
              <Button onClick={analyzeStatements} disabled={isLoading}>
                {isLoading ? 'Analyzing...' : 'Analyze Statements'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analysis Results */}
      {analyses.length > 0 && (
        <>
          {/* Currency Impacts */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <FileText className="h-5 w-5" />
                <span>Currency Impacts</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(currencyImpacts).map(([currency, impact]) => (
                  <div key={currency} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-lg">{currency}</span>
                      {getImpactIcon(impact.market_impact)}
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        {getBiasIcon(impact.overall_bias)}
                        <span className="text-sm">{impact.overall_bias}</span>
                      </div>
                      <Progress value={impact.confidence * 100} className="h-2" />
                      <div className="text-xs text-gray-600">
                        Confidence: {(impact.confidence * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs">
                        <span className="font-medium">Rate:</span> {impact.rate_outlook}
                      </div>
                      <div className="text-xs">
                        <span className="font-medium">Impact:</span> {impact.market_impact}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Analysis Details */}
          <Card>
            <CardHeader>
              <CardTitle>Analysis Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {analyses.map((analysis, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold">{analysis.bank}</span>
                        {getBiasIcon(analysis.policy_bias)}
                      </div>
                      <Badge className={getBiasColor(analysis.policy_bias)}>
                        {analysis.policy_bias}
                      </Badge>
                    </div>
                    
                    <div className="space-y-3">
                      {/* Confidence */}
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Confidence</span>
                          <span>{(analysis.confidence * 100).toFixed(1)}%</span>
                        </div>
                        <Progress value={analysis.confidence * 100} className="h-2" />
                      </div>

                      {/* Key Metrics */}
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div className="text-center">
                          <div className="font-medium">Rate</div>
                          <div className="text-blue-600">{analysis.rate_outlook}</div>
                        </div>
                        <div className="text-center">
                          <div className="font-medium">Inflation</div>
                          <div className="text-orange-600">{analysis.inflation_outlook}</div>
                        </div>
                        <div className="text-center">
                          <div className="font-medium">Economy</div>
                          <div className="text-green-600">{analysis.economic_outlook}</div>
                        </div>
                      </div>

                      {/* Key Points */}
                      <div>
                        <h4 className="font-medium text-sm mb-2">Key Points</h4>
                        <ul className="text-sm space-y-1">
                          {analysis.key_points.map((point, idx) => (
                            <li key={idx} className="flex items-start space-x-2">
                              <CheckCircle className="h-3 w-3 text-green-500 mt-0.5 flex-shrink-0" />
                              <span>{point}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Reasoning */}
                      <div>
                        <h4 className="font-medium text-sm mb-2">Reasoning</h4>
                        <p className="text-sm text-gray-600">{analysis.reasoning}</p>
                      </div>

                      {/* Timestamp */}
                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                        <Clock className="h-3 w-3" />
                        <span>{new Date(analysis.timestamp).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Instructions */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-3">
            <h4 className="font-semibold">LLM Analysis Instructions:</h4>
            <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
              <li>Sample statements are loaded automatically from major central banks</li>
              <li>Click "Analyze Statements" to process with GPT-4 (mock analysis if no API key)</li>
              <li>View currency impacts and policy bias analysis</li>
              <li>Filter results by specific banks for focused analysis</li>
              <li>Review key points and reasoning for each analysis</li>
            </ol>
            <div className="mt-4 p-3 bg-blue-50 rounded">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> For production use, add your OpenAI API key to enable real GPT-4 analysis.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
