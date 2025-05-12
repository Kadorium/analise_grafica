import pandas as pd
import numpy as np
from indicators.momentum import stochastic_oscillator, add_momentum_indicators

def generate_signals(df: pd.DataFrame, k_period=14, d_period=3, slowing=3, oversold=20, overbought=80, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on Stochastic Oscillator.
    - Buy when %K crosses above %D from below oversold level (20)
    - Sell when %K crosses below %D from above overbought level (80)
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        k_period (int): Lookback period for %K. Default is 14.
        d_period (int): Smoothing period for %D. Default is 3.
        slowing (int): Slowing period. Default is 3.
        oversold (int): Level for oversold conditions. Default is 20.
        overbought (int): Level for overbought conditions. Default is 80.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if Stochastic Oscillator is already calculated
    if 'stoch_k' not in result.columns or 'stoch_d' not in result.columns:
        # Calculate Stochastic or add momentum indicators
        if 'rsi' in result.columns or 'macd' in result.columns:
            # If other momentum indicators exist, just calculate Stochastic
            stoch_data = stochastic_oscillator(result, k_period=k_period, d_period=d_period, slowing=slowing)
            result['stoch_k'] = stoch_data['%K']
            result['stoch_d'] = stoch_data['%D']
        else:
            # Add all momentum indicators
            result = add_momentum_indicators(result, stoch_k=k_period, stoch_d=d_period, stoch_slowing=slowing)
    
    # Track if Stochastic was previously oversold or overbought
    result['was_oversold'] = result['stoch_k'].shift(1) < oversold
    result['was_overbought'] = result['stoch_k'].shift(1) > overbought
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - %K crosses above %D from previously being below oversold level
    buy_condition = (result['stoch_k'] > result['stoch_d']) & (result['stoch_k'].shift(1) <= result['stoch_d'].shift(1)) & result['was_oversold']
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - %K crosses below %D from previously being above overbought level
    sell_condition = (result['stoch_k'] < result['stoch_d']) & (result['stoch_k'].shift(1) >= result['stoch_d'].shift(1)) & result['was_overbought']
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 