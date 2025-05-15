import pandas as pd
import numpy as np
from indicators.cci import add_cci_indicator

def generate_signals(df: pd.DataFrame, period=20, oversold=-100, overbought=100, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on Commodity Channel Index (CCI).
    - Buy when CCI crosses above the oversold level (-100)
    - Sell when CCI crosses below the overbought level (+100)
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        period (int): Period for CCI calculation. Default is 20.
        oversold (int): CCI level for oversold conditions. Default is -100.
        overbought (int): CCI level for overbought conditions. Default is 100.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if CCI is already calculated
    if 'cci' not in result.columns:
        # Add CCI indicator
        result = add_cci_indicator(result, period=period)
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - CCI crosses above oversold level
    buy_condition = (result['cci'] > oversold) & (result['cci'].shift(1) <= oversold)
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - CCI crosses below overbought level
    sell_condition = (result['cci'] < overbought) & (result['cci'].shift(1) >= overbought)
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 