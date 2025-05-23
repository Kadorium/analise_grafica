import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import io
import base64
import json
from datetime import datetime
import logging

# Helper function to convert NumPy types to Python native types
def convert_numpy_types(obj):
    """Convert NumPy types to Python native types for JSON serialization."""
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, (dict,)):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(i) for i in obj]
    else:
        return obj

class Backtester:
    """
    A class for backtesting trading strategies.
    """
    
    def __init__(self, data=None, initial_capital=100.0, commission=0.001):
        """
        Initialize the Backtester.
        
        Args:
            data (pandas.DataFrame, optional): DataFrame containing the price data. Defaults to None.
            initial_capital (float, optional): Initial capital for the backtest. Defaults to 100.0.
            commission (float, optional): Commission rate per trade. Defaults to 0.001 (0.1%).
        """
        self.data = data
        self.initial_capital = initial_capital
        self.commission = commission
        self.results = {}
        
    def set_data(self, data):
        """
        Set the data for backtesting.
        
        Args:
            data (pandas.DataFrame): DataFrame containing the price data.
        """
        self.data = data
        
    def run_backtest(self, strategy, start_date=None, end_date=None):
        """
        Run a backtest for a specific strategy.
        
        Args:
            strategy: An instance of a trading strategy class.
            start_date (str, optional): Start date for the backtest. Format: 'YYYY-MM-DD'.
            end_date (str, optional): End date for the backtest. Format: 'YYYY-MM-DD'.
            
        Returns:
            dict: Dictionary containing backtest results and performance metrics.
        """
        if self.data is None:
            raise ValueError("No data set for backtesting. Call set_data() first.")
            
        # Filter data by date range if specified
        data = self.data.copy()
        
        if start_date:
            start_date = pd.to_datetime(start_date)
            data = data[data['date'] >= start_date]
            
        if end_date:
            end_date = pd.to_datetime(end_date)
            data = data[data['date'] <= end_date]
            
        # Run the backtest using the strategy
        backtest_results = strategy.backtest(data, self.initial_capital, self.commission)
        
        # Get performance metrics
        metrics_result = strategy.get_performance_metrics(backtest_results)
        
        strategy_debug_logs = []
        if isinstance(metrics_result, tuple) and len(metrics_result) == 2:
            # Assuming (metrics_dict, debug_logs_list) for StrategyAdapter
            performance_metrics = metrics_result[0]
            strategy_debug_logs = metrics_result[1]
        else:
            # Assuming metrics_dict directly for other strategy types
            performance_metrics = metrics_result
            
        # Convert NumPy types to Python native types for JSON serialization
        performance_metrics = convert_numpy_types(performance_metrics)
        
        # Store results
        strategy_name = strategy.name
        self.results[strategy_name] = {
            'backtest_results': backtest_results,
            'performance_metrics': performance_metrics,
            'strategy_parameters': strategy.get_parameters(),
            'debug_logs': strategy_debug_logs
        }
        
        return {
            'strategy_name': strategy_name,
            'performance_metrics': performance_metrics,
            'signals': backtest_results,
            'debug_logs': strategy_debug_logs
        }
    
    def compare_strategies(self, strategies, start_date=None, end_date=None):
        """
        Run backtests for multiple strategies and compare their performance.
        
        Args:
            strategies (list): List of strategy instances.
            start_date (str, optional): Start date for the backtest. Format: 'YYYY-MM-DD'.
            end_date (str, optional): End date for the backtest. Format: 'YYYY-MM-DD'.
            
        Returns:
            dict: Dictionary containing performance metrics for all strategies.
        """
        results = {}
        
        for strategy in strategies:
            result = self.run_backtest(strategy, start_date, end_date)
            results[result['strategy_name']] = result['performance_metrics']
            
        # Convert any remaining NumPy types to Python native types
        results = convert_numpy_types(results)
        
        return results
    
    def get_best_strategy(self, metric='sharpe_ratio'):
        """
        Get the best-performing strategy based on a specific metric.
        
        Args:
            metric (str, optional): The metric to use for comparison. 
                                    Options: 'total_return', 'annual_return', 'sharpe_ratio', 'max_drawdown', 'win_rate'.
                                    Defaults to 'sharpe_ratio'.
                                    
        Returns:
            tuple: (best_strategy_name, best_strategy_metrics)
        """
        if not self.results:
            raise ValueError("No backtest results available. Run backtest first.")
            
        metrics = {}
        
        for strategy_name, result in self.results.items():
            metrics[strategy_name] = result['performance_metrics'][metric]
            
        # Find the best strategy based on the metric
        # For drawdown, lower is better; for everything else, higher is better
        if metric == 'max_drawdown':
            best_strategy = min(metrics.items(), key=lambda x: x[1])
        else:
            best_strategy = max(metrics.items(), key=lambda x: x[1])
            
        strategy_name = best_strategy[0]
        return strategy_name, self.results[strategy_name]['performance_metrics']
    
    def plot_equity_curves(self, strategy_names=None):
        """
        Plot equity curves for the specified strategies.
        
        Args:
            strategy_names (list, optional): List of strategy names to include in the plot.
                                           If None, all strategies are included.
                                           
        Returns:
            str: Base64 encoded image.
        """
        if not self.results:
            raise ValueError("No backtest results available. Run backtest first.")
            
        if strategy_names is None:
            strategy_names = list(self.results.keys())
            
        # Create figure
        plt.figure(figsize=(12, 6))
        
        # Plot equity curves for each strategy
        for strategy_name in strategy_names:
            if strategy_name in self.results:
                backtest_results = self.results[strategy_name]['backtest_results']
                plt.plot(backtest_results['date'], backtest_results['equity'], label=strategy_name)
                
        # Plot buy-and-hold equity curve
        if len(strategy_names) > 0:
            first_strategy = strategy_names[0]
            backtest_results = self.results[first_strategy]['backtest_results']
            plt.plot(backtest_results['date'], self.initial_capital * backtest_results['cumulative_market_return'], 
                    label='Buy & Hold', linestyle='--')
        
        plt.title('Equity Curves')
        plt.xlabel('Date')
        plt.ylabel('Equity ($)')
        plt.grid(True)
        plt.legend()
        
        # Format x-axis date
        plt.gca().xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Convert plot to base64 encoded string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return image_base64
    
    def plot_drawdowns(self, strategy_names=None):
        """
        Plot drawdowns for the specified strategies.
        
        Args:
            strategy_names (list, optional): List of strategy names to include in the plot.
                                           If None, all strategies are included.
                                           
        Returns:
            str: Base64 encoded image.
        """
        if not self.results:
            raise ValueError("No backtest results available. Run backtest first.")
            
        if strategy_names is None:
            strategy_names = list(self.results.keys())
            
        # Create figure
        plt.figure(figsize=(12, 6))
        
        # Plot drawdowns for each strategy
        for strategy_name in strategy_names:
            if strategy_name in self.results:
                backtest_results = self.results[strategy_name]['backtest_results']
                plt.plot(backtest_results['date'], backtest_results['drawdown'] * 100, label=strategy_name)
        
        plt.title('Drawdowns')
        plt.xlabel('Date')
        plt.ylabel('Drawdown (%)')
        plt.grid(True)
        plt.legend()
        
        # Format x-axis date
        plt.gca().xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        
        # Invert y-axis for better visualization (drawdowns are negative)
        plt.gca().invert_yaxis()
        
        plt.tight_layout()
        
        # Convert plot to base64 encoded string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return image_base64
    
    def get_trade_statistics(self, strategy_name):
        """
        Get detailed trade statistics for a specific strategy.
        
        Args:
            strategy_name (str): Name of the strategy.
            
        Returns:
            dict: Dictionary containing trade statistics.
        """
        if strategy_name not in self.results:
            raise ValueError(f"Strategy '{strategy_name}' not found in backtest results.")
            
        backtest_results = self.results[strategy_name]['backtest_results']
        
        # Find trades
        trades = []
        position = 0
        entry_date = None
        entry_price = 0
        
        for i, row in backtest_results.iterrows():
            if row['position'] == 1 and position == 0:
                # Entry
                position = 1
                entry_date = row['date']
                entry_price = row['close']
            elif row['position'] == 0 and position == 1:
                # Exit
                exit_date = row['date']
                exit_price = row['close']
                
                # Calculate trade metrics
                trade_return = (exit_price / entry_price) - 1
                trade_length = (exit_date - entry_date).days
                
                trades.append({
                    'entry_date': entry_date.strftime('%Y-%m-%d'),
                    'exit_date': exit_date.strftime('%Y-%m-%d'),
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'trade_return': trade_return * 100,  # Convert to percentage
                    'trade_length': trade_length
                })
                
                position = 0
        
        # Calculate trade statistics
        if trades:
            returns = [trade['trade_return'] for trade in trades]
            lengths = [trade['trade_length'] for trade in trades]
            winning_trades = sum(1 for ret in returns if ret > 0)
            losing_trades = sum(1 for ret in returns if ret <= 0)
            
            statistics = {
                'total_trades': len(trades),
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': (winning_trades / len(trades)) * 100 if len(trades) > 0 else 0,
                'average_return': sum(returns) / len(returns) if len(returns) > 0 else 0,
                'average_winning_return': sum(ret for ret in returns if ret > 0) / winning_trades if winning_trades > 0 else 0,
                'average_losing_return': sum(ret for ret in returns if ret <= 0) / losing_trades if losing_trades > 0 else 0,
                'average_trade_length': sum(lengths) / len(lengths) if len(lengths) > 0 else 0,
                'max_return': max(returns) if returns else 0,
                'min_return': min(returns) if returns else 0,
                'trades': trades
            }
        else:
            statistics = {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'average_return': 0,
                'average_winning_return': 0,
                'average_losing_return': 0,
                'average_trade_length': 0,
                'max_return': 0,
                'min_return': 0,
                'trades': []
            }
            
        return statistics
    
    def save_results(self, filepath):
        """
        Save backtest results to a JSON file.
        
        Args:
            filepath (str): Path to save the JSON file.
            
        Returns:
            str: Path to the saved file.
        """
        if not self.results:
            raise ValueError("No backtest results available. Run backtest first.")
            
        # Create a dict with serializable results
        output = {}
        
        for strategy_name, result in self.results.items():
            # Convert DataFrames to JSON
            backtest_json = {}
            for col in result['backtest_results'].columns:
                if col == 'date':
                    # Convert dates to strings
                    backtest_json[col] = [d.strftime('%Y-%m-%d') for d in result['backtest_results'][col]]
                else:
                    # Convert other columns to lists
                    backtest_json[col] = result['backtest_results'][col].tolist()
            
            output[strategy_name] = {
                'performance_metrics': result['performance_metrics'],
                'strategy_parameters': result['strategy_parameters'],
                'backtest_summary': {
                    'initial_capital': self.initial_capital,
                    'final_equity': result['backtest_results']['equity'].iloc[-1],
                    'start_date': result['backtest_results']['date'].iloc[0].strftime('%Y-%m-%d'),
                    'end_date': result['backtest_results']['date'].iloc[-1].strftime('%Y-%m-%d'),
                    'total_days': len(result['backtest_results'])
                }
            }
        
        # Save to JSON file
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=4)
            
        return filepath
    
    def load_results(self, filepath):
        """
        Load backtest results from a JSON file.
        
        Args:
            filepath (str): Path to the JSON file.
            
        Returns:
            dict: Loaded backtest results.
        """
        # Load from JSON file
        with open(filepath, 'r') as f:
            loaded_results = json.load(f)
            
        self.results = loaded_results
        return loaded_results
    
    def plot_price_with_trade_signals(self, signals_df, strategy_name='Strategy', initial_capital=100.0):
        """
        Plot price with buy/sell/exit signals and equity as a subplot.
        Args:
            signals_df (pd.DataFrame): DataFrame with backtest results (must include 'date', 'close', 'signal', 'equity')
            strategy_name (str): Name of the strategy
            initial_capital (float): Initial capital for Buy & Hold calculation
        Returns:
            str: Base64 encoded image.
        """
        import matplotlib.pyplot as plt
        from matplotlib.dates import DateFormatter
        import io, base64
        logger = logging.getLogger("trading-app")
        df = signals_df.copy()
        logger.info(f"[plot_price_with_trade_signals] DataFrame shape: {df.shape}, columns: {list(df.columns)}")
        logger.info(f"[plot_price_with_trade_signals] DataFrame head:\n{df.head(5)}")
        # Check for required columns
        required_cols = ['date', 'close', 'signal', 'equity', 'position']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if len(df) == 0 or missing_cols:
            logger.warning(f"[plot_price_with_trade_signals] DataFrame is empty or missing columns: {missing_cols}")
            # Create a simple error plot
            fig, ax = plt.subplots(figsize=(10, 6))
            msg = "No data to plot. "
            if missing_cols:
                msg += f"Missing columns: {', '.join(missing_cols)}"
            else:
                msg += "DataFrame is empty."
            ax.text(0.5, 0.5, msg, horizontalalignment='center', verticalalignment='center', fontsize=14, color='red')
            ax.set_xticks([])
            ax.set_yticks([])
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
            return image_base64
        # Ensure date is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        # Prepare buy/sell/exit points
        buy_mask = df['signal'] == 'buy'
        sell_mask = df['signal'] == 'sell'
        # Find exit points (where position goes from 1 to 0)
        exit_mask = (df['position'].shift(1) == 1) & (df['position'] == 0)
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True, gridspec_kw={'height_ratios': [2, 1]})
        # --- Top: Price with trade signals ---
        ax1.plot(df['date'], df['close'], label='Price', color='black', linewidth=1.5, zorder=1)
        ax1.scatter(df.loc[buy_mask, 'date'], df.loc[buy_mask, 'close'], marker='^', color='green', s=80, label='Buy', zorder=3)
        ax1.scatter(df.loc[sell_mask, 'date'], df.loc[sell_mask, 'close'], marker='v', color='red', s=80, label='Sell', zorder=3)
        ax1.scatter(df.loc[exit_mask, 'date'], df.loc[exit_mask, 'close'], marker='o', color='blue', s=60, label='Exit', zorder=3)
        ax1.set_ylabel('Price')
        ax1.set_title(f'Price with Trade Signals ({strategy_name})')
        ax1.legend(loc='upper left')
        ax1.grid(True)
        # --- Bottom: Equity curve ---
        ax2.plot(df['date'], df['equity'], label='Strategy Equity', color='teal', linewidth=1.5)
        if 'cumulative_market_return' in df.columns:
            ax2.plot(df['date'], initial_capital * df['cumulative_market_return'], label='Buy & Hold', color='grey', linestyle='--')
        ax2.set_ylabel('Equity')
        ax2.set_title('Equity Curve')
        ax2.legend(loc='upper left')
        ax2.grid(True)
        # Format x-axis
        date_format = DateFormatter('%Y-%m-%d')
        ax2.xaxis.set_major_formatter(date_format)
        plt.xticks(rotation=45)
        plt.tight_layout()
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        return image_base64 