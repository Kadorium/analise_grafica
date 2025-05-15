import pandas as pd
import numpy as np
from indicators.momentum import macd, add_momentum_indicators

def generate_signals(df: pd.DataFrame, fast_period=12, slow_period=26, signal_period=9, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on MACD crossover.
    - Buy when MACD line crosses above signal line
    - Sell when MACD line crosses below signal line
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        fast_period (int): Fast period for MACD. Default is 12.
        slow_period (int): Slow period for MACD. Default is 26.
        signal_period (int): Signal period for MACD. Default is 9.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if MACD is already calculated
    if 'macd' not in result.columns or 'macd_signal' not in result.columns:
        # Calculate MACD or add full momentum indicators
        if 'rsi' in result.columns or 'stoch_k' in result.columns:
            # If other momentum indicators exist, just calculate MACD
            macd_data = macd(result, fast_period=fast_period, slow_period=slow_period, signal_period=signal_period)
            result['macd'] = macd_data['macd']
            result['macd_signal'] = macd_data['signal']
            result['macd_histogram'] = macd_data['histogram']
        else:
            # Add all momentum indicators
            result = add_momentum_indicators(result, macd_fast=fast_period, macd_slow=slow_period, macd_signal=signal_period)
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - MACD crosses above signal line
    buy_condition = (result['macd'] > result['macd_signal']) & (result['macd'].shift(1) <= result['macd_signal'].shift(1))
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - MACD crosses below signal line
    sell_condition = (result['macd'] < result['macd_signal']) & (result['macd'].shift(1) >= result['macd_signal'].shift(1))
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 