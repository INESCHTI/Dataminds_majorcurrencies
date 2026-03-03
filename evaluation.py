"""
Model Evaluation and Backtesting Framework
TDSP Phase 5 - Evaluation
Comprehensive evaluation metrics and backtesting for Forex models
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (confusion_matrix, classification_report, roc_curve, auc,
                             precision_recall_curve, mean_absolute_error, mean_squared_error,
                             r2_score)
import warnings
warnings.filterwarnings('ignore')


class ModelEvaluator:
    """
    Comprehensive model evaluation with financial metrics
    """
    
    def __init__(self, initial_capital: float = 10000.0, transaction_cost: float = 0.0001):
        """
        Initialize evaluator
        
        Args:
            initial_capital: Starting capital for backtesting
            transaction_cost: Transaction cost as fraction (e.g., 0.0001 = 1 pip)
        """
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost
        self.evaluation_results = {}
        
    def evaluate_classification(self, y_true, y_pred, y_proba=None) -> Dict:
        """
        Evaluate classification model
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_proba: Predicted probabilities (optional)
            
        Returns:
            Dictionary of metrics
        """
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0),
            'f1_score': f1_score(y_true, y_pred, average='weighted', zero_division=0)
        }
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        metrics['confusion_matrix'] = cm.tolist()
        
        # ROC AUC if probabilities available
        if y_proba is not None and len(np.unique(y_true)) == 2:
            fpr, tpr, _ = roc_curve(y_true, y_proba[:, 1] if y_proba.ndim > 1 else y_proba)
            metrics['roc_auc'] = auc(fpr, tpr)
            metrics['fpr'] = fpr.tolist()
            metrics['tpr'] = tpr.tolist()
        
        # Classification report
        metrics['classification_report'] = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
        
        return metrics
    
    def evaluate_regression(self, y_true, y_pred) -> Dict:
        """
        Evaluate regression model
        
        Args:
            y_true: True values
            y_pred: Predicted values
            
        Returns:
            Dictionary of metrics
        """
        metrics = {
            'mae': mean_absolute_error(y_true, y_pred),
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'r2': r2_score(y_true, y_pred),
            'mape': np.mean(np.abs((y_true - y_pred) / y_true)) * 100  # Mean Absolute Percentage Error
        }
        
        # Directional accuracy (important for trading)
        y_true_direction = np.sign(y_true)
        y_pred_direction = np.sign(y_pred)
        metrics['directional_accuracy'] = np.mean(y_true_direction == y_pred_direction)
        
        return metrics
    
    def backtest_strategy(self, 
                         predictions: pd.DataFrame,
                         prices: pd.Series,
                         signal_col: str = 'direction',
                         confidence_col: str = 'confidence',
                         min_confidence: float = 0.5) -> Dict:
        """
        Backtest trading strategy
        
        Args:
            predictions: DataFrame with predictions and confidence
            prices: Series of prices aligned with predictions
            signal_col: Column name for trading signals
            confidence_col: Column name for confidence scores
            min_confidence: Minimum confidence threshold to trade
            
        Returns:
            Dictionary of backtest results
        """
        # Initialize
        capital = self.initial_capital
        position = 0  # -1 = short, 0 = neutral, 1 = long
        trades = []
        equity_curve = [capital]
        
        # Align data
        df = pd.DataFrame({
            'signal': predictions[signal_col],
            'confidence': predictions[confidence_col],
            'price': prices
        }).dropna()
        
        # Convert signals to numeric
        signal_mapping = {'BUY': 1, 'HOLD': 0, 'SELL': -1}
        df['signal_numeric'] = df['signal'].map(signal_mapping)
        
        # Backtest loop
        for i in range(1, len(df)):
            current_signal = df['signal_numeric'].iloc[i-1]
            current_confidence = df['confidence'].iloc[i-1]
            entry_price = df['price'].iloc[i-1]
            exit_price = df['price'].iloc[i]
            
            # Check if we should trade
            if current_confidence < min_confidence:
                current_signal = 0
            
            # Calculate returns
            if position != 0:
                # Close existing position
                if position == 1:  # Long
                    returns = (exit_price - entry_price) / entry_price
                else:  # Short
                    returns = (entry_price - exit_price) / entry_price
                
                # Apply transaction costs
                returns -= self.transaction_cost
                
                # Update capital
                capital *= (1 + returns)
                
                # Record trade
                trades.append({
                    'entry_time': df.index[i-1],
                    'exit_time': df.index[i],
                    'direction': 'LONG' if position == 1 else 'SHORT',
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'returns': returns,
                    'capital': capital
                })
            
            # Open new position
            position = current_signal
            equity_curve.append(capital)
        
        # Calculate metrics
        trades_df = pd.DataFrame(trades)
        
        if len(trades_df) == 0:
            return {
                'total_return': 0.0,
                'num_trades': 0,
                'win_rate': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'trades': [],
                'equity_curve': equity_curve
            }
        
        # Performance metrics
        total_return = (capital - self.initial_capital) / self.initial_capital
        num_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['returns'] > 0])
        win_rate = winning_trades / num_trades if num_trades > 0 else 0.0
        
        # Sharpe ratio
        returns_series = trades_df['returns']
        sharpe_ratio = (returns_series.mean() / returns_series.std() * np.sqrt(252)) if returns_series.std() > 0 else 0.0
        
        # Max drawdown
        equity_series = pd.Series(equity_curve)
        cumulative_max = equity_series.cummax()
        drawdown = (equity_series - cumulative_max) / cumulative_max
        max_drawdown = drawdown.min()
        
        # Average trade metrics
        avg_win = trades_df[trades_df['returns'] > 0]['returns'].mean() if winning_trades > 0 else 0.0
        losing_trades = len(trades_df[trades_df['returns'] < 0])
        avg_loss = trades_df[trades_df['returns'] < 0]['returns'].mean() if losing_trades > 0 else 0.0
        
        # Profit factor
        gross_profit = trades_df[trades_df['returns'] > 0]['returns'].sum()
        gross_loss = abs(trades_df[trades_df['returns'] < 0]['returns'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
        
        return {
            'total_return': total_return,
            'final_capital': capital,
            'num_trades': num_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'trades': trades_df.to_dict('records'),
            'equity_curve': equity_curve
        }
    
    def calculate_financial_metrics(self, returns: pd.Series) -> Dict:
        """
        Calculate financial performance metrics
        
        Args:
            returns: Time series of returns
            
        Returns:
            Dictionary of financial metrics
        """
        # Annualization factor (assuming daily returns)
        annualization_factor = 252
        
        metrics = {
            'total_return': returns.sum(),
            'mean_return': returns.mean(),
            'std_return': returns.std(),
            'sharpe_ratio': (returns.mean() / returns.std() * np.sqrt(annualization_factor)) if returns.std() > 0 else 0.0,
            'sortino_ratio': self._calculate_sortino_ratio(returns, annualization_factor),
            'calmar_ratio': self._calculate_calmar_ratio(returns, annualization_factor),
            'max_drawdown': self._calculate_max_drawdown(returns),
            'win_rate': len(returns[returns > 0]) / len(returns) if len(returns) > 0 else 0.0
        }
        
        return metrics
    
    def _calculate_sortino_ratio(self, returns: pd.Series, annualization_factor: int = 252) -> float:
        """Calculate Sortino ratio"""
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std()
        
        if downside_std == 0:
            return 0.0
        
        return (returns.mean() / downside_std * np.sqrt(annualization_factor))
    
    def _calculate_calmar_ratio(self, returns: pd.Series, annualization_factor: int = 252) -> float:
        """Calculate Calmar ratio"""
        max_dd = abs(self._calculate_max_drawdown(returns))
        
        if max_dd == 0:
            return 0.0
        
        annual_return = returns.mean() * annualization_factor
        return annual_return / max_dd
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def compare_models(self, results_dict: Dict[str, Dict]) -> pd.DataFrame:
        """
        Compare multiple models
        
        Args:
            results_dict: Dictionary mapping model name to results dictionary
            
        Returns:
            DataFrame comparing models
        """
        comparison_data = []
        
        for model_name, results in results_dict.items():
            row = {'model': model_name}
            row.update(results)
            comparison_data.append(row)
        
        return pd.DataFrame(comparison_data)
    
    def generate_report(self, 
                       model_name: str,
                       classification_metrics: Dict = None,
                       backtest_results: Dict = None,
                       save_path: str = None) -> str:
        """
        Generate comprehensive evaluation report
        
        Args:
            model_name: Name of the model
            classification_metrics: Classification metrics
            backtest_results: Backtest results
            save_path: Path to save report (optional)
            
        Returns:
            Report as string
        """
        report = f"""
{'='*80}
MODEL EVALUATION REPORT: {model_name}
{'='*80}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        if classification_metrics:
            report += f"""
CLASSIFICATION METRICS
{'-'*80}
Accuracy:  {classification_metrics['accuracy']:.4f}
Precision: {classification_metrics['precision']:.4f}
Recall:    {classification_metrics['recall']:.4f}
F1 Score:  {classification_metrics['f1_score']:.4f}
"""
            
            if 'roc_auc' in classification_metrics:
                report += f"ROC AUC:   {classification_metrics['roc_auc']:.4f}\n"
        
        if backtest_results:
            report += f"""
BACKTEST RESULTS
{'-'*80}
Initial Capital:  ${self.initial_capital:,.2f}
Final Capital:    ${backtest_results['final_capital']:,.2f}
Total Return:     {backtest_results['total_return']*100:.2f}%

Number of Trades: {backtest_results['num_trades']}
Winning Trades:   {backtest_results['winning_trades']}
Losing Trades:    {backtest_results['losing_trades']}
Win Rate:         {backtest_results['win_rate']*100:.2f}%

Average Win:      {backtest_results['avg_win']*100:.2f}%
Average Loss:     {backtest_results['avg_loss']*100:.2f}%
Profit Factor:    {backtest_results['profit_factor']:.2f}

Sharpe Ratio:     {backtest_results['sharpe_ratio']:.4f}
Max Drawdown:     {backtest_results['max_drawdown']*100:.2f}%
"""
        
        report += f"\n{'='*80}\n"
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(report)
            print(f"Report saved to {save_path}")
        
        return report


