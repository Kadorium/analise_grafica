import pandas as pd
import numpy as np

def on_balance_volume(data):
    """
    Calculate On-Balance Volume (OBV).
    
    Args:
        data (pandas.DataFrame): DataFrame containing 'close' and 'volume' columns.
        
    Returns:
        pandas.Series: Series containing OBV values.
    """
    # Check if required columns exist
    required_columns = ['close', 'volume']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    # Initialize OBV with the first volume value
    obv = pd.Series(0, index=data.index)
    
    # Calculate OBV
    close_diff = data['close'].diff()
    
    # When close price increases
    obv[close_diff > 0] = data.loc[close_diff > 0, 'volume']
    
    # When close price decreases
    obv[close_diff < 0] = -data.loc[close_diff < 0, 'volume']
    
    # When close price doesn't change
    obv[close_diff == 0] = 0
    
    # Cumulative sum
    return obv.cumsum()

def volume_price_trend(data):
    """
    Calculate Volume Price Trend (VPT).
    
    Args:
        data (pandas.DataFrame): DataFrame containing 'close' and 'volume' columns.
        
    Returns:
        pandas.Series: Series containing VPT values.
    """
    # Check if required columns exist
    required_columns = ['close', 'volume']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    # Calculate price change percentage
    price_change_pct = data['close'].pct_change()
    
    # Calculate VPT components
    vpt_components = data['volume'] * price_change_pct
    
    # Cumulative sum
    return vpt_components.cumsum()

def add_volume_indicators(data):
    """
    Add volume indicators to the input DataFrame.
    
    Args:
        data (pandas.DataFrame): DataFrame containing price and volume data.
        
    Returns:
        pandas.DataFrame: DataFrame with added volume indicator columns.
    """
    result = data.copy()
    
    # Add OBV
    result['obv'] = on_balance_volume(data)
    
    # Add VPT
    result['vpt'] = volume_price_trend(data)
    
    # Calculate volume moving averages
    result['volume_sma_20'] = data['volume'].rolling(window=20).mean()
    result['volume_sma_50'] = data['volume'].rolling(window=50).mean()
    
    # Volume ratio (current volume / average volume)
    result['volume_ratio_20'] = data['volume'] / result['volume_sma_20']
    
    return result

def detect_volume_breakouts(data, volume_column='volume', price_column='close', 
                           volume_ma_column='volume_sma_20', price_ma_column='sma_20',
                           volume_threshold=2.0, price_threshold=0.02):
    """
    Detect volume and price breakouts.
    
    Args:
        data (pandas.DataFrame): DataFrame containing volume and price data.
        volume_column (str): Column name for volume. Default is 'volume'.
        price_column (str): Column name for price. Default is 'close'.
        volume_ma_column (str): Column name for volume moving average. Default is 'volume_sma_20'.
        price_ma_column (str): Column name for price moving average. Default is 'sma_20'.
        volume_threshold (float): Volume threshold for breakout. Default is 2.0 (200% of average).
        price_threshold (float): Price threshold for breakout. Default is 0.02 (2% above average).
        
    Returns:
        pandas.DataFrame: DataFrame with added columns for breakout signals.
    """
    # Check if required columns exist
    required_columns = [volume_column, price_column, volume_ma_column, price_ma_column]
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    result = data.copy()
    
    # Calculate volume ratio
    volume_ratio = data[volume_column] / data[volume_ma_column]
    
    # Calculate price percentage difference
    price_pct_diff = (data[price_column] - data[price_ma_column]) / data[price_ma_column]
    
    # Detect volume breakout
    result['volume_breakout'] = (volume_ratio > volume_threshold).astype(int)
    
    # Detect price breakout with volume confirmation
    result['price_volume_breakout'] = ((price_pct_diff > price_threshold) & 
                                     (volume_ratio > volume_threshold)).astype(int)
    
    # Detect price breakdown with volume confirmation
    result['price_volume_breakdown'] = ((price_pct_diff < -price_threshold) & 
                                      (volume_ratio > volume_threshold)).astype(int)
    
    return result 