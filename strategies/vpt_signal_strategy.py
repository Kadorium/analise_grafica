import pandas as pd
import numpy as np
from indicators.volume import add_volume_indicators

def generate_signals(df: pd.DataFrame, vpt_period=20, signal_period=9, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on Volume-Price Trend (VPT) indicator.
    Similar to MACD but using VPT, with a signal line crossover strategy.
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        vpt_period (int): Period for VPT moving average. Default is 20.
        signal_period (int): Period for VPT signal line. Default is 9.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if VPT is already calculated
    if 'vpt' not in result.columns:
        # Add volume indicators
        result = add_volume_indicators(result)
    
    # Calculate VPT moving average
    result['vpt_ma'] = result['vpt'].rolling(window=vpt_period).mean()
    
    # Calculate VPT signal line (like MACD)
    result['vpt_signal'] = result['vpt'].rolling(window=signal_period).mean()
    
    # Calculate VPT histogram
    result['vpt_histogram'] = result['vpt'] - result['vpt_signal']
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - VPT crosses above signal line
    buy_condition = (result['vpt'] > result['vpt_signal']) & (result['vpt'].shift(1) <= result['vpt_signal'].shift(1))
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - VPT crosses below signal line
    sell_condition = (result['vpt'] < result['vpt_signal']) & (result['vpt'].shift(1) >= result['vpt_signal'].shift(1))
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 