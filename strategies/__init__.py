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
        
        # Initialize position and equity columns
        df['position'] = 0
        df['entry_price'] = 0.0
        df['equity'] = initial_capital
        df['trade_profit'] = 0.0
        df['trade_returns'] = 0.0
        
        # Calculate positions
        position = 0
        entry_price = 0.0
        equity = initial_capital
        
        for i in range(len(df)):
            if df.iloc[i]['signal'] == 'buy' and position == 0:
                position = 1
                entry_price = df.iloc[i]['close'] * (1 + commission)  # Include commission
            elif df.iloc[i]['signal'] == 'sell' and position == 1:
                position = 0
                exit_price = df.iloc[i]['close'] * (1 - commission)  # Include commission
                trade_profit = exit_price - entry_price
                trade_return = trade_profit / entry_price
                equity += trade_profit
                df.at[df.index[i], 'trade_profit'] = trade_profit
                df.at[df.index[i], 'trade_returns'] = trade_return
            
            df.at[df.index[i], 'position'] = position
            df.at[df.index[i], 'equity'] = equity
            df.at[df.index[i], 'entry_price'] = entry_price
        
        # Calculate market returns for comparison
        df['market_return'] = df['close'].pct_change().fillna(0)
        df['cumulative_market_return'] = (1 + df['market_return']).cumprod()
        
        # Calculate drawdown
        df['peak'] = df['equity'].cummax()
        df['drawdown'] = (df['equity'] - df['peak']) / df['peak']
        
        # Calculate daily returns
        df['daily_return'] = df['equity'].pct_change().fillna(0)
        
        return df
    
    def get_performance_metrics(self, backtest_results):
        """Calculate performance metrics from backtest results"""
        df = backtest_results
        
        # Calculate total return
        total_return = df['equity'].iloc[-1] / df['equity'].iloc[0] - 1
        
        # Calculate annualized return
        days = (df['date'].iloc[-1] - df['date'].iloc[0]).days
        annual_return = (1 + total_return) ** (365 / max(days, 1)) - 1
        
        # Calculate Sharpe ratio (assuming risk-free rate of 0)
        if len(df) > 1:
            sharpe_ratio = df['daily_return'].mean() / df['daily_return'].std() * (252 ** 0.5)
        else:
            sharpe_ratio = 0
        
        # Calculate maximum drawdown
        max_drawdown = df['drawdown'].min()
        
        # Calculate win rate
        trades = df[df['trade_profit'] != 0]
        win_rate = (trades['trade_profit'] > 0).mean() if len(trades) > 0 else 0
        
        # Calculate profit factor
        profit_factor = 0
        if len(trades) > 0:
            winning_trades = trades[trades['trade_profit'] > 0]
            losing_trades = trades[trades['trade_profit'] < 0]
            
            total_profit = winning_trades['trade_profit'].sum() if len(winning_trades) > 0 else 0
            total_loss = abs(losing_trades['trade_profit'].sum()) if len(losing_trades) > 0 else 0
            
            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        return {
            'total_return': total_return,
            'total_return_percent': total_return * 100,
            'annual_return': annual_return,
            'annual_return_percent': annual_return * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_percent': max_drawdown * 100,
            'win_rate': win_rate,
            'win_rate_percent': win_rate * 100,
            'profit_factor': profit_factor,
            'number_of_trades': len(trades)
        }
    
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