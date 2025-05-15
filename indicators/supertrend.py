import pandas as pd
import numpy as np

def supertrend(data, atr_period=10, multiplier=3):
    """
    Calculate SuperTrend indicator based on ATR.
    
    Args:
        data (pandas.DataFrame): DataFrame containing 'high', 'low', 'close' columns.
        atr_period (int): Period for ATR calculation. Default is 10.
        multiplier (float): Multiplier for ATR. Default is 3.
        
    Returns:
        pandas.DataFrame: DataFrame containing 'supertrend', 'supertrend_direction', and 'supertrend_signal' columns.
    """
    # Check if required columns exist
    required_columns = ['high', 'low', 'close']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    df = data.copy()
    
    # Calculate True Range
    df['high_low'] = df['high'] - df['low']
    df['high_close'] = abs(df['high'] - df['close'].shift(1))
    df['low_close'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
    
    # Calculate ATR
    df['atr'] = df['tr'].rolling(window=atr_period).mean()
    
    # Calculate Basic Upper and Lower Band
    df['basic_upper_band'] = (df['high'] + df['low']) / 2 + (multiplier * df['atr'])
    df['basic_lower_band'] = (df['high'] + df['low']) / 2 - (multiplier * df['atr'])
    
    # Initialize SuperTrend columns
    df['supertrend'] = 0.0
    df['supertrend_direction'] = 0  # 1 for uptrend, -1 for downtrend
    df['final_upper_band'] = 0.0
    df['final_lower_band'] = 0.0
    
    # Calculate SuperTrend using recursive logic
    for i in range(atr_period, len(df)):
        if i == atr_period:
            # First value
            df.loc[df.index[i], 'final_upper_band'] = df.loc[df.index[i], 'basic_upper_band']
            df.loc[df.index[i], 'final_lower_band'] = df.loc[df.index[i], 'basic_lower_band']
            
            if df.loc[df.index[i], 'close'] <= df.loc[df.index[i], 'final_upper_band']:
                df.loc[df.index[i], 'supertrend'] = df.loc[df.index[i], 'final_upper_band']
                df.loc[df.index[i], 'supertrend_direction'] = -1
            else:
                df.loc[df.index[i], 'supertrend'] = df.loc[df.index[i], 'final_lower_band']
                df.loc[df.index[i], 'supertrend_direction'] = 1
        else:
            # Current upper band depends on previous values
            if (df.loc[df.index[i-1], 'final_upper_band'] < df.loc[df.index[i], 'basic_upper_band'] or 
                df.loc[df.index[i-1], 'close'] > df.loc[df.index[i-1], 'final_upper_band']):
                df.loc[df.index[i], 'final_upper_band'] = df.loc[df.index[i], 'basic_upper_band']
            else:
                df.loc[df.index[i], 'final_upper_band'] = df.loc[df.index[i-1], 'final_upper_band']
            
            # Current lower band depends on previous values
            if (df.loc[df.index[i-1], 'final_lower_band'] > df.loc[df.index[i], 'basic_lower_band'] or 
                df.loc[df.index[i-1], 'close'] < df.loc[df.index[i-1], 'final_lower_band']):
                df.loc[df.index[i], 'final_lower_band'] = df.loc[df.index[i], 'basic_lower_band']
            else:
                df.loc[df.index[i], 'final_lower_band'] = df.loc[df.index[i-1], 'final_lower_band']
            
            # Update SuperTrend based on current close and direction
            if (df.loc[df.index[i-1], 'supertrend_direction'] == -1 and 
                df.loc[df.index[i], 'close'] > df.loc[df.index[i], 'final_upper_band']):
                df.loc[df.index[i], 'supertrend'] = df.loc[df.index[i], 'final_lower_band']
                df.loc[df.index[i], 'supertrend_direction'] = 1
            elif (df.loc[df.index[i-1], 'supertrend_direction'] == 1 and 
                  df.loc[df.index[i], 'close'] < df.loc[df.index[i], 'final_lower_band']):
                df.loc[df.index[i], 'supertrend'] = df.loc[df.index[i], 'final_upper_band']
                df.loc[df.index[i], 'supertrend_direction'] = -1
            else:
                # Continue with the same direction
                df.loc[df.index[i], 'supertrend_direction'] = df.loc[df.index[i-1], 'supertrend_direction']
                if df.loc[df.index[i], 'supertrend_direction'] == 1:
                    df.loc[df.index[i], 'supertrend'] = df.loc[df.index[i], 'final_lower_band']
                else:
                    df.loc[df.index[i], 'supertrend'] = df.loc[df.index[i], 'final_upper_band']
    
    # Generate SuperTrend signal (1 for buy, -1 for sell, 0 for no signal/hold)
    df['supertrend_signal'] = df['supertrend_direction'].diff()
    
    # Create result DataFrame with only the necessary columns
    result = pd.DataFrame({
        'supertrend': df['supertrend'],
        'supertrend_direction': df['supertrend_direction'],
        'supertrend_signal': df['supertrend_signal']
    }, index=data.index)
    
    return result

def add_supertrend_indicator(data, atr_period=10, multiplier=3):
    """
    Add SuperTrend indicator to the input DataFrame.
    
    Args:
        data (pandas.DataFrame): DataFrame containing OHLC data.
        atr_period (int): Period for ATR calculation. Default is 10.
        multiplier (float): Multiplier for ATR. Default is 3.
        
    Returns:
        pandas.DataFrame: DataFrame with added SuperTrend indicator columns.
    """
    result = data.copy()
    
    # Add SuperTrend
    supertrend_data = supertrend(data, atr_period=atr_period, multiplier=multiplier)
    result['supertrend'] = supertrend_data['supertrend']
    result['supertrend_direction'] = supertrend_data['supertrend_direction']
    result['supertrend_signal'] = supertrend_data['supertrend_signal']
    
    return result 