class PerformanceVisualizer:
    """
    Visualization tools for model performance
    """
    
    @staticmethod
    def plot_confusion_matrix(cm, labels=None, title='Confusion Matrix', save_path=None):
        """Plot confusion matrix"""
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
        plt.title(title)
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    @staticmethod
    def plot_roc_curve(fpr, tpr, auc_score, title='ROC Curve', save_path=None):
        """Plot ROC curve"""
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, label=f'AUC = {auc_score:.4f}', linewidth=2)
        plt.plot([0, 1], [0, 1], 'k--', label='Random')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(title)
        plt.legend(loc='lower right')
        plt.grid(alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    @staticmethod
    def plot_equity_curve(equity_curve, title='Equity Curve', save_path=None):
        """Plot equity curve from backtesting"""
        plt.figure(figsize=(12, 6))
        plt.plot(equity_curve, linewidth=2)
        plt.xlabel('Trade Number')
        plt.ylabel('Capital ($)')
        plt.title(title)
        plt.grid(alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    @staticmethod
    def plot_feature_importance(feature_importance: Dict, top_n: int = 20, 
                               title='Feature Importance', save_path=None):
        """Plot feature importance"""
        # Sort features by importance
        sorted_features = sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)[:top_n]
        features, importances = zip(*sorted_features)
        
        plt.figure(figsize=(10, 8))
        plt.barh(range(len(features)), importances)
        plt.yticks(range(len(features)), features)
        plt.xlabel('Importance')
        plt.title(title)
        plt.grid(alpha=0.3, axis='x')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    @staticmethod
    def plot_returns_distribution(returns: pd.Series, title='Returns Distribution', save_path=None):
        """Plot distribution of returns"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Histogram
        axes[0].hist(returns, bins=50, alpha=0.7, edgecolor='black')
        axes[0].axvline(returns.mean(), color='red', linestyle='--', label=f'Mean: {returns.mean():.4f}')
        axes[0].set_xlabel('Returns')
        axes[0].set_ylabel('Frequency')
        axes[0].set_title('Returns Histogram')
        axes[0].legend()
        axes[0].grid(alpha=0.3)
        
        # Q-Q plot
        from scipy import stats
        stats.probplot(returns, dist="norm", plot=axes[1])
        axes[1].set_title('Q-Q Plot')
        axes[1].grid(alpha=0.3)
        
        plt.suptitle(title)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    @staticmethod
    def plot_prediction_vs_actual(y_true, y_pred, title='Predictions vs Actual', save_path=None):
        """Plot predictions against actual values"""
        plt.figure(figsize=(10, 6))
        plt.scatter(y_true, y_pred, alpha=0.5)
        plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', lw=2)
        plt.xlabel('Actual Values')
        plt.ylabel('Predicted Values')
        plt.title(title)
        plt.grid(alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()


if __name__ == "__main__":
    print("Model Evaluation Framework - Example Usage")
    
    # Create sample data
    np.random.seed(42)
    y_true = np.random.randint(0, 2, 1000)
    y_pred = np.random.randint(0, 2, 1000)
    
    # Initialize evaluator
    evaluator = ModelEvaluator()
    
    # Evaluate classification
    metrics = evaluator.evaluate_classification(y_true, y_pred)
    print(f"\nClassification Metrics:")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"F1 Score: {metrics['f1_score']:.4f}")
    
    # Generate report
    report = evaluator.generate_report('Example Model', classification_metrics=metrics)
    print(report)
