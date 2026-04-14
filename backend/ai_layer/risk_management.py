"""
Advanced Risk Management Module
VaR, CVaR, and portfolio-level risk analytics
Replaces simple circuit breakers with statistical risk models
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from scipy import stats

try:
    from arch import arch_model
    ARCH_AVAILABLE = True
except ImportError:
    ARCH_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics for trading"""
    timestamp: datetime
    symbol: str
    
    # Value at Risk
    var_95: float  # 95% VaR (1-day)
    var_99: float  # 99% VaR (1-day)
    cvar_95: float  # Conditional VaR (Expected Shortfall)
    cvar_99: float
    
    # Volatility metrics
    realized_vol: float  # Annualized realized volatility
    ewma_vol: float  # EWMA volatility estimate
    garch_vol: Optional[float]  # GARCH forecast volatility
    
    # Drawdown metrics
    current_drawdown: float
    max_drawdown: float
    drawdown_duration: int
    
    # Tail risk
    skewness: float
    kurtosis: float
    tail_ratio: float  # Ratio of 95th to 5th percentile returns
    
    # Position sizing recommendation
    position_size_mult: float  # Multiplier based on risk
    max_position_pct: float  # Maximum position as % of capital
    
    # Risk status
    risk_level: str  # 'LOW', 'MODERATE', 'HIGH', 'EXTREME'
    risk_adjusted: bool
    
    # Explanation
    risk_factors: Dict[str, float]
    recommendation: str


