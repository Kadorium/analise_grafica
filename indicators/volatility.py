import pandas as pd
import numpy as np

def average_true_range(data, period=14):
    """
    Calculate Average True Range (ATR).
    
    Args:
        data (pandas.DataFrame): DataFrame containing 'high', 'low', and 'close' columns.
        period (int): Period for ATR calculation. Default is 14.
        
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

def bollinger_bands(data, column='close', window=20, num_std=2):
    """
    Calculate Bollinger Bands.
    
    Args:
        data (pandas.DataFrame): DataFrame containing price data.
        column (str): Column name for which to calculate Bollinger Bands. Default is 'close'.
        window (int): Window size for the moving average. Default is 20.
        num_std (int/float): Number of standard deviations for the bands. Default is 2.
        
    Returns:
        pandas.DataFrame: DataFrame containing 'middle_band', 'upper_band', and 'lower_band' columns.
    """
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data")
    
    # Calculate middle band (simple moving average)
    middle_band = data[column].rolling(window=window).mean()
    
    # Calculate the standard deviation
    std = data[column].rolling(window=window).std()
    
    # Calculate upper and lower bands
    upper_band = middle_band + (std * num_std)
    lower_band = middle_band - (std * num_std)
    
    # Create DataFrame with results
    result = pd.DataFrame({
        'middle_band': middle_band,
        'upper_band': upper_band,
        'lower_band': lower_band
    }, index=data.index)
    
    return result

def add_volatility_indicators(data, atr_period=14, bollinger_window=20, bollinger_std=2):
    """
    Add volatility indicators to the input DataFrame.
    
    Args:
        data (pandas.DataFrame): DataFrame containing price data.
        atr_period (int): Period for ATR calculation. Default is 14.
        bollinger_window (int): Window size for Bollinger Bands. Default is 20.
        bollinger_std (int/float): Number of standard deviations for Bollinger Bands. Default is 2.
        
    Returns:
        pandas.DataFrame: DataFrame with added volatility indicator columns.
    """
    result = data.copy()
    
    # Add ATR
    result['atr'] = average_true_range(data, period=atr_period)
    
    # Calculate ATR percentage (ATR/Close)
    result['atr_pct'] = result['atr'] / data['close'] * 100
    
    # Add Bollinger Bands
    bb_result = bollinger_bands(data, window=bollinger_window, num_std=bollinger_std)
    result['bb_middle'] = bb_result['middle_band']
    result['bb_upper'] = bb_result['upper_band']
    result['bb_lower'] = bb_result['lower_band']
    
    # Calculate bandwidth (a measure of volatility)
    result['bb_bandwidth'] = (result['bb_upper'] - result['bb_lower']) / result['bb_middle'] * 100
    
    # Calculate %B indicator (position within the bands)
    result['bb_percent_b'] = (data['close'] - result['bb_lower']) / (result['bb_upper'] - result['bb_lower'])
    
    return result

def detect_volatility_breakouts(data, column='close', bb_upper_col='bb_upper', bb_lower_col='bb_lower',
                              atr_col='atr', price_col='close'):
    """
    Detect volatility-based breakouts.
    
    Args:
        data (pandas.DataFrame): DataFrame containing Bollinger Bands and ATR data.
        column (str): Column name for price. Default is 'close'.
        bb_upper_col (str): Column name for Bollinger upper band. Default is 'bb_upper'.
        bb_lower_col (str): Column name for Bollinger lower band. Default is 'bb_lower'.
        atr_col (str): Column name for ATR. Default is 'atr'.
        price_col (str): Column name for price. Default is 'close'.
        
    Returns:
        pandas.DataFrame: DataFrame with added breakout signal columns.
    """
    # Check if required columns exist
    required_columns = [column, bb_upper_col, bb_lower_col, atr_col]
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    result = data.copy()
    
    # Bollinger Band breakouts
    result['bb_upper_breakout'] = (data[column] > data[bb_upper_col]).astype(int)
    result['bb_lower_breakout'] = (data[column] < data[bb_lower_col]).astype(int)
    
    # Price movement greater than ATR (sudden large moves)
    result['price_change'] = data[price_col].diff().abs()
    result['atr_breakout'] = (result['price_change'] > (data[atr_col] * 1.5)).astype(int)
    
    return result 