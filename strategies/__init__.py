import os
import importlib
from strategies.trend_following import TrendFollowingStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.breakout import BreakoutStrategy

__all__ = [
    'TrendFollowingStrategy',
    'MeanReversionStrategy',
    'BreakoutStrategy',
    'STRATEGY_REGISTRY',
    'create_strategy',
    'get_default_parameters',
    'AVAILABLE_STRATEGIES'
]

# Dynamically import all strategy modules
STRATEGY_REGISTRY = {}
strategy_dir = os.path.dirname(__file__)
for filename in os.listdir(strategy_dir):
    if filename.endswith('_strategy.py'):
        module_name = filename[:-3]  # Remove .py
        strategy_name = module_name.replace('_strategy', '')  # e.g., sma_crossover
        try:
            module = importlib.import_module(f'.{module_name}', package='strategies')
            if hasattr(module, 'generate_signals'):
                STRATEGY_REGISTRY[strategy_name] = module.generate_signals
                print(f"Registered strategy: {strategy_name}")
        except Exception as e:
            print(f"Error importing {module_name}: {e}")

# Adapter class to make function-based strategies compatible with the Backtester
class StrategyAdapter:
    def __init__(self, name, strategy_func, parameters):
        self.name = name
        self.strategy_func = strategy_func
        self.parameters = parameters
    
    def backtest(self, data, initial_capital=10000.0, commission=0.001):
        """Run backtest using the strategy function"""
        # Call the strategy function to get signals
        result_df = self.strategy_func(data, **self.parameters)
        
        # Ensure required columns exist
        if 'signal' not in result_df.columns:
            raise ValueError("Strategy must provide a 'signal' column")
        
        # Calculate positions, equity, returns, and drawdowns
        df = result_df.copy()
        
        # Initialize position and equity columns if they don't exist
        if 'position' not in df.columns:
            df['position'] = 0
            # Convert signals to positions (cumulative sum of signals)
            df['position'] = df['signal'].cumsum()
        
        # Calculate price returns
        if 'price_return' not in df.columns:
            df['price_return'] = df['close'].pct_change().fillna(0)
            df['price_return_cumulative'] = (1 + df['price_return']).cumprod() - 1
        
        # Calculate strategy returns
        if 'strategy_return' not in df.columns:
            df['strategy_return'] = df['position'].shift(1) * df['price_return']
            df['strategy_return'].iloc[0] = 0  # Set first day's return to 0
            df['strategy_return_cumulative'] = (1 + df['strategy_return']).cumprod() - 1
        
        # Calculate equity curve
        if 'equity' not in df.columns:
            df['equity'] = initial_capital * (1 + df['strategy_return_cumulative'])
        
        # Calculate drawdowns
        if 'drawdown' not in df.columns:
            df['peak'] = df['equity'].cummax()
            df['drawdown'] = (df['peak'] - df['equity']) / df['peak']
        
        # Calculate trade statistics
        if 'trade' not in df.columns:
            # Identify trades (position changes)
            df['trade'] = df['position'].diff().ne(0).astype(int)
            
            # Calculate trade profits
            df['trade_profit'] = 0.0
            trades = df[df['trade'] == 1].index
            
            for i in range(1, len(trades)):
                entry_idx = trades[i-1]
                exit_idx = trades[i]
                
                # Calculate profit for this trade
                entry_price = df.loc[entry_idx, 'close']
                exit_price = df.loc[exit_idx, 'close']
                position = df.loc[entry_idx, 'position']
                
                # If position is positive, long trade; if negative, short trade
                profit = position * (exit_price - entry_price) * initial_capital / entry_price
                
                # Apply commission
                profit -= abs(position) * commission * initial_capital
                
                # Store profit at exit point
                df.loc[exit_idx, 'trade_profit'] = profit
        
        # Calculate daily returns
        if 'daily_return' not in df.columns:
            df['daily_return'] = df['equity'].pct_change().fillna(0)
        
        # Store the backtest results for use in get_performance_metrics
        self.backtest_results = df
        
        return df
    
    def _sanitize_float(self, value):
        """
        Sanitize float values to ensure they are JSON-compatible
        - Replace inf with a large number
        - Replace -inf with a large negative number
        - Replace NaN with 0
        """
        import math
        import numpy as np
        
        if value is None:
            return 0
        
        # Check for numpy types
        if isinstance(value, (np.integer, np.int64, np.int32)):
            return int(value)
        elif isinstance(value, (np.floating, np.float64, np.float32)):
            value = float(value)
        
        # Handle non-finite values
        if math.isnan(value):
            return 0
        elif math.isinf(value):
            if value > 0:
                return 1.0e+308  # Max JSON-compatible float
            else:
                return -1.0e+308
        
        return value
    
    def get_performance_metrics(self):
        """Calculate performance metrics from backtest results"""
        if not hasattr(self, 'backtest_results') or self.backtest_results is None:
            return {}
            
        df = self.backtest_results
        
        # Initialize metrics dictionary
        metrics = {}
        
        try:
            # Calculate total return
            total_return = df['equity'].iloc[-1] / df['equity'].iloc[0] - 1
            metrics['total_return'] = total_return
            
            # Calculate annualized return
            days = (df['date'].iloc[-1] - df['date'].iloc[0]).days
            annual_return = (1 + total_return) ** (365 / max(days, 1)) - 1
            metrics['annual_return'] = annual_return
            
            # Calculate daily returns
            if 'daily_return' not in df.columns:
                df['daily_return'] = df['equity'].pct_change().fillna(0)
            
            # Calculate Sharpe ratio (assuming risk-free rate of 0)
            daily_return_std = df['daily_return'].std()
            if daily_return_std > 0:
                metrics['sharpe_ratio'] = (df['daily_return'].mean() * 252) / (daily_return_std * (252 ** 0.5))
            else:
                metrics['sharpe_ratio'] = 0.0
            
            # Calculate Sortino ratio (downside risk only)
            negative_returns = df['daily_return'][df['daily_return'] < 0]
            if len(negative_returns) > 0:
                downside_std = negative_returns.std() * (252 ** 0.5)
                metrics['sortino_ratio'] = (df['daily_return'].mean() * 252) / downside_std if downside_std > 0 else 0
            else:
                metrics['sortino_ratio'] = metrics['sharpe_ratio'] * 1.5  # Approximation if no negative returns
            
            # Calculate max drawdown
            if 'drawdown' in df.columns:
                metrics['max_drawdown'] = df['drawdown'].max()
            else:
                df['peak'] = df['equity'].cummax()
                df['drawdown'] = (df['peak'] - df['equity']) / df['peak']
                metrics['max_drawdown'] = df['drawdown'].max()
            
            # Calculate Calmar ratio
            if metrics['max_drawdown'] > 0:
                metrics['calmar_ratio'] = annual_return / metrics['max_drawdown']
            else:
                metrics['calmar_ratio'] = metrics['sharpe_ratio'] / 2  # Approximation if no drawdown
            
            # Calculate win rate and profit factor
            if 'trade_profit' in df.columns:
                trades = df[df['trade_profit'] != 0]
                if len(trades) > 0:
                    winning_trades = trades[trades['trade_profit'] > 0]
                    losing_trades = trades[trades['trade_profit'] < 0]
                    
                    win_count = len(winning_trades)
                    total_trades = len(trades)
                    
                    metrics['win_rate'] = win_count / total_trades
                    metrics['number_of_trades'] = total_trades
                    
                    # Calculate profit factor
                    total_profit = winning_trades['trade_profit'].sum() if len(winning_trades) > 0 else 0
                    total_loss = abs(losing_trades['trade_profit'].sum()) if len(losing_trades) > 0 else 0
                    
                    if total_loss > 0:
                        metrics['profit_factor'] = total_profit / total_loss
                    else:
                        metrics['profit_factor'] = 1.0 if total_profit == 0 else 10.0
                    
                    # Calculate consecutive wins and losses
                    # Extract trade results as sequence of wins (True) and losses (False)
                    trade_results = []
                    for _, row in trades.iterrows():
                        if row['trade_profit'] > 0:
                            trade_results.append(True)  # Win
                        else:
                            trade_results.append(False)  # Loss
                    
                    # Find max consecutive wins
                    max_wins = 0
                    current_streak = 0
                    for result in trade_results:
                        if result:  # Win
                            current_streak += 1
                            max_wins = max(max_wins, current_streak)
                        else:
                            current_streak = 0
                    
                    metrics['max_consecutive_wins'] = max_wins
                    
                    # Find max consecutive losses
                    max_losses = 0
                    current_streak = 0
                    for result in trade_results:
                        if not result:  # Loss
                            current_streak += 1
                            max_losses = max(max_losses, current_streak)
                        else:
                            current_streak = 0
                    
                    metrics['max_consecutive_losses'] = max_losses
            else:
                metrics['win_rate'] = 0.5  # Default
                metrics['profit_factor'] = 1.0  # Default
                metrics['max_consecutive_wins'] = 0
                metrics['max_consecutive_losses'] = 0
                metrics['number_of_trades'] = 0
            
            # Calculate percent profitable days
            profitable_days = (df['daily_return'] > 0).sum()
            total_days = len(df)
            metrics['percent_profitable_days'] = (profitable_days / total_days) if total_days > 0 else 0
            
            # Add percentage versions of metrics for frontend compatibility
            metrics['total_return_percent'] = metrics['total_return'] * 100
            metrics['annual_return_percent'] = metrics['annual_return'] * 100
            metrics['max_drawdown_percent'] = metrics['max_drawdown'] * 100
            metrics['win_rate_percent'] = metrics['win_rate'] * 100
            
            # Sanitize metrics for JSON serialization
            metrics = {k: self._sanitize_float(v) for k, v in metrics.items()}
            
            # Add logging to see what metrics are being calculated
            print(f"[DEBUG] Strategy '{self.name}' metrics: {metrics}")
            
        except Exception as e:
            print(f"Error calculating metrics: {str(e)}")
            # Return minimal set of metrics if calculation fails
            metrics = {
                'total_return': 0,
                'annual_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'win_rate': 0,
                'profit_factor': 1.0,
                'sortino_ratio': 0,
                'calmar_ratio': 0,
                'percent_profitable_days': 0,
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0,
                'total_return_percent': 0,
                'annual_return_percent': 0,
                'max_drawdown_percent': 0,
                'win_rate_percent': 0
            }
        
        return metrics
    
    def get_parameters(self):
        """Return the strategy parameters"""
        return self.parameters

