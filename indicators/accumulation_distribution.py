import pandas as pd
import numpy as np

def accumulation_distribution_line(data):
    """
    Calculate Accumulation/Distribution Line (A/D Line).
    
    Args:
        data (pandas.DataFrame): DataFrame containing 'high', 'low', 'close', 'volume' columns.
        
    Returns:
        pandas.Series: Series containing the A/D Line values.
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
    
    # Replace NaN with 0 to avoid propagating NaN values
    money_flow_multiplier = money_flow_multiplier.fillna(0)
    
    # Calculate Money Flow Volume
    money_flow_volume = money_flow_multiplier * data['volume']
    
    # Calculate Accumulation/Distribution Line
    ad_line = money_flow_volume.cumsum()
    
    return ad_line

def add_accumulation_distribution_indicator(data):
    """
    Add Accumulation/Distribution Line (A/D Line) indicator to the input DataFrame.
    
    Args:
        data (pandas.DataFrame): DataFrame containing OHLC and volume data.
        
    Returns:
        pandas.DataFrame: DataFrame with added A/D Line indicator column.
    """
    result = data.copy()
    
    # Add A/D Line
    result['ad_line'] = accumulation_distribution_line(data)
    
    return result 