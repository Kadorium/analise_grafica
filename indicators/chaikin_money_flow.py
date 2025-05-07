import pandas as pd
import numpy as np

def chaikin_money_flow(data, period=20):
    """
    Calculate Chaikin Money Flow (CMF).
    
    Args:
        data (pandas.DataFrame): DataFrame containing 'high', 'low', 'close', 'volume' columns.
        period (int): Period for calculation. Default is 20.
        
    Returns:
        pandas.Series: Series containing the CMF values.
    """
    # Check if required columns exist
    required_columns = ['high', 'low', 'close', 'volume']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    # Calculate Money Flow Multiplier
    # MFM = [(Close - Low) - (High - Close)] / (High - Low)
    high_low = data['high'] - data['low']
    
    # Avoid division by zero
    high_low = high_low.replace(0, np.nan)
    
    money_flow_multiplier = ((data['close'] - data['low']) - (data['high'] - data['close'])) / high_low
    
    # Calculate Money Flow Volume
    money_flow_volume = money_flow_multiplier * data['volume']
    
    # Calculate Chaikin Money Flow
    # CMF = Sum of Money Flow Volume over n periods / Sum of Volume over n periods
    cmf = money_flow_volume.rolling(window=period).sum() / data['volume'].rolling(window=period).sum()
    
    return cmf

def add_chaikin_money_flow_indicator(data, period=20):
    """
    Add Chaikin Money Flow (CMF) indicator to the input DataFrame.
    
    Args:
        data (pandas.DataFrame): DataFrame containing OHLC and volume data.
        period (int): Period for calculation. Default is 20.
        
    Returns:
        pandas.DataFrame: DataFrame with added CMF indicator column.
    """
    result = data.copy()
    
    # Add CMF
    result['cmf'] = chaikin_money_flow(data, period=period)
    
    return result 