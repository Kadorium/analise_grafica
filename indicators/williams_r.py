import pandas as pd
import numpy as np

def williams_r(data, period=14):
    """
    Calculate Williams %R (Williams Percent Range).
    
    Args:
        data (pandas.DataFrame): DataFrame containing 'high', 'low', 'close' columns.
        period (int): Lookback period for calculation. Default is 14.
        
    Returns:
        pandas.Series: Series containing the Williams %R values.
    """
    # Check if required columns exist
    required_columns = ['high', 'low', 'close']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    # Find highest high and lowest low over the lookback period
    highest_high = data['high'].rolling(window=period).max()
    lowest_low = data['low'].rolling(window=period).min()
    
    # Calculate Williams %R
    # %R = (Highest High - Close) / (Highest High - Lowest Low) * -100
    williams_percent_r = ((highest_high - data['close']) / (highest_high - lowest_low)) * -100
    
    return williams_percent_r

def add_williams_r_indicator(data, period=14):
    """
    Add Williams %R indicator to the input DataFrame.
    
    Args:
        data (pandas.DataFrame): DataFrame containing OHLC data.
        period (int): Lookback period for calculation. Default is 14.
        
    Returns:
        pandas.DataFrame: DataFrame with added Williams %R indicator column.
    """
    result = data.copy()
    
    # Add Williams %R
    result['williams_r'] = williams_r(data, period=period)
    
    return result 