# Factory function to create strategy instances based on type
def create_strategy(strategy_type, **parameters):
    """
    Create a strategy instance based on the strategy type.
    
    Args:
        strategy_type (str): Type of strategy ('trend_following', 'mean_reversion', or 'breakout').
        **parameters: Strategy-specific parameters.
        
    Returns:
        Strategy: An instance of the requested strategy.
    """
    # First check if it's one of the new modular strategies
    if strategy_type in STRATEGY_REGISTRY:
        # Use the default parameters and update with the provided parameters
        all_params = get_default_parameters(strategy_type).copy()
        all_params.update(parameters)
        
        # Create a strategy adapter that wraps the function
        return StrategyAdapter(
            name=strategy_type,
            strategy_func=STRATEGY_REGISTRY[strategy_type],
            parameters=all_params
        )
    
    # Otherwise use the legacy strategy classes
    if strategy_type == 'trend_following':
        return TrendFollowingStrategy.from_parameters(parameters)
    elif strategy_type == 'mean_reversion':
        return MeanReversionStrategy.from_parameters(parameters)
    elif strategy_type == 'breakout':
        return BreakoutStrategy.from_parameters(parameters)
    else:
        raise ValueError(f"Unknown strategy type: {strategy_type}")

# Function to get default parameters for each strategy type
def get_default_parameters(strategy_type):
    """
    Get default parameters for a strategy type.
    
    Args:
        strategy_type (str): Type of strategy ('trend_following', 'mean_reversion', or 'breakout').
        
    Returns:
        dict: Default parameters for the strategy.
    """
    # Default parameters for new strategy types
    default_params = {
        'sma_crossover': {'short_period': 50, 'long_period': 200},
        'ema_crossover': {'short_period': 20, 'long_period': 50},
        'supertrend': {'period': 10, 'multiplier': 2.0},
        'adx': {'period': 14, 'threshold': 25},
        'bollinger_breakout': {'period': 20, 'std_dev': 2.0},
        'atr_breakout': {'period': 14, 'multiplier': 1.5},
        'donchian_breakout': {'period': 20},
        'keltner_reversal': {'period': 20, 'multiplier': 2.0},
        'rsi': {'period': 14, 'buy_level': 30, 'sell_level': 70},
        'macd_crossover': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
        'stochastic': {'k_period': 14, 'd_period': 3},
        'cci': {'period': 20},
        'williams_r': {'period': 14},
        'obv_trend': {'period': 20},
        'vpt_signal': {'period': 20},
        'volume_ratio': {'period': 20, 'threshold': 2.0},
        'cmf': {'period': 20},
        'accum_dist': {'period': 20},
        'candlestick': {},
        'adaptive_trend': {'fast_period': 10, 'slow_period': 30, 'signal_period': 9},
        'hybrid_momentum_volatility': {'rsi_period': 14, 'bb_period': 20, 'std_dev': 2.0},
        'pattern_recognition': {'lookback': 5}
    }
    
    # Check if it's one of the new strategies
    if strategy_type in default_params:
        return default_params[strategy_type]
    
    # Legacy strategies
    if strategy_type == 'trend_following':
        return {
            'fast_ma_type': 'ema',
            'fast_ma_period': 20,
            'slow_ma_type': 'sma',
            'slow_ma_period': 50
        }
    elif strategy_type == 'mean_reversion':
        return {
            'rsi_period': 14,
            'oversold': 30,
            'overbought': 70,
            'exit_middle': 50
        }
    elif strategy_type == 'breakout':
        return {
            'lookback_period': 20,
            'volume_threshold': 1.5,
            'price_threshold': 0.02,
            'volatility_exit': True,
            'atr_multiplier': 2.0,
            'use_bbands': True
        }
    else:
        raise ValueError(f"Unknown strategy type: {strategy_type}")

