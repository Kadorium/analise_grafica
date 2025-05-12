import pandas as pd
import numpy as np
from indicators.supertrend import add_supertrend_indicator

def generate_signals(df: pd.DataFrame, atr_period=10, multiplier=3, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on SuperTrend indicator.
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        atr_period (int): Period for ATR calculation. Default is 10.
        multiplier (float): Multiplier for ATR. Default is 3.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if SuperTrend is already calculated
    if 'supertrend' not in result.columns or 'supertrend_direction' not in result.columns:
        # Add SuperTrend indicator
        result = add_supertrend_indicator(result, atr_period=atr_period, multiplier=multiplier)
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - when price closes above SuperTrend (direction changes to uptrend)
    result.loc[result['supertrend_direction'] == 1, 'signal'] = 'buy'
    
    # Generate sell signals - when price closes below SuperTrend (direction changes to downtrend)
    result.loc[result['supertrend_direction'] == -1, 'signal'] = 'sell'
    
    return result 