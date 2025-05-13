import pandas as pd
import numpy as np
from indicators.momentum import relative_strength_index, detect_overbought_oversold

class MeanReversionStrategy:
    """
    A mean reversion strategy that uses RSI to identify overbought and oversold conditions.
    - Buy when RSI goes below oversold level and then crosses back above it
    - Sell when RSI goes above overbought level and then crosses back below it
    """
    
    def __init__(self, rsi_period=14, oversold=30, overbought=70, exit_middle=50):
        """
        Initialize the strategy with the specified parameters.
        
        Args:
            rsi_period (int): Period for RSI calculation. Default is 14.
            oversold (int): RSI level that indicates oversold conditions. Default is 30.
            overbought (int): RSI level that indicates overbought conditions. Default is 70.
            exit_middle (int): Middle RSI level for exit signals. Default is 50.
        """
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.exit_middle = exit_middle
        self.name = f"Mean Reversion (RSI{rsi_period}: {oversold}/{overbought})"
        
    def prepare_data(self, data):
        """
        Add necessary indicators to the data for this strategy.
        
        Args:
            data (pandas.DataFrame): DataFrame containing the price data.
            
        Returns:
            pandas.DataFrame: DataFrame with added indicators.
        """
        # Create a copy of the input data
        result = data.copy()
        
        # Calculate RSI
        result['rsi'] = relative_strength_index(data, period=self.rsi_period)
        
        # Add overbought/oversold indicators
        result = detect_overbought_oversold(
            result, 
            rsi_lower=self.oversold, 
            rsi_upper=self.overbought
        )
        
        return result
    
    def generate_signals(self, data):
        """
        Generate buy/sell signals based on the strategy.
        
        Args:
            data (pandas.DataFrame): DataFrame containing price data and indicators.
            
        Returns:
            pandas.DataFrame: DataFrame with added signal columns.
        """
        # Make sure necessary indicators are added
        if 'rsi' not in data.columns:
            data = self.prepare_data(data)
            
        result = data.copy()
        
        # Create columns for entry and exit conditions
        result['was_oversold'] = result['rsi'] < self.oversold
        result['was_overbought'] = result['rsi'] > self.overbought
        
        # Shift to get the previous state
        result['prev_was_oversold'] = result['was_oversold'].shift(1)
        result['prev_was_overbought'] = result['was_overbought'].shift(1)
        
        # Generate signals
        result['signal'] = 0
        
        # Buy signal: RSI was below oversold and has now crossed above
        buy_signal = (result['prev_was_oversold'] == True) & (result['rsi'] >= self.oversold)
        result.loc[buy_signal, 'signal'] = 1
        
        # Sell signal: RSI was above overbought and has now crossed below
        sell_signal = (result['prev_was_overbought'] == True) & (result['rsi'] <= self.overbought)
        result.loc[sell_signal, 'signal'] = -1
        
        # Additional exit signals when RSI crosses middle level
        exit_long = (result['rsi'] > self.exit_middle) & (result['rsi'].shift(1) <= self.exit_middle)
        exit_short = (result['rsi'] < self.exit_middle) & (result['rsi'].shift(1) >= self.exit_middle)
        
        result.loc[exit_long, 'signal'] = -1  # Exit long positions
        result.loc[exit_short, 'signal'] = 1   # Exit short positions (for future implementation)
        
        # Generate positions (1 = long, 0 = no position, -1 = short)
        result['position'] = 0
        
        # For a long-only strategy
        current_position = 0
        positions = []
        
        for signal in result['signal']:
            if signal == 1 and current_position <= 0:  # Buy if we don't have a long position
                current_position = 1
            elif signal == -1 and current_position >= 0:  # Sell if we have a long position
                current_position = 0
                
            positions.append(current_position)
            
        result['position'] = positions
        
        return result
    
    def backtest(self, data, initial_capital=10000.0, commission=0.001):
        """
        Run a backtest of the strategy.
        
        Args:
            data (pandas.DataFrame): DataFrame containing price data.
            initial_capital (float): Initial capital for the backtest. Default is 10000.0.
            commission (float): Commission rate per trade. Default is 0.001 (0.1%).
            
        Returns:
            pandas.DataFrame: DataFrame with backtest results.
        """
        # Generate signals and positions
        result = self.generate_signals(data)
        
        # Calculate returns
        result['market_return'] = result['close'].pct_change()
        result['strategy_return'] = result['market_return'] * result['position'].shift(1)
        
        # Account for commissions
        result['trade'] = result['position'].diff().abs()
        result['commission'] = result['trade'] * commission
        result['strategy_return'] = result['strategy_return'] - result['commission']
        
        # Calculate cumulative returns
        result['cumulative_market_return'] = (1 + result['market_return']).cumprod()
        result['cumulative_strategy_return'] = (1 + result['strategy_return']).cumprod()
        
        # Calculate equity and drawdown
        result['equity'] = initial_capital * result['cumulative_strategy_return']
        result['peak'] = result['equity'].cummax()
        result['drawdown'] = (result['peak'] - result['equity']) / result['peak']
        
        return result
    
    def get_performance_metrics(self, backtest_results):
        """
        Calculate performance metrics for the strategy.
        
        Args:
            backtest_results (pandas.DataFrame): DataFrame with backtest results.
            
        Returns:
            dict: Dictionary containing performance metrics as ratios.
        """
        metrics = {}
        metrics['strategy_name'] = self.name

        # Ensure 'strategy_return' and 'cumulative_strategy_return' exist
        if 'strategy_return' not in backtest_results.columns or \
           'cumulative_strategy_return' not in backtest_results.columns:
            # Minimal placeholder if critical columns are missing
            metrics.update({
                'total_return': 0.0, 'market_return': 0.0, 'annual_return': 0.0,
                'volatility': 0.0, 'sharpe_ratio': 0.0, 'max_drawdown': 0.0,
                'trades': 0, 'win_rate': 0.0, 'profit_factor': 0.0
            })
            return metrics

        # Basic metrics - ensure these are ratios
        metrics['total_return'] = backtest_results['cumulative_strategy_return'].iloc[-1] - 1.0
        if 'cumulative_market_return' in backtest_results.columns:
            metrics['market_return'] = backtest_results['cumulative_market_return'].iloc[-1] - 1.0
        else:
            metrics['market_return'] = 0.0
        
        # Annualized metrics (assuming 252 trading days in a year)
        n_days = len(backtest_results)
        n_years = n_days / 252.0 if n_days > 0 else 0 # Avoid division by zero

        if n_years > 0:
            metrics['annual_return'] = (1 + metrics['total_return']) ** (1 / n_years) - 1
        elif metrics['total_return'] != 0 and n_days > 0: # Handle very short periods (less than a year)
             metrics['annual_return'] = metrics['total_return'] * (252.0 / n_days) # Simple scaling
        else: # No trading days or no returns
            metrics['annual_return'] = 0.0
        
        daily_returns = backtest_results['strategy_return'].dropna().fillna(0)
        
        if not daily_returns.empty and len(daily_returns) > 1:
            metrics['volatility'] = daily_returns.std() * np.sqrt(252)
        else:
            metrics['volatility'] = 0.0
            
        if metrics['volatility'] > 0:
            metrics['sharpe_ratio'] = metrics['annual_return'] / metrics['volatility']
        else:
            metrics['sharpe_ratio'] = 0.0
        
        if 'drawdown' in backtest_results.columns and not backtest_results['drawdown'].empty:
            metrics['max_drawdown'] = backtest_results['drawdown'].max() # Already a positive ratio
        else:
            metrics['max_drawdown'] = 0.0
        
        # Trade metrics
        if 'trade' in backtest_results.columns and 1 in backtest_results['trade'].value_counts():
            metrics['trades'] = backtest_results['trade'].value_counts()[1]
        else:
            metrics['trades'] = 0
            
        winning_trades_count = 0
        if metrics['trades'] > 0 and not daily_returns.empty:
            winning_trades_count = (daily_returns[daily_returns > 0]).count()
            metrics['win_rate'] = winning_trades_count / metrics['trades']
        else:
            metrics['win_rate'] = 0.0
        
        # Profit factor
        if metrics['trades'] > 0 and not daily_returns.empty:
            gross_wins = daily_returns[daily_returns > 0].sum()
            gross_losses = abs(daily_returns[daily_returns < 0].sum()) # abs to make it positive
            
            if gross_losses > 0:
                metrics['profit_factor'] = gross_wins / gross_losses
            elif gross_wins > 0: # No losses, but wins
                metrics['profit_factor'] = 1000.0  # Represent high profit factor
            else: # No wins and no losses (or wins are zero, losses are zero)
                metrics['profit_factor'] = 0.0 # Or 1.0 depending on convention for no P/L
        else:
            metrics['profit_factor'] = 0.0
            
        # Ensure all expected keys are present, even if zero
        expected_keys = [
            'strategy_name', 'total_return', 'market_return', 'annual_return',
            'volatility', 'sharpe_ratio', 'max_drawdown', 'trades', 
            'win_rate', 'profit_factor'
        ]
        for key in expected_keys:
            if key not in metrics:
                metrics[key] = 0.0 # Default to 0.0 if somehow missed
        metrics['strategy_name'] = self.name # Ensure name is set

        return metrics
    
    def get_parameters(self):
        """
        Get the parameters for this strategy.
        
        Returns:
            dict: Dictionary containing the strategy parameters.
        """
        return {
            'strategy_type': 'mean_reversion',
            'rsi_period': self.rsi_period,
            'oversold': self.oversold,
            'overbought': self.overbought,
            'exit_middle': self.exit_middle
        }
    
    @staticmethod
    def from_parameters(parameters):
        """
        Create a strategy instance from parameters.
        
        Args:
            parameters (dict): Dictionary containing the strategy parameters.
            
        Returns:
            MeanReversionStrategy: A new instance with the specified parameters.
        """
        return MeanReversionStrategy(
            rsi_period=parameters.get('rsi_period', 14),
            oversold=parameters.get('oversold', 30),
            overbought=parameters.get('overbought', 70),
            exit_middle=parameters.get('exit_middle', 50)
        ) 