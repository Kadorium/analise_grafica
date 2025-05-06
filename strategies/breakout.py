import pandas as pd
import numpy as np
from indicators.volume import add_volume_indicators, detect_volume_breakouts
from indicators.volatility import add_volatility_indicators, detect_volatility_breakouts

class BreakoutStrategy:
    """
    A breakout strategy that uses price and volume to detect breakouts.
    - Buy when price breaks above resistance with volume confirmation
    - Sell when price breaks below support with volume confirmation
    """
    
    def __init__(self, lookback_period=20, volume_threshold=1.5, price_threshold=0.02, 
                 volatility_exit=True, atr_multiplier=2.0, use_bbands=True):
        """
        Initialize the strategy with the specified parameters.
        
        Args:
            lookback_period (int): Lookback period for moving averages and volatility. Default is 20.
            volume_threshold (float): Volume threshold for breakout confirmation. Default is 1.5 (150% of average).
            price_threshold (float): Price threshold for breakout detection. Default is 0.02 (2%).
            volatility_exit (bool): Whether to use volatility-based exits. Default is True.
            atr_multiplier (float): Multiplier for ATR to determine stop loss. Default is 2.0.
            use_bbands (bool): Whether to use Bollinger Bands for breakout detection. Default is True.
        """
        self.lookback_period = lookback_period
        self.volume_threshold = volume_threshold
        self.price_threshold = price_threshold
        self.volatility_exit = volatility_exit
        self.atr_multiplier = atr_multiplier
        self.use_bbands = use_bbands
        self.name = f"Breakout (Period:{lookback_period}, Vol:{volume_threshold}x, Price:{price_threshold*100}%)"
        
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
        
        # Add volume indicators
        result = add_volume_indicators(result)
        
        # Add volatility indicators
        result = add_volatility_indicators(result, 
                                         atr_period=self.lookback_period, 
                                         bollinger_window=self.lookback_period)
        
        # Add price moving average
        result[f'sma_{self.lookback_period}'] = data['close'].rolling(window=self.lookback_period).mean()
        
        # Detect volume-based breakouts
        result = detect_volume_breakouts(
            result,
            volume_threshold=self.volume_threshold,
            price_threshold=self.price_threshold
        )
        
        # Detect volatility-based breakouts
        result = detect_volatility_breakouts(result)
        
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
        required_columns = ['price_volume_breakout', 'price_volume_breakdown', 'volume_ratio_20', 'atr']
        if not all(col in data.columns for col in required_columns):
            data = self.prepare_data(data)
            
        result = data.copy()
        
        # Generate signals
        result['signal'] = 0
        
        # Buy signal: Price breakout with volume confirmation
        result.loc[result['price_volume_breakout'] == 1, 'signal'] = 1
        
        # Sell signal: Price breakdown with volume confirmation
        result.loc[result['price_volume_breakdown'] == 1, 'signal'] = -1
        
        # Additional buy signals if using Bollinger Bands
        if self.use_bbands and 'bb_upper_breakout' in result.columns:
            # Buy when price breaks above upper Bollinger Band with volume confirmation
            bb_breakout = (result['bb_upper_breakout'] == 1) & (result['volume_ratio_20'] > self.volume_threshold)
            result.loc[bb_breakout, 'signal'] = 1
            
            # Sell when price breaks below lower Bollinger Band with volume confirmation
            bb_breakdown = (result['bb_lower_breakout'] == 1) & (result['volume_ratio_20'] > self.volume_threshold)
            result.loc[bb_breakdown, 'signal'] = -1
        
        # Generate positions (1 = long, 0 = no position, -1 = short)
        result['position'] = 0
        
        # For a long-only strategy
        current_position = 0
        entry_price = 0
        stop_loss = 0
        positions = []
        
        for i, row in result.iterrows():
            # Check for exit based on stop loss if we have a position
            if current_position > 0 and self.volatility_exit:
                if row['close'] < stop_loss:
                    current_position = 0  # Exit position
            
            # Check for signal-based entries and exits
            if row['signal'] == 1 and current_position <= 0:  # Buy if we don't have a long position
                current_position = 1
                entry_price = row['close']
                # Set stop loss based on ATR
                stop_loss = entry_price - (row['atr'] * self.atr_multiplier)
                
            elif row['signal'] == -1 and current_position >= 0:  # Sell if we have a long position
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
            'strategy_type': 'breakout',
            'lookback_period': self.lookback_period,
            'volume_threshold': self.volume_threshold,
            'price_threshold': self.price_threshold,
            'volatility_exit': self.volatility_exit,
            'atr_multiplier': self.atr_multiplier,
            'use_bbands': self.use_bbands
        }
    
    @staticmethod
    def from_parameters(parameters):
        """
        Create a strategy instance from parameters.
        
        Args:
            parameters (dict): Dictionary containing the strategy parameters.
            
        Returns:
            BreakoutStrategy: A new instance with the specified parameters.
        """
        return BreakoutStrategy(
            lookback_period=parameters.get('lookback_period', 20),
            volume_threshold=parameters.get('volume_threshold', 1.5),
            price_threshold=parameters.get('price_threshold', 0.02),
            volatility_exit=parameters.get('volatility_exit', True),
            atr_multiplier=parameters.get('atr_multiplier', 2.0),
            use_bbands=parameters.get('use_bbands', True)
        ) 