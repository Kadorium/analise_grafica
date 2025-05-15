import pandas as pd
import numpy as np
from indicators.volume import add_volume_indicators

def generate_signals(df: pd.DataFrame, period=20, volume_threshold=2.0, price_change_threshold=0.01, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on volume spikes compared to average.
    - Buy when volume spike with price increase
    - Sell when volume spike with price decrease
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        period (int): Period for volume moving average. Default is 20.
        volume_threshold (float): Multiplier to define a volume spike. Default is 2.0 (200% of average).
        price_change_threshold (float): Minimum price change to confirm signal. Default is 0.01 (1%).
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if volume indicators are already calculated
    volume_ma_col = f'volume_sma_{period}'
    if 'volume_ratio_20' not in result.columns or volume_ma_col not in result.columns:
        # Add volume indicators
        result = add_volume_indicators(result)
        
        # If we don't have the exact MA period, calculate it
        if volume_ma_col not in result.columns:
            result[volume_ma_col] = result['volume'].rolling(window=period).mean()
    
    # Calculate volume ratio if not present
    volume_ratio_col = f'volume_ratio_{period}'
    if volume_ratio_col not in result.columns:
        result[volume_ratio_col] = result['volume'] / result[volume_ma_col]
    
    # Calculate price change
    result['price_change_pct'] = result['close'].pct_change()
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - volume spike with price increase
    buy_condition = (result[volume_ratio_col] > volume_threshold) & \
                    (result['price_change_pct'] > price_change_threshold)
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - volume spike with price decrease
    sell_condition = (result[volume_ratio_col] > volume_threshold) & \
                     (result['price_change_pct'] < -price_change_threshold)
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 