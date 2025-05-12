import pandas as pd
import numpy as np
from indicators.chaikin_money_flow import add_chaikin_money_flow_indicator

def generate_signals(df: pd.DataFrame, period=20, buy_threshold=0.05, sell_threshold=-0.05, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on Chaikin Money Flow (CMF).
    - Buy when CMF crosses above positive threshold (0.05)
    - Sell when CMF crosses below negative threshold (-0.05)
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        period (int): Period for CMF calculation. Default is 20.
        buy_threshold (float): Positive threshold for buy signals. Default is 0.05.
        sell_threshold (float): Negative threshold for sell signals. Default is -0.05.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if CMF is already calculated
    if 'cmf' not in result.columns:
        # Add CMF indicator
        result = add_chaikin_money_flow_indicator(result, period=period)
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - CMF crosses above positive threshold
    buy_condition = (result['cmf'] > buy_threshold) & (result['cmf'].shift(1) <= buy_threshold)
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - CMF crosses below negative threshold
    sell_condition = (result['cmf'] < sell_threshold) & (result['cmf'].shift(1) >= sell_threshold)
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 