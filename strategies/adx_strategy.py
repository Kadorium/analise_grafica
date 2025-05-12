import pandas as pd
import numpy as np
from indicators.adx import add_adx_indicator

def generate_signals(df: pd.DataFrame, period=14, adx_threshold=20, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on ADX and Directional Indicators.
    - Buy if ADX > threshold and +DI > -DI
    - Sell if ADX > threshold and -DI > +DI
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        period (int): Period for ADX calculation. Default is 14.
        adx_threshold (int): Threshold for ADX to indicate significant trend. Default is 20.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if ADX indicators are already calculated
    if 'adx' not in result.columns or 'plus_di' not in result.columns or 'minus_di' not in result.columns:
        # Add ADX indicators
        result = add_adx_indicator(result, period=period)
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - ADX > threshold and +DI > -DI
    buy_condition = (result['adx'] > adx_threshold) & (result['plus_di'] > result['minus_di'])
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - ADX > threshold and -DI > +DI
    sell_condition = (result['adx'] > adx_threshold) & (result['minus_di'] > result['plus_di'])
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 