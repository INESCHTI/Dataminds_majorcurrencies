/**
 * Chart Pattern Recognition Panel Component
 * Displays computer vision-based pattern analysis
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  TrendingUp, 
  TrendingDown, 
  BarChart3,
  Target,
  Eye,
  AlertTriangle,
  CheckCircle,
  Minus,
  RefreshCw,
  Image as ImageIcon
} from 'lucide-react';
import { api } from '@/lib/api';

interface ChartPattern {
  pattern_type: string;
  confidence: number;
  start_time: string;
  end_time: string;
  price_level: number;
  direction: string;
  description: string;
  key_points: Array<[string, number]>;
  pattern_data: any;
}

interface PatternAnalysis {
  symbol: string;
  timeframe: string;
  timestamp: string;
  patterns: ChartPattern[];
  overall_sentiment: string;
  confidence: number;
  chart_image: string;
  analysis_summary: string;
}

interface PatternRecognitionPanelProps {
  className?: string;
}

export default function PatternRecognitionPanel({ className }: PatternRecognitionPanelProps) {
  const [analysis, setAnalysis] = useState<PatternAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState('EURUSD');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1H');

  const analyzeWithSampleData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await api.advanced.patterns.analyzeWithSampleData(selectedSymbol, selectedTimeframe);
      setAnalysis(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const getDirectionIcon = (direction: string) => {
    switch (direction) {
      case 'BULLISH':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'BEARISH':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };

  const getDirectionColor = (direction: string) => {
    switch (direction) {
      case 'BULLISH':
        return 'bg-green-500';
      case 'BEARISH':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'BULLISH':
        return <TrendingUp className="h-5 w-5 text-green-500" />;
      case 'BEARISH':
        return <TrendingDown className="h-5 w-5 text-red-500" />;
      default:
        return <Minus className="h-5 w-5 text-gray-500" />;
    }
  };

  const getPatternTypeIcon = (patternType: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      'head_shoulders': <Target className="h-4 w-4" />,
      'double_top': <BarChart3 className="h-4 w-4" />,
      'double_bottom': <BarChart3 className="h-4 w-4" />,
      'triangle': <Target className="h-4 w-4" />,
      'flag': <BarChart3 className="h-4 w-4" />,
      'wedge': <Target className="h-4 w-4" />,
      'support_level': <TrendingUp className="h-4 w-4" />,
      'resistance_level': <TrendingDown className="h-4 w-4" />,
      'doji': <Minus className="h-4 w-4" />
    };
    return iconMap[patternType] || <Eye className="h-4 w-4" />;
  };

  const getConfidenceLevel = (confidence: number) => {
    if (confidence >= 0.8) return { level: 'High', color: 'text-green-600' };
    if (confidence >= 0.6) return { level: 'Medium', color: 'text-yellow-600' };
    return { level: 'Low', color: 'text-red-600' };
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center space-x-2">
            <Eye className="h-6 w-6" />
            <span>Pattern Recognition</span>
          </h2>
          <p className="text-gray-600">Computer vision-based chart pattern analysis</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button onClick={analyzeWithSampleData} disabled={isLoading}>
            {isLoading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                Analyzing...
              </>
            ) : (
              'Analyze Patterns'
            )}
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

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Analysis Parameters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div>
              <label className="text-sm font-medium">Symbol</label>
              <select 
                value={selectedSymbol} 
                onChange={(e) => setSelectedSymbol(e.target.value)}
                className="ml-2 px-3 py-1 border rounded"
              >
                <option value="EURUSD">EUR/USD</option>
                <option value="GBPUSD">GBP/USD</option>
                <option value="USDJPY">USD/JPY</option>
                <option value="USDCHF">USD/CHF</option>
                <option value="AUDUSD">AUD/USD</option>
                <option value="NZDUSD">NZD/USD</option>
                <option value="USDCAD">USD/CAD</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium">Timeframe</label>
              <select 
                value={selectedTimeframe} 
                onChange={(e) => setSelectedTimeframe(e.target.value)}
                className="ml-2 px-3 py-1 border rounded"
              >
                <option value="1M">1 Minute</option>
                <option value="5M">5 Minutes</option>
                <option value="15M">15 Minutes</option>
                <option value="1H">1 Hour</option>
                <option value="4H">4 Hours</option>
                <option value="1D">1 Day</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Analysis Results */}
      {analysis && (
        <>
          {/* Overall Analysis */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span>Overall Analysis</span>
                  {getSentimentIcon(analysis.overall_sentiment)}
                </div>
                <Badge className={getDirectionColor(analysis.overall_sentiment)}>
                  {analysis.overall_sentiment}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-sm font-medium">Confidence</span>
                    <span className="text-sm text-gray-600">({(analysis.confidence * 100).toFixed(1)}%)</span>
                  </div>
                  <Progress value={analysis.confidence * 100} className="h-2" />
                </div>
                <div>
                  <div className="text-sm font-medium mb-2">Analysis Summary</div>
                  <p className="text-sm text-gray-600">{analysis.analysis_summary}</p>
                </div>
                <div>
                  <div className="text-sm font-medium mb-2">Chart Image</div>
                  {analysis.chart_image ? (
                    <div className="flex items-center space-x-2">
                      <ImageIcon className="h-4 w-4 text-green-500" />
                      <span className="text-sm text-green-600">Generated</span>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <AlertTriangle className="h-4 w-4 text-yellow-500" />
                      <span className="text-sm text-yellow-600">Not Available</span>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Detected Patterns */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Target className="h-5 w-5" />
                <span>Detected Patterns ({analysis.patterns.length})</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {analysis.patterns.map((pattern, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        {getPatternTypeIcon(pattern.pattern_type)}
                        <span className="font-semibold">{pattern.pattern_type.replace('_', ' ').toUpperCase()}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        {getDirectionIcon(pattern.direction)}
                        <Badge className={getDirectionColor(pattern.direction)} variant="secondary">
                          {pattern.direction}
                        </Badge>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      {/* Confidence */}
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Confidence</span>
                          <span className={getConfidenceLevel(pattern.confidence).color}>
                            {getConfidenceLevel(pattern.confidence).level}
                          </span>
                        </div>
                        <Progress value={pattern.confidence * 100} className="h-2" />
                      </div>

                      {/* Pattern Details */}
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium">Price Level:</span>
                          <div className="text-blue-600">{pattern.price_level.toFixed(5)}</div>
                        </div>
                        <div>
                          <span className="font-medium">Direction:</span>
                          <div className="flex items-center space-x-1">
                            {getDirectionIcon(pattern.direction)}
                            <span>{pattern.direction}</span>
                          </div>
                        </div>
                      </div>

                      {/* Description */}
                      <div>
                        <div className="text-sm font-medium mb-1">Description</div>
                        <p className="text-sm text-gray-600">{pattern.description}</p>
                      </div>

                      {/* Key Points */}
                      {pattern.key_points.length > 0 && (
                        <div>
                          <div className="text-sm font-medium mb-1">Key Points</div>
                          <div className="text-sm text-gray-600">
                            {pattern.key_points.length} critical points identified
                          </div>
                        </div>
                      )}

                      {/* Time Range */}
                      <div className="text-xs text-gray-500">
                        <span>From: {new Date(pattern.start_time).toLocaleString()}</span>
                        <br />
                        <span>To: {new Date(pattern.end_time).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Chart Image Display */}
          {analysis.chart_image && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <ImageIcon className="h-5 w-5" />
                  <span>Chart Visualization</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <img 
                    src={`data:image/png;base64,${analysis.chart_image}`}
                    alt="Chart with patterns"
                    className="max-w-full h-auto rounded border"
                  />
                  <p className="text-sm text-gray-600 mt-2">
                    Generated chart with detected patterns
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Instructions */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-3">
            <h4 className="font-semibold">Pattern Recognition Instructions:</h4>
            <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
              <li>Select symbol and timeframe for analysis</li>
              <li>Click "Analyze Patterns" to run computer vision analysis</li>
              <li>View detected patterns with confidence scores</li>
              <li>Review overall market sentiment and analysis summary</li>
              <li>Examine chart visualization with pattern annotations</li>
            </ol>
            <div className="mt-4 p-3 bg-blue-50 rounded">
              <p className="text-sm text-blue-800">
                <strong>Pattern Types:</strong> Head & Shoulders, Double Top/Bottom, Triangles, Flags, Wedges, Support/Resistance, Candlestick patterns
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
