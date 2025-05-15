import pandas as pd
import numpy as np
from indicators.moving_averages import add_moving_averages, add_crossover_signals

def generate_signals(df: pd.DataFrame, short_period=50, long_period=200, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on SMA crossover strategy (Golden Cross / Death Cross).
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        short_period (int): Period for the short-term SMA. Default is 50.
        long_period (int): Period for the long-term SMA. Default is 200.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if SMAs are already calculated
    sma_short_col = f"sma_{short_period}"
    sma_long_col = f"sma_{long_period}"
    
    if sma_short_col not in result.columns or sma_long_col not in result.columns:
        # Add the moving averages
        result = add_moving_averages(result, sma_periods=[short_period, long_period])
    
    # Check if crossover signals are already calculated
    if 'golden_cross' not in result.columns or 'death_cross' not in result.columns:
        # Add crossover signals
        result = add_crossover_signals(result, sma_short_col, sma_long_col)
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals (Golden Cross)
    result.loc[result['golden_cross'] == 1, 'signal'] = 'buy'
    
    # Generate sell signals (Death Cross)
    result.loc[result['death_cross'] == 1, 'signal'] = 'sell'
    
    return result 