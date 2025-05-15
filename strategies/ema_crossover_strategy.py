import pandas as pd
import numpy as np
from indicators.moving_averages import add_moving_averages, add_crossover_signals

def generate_signals(df: pd.DataFrame, short_period=20, long_period=50, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on EMA crossover strategy.
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        short_period (int): Period for the short-term EMA. Default is 20.
        long_period (int): Period for the long-term EMA. Default is 50.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if EMAs are already calculated
    ema_short_col = f"ema_{short_period}"
    ema_long_col = f"ema_{long_period}"
    
    if ema_short_col not in result.columns or ema_long_col not in result.columns:
        # Add the moving averages
        result = add_moving_averages(result, ema_periods=[short_period, long_period])
    
    # Check if we need to calculate crossover signals
    crossover_col = f"crossover_{ema_short_col}_{ema_long_col}"
    
    if crossover_col not in result.columns:
        # Calculate crossover manually if the specific columns don't exist
        result['crossover'] = 0
        result.loc[(result[ema_short_col] > result[ema_long_col]) & 
                  (result[ema_short_col].shift(1) <= result[ema_long_col].shift(1)), 'crossover'] = 1  # Buy signal
        result.loc[(result[ema_short_col] < result[ema_long_col]) & 
                  (result[ema_short_col].shift(1) >= result[ema_long_col].shift(1)), 'crossover'] = -1  # Sell signal
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals
    result.loc[result['crossover'] == 1, 'signal'] = 'buy'
    
    # Generate sell signals
    result.loc[result['crossover'] == -1, 'signal'] = 'sell'
    
    return result 