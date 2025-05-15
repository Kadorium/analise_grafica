import pandas as pd
import numpy as np

def average_directional_index(data, period=14):
    """
    Calculate Average Directional Index (ADX) with +DI and -DI lines.
    
    Args:
        data (pandas.DataFrame): DataFrame containing 'high', 'low', 'close' columns.
        period (int): Period for ADX calculation. Default is 14.
        
    Returns:
        pandas.DataFrame: DataFrame containing 'adx', 'plus_di', and 'minus_di' columns.
    """
    # Check if required columns exist
    required_columns = ['high', 'low', 'close']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    df = data.copy()
    
    # Calculate True Range (TR)
    df['high_low'] = df['high'] - df['low']
    df['high_close'] = abs(df['high'] - df['close'].shift(1))
    df['low_close'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
    
    # Calculate Directional Movement (DM)
    df['up_move'] = df['high'] - df['high'].shift(1)
    df['down_move'] = df['low'].shift(1) - df['low']
    
    # Calculate +DM and -DM
    df['+dm'] = np.where((df['up_move'] > df['down_move']) & (df['up_move'] > 0), df['up_move'], 0)
    df['-dm'] = np.where((df['down_move'] > df['up_move']) & (df['down_move'] > 0), df['down_move'], 0)
    
    # Calculate smoothed TR, +DM, and -DM
    # First period uses simple moving average
    df['tr_period'] = df['tr'].rolling(window=period).sum()
    df['+dm_period'] = df['+dm'].rolling(window=period).sum()
    df['-dm_period'] = df['-dm'].rolling(window=period).sum()
    
    # For subsequent periods, use Wilder's smoothing
    for i in range(period, len(df)):
        df.loc[df.index[i], 'tr_period'] = df.loc[df.index[i-1], 'tr_period'] - (df.loc[df.index[i-1], 'tr_period'] / period) + df.loc[df.index[i], 'tr']
        df.loc[df.index[i], '+dm_period'] = df.loc[df.index[i-1], '+dm_period'] - (df.loc[df.index[i-1], '+dm_period'] / period) + df.loc[df.index[i], '+dm']
        df.loc[df.index[i], '-dm_period'] = df.loc[df.index[i-1], '-dm_period'] - (df.loc[df.index[i-1], '-dm_period'] / period) + df.loc[df.index[i], '-dm']
    
    # Calculate +DI and -DI
    df['plus_di'] = 100 * (df['+dm_period'] / df['tr_period'])
    df['minus_di'] = 100 * (df['-dm_period'] / df['tr_period'])
    
    # Calculate DX (Directional Index)
    df['dx'] = 100 * (abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di']))
    
    # Calculate ADX (smooth DX)
    df['adx'] = df['dx'].rolling(window=period).mean()
    
    # For subsequent periods, use Wilder's smoothing for ADX
    for i in range(2*period, len(df)):
        df.loc[df.index[i], 'adx'] = ((period - 1) * df.loc[df.index[i-1], 'adx'] + df.loc[df.index[i], 'dx']) / period
    
    # Create result DataFrame with only the necessary columns
    result = pd.DataFrame({
        'adx': df['adx'],
        'plus_di': df['plus_di'],
        'minus_di': df['minus_di']
    }, index=data.index)
    
    return result

def add_adx_indicator(data, period=14):
    """
    Add ADX indicator to the input DataFrame.
    
    Args:
        data (pandas.DataFrame): DataFrame containing OHLC data.
        period (int): Period for ADX calculation. Default is 14.
        
    Returns:
        pandas.DataFrame: DataFrame with added ADX indicator columns.
    """
    result = data.copy()
    
    # Add ADX
    adx_data = average_directional_index(data, period=period)
    result['adx'] = adx_data['adx']
    result['plus_di'] = adx_data['plus_di']
    result['minus_di'] = adx_data['minus_di']
    
    return result 