import pandas as pd
import numpy as np
from indicators.moving_averages import add_moving_averages, add_crossover_signals

class TrendFollowingStrategy:
    """
    A trend following strategy that uses moving average crossovers for signals.
    - Buy when fast MA crosses above slow MA (golden cross)
    - Sell when fast MA crosses below slow MA (death cross)
    """
    
    def __init__(self, fast_ma_type='ema', fast_ma_period=20, slow_ma_type='sma', slow_ma_period=50):
        """
        Initialize the strategy with the specified parameters.
        
        Args:
            fast_ma_type (str): Type of fast moving average ('sma' or 'ema'). Default is 'ema'.
            fast_ma_period (int): Period for the fast moving average. Default is 20.
            slow_ma_type (str): Type of slow moving average ('sma' or 'ema'). Default is 'sma'.
            slow_ma_period (int): Period for the slow moving average. Default is 50.
        """
        self.fast_ma_type = fast_ma_type
        self.fast_ma_period = fast_ma_period
        self.slow_ma_type = slow_ma_type
        self.slow_ma_period = slow_ma_period
        self.name = f"Trend Following ({fast_ma_type.upper()}{fast_ma_period}/{slow_ma_type.upper()}{slow_ma_period})"
        
    def prepare_data(self, data):
        """
        Add necessary indicators to the data for this strategy.
        
        Args:
            data (pandas.DataFrame): DataFrame containing the price data.
            
        Returns:
            pandas.DataFrame: DataFrame with added indicators.
        """
        # Define the periods to add
        sma_periods = []
        ema_periods = []
        
        if self.fast_ma_type == 'sma':
            sma_periods.append(self.fast_ma_period)
        else:
            ema_periods.append(self.fast_ma_period)
            
        if self.slow_ma_type == 'sma':
            sma_periods.append(self.slow_ma_period)
        else:
            ema_periods.append(self.slow_ma_period)
        
        # Add the moving averages
        result = add_moving_averages(data, sma_periods=sma_periods, ema_periods=ema_periods)
        
        # Get the column names for the fast and slow MAs
        fast_ma_col = f"{self.fast_ma_type}_{self.fast_ma_period}"
        slow_ma_col = f"{self.slow_ma_type}_{self.slow_ma_period}"
        
        # Add crossover signals
        result = add_crossover_signals(result, fast_ma_col, slow_ma_col)
        
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
        if 'golden_cross' not in data.columns or 'death_cross' not in data.columns:
            data = self.prepare_data(data)
            
        result = data.copy()
        
        # Generate signals
        result['signal'] = 0
        result.loc[result['golden_cross'] == 1, 'signal'] = 1  # Buy signal
        result.loc[result['death_cross'] == 1, 'signal'] = -1  # Sell signal
        
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
            'strategy_type': 'trend_following',
            'fast_ma_type': self.fast_ma_type,
            'fast_ma_period': self.fast_ma_period,
            'slow_ma_type': self.slow_ma_type,
            'slow_ma_period': self.slow_ma_period
        }
    
    @staticmethod
    def from_parameters(parameters):
        """
        Create a strategy instance from parameters.
        
        Args:
            parameters (dict): Dictionary containing the strategy parameters.
            
        Returns:
            TrendFollowingStrategy: A new instance with the specified parameters.
        """
        return TrendFollowingStrategy(
            fast_ma_type=parameters.get('fast_ma_type', 'ema'),
            fast_ma_period=parameters.get('fast_ma_period', 20),
            slow_ma_type=parameters.get('slow_ma_type', 'sma'),
            slow_ma_period=parameters.get('slow_ma_period', 50)
        ) 