class VaRModel:
    """
    Value at Risk calculation using multiple methods
    
    Methods:
    - Historical simulation (non-parametric)
    - Variance-Covariance (parametric)
    - Monte Carlo simulation
    - GARCH-based conditional volatility
    """
    
    def __init__(
        self,
        confidence_levels: List[float] = None,
        lookback_window: int = 252,  # 1 year of trading days
        method: str = 'historical'
    ):
        self.confidence_levels = confidence_levels or [0.95, 0.99]
        self.lookback_window = lookback_window
        self.method = method
        self.returns_history = []
        self.lambda_ewma = 0.94  # JP Morgan RiskMetrics standard
        
    def calculate_var(
        self,
        returns: np.ndarray,
        position_value: float = 1.0
    ) -> Dict[str, float]:
        """
        Calculate VaR for given returns series
        
        Returns VaR at multiple confidence levels
        """
        if len(returns) < 30:
            logger.warning("Insufficient data for VaR calculation")
            return {f'var_{int(c*100)}': 0.0 for c in self.confidence_levels}
        
        vars_dict = {}
        
        if self.method == 'historical':
            # Historical simulation (non-parametric)
            for conf in self.confidence_levels:
                var = np.percentile(returns, (1 - conf) * 100)
                vars_dict[f'var_{int(conf*100)}'] = abs(var) * position_value
                
        elif self.method == 'parametric':
            # Variance-covariance (assuming normal distribution)
            mean = np.mean(returns)
            std = np.std(returns)
            
            for conf in self.confidence_levels:
                z_score = stats.norm.ppf(1 - conf)
                var = -(mean + z_score * std)
                vars_dict[f'var_{int(conf*100)}'] = abs(var) * position_value
                
        elif self.method == 'monte_carlo':
            # Monte Carlo simulation
            mean = np.mean(returns)
            std = np.std(returns)
            
            # Simulate 10000 paths
            simulated = np.random.normal(mean, std, 10000)
            
            for conf in self.confidence_levels:
                var = np.percentile(simulated, (1 - conf) * 100)
                vars_dict[f'var_{int(conf*100)}'] = abs(var) * position_value
        
        return vars_dict
    
    def calculate_cvar(self, returns: np.ndarray, var_threshold: float) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall)
        
        Average of returns worse than VaR threshold
        """
        tail_returns = returns[returns <= -abs(var_threshold)]
        if len(tail_returns) == 0:
            return abs(var_threshold)  # Fallback to VaR
        return abs(np.mean(tail_returns))
    
    def ewma_volatility(self, returns: np.ndarray) -> float:
        """
        Calculate EWMA volatility (RiskMetrics approach)
        
        More weight on recent observations
        """
        if len(returns) < 2:
            return 0.0
        
        squared_returns = returns ** 2
        n = len(squared_returns)
        
        # EWMA variance
        weights = np.array([self.lambda_ewma ** i for i in range(n)])
        weights = weights / weights.sum()
        
        ewma_var = np.sum(weights * squared_returns[::-1])
        return np.sqrt(ewma_var) * np.sqrt(252)  # Annualize
    
    def garch_forecast(self, returns: np.ndarray, horizon: int = 1) -> Optional[float]:
        """
        GARCH(1,1) volatility forecast
        
        More sophisticated than EWMA, captures volatility clustering
        """
        if not ARCH_AVAILABLE or len(returns) < 60:
            return None
        
        try:
            # Fit GARCH
            model = arch_model(returns, vol='Garch', p=1, q=1)
            fitted = model.fit(disp='off')
            
            # Forecast
            forecast = fitted.forecast(horizon=horizon)
            variance = forecast.variance.values[-1][0]
            
            return np.sqrt(variance) * np.sqrt(252)  # Annualize
        except Exception as e:
            logger.warning(f"GARCH fitting failed: {e}")
            return None


class PortfolioRiskManager:
    """
    Portfolio-level risk management
    
    Calculates:
    - Portfolio VaR with correlation
    - Beta to market factors
    - Diversification metrics
    - Risk-adjusted position limits
    """
    
    def __init__(
        self,
        max_var_pct: float = 0.02,  # 2% max daily VaR
        max_drawdown_pct: float = 0.10,  # 10% max drawdown
        target_volatility: float = 0.10  # 10% target annual vol
    ):
        self.max_var_pct = max_var_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.target_volatility = target_volatility
        self.var_model = VaRModel()
        
        # Track positions and history
        self.position_history = {}
        self.peak_value = 0
        self.current_drawdown_start = None
    
    def calculate_portfolio_var(
        self,
        positions: Dict[str, float],  # symbol -> position size
        returns_data: Dict[str, pd.Series]  # symbol -> returns series
    ) -> Dict[str, float]:
        """
        Calculate portfolio VaR accounting for correlations
        
        Uses variance-covariance method with empirical correlation matrix
        """
        # Align returns
        common_dates = None
        for symbol, returns in returns_data.items():
            if common_dates is None:
                common_dates = returns.index
            else:
                common_dates = common_dates.intersection(returns.index)
        
        if len(common_dates) < 30:
            logger.warning("Insufficient common history for portfolio VaR")
            return {'portfolio_var_95': 0.0, 'portfolio_var_99': 0.0}
        
        # Create aligned returns matrix
        aligned_returns = pd.DataFrame({
            symbol: returns.loc[common_dates]
            for symbol, returns in returns_data.items()
        })
        
        # Calculate covariance matrix
        cov_matrix = aligned_returns.cov()
        
        # Position vector
        position_vector = np.array([positions.get(s, 0) for s in cov_matrix.index])
        
        # Portfolio variance
        portfolio_var = np.dot(position_vector, np.dot(cov_matrix, position_vector))
        portfolio_vol = np.sqrt(portfolio_var) * np.sqrt(252)  # Annualize
        
        # VaR
        var_95 = 1.645 * np.sqrt(portfolio_var)  # 95% confidence
        var_99 = 2.326 * np.sqrt(portfolio_var)  # 99% confidence
        
        return {
            'portfolio_var_95': var_95,
            'portfolio_var_99': var_99,
            'portfolio_volatility': portfolio_vol,
            'diversification_ratio': self._calculate_diversification_ratio(
                aligned_returns, positions
            )
        }
    
    def _calculate_diversification_ratio(
        self,
        returns: pd.DataFrame,
        positions: Dict[str, float]
    ) -> float:
        """
        Calculate diversification ratio
        
        Ratio of weighted sum of individual vols to portfolio vol
        Higher = better diversification
        """
        individual_vols = returns.std() * np.sqrt(252)
        weighted_individual_vol = sum(
            abs(positions.get(symbol, 0)) * vol
            for symbol, vol in individual_vols.items()
        )
        
        portfolio_vol = np.sqrt(
            np.dot(
                list(positions.values()),
                np.dot(returns.cov() * 252, list(positions.values()))
            )
        )
        
        if portfolio_vol == 0:
            return 1.0
        
        return weighted_individual_vol / portfolio_vol
    
    def calculate_risk_metrics(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        position_value: float = 1.0,
        current_equity: float = 100000
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics for a symbol
        """
        timestamp = datetime.now()
        
        # Calculate returns
        returns = price_data['close'].pct_change().dropna()
        
        if len(returns) < 30:
            logger.warning(f"Insufficient data for {symbol} risk calculation")
            return self._default_risk_metrics(timestamp, symbol)
        
        # VaR calculations
        var_results = self.var_model.calculate_var(returns.values, position_value)
        var_95 = var_results.get('var_95', 0.0)
        var_99 = var_results.get('var_99', 0.0)
        
        # CVaR
        cvar_95 = self.var_model.calculate_cvar(returns.values, var_95)
        cvar_99 = self.var_model.calculate_cvar(returns.values, var_99)
        
        # Volatility
        realized_vol = returns.std() * np.sqrt(252)
        ewma_vol = self.var_model.ewma_volatility(returns.values)
        garch_vol = self.var_model.garch_forecast(returns.values) if ARCH_AVAILABLE else None
        
        # Drawdown calculation
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        
        current_dd = drawdown.iloc[-1]
        max_dd = drawdown.min()
        dd_duration = self._calculate_drawdown_duration(drawdown)
        
        # Tail risk
        skew = returns.skew()
        kurt = returns.kurtosis()
        tail_ratio = abs(np.percentile(returns, 95)) / abs(np.percentile(returns, 5))
        
        # Position sizing
        # Kelly-like formula adjusted for risk
        kelly_fraction = 0.25  # Conservative half-Kelly
        
        # Volatility targeting
        vol_mult = min(self.target_volatility / (realized_vol + 1e-6), 2.0)
        
        # VaR-based limit
        var_limit = min(self.max_var_pct / (var_95 / current_equity + 1e-6), 1.0)
        
        # Combined position size
        position_mult = min(kelly_fraction * vol_mult * var_limit, 1.0)
        max_position = position_mult * 0.10  # Max 10% of capital per position
        
        # Risk level classification
        risk_level = self._classify_risk_level(
            var_95, current_dd, realized_vol, current_equity
        )
        
        # Risk factors
        risk_factors = {
            'volatility_risk': min(realized_vol / 0.20, 1.0),  # 20% vol = high risk
            'tail_risk': min(tail_ratio / 2.0, 1.0),
            'drawdown_risk': abs(current_dd) / self.max_drawdown_pct,
            'var_risk': var_95 / (self.max_var_pct * current_equity)
        }
        
        # Generate recommendation
        if risk_level == 'EXTREME':
            rec = "CLOSE POSITION: Risk exceeds maximum thresholds"
        elif risk_level == 'HIGH':
            rec = f"REDUCE SIZE: Position size multiplier {position_mult:.2f}"
        elif risk_level == 'MODERATE':
            rec = f"MONITOR: Risk within acceptable range, size {position_mult:.2f}"
        else:
            rec = f"ACCEPTABLE: Risk low, optimal size {position_mult:.2f}"
        
        return RiskMetrics(
            timestamp=timestamp,
            symbol=symbol,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            realized_vol=realized_vol,
            ewma_vol=ewma_vol,
            garch_vol=garch_vol,
            current_drawdown=current_dd,
            max_drawdown=max_dd,
            drawdown_duration=dd_duration,
            skewness=skew,
            kurtosis=kurt,
            tail_ratio=tail_ratio,
            position_size_mult=position_mult,
            max_position_pct=max_position,
            risk_level=risk_level,
            risk_adjusted=True,
            risk_factors=risk_factors,
            recommendation=rec
        )
    
    def _calculate_drawdown_duration(self, drawdown: pd.Series) -> int:
        """Calculate current drawdown duration in periods"""
        current_dd = drawdown.iloc[-1]
        if current_dd == 0:
            return 0
        
        # Count how many periods we've been in drawdown
        in_drawdown = drawdown < 0
        if not in_drawdown.iloc[-1]:
            return 0
        
        # Find when drawdown started
        duration = 0
        for i in range(len(in_drawdown) - 1, -1, -1):
            if in_drawdown.iloc[i]:
                duration += 1
            else:
                break
        
        return duration
    
    def _classify_risk_level(
        self,
        var_95: float,
        current_dd: float,
        realized_vol: float,
        equity: float
    ) -> str:
        """Classify overall risk level"""
        var_pct = var_95 / equity
        dd_pct = abs(current_dd)
        
        # Score from 0-4
        risk_score = 0
        if var_pct > self.max_var_pct * 1.5:
            risk_score += 2
        elif var_pct > self.max_var_pct:
            risk_score += 1
        
        if dd_pct > self.max_drawdown_pct * 1.5:
            risk_score += 2
        elif dd_pct > self.max_drawdown_pct:
            risk_score += 1
        
        if realized_vol > 0.30:  # >30% annual vol
            risk_score += 1
        
        if risk_score >= 4:
            return 'EXTREME'
        elif risk_score >= 2:
            return 'HIGH'
        elif risk_score >= 1:
            return 'MODERATE'
        else:
            return 'LOW'
    
    def _default_risk_metrics(self, timestamp: datetime, symbol: str) -> RiskMetrics:
        """Default metrics when data insufficient"""
        return RiskMetrics(
            timestamp=timestamp,
            symbol=symbol,
            var_95=0.0,
            var_99=0.0,
            cvar_95=0.0,
            cvar_99=0.0,
            realized_vol=0.1,
            ewma_vol=0.1,
            garch_vol=None,
            current_drawdown=0.0,
            max_drawdown=0.0,
            drawdown_duration=0,
            skewness=0.0,
            kurtosis=3.0,
            tail_ratio=1.0,
            position_size_mult=0.5,
            max_position_pct=0.05,
            risk_level='MODERATE',
            risk_adjusted=False,
            risk_factors={},
            recommendation="INSUFFICIENT DATA: Use conservative sizing"
        )
    
    def check_risk_limits(self, metrics: RiskMetrics) -> Tuple[bool, List[str]]:
        """
        Check if position violates risk limits
        
        Returns (is_safe, list_of_violations)
        """
        violations = []
        
        if metrics.var_95 > self.max_var_pct * 100000:  # Assuming 100k equity
            violations.append(f"VaR 95% {metrics.var_95:.2%} exceeds limit {self.max_var_pct:.2%}")
        
        if abs(metrics.current_drawdown) > self.max_drawdown_pct:
            violations.append(f"Drawdown {abs(metrics.current_drawdown):.2%} exceeds limit {self.max_drawdown_pct:.2%}")
        
        if metrics.realized_vol > 0.50:  # 50% annual vol
            violations.append(f"Volatility {metrics.realized_vol:.2%} extremely high")
        
        return len(violations) == 0, violations


