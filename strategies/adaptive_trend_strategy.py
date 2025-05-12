import pandas as pd
import numpy as np
from indicators.moving_averages import add_moving_averages
from indicators.volatility import add_volatility_indicators
from indicators.adx import add_adx_indicator

def generate_signals(df: pd.DataFrame, fast_period=10, slow_period=30, adx_period=14, 
                    adx_threshold=20, atr_period=14, volatility_factor=0.5, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on an adaptive trend following strategy.
    This strategy dynamically adjusts MA periods based on market volatility and
    uses ADX to confirm trend strength.
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        fast_period (int): Base period for the short-term MA. Default is 10.
        slow_period (int): Base period for the long-term MA. Default is 30.
        adx_period (int): Period for ADX calculation. Default is 14.
        adx_threshold (int): Threshold for ADX to indicate significant trend. Default is 20.
        atr_period (int): Period for ATR calculation. Default is 14.
        volatility_factor (float): Factor to adjust MA periods based on volatility. Default is 0.5.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check and add required indicators
    if 'atr' not in result.columns:
        result = add_volatility_indicators(result, atr_period=atr_period)
    
    if 'adx' not in result.columns or 'plus_di' not in result.columns or 'minus_di' not in result.columns:
        result = add_adx_indicator(result, period=adx_period)
    
    # Calculate adaptive MA periods based on volatility
    # Higher volatility = shorter periods to respond faster
    # Lower volatility = longer periods to reduce noise
    
    # Calculate normalized volatility (ATR as percentage of price)
    result['norm_volatility'] = result['atr'] / result['close']
    
    # Calculate median volatility for scaling
    median_volatility = result['norm_volatility'].median()
    
    # Adjust MA periods based on relative volatility
    result['volatility_ratio'] = result['norm_volatility'] / median_volatility
    result['adaptive_fast_period'] = np.maximum(5, fast_period - (result['volatility_ratio'] - 1) * volatility_factor * fast_period)
    result['adaptive_slow_period'] = np.maximum(10, slow_period - (result['volatility_ratio'] - 1) * volatility_factor * slow_period)
    
    # Convert to integer periods (required for moving averages)
    result['adaptive_fast_period'] = result['adaptive_fast_period'].astype(int)
    result['adaptive_slow_period'] = result['adaptive_slow_period'].astype(int)
    
    # Calculate adaptive moving averages
    # Since periods are different for each row, we need to calculate them iteratively
    result['adaptive_fast_ma'] = np.nan
    result['adaptive_slow_ma'] = np.nan
    
    # Calculate the initial MAs for a reasonable lookback window
    max_period = max(slow_period * 2, 50)  # Use a sufficient lookback to initialize
    for i in range(max_period, len(result)):
        # Get adaptive periods for this row
        fast_window = result.iloc[i]['adaptive_fast_period']
        slow_window = result.iloc[i]['adaptive_slow_period']
        
        # Calculate custom MAs for this specific row
        if i >= fast_window:
            result.iloc[i, result.columns.get_loc('adaptive_fast_ma')] = result.iloc[i-fast_window:i+1]['close'].mean()
        
        if i >= slow_window:
            result.iloc[i, result.columns.get_loc('adaptive_slow_ma')] = result.iloc[i-slow_window:i+1]['close'].mean()
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - adaptive fast MA crosses above adaptive slow MA with strong trend
    buy_condition = ((result['adaptive_fast_ma'] > result['adaptive_slow_ma']) & 
                    (result['adaptive_fast_ma'].shift(1) <= result['adaptive_slow_ma'].shift(1)) & 
                    (result['adx'] > adx_threshold) &
                    (result['plus_di'] > result['minus_di']))
    
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - adaptive fast MA crosses below adaptive slow MA with strong trend
    sell_condition = ((result['adaptive_fast_ma'] < result['adaptive_slow_ma']) & 
                     (result['adaptive_fast_ma'].shift(1) >= result['adaptive_slow_ma'].shift(1)) & 
                     (result['adx'] > adx_threshold) &
                     (result['minus_di'] > result['plus_di']))
    
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 