import pandas as pd
import numpy as np

def commodity_channel_index(data, period=20):
    """
    Calculate Commodity Channel Index (CCI).
    
    Args:
        data (pandas.DataFrame): DataFrame containing 'high', 'low', 'close' columns.
        period (int): Period for CCI calculation. Default is 20.
        
    Returns:
        pandas.Series: Series containing the CCI values.
    """
    # Check if required columns exist
    required_columns = ['high', 'low', 'close']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    # Calculate Typical Price (TP)
    typical_price = (data['high'] + data['low'] + data['close']) / 3
    
    # Calculate Simple Moving Average of Typical Price
    tp_sma = typical_price.rolling(window=period).mean()
    
    # Calculate Mean Deviation manually without using .mad()
    # Calculate the absolute deviation from the mean
    # First get the difference of each value from the SMA
    # Then calculate the absolute value of those differences
    # Then take the mean of those absolute values
    mean_deviation = typical_price.rolling(window=period).apply(
        lambda x: np.abs(x - x.mean()).mean(), raw=True
    )
    
    # Calculate CCI
    # CCI = (Typical Price - SMA of Typical Price) / (0.015 * Mean Deviation)
    cci = (typical_price - tp_sma) / (0.015 * mean_deviation)
    
    return cci

def add_cci_indicator(data, period=20):
    """
    Add Commodity Channel Index (CCI) indicator to the input DataFrame.
    
    Args:
        data (pandas.DataFrame): DataFrame containing OHLC data.
        period (int): Period for CCI calculation. Default is 20.
        
    Returns:
        pandas.DataFrame: DataFrame with added CCI indicator column.
    """
    result = data.copy()
    
    # Add CCI
    result['cci'] = commodity_channel_index(data, period=period)
    
    return result 