/**
 * Risk Management Panel Component
 * Position sizing and risk controls
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Shield, 
  Calculator, 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown,
  DollarSign,
  Percent,
  Target,
  Activity
} from 'lucide-react';

interface PositionSizeResult {
  position_size: number;
  details: {
    method: string;
    risk_amount: number;
    potential_profit: number;
    risk_reward_ratio: number;
    take_profit: number;
    portfolio_risk: number;
  };
  risk_metrics: {
    account_balance: number;
    total_risk: number;
    risk_utilization: number;
  };
}

interface PortfolioSummary {
  account_balance: number;
  open_positions: number;
  total_risk: number;
  total_risk_percentage: number;
  max_positions: number;
  risk_utilization: number;
  positions: Record<string, any>;
}

interface RiskValidation {
  violations: string[];
  is_compliant: boolean;
  portfolio_risk_pct: number;
  position_count: number;
  total_risk: number;
}

export default function RiskManagementPanel() {
  const [positionResult, setPositionResult] = useState<PositionSizeResult | null>(null);
  const [portfolioSummary, setPortfolioSummary] = useState<PortfolioSummary | null>(null);
  const [riskValidation, setRiskValidation] = useState<RiskValidation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    symbol: 'EURUSD',
    direction: 'BUY',
    entry_price: '1.0850',
    stop_loss: '1.0750',
    method: 'percentage',
    confidence: '0.7',
    volatility: '0.01'
  });

  const [accountBalance, setAccountBalance] = useState('100000');

  useEffect(() => {
    fetchPortfolioSummary();
    fetchRiskValidation();
  }, []);

  const fetchPortfolioSummary = async () => {
    try {
      const response = await fetch('/api/v2/risk-management/portfolio_summary/');
      const data = await response.json();
      
      if (data.success) {
        setPortfolioSummary(data.portfolio);
        setAccountBalance(data.portfolio.account_balance.toString());
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const fetchRiskValidation = async () => {
    try {
      const response = await fetch('/api/v2/risk-management/risk_validation/');
      const data = await response.json();
      
      if (data.success) {
        setRiskValidation(data.validation);
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const calculatePositionSize = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v2/risk-management/calculate_position_size/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: formData.symbol,
          direction: formData.direction,
          entry_price: parseFloat(formData.entry_price),
          stop_loss: parseFloat(formData.stop_loss),
          method: formData.method,
          confidence: parseFloat(formData.confidence),
          volatility: parseFloat(formData.volatility)
        }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setPositionResult(data);
        await fetchPortfolioSummary(); // Refresh portfolio data
      } else {
        setError(data.error);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const updateAccountBalance = async () => {
    try {
      const response = await fetch('/api/v2/risk-management/update_account_balance/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          balance: parseFloat(accountBalance)
        }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        await fetchPortfolioSummary();
        await fetchRiskValidation();
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  const getRiskLevelColor = (risk: number) => {
    if (risk < 50) return 'text-green-600';
    if (risk < 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRiskLevelBadge = (risk: number) => {
    if (risk < 50) return <Badge className="bg-green-500">Low Risk</Badge>;
    if (risk < 80) return <Badge className="bg-yellow-500">Medium Risk</Badge>;
    return <Badge variant="destructive">High Risk</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center space-x-2">
            <Shield className="h-6 w-6" />
            <span>Risk Management</span>
          </h2>
          <p className="text-gray-600">Position sizing and risk controls</p>
        </div>
        <div className="flex items-center space-x-2">
          {riskValidation && getRiskLevelBadge(riskValidation.portfolio_risk_pct)}
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

      {/* Portfolio Overview */}
      {portfolioSummary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <DollarSign className="h-5 w-5 text-blue-500" />
                <span className="font-medium">Account Balance</span>
              </div>
              <div className="text-2xl font-bold mt-2">{formatCurrency(portfolioSummary.account_balance)}</div>
              <div className="text-sm text-gray-600">Available capital</div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <Activity className="h-5 w-5 text-green-500" />
                <span className="font-medium">Open Positions</span>
              </div>
              <div className="text-2xl font-bold mt-2">{portfolioSummary.open_positions}</div>
              <div className="text-sm text-gray-600">of {portfolioSummary.max_positions} max</div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <Target className="h-5 w-5 text-purple-500" />
                <span className="font-medium">Total Risk</span>
              </div>
              <div className="text-2xl font-bold mt-2">{formatCurrency(portfolioSummary.total_risk)}</div>
              <div className="text-sm text-gray-600">{formatPercent(portfolioSummary.total_risk_percentage)}</div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <Percent className="h-5 w-5 text-orange-500" />
                <span className="font-medium">Risk Utilization</span>
              </div>
              <div className="text-2xl font-bold mt-2">{formatPercent(portfolioSummary.risk_utilization * 100)}</div>
              <Progress value={portfolioSummary.risk_utilization * 100} className="mt-2" />
            </CardContent>
          </Card>
        </div>
      )}

      {/* Position Sizing Calculator */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Calculator className="h-5 w-5" />
            <span>Position Size Calculator</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Input Form */}
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="symbol">Symbol</Label>
                  <Select value={formData.symbol} onValueChange={(value) => setFormData({...formData, symbol: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="EURUSD">EUR/USD</SelectItem>
                      <SelectItem value="GBPUSD">GBP/USD</SelectItem>
                      <SelectItem value="USDJPY">USD/JPY</SelectItem>
                      <SelectItem value="USDCHF">USD/CHF</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="direction">Direction</Label>
                  <Select value={formData.direction} onValueChange={(value) => setFormData({...formData, direction: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="BUY">BUY</SelectItem>
                      <SelectItem value="SELL">SELL</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="entry_price">Entry Price</Label>
                  <Input
                    id="entry_price"
                    type="number"
                    step="0.0001"
                    value={formData.entry_price}
                    onChange={(e) => setFormData({...formData, entry_price: e.target.value})}
                  />
                </div>
                <div>
                  <Label htmlFor="stop_loss">Stop Loss</Label>
                  <Input
                    id="stop_loss"
                    type="number"
                    step="0.0001"
                    value={formData.stop_loss}
                    onChange={(e) => setFormData({...formData, stop_loss: e.target.value})}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="method">Sizing Method</Label>
                  <Select value={formData.method} onValueChange={(value) => setFormData({...formData, method: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="fixed">Fixed</SelectItem>
                      <SelectItem value="percentage">Percentage Risk</SelectItem>
                      <SelectItem value="volatility">Volatility Adjusted</SelectItem>
                      <SelectItem value="kelly">Kelly Criterion</SelectItem>
                      <SelectItem value="risk_parity">Risk Parity</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="confidence">Confidence</Label>
                  <Input
                    id="confidence"
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={formData.confidence}
                    onChange={(e) => setFormData({...formData, confidence: e.target.value})}
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="volatility">Volatility</Label>
                <Input
                  id="volatility"
                  type="number"
                  step="0.001"
                  value={formData.volatility}
                  onChange={(e) => setFormData({...formData, volatility: e.target.value})}
                />
              </div>

              <Button onClick={calculatePositionSize} disabled={isLoading} className="w-full">
                {isLoading ? 'Calculating...' : 'Calculate Position Size'}
              </Button>
            </div>

            {/* Results */}
            {positionResult && (
              <div className="space-y-4">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-semibold text-blue-800 mb-2">Position Size Result</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Position Size:</span>
                      <span className="font-bold">{positionResult.position_size.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Risk Amount:</span>
                      <span className="font-bold">{formatCurrency(positionResult.details.risk_amount)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Potential Profit:</span>
                      <span className="font-bold">{formatCurrency(positionResult.details.potential_profit)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Risk/Reward Ratio:</span>
                      <span className="font-bold">{positionResult.details.risk_reward_ratio.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Take Profit:</span>
                      <span className="font-bold">{positionResult.details.take_profit.toFixed(5)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Portfolio Risk:</span>
                      <span className="font-bold">{formatPercent(positionResult.details.portfolio_risk * 100)}</span>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-green-50 rounded-lg">
                  <h4 className="font-semibold text-green-800 mb-2">Risk Metrics</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Account Balance:</span>
                      <span className="font-bold">{formatCurrency(positionResult.risk_metrics.account_balance)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Total Risk:</span>
                      <span className="font-bold">{formatCurrency(positionResult.risk_metrics.total_risk)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Risk Utilization:</span>
                      <span className="font-bold">{formatPercent(positionResult.risk_metrics.risk_utilization * 100)}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Risk Validation */}
      {riskValidation && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5" />
              <span>Risk Validation</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span>Compliance Status:</span>
                <Badge className={riskValidation.is_compliant ? 'bg-green-500' : 'bg-red-500'}>
                  {riskValidation.is_compliant ? 'Compliant' : 'Violations'}
                </Badge>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label>Portfolio Risk</Label>
                  <div className={`text-2xl font-bold ${getRiskLevelColor(riskValidation.portfolio_risk_pct)}`}>
                    {formatPercent(riskValidation.portfolio_risk_pct)}
                  </div>
                </div>
                <div>
                  <Label>Position Count</Label>
                  <div className="text-2xl font-bold">{riskValidation.position_count}</div>
                </div>
                <div>
                  <Label>Total Risk</Label>
                  <div className="text-2xl font-bold">{formatCurrency(riskValidation.total_risk)}</div>
                </div>
              </div>

              {riskValidation.violations.length > 0 && (
                <div className="p-4 bg-red-50 rounded-lg">
                  <h4 className="font-semibold text-red-800 mb-2">Risk Violations:</h4>
                  <ul className="space-y-1">
                    {riskValidation.violations.map((violation, index) => (
                      <li key={index} className="text-red-700 text-sm">• {violation}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Account Balance Update */}
      <Card>
        <CardHeader>
          <CardTitle>Update Account Balance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <Label htmlFor="account_balance">Account Balance</Label>
              <Input
                id="account_balance"
                type="number"
                value={accountBalance}
                onChange={(e) => setAccountBalance(e.target.value)}
              />
            </div>
            <Button onClick={updateAccountBalance}>
              Update Balance
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
