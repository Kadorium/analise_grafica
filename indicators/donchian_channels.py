import pandas as pd
import numpy as np

def donchian_channels(data, period=20):
    """
    Calculate Donchian Channels.
    
    Args:
        data (pandas.DataFrame): DataFrame containing 'high', 'low' columns.
        period (int): Period for calculation. Default is 20.
        
    Returns:
        pandas.DataFrame: DataFrame containing 'upper_band', 'middle_band', and 'lower_band' columns.
    """
    # Check if required columns exist
    required_columns = ['high', 'low']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    # Calculate upper band (highest high over the lookback period)
    upper_band = data['high'].rolling(window=period).max()
    
    # Calculate lower band (lowest low over the lookback period)
    lower_band = data['low'].rolling(window=period).min()
    
    # Calculate middle band (average of upper and lower bands)
    middle_band = (upper_band + lower_band) / 2
    
    # Create result DataFrame
    result = pd.DataFrame({
        'dc_upper': upper_band,
        'dc_middle': middle_band,
        'dc_lower': lower_band
    }, index=data.index)
    
    return result

def add_donchian_channels_indicator(data, period=20):
    """
    Add Donchian Channels indicator to the input DataFrame.
    
    Args:
        data (pandas.DataFrame): DataFrame containing OHLC data.
        period (int): Period for calculation. Default is 20.
        
    Returns:
        pandas.DataFrame: DataFrame with added Donchian Channels indicator columns.
    """
    result = data.copy()
    
    # Add Donchian Channels
    dc_result = donchian_channels(data, period=period)
    result['dc_upper'] = dc_result['dc_upper']
    result['dc_middle'] = dc_result['dc_middle']
    result['dc_lower'] = dc_result['dc_lower']
    
    return result 