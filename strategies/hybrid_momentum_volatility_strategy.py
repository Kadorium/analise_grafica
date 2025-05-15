import pandas as pd
import numpy as np
from indicators.momentum import relative_strength_index, add_momentum_indicators
from indicators.volatility import add_volatility_indicators
from indicators.volume import add_volume_indicators

def generate_signals(df: pd.DataFrame, rsi_period=14, bb_window=20, bb_std=2.0, 
                    rsi_oversold=30, rsi_overbought=70, volume_factor=1.5, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on a hybrid momentum-volatility strategy.
    - Buy when RSI is oversold AND price is near lower Bollinger Band with increased volume
    - Sell when RSI is overbought AND price is near upper Bollinger Band with increased volume
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        rsi_period (int): Period for RSI calculation. Default is 14.
        bb_window (int): Window for Bollinger Bands calculation. Default is 20.
        bb_std (float): Standard deviation multiplier for Bollinger Bands. Default is 2.0.
        rsi_oversold (int): RSI level for oversold conditions. Default is 30.
        rsi_overbought (int): RSI level for overbought conditions. Default is 70.
        volume_factor (float): Factor to compare current volume to average. Default is 1.5.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if RSI is already calculated
    if 'rsi' not in result.columns:
        # Add RSI indicators
        if 'momentum_indicators_added' not in result.columns:
            result = add_momentum_indicators(result, rsi_period=rsi_period)
        else:
            result['rsi'] = relative_strength_index(result, period=rsi_period)
    
    # Check if Bollinger Bands are already calculated
    if 'bb_upper' not in result.columns or 'bb_lower' not in result.columns or 'bb_middle' not in result.columns:
        # Add volatility indicators
        result = add_volatility_indicators(result, bollinger_window=bb_window, bollinger_std=bb_std)
    
    # Calculate relative volume (current volume compared to average)
    if 'volume_sma_20' not in result.columns:
        result = add_volume_indicators(result)
    
    # Calculate distance from price to Bollinger Bands as percentage
    result['bb_upper_dist'] = (result['bb_upper'] - result['close']) / result['close'] * 100
    result['bb_lower_dist'] = (result['close'] - result['bb_lower']) / result['close'] * 100
    
    # Create proximity indicators (when price is near the bands)
    result['near_upper_band'] = result['bb_upper_dist'] < 1.0  # Within 1% of upper band
    result['near_lower_band'] = result['bb_lower_dist'] < 1.0  # Within 1% of lower band
    
    # Volume condition
    result['high_volume'] = result['volume'] > result['volume_sma_20'] * volume_factor
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - RSI oversold + near lower band + high volume
    buy_condition = (
        (result['rsi'] < rsi_oversold) & 
        result['near_lower_band'] & 
        result['high_volume'] & 
        (result['rsi'].shift(1) <= result['rsi'])  # RSI starting to rise
    )
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - RSI overbought + near upper band + high volume
    sell_condition = (
        (result['rsi'] > rsi_overbought) & 
        result['near_upper_band'] & 
        result['high_volume'] & 
        (result['rsi'].shift(1) >= result['rsi'])  # RSI starting to fall
    )
    result.loc[sell_condition, 'signal'] = 'sell'
    
    # Add additional exit signals based on mean reversion
    # Exit long positions when price reaches middle band after being near lower band
    exit_buy_condition = (
        (result['close'] > result['bb_middle']) & 
        (result['close'].shift(1) <= result['bb_middle'].shift(1)) &
        (result['signal'].shift(1) != 'sell')  # Not already a sell signal
    )
    result.loc[exit_buy_condition, 'signal'] = 'sell'
    
    # Exit short positions when price reaches middle band after being near upper band
    exit_sell_condition = (
        (result['close'] < result['bb_middle']) & 
        (result['close'].shift(1) >= result['bb_middle'].shift(1)) &
        (result['signal'].shift(1) != 'buy')  # Not already a buy signal
    )
    result.loc[exit_sell_condition, 'signal'] = 'buy'
    
    return result 