import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from concurrent.futures import ProcessPoolExecutor, as_completed
import traceback
import logging
from datetime import datetime
import os

from backtesting.backtester import Backtester
from strategies import create_strategy, get_default_parameters
from optimization.optimizer import grid_search as grid_search_params

logger = logging.getLogger("trading-app.comparison")

class StrategyComparator:
    """
    A class for comparing multiple trading strategies with different parameter sets.
    Supports both regular comparison and optimized comparison.
    """
    
    def __init__(self, data, initial_capital=100.0, commission=0.001):
        """
        Initialize the StrategyComparator.
        
        Args:
            data (pandas.DataFrame): DataFrame containing the price data
            initial_capital (float): Initial capital for backtesting
            commission (float): Commission rate per trade
        """
        self.data = data
        self.initial_capital = initial_capital
        self.commission = commission
        self.backtester = Backtester(data, initial_capital, commission)
        self.results = {}
        
    def compare_strategies(self, strategy_configs, start_date=None, end_date=None):
        """
        Compare multiple strategies with specified parameters.
        
        Args:
            strategy_configs (list): List of dictionaries with keys 'strategy_id' and 'parameters'
            start_date (str, optional): Start date for backtesting in YYYY-MM-DD format
            end_date (str, optional): End date for backtesting in YYYY-MM-DD format
            
        Returns:
            dict: Dictionary containing comparison results
        """
        self.results = {}
        
        for config in strategy_configs:
            strategy_id = config['strategy_id']
            parameters = config['parameters']
            
            # Create strategy instance
            strategy = create_strategy(strategy_id, **parameters)
            
            # Run backtest
            result = self.backtester.run_backtest(strategy, start_date, end_date)
            
            # Store metrics and signals
            self.results[strategy_id] = {
                'parameters': parameters,
                'metrics': result['performance_metrics'],
                'signals': result['signals']
            }
        
        # Create comparison metrics and visualizations
        comparison_data = self._prepare_comparison_data()
        
        return {
            'results': self.results,
            'comparison': comparison_data,
            'chart_base64': self.plot_comparison()
        }
    
    def optimize_and_compare(self, strategy_configs, metric='sharpe_ratio', start_date=None, end_date=None, max_workers=4):
        """
        Optimize parameters for each strategy and then compare the optimized versions.
        
        Args:
            strategy_configs (list): List of dictionaries with keys 'strategy_id', 'parameters', and 'param_ranges'
            metric (str): Metric to optimize for (e.g., 'sharpe_ratio', 'total_return')
            start_date (str, optional): Start date for backtesting in YYYY-MM-DD format
            end_date (str, optional): End date for backtesting in YYYY-MM-DD format
            max_workers (int): Maximum number of parallel workers for optimization
            
        Returns:
            dict: Dictionary containing optimized comparison results
        """
        self.results = {}
        optimized_configs = []
        
        for config in strategy_configs:
            strategy_id = config['strategy_id']
            current_params = config['parameters']
            
            # Check if param_ranges are provided for optimization
            if 'param_ranges' in config and config['param_ranges']:
                param_ranges = config['param_ranges']
                logger.info(f"Optimizing {strategy_id} with parameter ranges: {param_ranges}")
                
                # Perform grid search optimization
                try:
                    best_params, best_score = grid_search_params(
                        data=self.data,
                        strategy_type=strategy_id,
                        param_ranges=param_ranges,
                        initial_capital=self.initial_capital,
                        commission=self.commission,
                        metric=metric,
                        start_date=start_date,
                        end_date=end_date,
                        max_workers=max_workers
                    )
                    
                    logger.info(f"Optimization for {strategy_id} complete. Best score ({metric}): {best_score}")
                    logger.info(f"Best parameters for {strategy_id}: {best_params}")
                    
                    # Use optimized parameters
                    optimized_configs.append({
                        'strategy_id': strategy_id,
                        'parameters': best_params,
                        'optimized': True,
                        'optimization_metric': metric,
                        'optimization_score': best_score
                    })
                except Exception as e:
                    logger.error(f"Error optimizing {strategy_id}: {str(e)}\n{traceback.format_exc()}")
                    # Fall back to provided parameters
                    optimized_configs.append({
                        'strategy_id': strategy_id,
                        'parameters': current_params,
                        'optimized': False,
                        'optimization_error': str(e)
                    })
            else:
                # No optimization requested, use provided parameters
                optimized_configs.append({
                    'strategy_id': strategy_id,
                    'parameters': current_params,
                    'optimized': False
                })
        
        # Compare the strategies with optimized parameters
        return self.compare_strategies(optimized_configs, start_date, end_date)
    
    def _prepare_comparison_data(self):
        """
        Prepare data for comparison visualization.
        
        Returns:
            dict: Dictionary containing comparison metrics
        """
        if not self.results:
            return {}
        
        # Extract metrics for comparison
        metrics_to_compare = ['total_return', 'annual_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']
        comparison_metrics = {}
        
        for metric in metrics_to_compare:
            comparison_metrics[metric] = {
                strategy_id: result['metrics'].get(metric, 0) 
                for strategy_id, result in self.results.items()
            }
        
        # Find best strategy for each metric
        best_strategies = {}
        for metric in metrics_to_compare:
            metric_values = comparison_metrics[metric]
            
            if metric == 'max_drawdown':  # For drawdown, lower is better
                best_strategy = min(metric_values.items(), key=lambda x: x[1])
            else:  # For other metrics, higher is better
                best_strategy = max(metric_values.items(), key=lambda x: x[1])
                
            best_strategies[metric] = best_strategy[0]
        
        return {
            'metrics': comparison_metrics,
            'best_strategies': best_strategies
        }
    
    def plot_comparison(self):
        """
        Create comparison charts.
        
        Returns:
            str: Base64 encoded chart image
        """
        if not self.results:
            return ""
        
        # Equity curve comparison
        plt.figure(figsize=(12, 8))
        
        # Extract dates and equity curves
        for strategy_id, result in self.results.items():
            signals_df = result['signals']
            plt.plot(signals_df['date'], signals_df['equity'], label=f"{strategy_id}")
        
        # Add buy & hold for reference
        first_strategy = list(self.results.keys())[0]
        signals_df = self.results[first_strategy]['signals']
        plt.plot(
            signals_df['date'], 
            self.initial_capital * signals_df['cumulative_market_return'], 
            label='Buy & Hold', 
            linestyle='--', 
            color='gray'
        )
        
        plt.title('Strategy Comparison: Equity Curves')
        plt.xlabel('Date')
        plt.ylabel('Equity ($)')
        plt.legend()
        plt.grid(True)
        
        # Adjust margins and save
        plt.tight_layout()
        
        # Convert plot to base64 encoded string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return image_base64
    
    def get_comparison_table_data(self):
        """
        Generate data for comparison tables.
        
        Returns:
            dict: Dictionary with data for metrics table, parameters table, and trades table
        """
        if not self.results:
            return {}
        
        # Metrics comparison
        comparison_data = self._prepare_comparison_data()
        
        # Parameters comparison
        parameters_data = {
            strategy_id: result['parameters'] 
            for strategy_id, result in self.results.items()
        }
        
        # Trade statistics
        trades_data = {}
        for strategy_id, result in self.results.items():
            signals_df = result['signals']
            
            # Extract buy and sell signals
            trades = []
            buy_signals = signals_df[signals_df['signal'] == 'buy'].copy()
            sell_signals = signals_df[signals_df['signal'] == 'sell'].copy()
            
            for i, buy_row in buy_signals.iterrows():
                # Find next sell after this buy
                next_sells = sell_signals[sell_signals['date'] > buy_row['date']]
                if not next_sells.empty:
                    sell_row = next_sells.iloc[0]
                    
                    # Calculate profit
                    buy_price = buy_row['close']
                    sell_price = sell_row['close']
                    profit_pct = (sell_price - buy_price) / buy_price * 100
                    
                    trades.append({
                        'entry_date': buy_row['date'].strftime('%Y-%m-%d'),
                        'exit_date': sell_row['date'].strftime('%Y-%m-%d'),
                        'entry_price': buy_price,
                        'exit_price': sell_price,
                        'profit_pct': profit_pct,
                        'result': 'win' if profit_pct > 0 else 'loss'
                    })
            
            trades_data[strategy_id] = trades
        
        return {
            'metrics': comparison_data['metrics'],
            'best_strategies': comparison_data['best_strategies'],
            'parameters': parameters_data,
            'trades': trades_data
        }

# Helper function to run comparison outside of the class
def run_comparison(data, strategy_configs, initial_capital=100.0, commission=0.001, 
                  start_date=None, end_date=None, optimize=False, optimization_metric='sharpe_ratio'):
    """
    Run a comparison of multiple strategies.
    
    Args:
        data (pandas.DataFrame): DataFrame containing the price data
        strategy_configs (list): List of strategy configuration dictionaries
        initial_capital (float): Initial capital for backtesting
        commission (float): Commission rate per trade
        start_date (str, optional): Start date for backtesting
        end_date (str, optional): End date for backtesting
        optimize (bool): Whether to optimize strategies before comparison
        optimization_metric (str): Metric to optimize for if optimize=True
        
    Returns:
        dict: Comparison results
    """
    comparator = StrategyComparator(data, initial_capital, commission)
    
    if optimize:
        return comparator.optimize_and_compare(
            strategy_configs=strategy_configs,
            metric=optimization_metric,
            start_date=start_date,
            end_date=end_date
        )
    else:
        return comparator.compare_strategies(
            strategy_configs=strategy_configs,
            start_date=start_date,
            end_date=end_date
        ) 