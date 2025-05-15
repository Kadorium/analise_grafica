import pandas as pd
import numpy as np
from indicators.volume import add_volume_indicators

def generate_signals(df: pd.DataFrame, obv_period=20, price_period=20, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on On-Balance Volume (OBV) and price trends.
    - Buy when OBV and price both trend upward
    - Sell when OBV and price diverge or both trend downward
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        obv_period (int): Period for OBV moving average. Default is 20.
        price_period (int): Period for price moving average. Default is 20.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if OBV is already calculated
    if 'obv' not in result.columns:
        # Add volume indicators
        result = add_volume_indicators(result)
    
    # Calculate moving averages for OBV and price
    result['obv_ma'] = result['obv'].rolling(window=obv_period).mean()
    
    # Calculate MA for price if not already done
    price_ma_col = f'sma_{price_period}'
    if price_ma_col not in result.columns:
        result[price_ma_col] = result['close'].rolling(window=price_period).mean()
    
    # Calculate trends (current value vs. moving average)
    result['obv_trend'] = (result['obv'] > result['obv_ma']).astype(int)
    result['price_trend'] = (result['close'] > result[price_ma_col]).astype(int)
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals - OBV and price both trending up
    buy_condition = (result['obv_trend'] == 1) & (result['price_trend'] == 1) & \
                    ((result['obv_trend'].shift(1) == 0) | (result['price_trend'].shift(1) == 0))
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - OBV trending down while price still up (negative divergence)
    # or both OBV and price trending down
    sell_condition_1 = (result['obv_trend'] == 0) & (result['price_trend'] == 1) & \
                      (result['obv_trend'].shift(1) == 1)  # OBV trend changes from up to down while price still up
    
    sell_condition_2 = (result['obv_trend'] == 0) & (result['price_trend'] == 0) & \
                      ((result['obv_trend'].shift(1) == 1) | (result['price_trend'].shift(1) == 1))  # Both turn down
    
    result.loc[sell_condition_1 | sell_condition_2, 'signal'] = 'sell'
    
    return result 