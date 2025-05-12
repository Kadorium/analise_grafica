import pandas as pd
import numpy as np
from indicators.momentum import relative_strength_index, detect_overbought_oversold

def generate_signals(df: pd.DataFrame, period=14, oversold=30, overbought=70, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on RSI indicator.
    - Buy when RSI crosses above oversold level (30)
    - Sell when RSI crosses below overbought level (70)
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        period (int): Period for RSI calculation. Default is 14.
        oversold (int): RSI level for oversold conditions. Default is 30.
        overbought (int): RSI level for overbought conditions. Default is 70.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if RSI is already calculated
    if 'rsi' not in result.columns:
        # Calculate RSI
        result['rsi'] = relative_strength_index(result, period=period)
    
    # Check if overbought/oversold indicators are already calculated
    if 'rsi_overbought' not in result.columns or 'rsi_oversold' not in result.columns:
        # Add overbought/oversold indicators
        result = detect_overbought_oversold(result, rsi_upper=overbought, rsi_lower=oversold)
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - RSI crosses above oversold level
    buy_condition = (result['rsi'] > oversold) & (result['rsi'].shift(1) <= oversold)
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - RSI crosses below overbought level
    sell_condition = (result['rsi'] < overbought) & (result['rsi'].shift(1) >= overbought)
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 