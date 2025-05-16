import os
import importlib
from strategies.trend_following import TrendFollowingStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.breakout import BreakoutStrategy
import pandas as pd
import numpy as np

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
    
    def backtest(self, data, initial_capital=100.0, commission=0.001):
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
    
    def _sanitize_float(self, value):
        """
        Sanitize float values to ensure they are JSON-compatible
        - Replace inf with a large number
        - Replace -inf with a large negative number
        - Replace NaN with 0
        """
        if value is None:
            return 0
        
        # Check for numpy types
        if isinstance(value, (np.integer, np.int64, np.int32)):
            return int(value)
        elif isinstance(value, (np.floating, np.float64, np.float32)):
            value = float(value)
        
        # Handle non-finite values
        if np.isnan(value):
            return 0
        elif np.isinf(value):
            if value > 0:
                return 1.0e+308  # Max JSON-compatible float
            else:
                return -1.0e+308
        
        return value
    
    def get_performance_metrics(self, backtest_results):
        """Calculate performance metrics from backtest results"""
        df = backtest_results
        metrics = {}
        debug_logs = [] # Initialize list to collect debug logs

        # --- Start Enhanced Debug Logging ---
        debug_logs.append("\n[DEBUG] StrategyAdapter.get_performance_metrics entry")
        debug_logs.append(f"[DEBUG] Input DataFrame shape: {df.shape}")
        if 'trade_profit' in df.columns:
            debug_logs.append(f"[DEBUG] Unique trade_profit values: {df['trade_profit'].unique()}")
        else:
            debug_logs.append("[DEBUG] 'trade_profit' column NOT FOUND in input DataFrame")
        # --- End Enhanced Debug Logging ---

        # Ensure 'date' column is datetime
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        
        initial_capital_for_calc = self.parameters.get('initial_capital', 100.0)
        if not isinstance(initial_capital_for_calc, (int, float)) or initial_capital_for_calc <= 0:
            initial_capital_for_calc = 100.0 # Default if invalid

        # Ensure 'equity' and 'daily_return' columns are numeric and exist
        if 'equity' in df.columns:
            df['equity'] = pd.to_numeric(df['equity'], errors='coerce')
            # If first equity is NaN or 0, try to fill forward, then with initial capital
            if pd.isna(df['equity'].iloc[0]) or df['equity'].iloc[0] == 0:
                 df['equity'] = df['equity'].fillna(method='ffill').fillna(initial_capital_for_calc)
        else: 
            df['equity'] = pd.Series([initial_capital_for_calc] * len(df))

        if 'daily_return' not in df.columns or df['daily_return'].isnull().all():
            df['daily_return'] = df['equity'].pct_change()
            # For first row, pct_change is NaN. If only one row, daily_return can be 0.
            if len(df['daily_return']) > 0:
                 df['daily_return'].iloc[0] = 0 
            df['daily_return'] = df['daily_return'].fillna(0)

        # Total Return (as a ratio, e.g., 0.1 for 10%)
        total_return_ratio = 0.0
        if not df.empty and 'equity' in df.columns and len(df['equity']) > 0 and df['equity'].iloc[0] != 0:
            total_return_ratio = (df['equity'].iloc[-1] / df['equity'].iloc[0]) - 1
        metrics['total_return'] = total_return_ratio 
        
        # Annualized Return (as a ratio)
        annual_return_ratio = 0.0
        if not df.empty and 'date' in df.columns and len(df['date']) > 1:
            start_date = df['date'].iloc[0]
            end_date = df['date'].iloc[-1]
            if pd.notna(start_date) and pd.notna(end_date):
                days = (end_date - start_date).days
                if days > 0:
                    annual_return_ratio = (1 + total_return_ratio) ** (365 / days) - 1
                # If days is 0 (same day start/end) but multiple entries, it's effectively 0 duration for annualization.
                # If only 1 data point, annual return is effectively total_return for that point if we consider it a 1-day period.
                # However, standard annualization needs >0 days. Let total_return_ratio be the proxy if duration is too short.
                elif days == 0 and total_return_ratio != 0 : # Eg, intraday or single day data
                    annual_return_ratio = total_return_ratio # Or could be set to 0 if annualization is not meaningful
                else: 
                    annual_return_ratio = total_return_ratio 
            else: 
                annual_return_ratio = total_return_ratio
        else: 
             annual_return_ratio = total_return_ratio
        metrics['annual_return'] = annual_return_ratio
        
        # Sharpe Ratio
        sharpe_ratio = 0.0
        if not df.empty and 'daily_return' in df.columns and len(df['daily_return']) > 1:
            daily_returns_numeric = pd.to_numeric(df['daily_return'], errors='coerce').fillna(0)
            daily_return_std = daily_returns_numeric.std()
            if daily_return_std is not None and daily_return_std > 0:
                sharpe_ratio = daily_returns_numeric.mean() / daily_return_std * (252 ** 0.5)
        metrics['sharpe_ratio'] = sharpe_ratio
        
        # Max Drawdown (as a positive ratio, e.g., 0.1 for 10%)
        max_drawdown_ratio = 0.0 
        if 'equity' in df.columns and not df.empty:
            equity_numeric = pd.to_numeric(df['equity'], errors='coerce').fillna(initial_capital_for_calc)
            df_peak = equity_numeric.cummax()
            # Ensure peak is not zero to avoid division by zero if equity starts/drops to zero
            df_peak_safe = df_peak.replace(0, np.nan) # Replace 0 with NaN so division results in NaN
            
            df_drawdown_values = (equity_numeric - df_peak_safe) / df_peak_safe
            df_drawdown_values = pd.to_numeric(df_drawdown_values, errors='coerce').fillna(0) # Fill NaN with 0
            
            if not df_drawdown_values.empty:
                # Max drawdown is the minimum value (most negative), so take absolute
                max_drawdown_ratio = abs(df_drawdown_values.min()) 
        metrics['max_drawdown'] = max_drawdown_ratio
        
        # Trades, Win Rate, Profit Factor, Avg Win/Loss, Expectancy
        num_trades = 0
        win_rate_ratio = 0.0 # ratio 0.0 to 1.0
        profit_factor = 0.0
        avg_win_raw = 0.0
        avg_loss_raw = 0.0
        expectancy_raw = 0.0

        if 'trade_profit' in df.columns:
            trade_profit_series = pd.to_numeric(df['trade_profit'], errors='coerce').fillna(0)
            trades_df = df[trade_profit_series != 0]
            num_trades = len(trades_df)
            # --- Debug Logging for Trades ---
            debug_logs.append(f"[DEBUG] trade_profit_series (first 5):\n{trade_profit_series.head()}")
            debug_logs.append(f"[DEBUG] trades_df (actual trades) shape: {trades_df.shape}")
            debug_logs.append(f"[DEBUG] Calculated num_trades: {num_trades}")
            # --- End Debug Logging for Trades ---

            if num_trades > 0:
                winning_trades_df = trades_df[trades_df['trade_profit'] > 0]
                losing_trades_df = trades_df[trades_df['trade_profit'] < 0]
                num_winning_trades = len(winning_trades_df)
                num_losing_trades = len(losing_trades_df)
                # --- Debug Logging for Wins/Losses ---
                debug_logs.append(f"[DEBUG] num_winning_trades: {num_winning_trades}")
                debug_logs.append(f"[DEBUG] num_losing_trades: {num_losing_trades}")
                # --- End Debug Logging for Wins/Losses ---

                win_rate_ratio = num_winning_trades / num_trades if num_trades > 0 else 0.0 # Guard against division by zero
                # --- Debug Logging for Win Rate ---
                debug_logs.append(f"[DEBUG] Calculated win_rate_ratio (raw): {win_rate_ratio}")
                # --- End Debug Logging for Win Rate ---
                
                total_profit_from_wins = winning_trades_df['trade_profit'].sum()
                total_loss_from_losses = abs(losing_trades_df['trade_profit'].sum())
                # --- Debug Logging for Profit/Loss Sums ---
                debug_logs.append(f"[DEBUG] total_profit_from_wins: {total_profit_from_wins}")
                debug_logs.append(f"[DEBUG] total_loss_from_losses: {total_loss_from_losses}")
                # --- End Debug Logging for Profit/Loss Sums ---
                
                if total_loss_from_losses > 0:
                    profit_factor = total_profit_from_wins / total_loss_from_losses
                elif total_profit_from_wins > 0: # Losses are zero, profits are positive
                    profit_factor = 1000.0 
                else: # No profits and no losses (or profits are zero and losses are zero)
                    profit_factor = 0.0 
                # --- Debug Logging for Profit Factor ---
                debug_logs.append(f"[DEBUG] Calculated profit_factor: {profit_factor}")
                # --- End Debug Logging for Profit Factor ---

                if num_winning_trades > 0:
                    avg_win_raw = total_profit_from_wins / num_winning_trades
                if num_losing_trades > 0:
                    avg_loss_raw = total_loss_from_losses / num_losing_trades 

                loss_rate_ratio = 1.0 - win_rate_ratio
                expectancy_raw = (win_rate_ratio * avg_win_raw) - (loss_rate_ratio * avg_loss_raw)

        metrics['number_of_trades'] = num_trades
        metrics['win_rate'] = win_rate_ratio 
        metrics['profit_factor'] = profit_factor
        # Raw avg win/loss are not directly displayed but can be useful for logs/other calcs
        metrics['avg_win_raw'] = avg_win_raw 
        metrics['avg_loss_raw'] = avg_loss_raw 
        metrics['expectancy_raw'] = expectancy_raw 

        # Sanitize all metrics before returning
        # Note: Frontend will multiply ratio metrics by 100 for display
        sanitized_metrics = {k: self._sanitize_float(v) for k, v in metrics.items()}
        # --- Debug Logging for Final Sanitized Metrics ---
        debug_logs.append(f"[DEBUG] Sanitized metrics being returned: {sanitized_metrics}")
        # --- End Debug Logging for Final Sanitized Metrics ---
        
        return sanitized_metrics, debug_logs # Return metrics and debug logs
    
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