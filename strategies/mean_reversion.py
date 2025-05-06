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
            dict: Dictionary containing performance metrics.
        """
        # Basic metrics
        total_return = backtest_results['cumulative_strategy_return'].iloc[-1] - 1.0
        market_return = backtest_results['cumulative_market_return'].iloc[-1] - 1.0
        
        # Annualized metrics (assuming 252 trading days in a year)
        n_days = len(backtest_results)
        n_years = n_days / 252
        
        annual_return = (1 + total_return) ** (1 / n_years) - 1
        
        # Risk metrics
        daily_returns = backtest_results['strategy_return'].dropna()
        volatility = daily_returns.std() * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        max_drawdown = backtest_results['drawdown'].max()
        
        # Trade metrics
        trades = backtest_results['trade'].value_counts()[1] if 1 in backtest_results['trade'].value_counts() else 0
        
        # Calculate win rate
        if trades > 0:
            winning_trades = (daily_returns[daily_returns > 0]).count()
            win_rate = winning_trades / trades
        else:
            win_rate = 0
        
        return {
            'strategy_name': self.name,
            'total_return': total_return * 100,  # Convert to percentage
            'market_return': market_return * 100,  # Convert to percentage
            'annual_return': annual_return * 100,  # Convert to percentage
            'volatility': volatility * 100,  # Convert to percentage
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,  # Convert to percentage
            'trades': trades,
            'win_rate': win_rate * 100  # Convert to percentage
        }
    
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