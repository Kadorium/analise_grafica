import pandas as pd
import numpy as np
from indicators.williams_r import add_williams_r_indicator

def generate_signals(df: pd.DataFrame, period=14, oversold=-80, overbought=-20, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on Williams %R indicator.
    - Buy when %R crosses above oversold level (-80)
    - Sell when %R crosses below overbought level (-20)
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        period (int): Lookback period for Williams %R calculation. Default is 14.
        oversold (int): %R level for oversold conditions. Default is -80.
        overbought (int): %R level for overbought conditions. Default is -20.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if Williams %R is already calculated
    if 'williams_r' not in result.columns:
        # Add Williams %R indicator
        result = add_williams_r_indicator(result, period=period)
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - %R crosses above oversold level
    buy_condition = (result['williams_r'] > oversold) & (result['williams_r'].shift(1) <= oversold)
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - %R crosses below overbought level
    sell_condition = (result['williams_r'] < overbought) & (result['williams_r'].shift(1) >= overbought)
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 