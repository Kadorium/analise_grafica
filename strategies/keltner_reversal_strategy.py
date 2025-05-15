import pandas as pd
import numpy as np
from indicators.keltner_channels import add_keltner_channels_indicator

def generate_signals(df: pd.DataFrame, ema_period=20, atr_period=10, multiplier=1.5, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on price reversals from Keltner Channel boundaries.
    - Buy when price touches lower band and then reverses up
    - Sell when price touches upper band and then reverses down
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        ema_period (int): Period for EMA calculation. Default is 20.
        atr_period (int): Period for ATR calculation. Default is 10.
        multiplier (float): Multiplier for ATR. Default is 1.5.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Check if Keltner Channels are already calculated
    if 'kc_upper' not in result.columns or 'kc_lower' not in result.columns:
        # Add Keltner Channels
        result = add_keltner_channels_indicator(result, ema_period=ema_period, 
                                                 atr_period=atr_period, multiplier=multiplier)
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Track when price is at/below lower band or at/above upper band
    result['at_lower_band'] = result['low'] <= result['kc_lower']
    result['at_upper_band'] = result['high'] >= result['kc_upper']
    
    # Track price movement after touching bands (reversal detection)
    result['price_change'] = result['close'].diff()
    
    # Generate buy signals - price touches lower band and then moves up
    buy_condition = (result['at_lower_band'].shift(1) == True) & (result['price_change'] > 0)
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals - price touches upper band and then moves down
    sell_condition = (result['at_upper_band'].shift(1) == True) & (result['price_change'] < 0)
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 