# List of available strategies with descriptions
AVAILABLE_STRATEGIES = [
    {
        'type': 'trend_following',
        'name': 'Trend Following (Moving Average Crossover)',
        'description': 'Buys when fast MA crosses above slow MA (golden cross) and sells when fast MA crosses below slow MA (death cross).'
    },
    {
        'type': 'mean_reversion',
        'name': 'Mean Reversion (RSI)',
        'description': 'Buys when RSI moves from oversold to normal levels and sells when RSI moves from overbought to normal levels.'
    },
    {
        'type': 'breakout',
        'name': 'Breakout (Price & Volume)',
        'description': 'Buys when price breaks above resistance with increased volume and sells when price breaks below support with increased volume.'
    }
]

# Add new strategies to AVAILABLE_STRATEGIES
strategy_descriptions = {
    'sma_crossover': 'SMA Crossover: Buys when short SMA crosses above long SMA and sells when it crosses below.',
    'ema_crossover': 'EMA Crossover: Buys when short EMA crosses above long EMA and sells when it crosses below.',
    'supertrend': 'SuperTrend: Trend following indicator that uses ATR for volatility-based entries and exits.',
    'adx': 'ADX (Average Directional Index): Identifies trend strength and potential reversals.',
    'bollinger_breakout': 'Bollinger Bands Breakout: Signals when price breaks out of the Bollinger Bands.',
    'atr_breakout': 'ATR Breakout: Uses Average True Range to identify significant price movements.',
    'donchian_breakout': 'Donchian Channel Breakout: Buys/sells when price breaks above/below the Donchian channel.',
    'keltner_reversal': 'Keltner Channel Reversal: Looks for reversals at Keltner channel boundaries.',
    'rsi': 'RSI (Relative Strength Index): Identifies overbought and oversold conditions.',
    'macd_crossover': 'MACD Crossover: Momentum indicator that shows the relationship between two moving averages.',
    'stochastic': 'Stochastic Oscillator: Compares current price to its range over a period of time.',
    'cci': 'Commodity Channel Index: Identifies cyclical trends in price movement.',
    'williams_r': 'Williams %R: Momentum indicator that measures overbought/oversold levels.',
    'obv_trend': 'On-Balance Volume Trend: Uses volume flow to predict changes in price.',
    'vpt_signal': 'Volume Price Trend: Relates volume to price changes to confirm price movements.',
    'volume_ratio': 'Volume Ratio: Identifies unusual volume that may signal price reversals.',
    'cmf': 'Chaikin Money Flow: Measures the Money Flow Volume over a period of time.',
    'accum_dist': 'Accumulation/Distribution: Volume indicator that assesses money flowing into or out of a security.',
    'candlestick': 'Candlestick Patterns: Identifies common candlestick patterns for potential reversals or continuations.',
    'adaptive_trend': 'Adaptive Trend: Dynamically adjusts to market conditions using multiple indicators.',
    'hybrid_momentum_volatility': 'Hybrid Momentum/Volatility: Combines momentum and volatility indicators.',
    'pattern_recognition': 'Pattern Recognition: Identifies chart patterns for potential trading signals.'
}

# Add all new strategies from STRATEGY_REGISTRY to AVAILABLE_STRATEGIES
for strategy_name in STRATEGY_REGISTRY:
    if strategy_name not in [s['type'] for s in AVAILABLE_STRATEGIES]:
        AVAILABLE_STRATEGIES.append({
            'type': strategy_name,
            'name': strategy_name.replace('_', ' ').title(),  # Format the name
            'description': strategy_descriptions.get(strategy_name, f"{strategy_name} strategy")  # Get description or default
        }) 