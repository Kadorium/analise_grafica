import pandas as pd
import numpy as np

def average_true_range(data, period=10):
    """
    Calculate Average True Range (ATR).
    
    Args:
        data (pandas.DataFrame): DataFrame containing 'high', 'low', 'close' columns.
        period (int): Period for ATR calculation. Default is 10.
        
    Returns:
        pandas.Series: Series containing ATR values.
    """
    # Check if required columns exist
    required_columns = ['high', 'low', 'close']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    # Calculate True Range
    high_low = data['high'] - data['low']
    high_close_prev = abs(data['high'] - data['close'].shift(1))
    low_close_prev = abs(data['low'] - data['close'].shift(1))
    
    # True Range is the maximum of the three values
    true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
    
    # Calculate ATR (Simple Moving Average of True Range)
    return true_range.rolling(window=period).mean()

def keltner_channels(data, ema_period=20, atr_period=10, multiplier=1.5):
    """
    Calculate Keltner Channels.
    
    Args:
        data (pandas.DataFrame): DataFrame containing 'high', 'low', 'close' columns.
        ema_period (int): Period for EMA calculation. Default is 20.
        atr_period (int): Period for ATR calculation. Default is 10.
        multiplier (float): Multiplier for ATR. Default is 1.5.
        
    Returns:
        pandas.DataFrame: DataFrame containing 'upper_band', 'middle_band', and 'lower_band' columns.
    """
    # Check if required columns exist
    required_columns = ['high', 'low', 'close']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    # Calculate middle band (EMA of close)
    middle_band = data['close'].ewm(span=ema_period, adjust=False).mean()
    
    # Calculate ATR
    atr = average_true_range(data, period=atr_period)
    
    # Calculate upper and lower bands
    upper_band = middle_band + (multiplier * atr)
    lower_band = middle_band - (multiplier * atr)
    
    # Create result DataFrame
    result = pd.DataFrame({
        'kc_upper': upper_band,
        'kc_middle': middle_band,
        'kc_lower': lower_band
    }, index=data.index)
    
    return result

def add_keltner_channels_indicator(data, ema_period=20, atr_period=10, multiplier=1.5):
    """
    Add Keltner Channels indicator to the input DataFrame.
    
    Args:
        data (pandas.DataFrame): DataFrame containing OHLC data.
        ema_period (int): Period for EMA calculation. Default is 20.
        atr_period (int): Period for ATR calculation. Default is 10.
        multiplier (float): Multiplier for ATR. Default is 1.5.
        
    Returns:
        pandas.DataFrame: DataFrame with added Keltner Channels indicator columns.
    """
    result = data.copy()
    
    # Add Keltner Channels
    kc_result = keltner_channels(data, ema_period=ema_period, atr_period=atr_period, multiplier=multiplier)
    result['kc_upper'] = kc_result['kc_upper']
    result['kc_middle'] = kc_result['kc_middle']
    result['kc_lower'] = kc_result['kc_lower']
    
    return result 