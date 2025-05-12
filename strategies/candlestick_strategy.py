import pandas as pd
import numpy as np
from indicators.candlestick_patterns import add_candlestick_patterns
from indicators.moving_averages import add_moving_averages

def generate_signals(df: pd.DataFrame, ma_period=20, resistance_check=True, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on candlestick patterns.
    - Buy on bullish patterns: Hammer, Morning Star, Bullish Engulfing
    - Sell on bearish patterns: Bearish Engulfing, Evening Star, or Doji at resistance
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        ma_period (int): Period for moving average to identify trend/resistance. Default is 20.
        resistance_check (bool): Whether to check for resistance levels for sell signals. Default is True.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if candlestick patterns are already calculated
    pattern_columns = ['doji', 'hammer', 'bullish_engulfing', 'bearish_engulfing', 'morning_star', 'evening_star']
    if not all(col in result.columns for col in pattern_columns):
        # Add candlestick patterns
        result = add_candlestick_patterns(result)
    
    # Calculate MA for resistance check if needed
    ma_col = f'sma_{ma_period}'
    if resistance_check and ma_col not in result.columns:
        result = add_moving_averages(result, sma_periods=[ma_period])
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - bullish patterns
    buy_condition = (result['hammer'] | result['morning_star'] | result['bullish_engulfing'])
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - bearish patterns
    # For Doji, check if it's near resistance (close to moving average from below)
    if resistance_check:
        near_resistance = (result['close'] > result[ma_col] * 0.98) & (result['close'] < result[ma_col] * 1.02)
        doji_at_resistance = result['doji'] & near_resistance
    else:
        doji_at_resistance = result['doji']
        
    sell_condition = (result['bearish_engulfing'] | result['evening_star'] | doji_at_resistance)
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 