class DynamicRiskAdjuster:
    """
    Dynamic risk adjustment based on market conditions
    
    Adjusts position sizes and risk parameters based on:
    - Current volatility regime
    - Portfolio heat (aggregate risk)
    - Correlation breakdown detection
    """
    
    def __init__(
        self,
        base_position_size: float = 0.10,
        max_portfolio_heat: float = 0.20  # Max 20% aggregate VaR
    ):
        self.base_position_size = base_position_size
        self.max_portfolio_heat = max_portfolio_heat
        self.risk_manager = PortfolioRiskManager()
    
    def adjust_position_sizes(
        self,
        signals: List[Dict],
        portfolio_value: float = 100000
    ) -> Dict[str, float]:
        """
        Adjust all position sizes based on portfolio risk
        
        Implements correlation-adjusted Kelly sizing
        """
        adjusted = {}
        total_heat = 0
        
        for signal in signals:
            symbol = signal.get('symbol', 'UNKNOWN')
            raw_size = signal.get('recommended_size', self.base_position_size)
            confidence = signal.get('confidence', 0.5)
            risk_level = signal.get('risk_level', 'MODERATE')
            
            # Adjust for confidence
            size = raw_size * (0.5 + confidence)
            
            # Adjust for risk level
            risk_mult = {
                'LOW': 1.0,
                'MODERATE': 0.8,
                'HIGH': 0.5,
                'EXTREME': 0.0
            }.get(risk_level, 0.5)
            
            size *= risk_mult
            
            # Check portfolio heat
            var_estimate = size * 0.02  # Rough 2% daily VaR estimate
            if total_heat + var_estimate > self.max_portfolio_heat:
                # Scale down to fit
                size *= (self.max_portfolio_heat - total_heat) / var_estimate
                size = max(0, size)
            
            adjusted[symbol] = size
            total_heat += var_estimate
        
        return adjusted


def create_var_model(method: str = 'historical') -> VaRModel:
    """Factory for VaR model"""
    return VaRModel(method=method)


def create_portfolio_risk_manager(
    max_var_pct: float = 0.02,
    max_drawdown_pct: float = 0.10
) -> PortfolioRiskManager:
    """Factory for portfolio risk manager"""
    return PortfolioRiskManager(
        max_var_pct=max_var_pct,
        max_drawdown_pct=max_drawdown_pct
    )


def create_risk_adjuster(
    base_position_size: float = 0.10
) -> DynamicRiskAdjuster:
    """Factory for dynamic risk adjuster"""
    return DynamicRiskAdjuster(base_position_size=base_position_size)
