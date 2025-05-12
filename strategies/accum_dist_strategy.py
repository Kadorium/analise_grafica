import pandas as pd
import numpy as np
from indicators.accumulation_distribution import add_accumulation_distribution_indicator

def generate_signals(df: pd.DataFrame, ad_period=20, price_period=20, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on Accumulation/Distribution Line divergence.
    - Buy when price makes a new low but A/D line makes a higher low (bullish divergence)
    - Sell when price makes a new high but A/D line makes a lower high (bearish divergence)
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        ad_period (int): Period for A/D line moving average. Default is 20.
        price_period (int): Period for detecting price extremes. Default is 20.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if A/D Line is already calculated
    if 'ad_line' not in result.columns:
        # Add A/D Line indicator
        result = add_accumulation_distribution_indicator(result)
    
    # Calculate A/D Line moving average
    result['ad_line_ma'] = result['ad_line'].rolling(window=ad_period).mean()
    
    # Calculate local minima and maxima for price
    result['price_low'] = result['close'].rolling(window=price_period).min()
    result['price_high'] = result['close'].rolling(window=price_period).max()
    
    # Calculate local minima and maxima for A/D Line
    result['ad_line_low'] = result['ad_line'].rolling(window=price_period).min()
    result['ad_line_high'] = result['ad_line'].rolling(window=price_period).max()
    
    # Calculate percentage changes to identify trends
    result['price_change'] = result['close'].pct_change(periods=price_period)
    result['ad_line_change'] = result['ad_line'].diff(periods=price_period) / result['ad_line'].abs()
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - bullish divergence
    # Price makes a new low but A/D Line doesn't
    buy_condition = (result['price_change'] < -0.02) & \
                    (result['ad_line_change'] > 0) & \
                    (result['close'] == result['price_low']) & \
                    (result['ad_line'] > result['ad_line_low'].shift(1))
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - bearish divergence
    # Price makes a new high but A/D Line doesn't
    sell_condition = (result['price_change'] > 0.02) & \
                    (result['ad_line_change'] < 0) & \
                    (result['close'] == result['price_high']) & \
                    (result['ad_line'] < result['ad_line_high'].shift(1))
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 