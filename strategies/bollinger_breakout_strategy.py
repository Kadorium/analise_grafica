import pandas as pd
import numpy as np
from indicators.volatility import add_volatility_indicators

def generate_signals(df: pd.DataFrame, window=20, num_std=2, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on Bollinger Bands breakouts.
    - Buy when price crosses above upper band
    - Sell when price crosses below lower band
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        window (int): Window size for Bollinger Bands. Default is 20.
        num_std (float): Number of standard deviations for Bollinger Bands. Default is 2.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if Bollinger Bands are already calculated
    if 'bb_upper' not in result.columns or 'bb_lower' not in result.columns:
        # Add volatility indicators including Bollinger Bands
        result = add_volatility_indicators(result, bollinger_window=window, bollinger_std=num_std)
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - price crosses above the upper band
    buy_condition = (result['close'] > result['bb_upper']) & (result['close'].shift(1) <= result['bb_upper'].shift(1))
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - price crosses below the lower band
    sell_condition = (result['close'] < result['bb_lower']) & (result['close'].shift(1) >= result['bb_lower'].shift(1))
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 