import pandas as pd
import numpy as np
from indicators.donchian_channels import add_donchian_channels_indicator

def generate_signals(df: pd.DataFrame, period=20, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on Donchian Channels breakouts.
    - Buy when price breaks above the upper channel
    - Sell when price breaks below the lower channel
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        period (int): Period for Donchian Channels calculation. Default is 20.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if Donchian Channels are already calculated
    if 'dc_upper' not in result.columns or 'dc_lower' not in result.columns:
        # Add Donchian Channels
        result = add_donchian_channels_indicator(result, period=period)
    
    # Calculate prior day's channels for comparison
    result['prev_dc_upper'] = result['dc_upper'].shift(1)
    result['prev_dc_lower'] = result['dc_lower'].shift(1)
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - price breaks above the upper channel
    buy_condition = (result['close'] > result['prev_dc_upper']) & (result['close'].shift(1) <= result['prev_dc_upper'].shift(1))
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - price breaks below the lower channel
    sell_condition = (result['close'] < result['prev_dc_lower']) & (result['close'].shift(1) >= result['prev_dc_lower'].shift(1))
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 