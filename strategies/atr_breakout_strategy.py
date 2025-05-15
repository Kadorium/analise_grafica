import pandas as pd
import numpy as np
from indicators.volatility import add_volatility_indicators

def generate_signals(df: pd.DataFrame, atr_period=14, atr_multiplier=1.5, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on price movements exceeding a multiple of ATR.
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        atr_period (int): Period for ATR calculation. Default is 14.
        atr_multiplier (float): Multiplier for ATR to identify significant moves. Default is 1.5.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if ATR is already calculated
    if 'atr' not in result.columns:
        # Add volatility indicators
        result = add_volatility_indicators(result, atr_period=atr_period)
    
    # Calculate price change
    result['price_change'] = result['close'].diff()
    
    # Calculate the ATR threshold for significant moves
    result['atr_threshold'] = result['atr'] * atr_multiplier
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - price increase exceeds ATR threshold
    buy_condition = result['price_change'] > result['atr_threshold']
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - price decrease exceeds ATR threshold
    sell_condition = result['price_change'] < -result['atr_threshold']
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 