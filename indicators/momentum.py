import pandas as pd
import numpy as np

def relative_strength_index(data, column='close', period=14):
    """
    Calculate the Relative Strength Index (RSI).
    
    Args:
        data (pandas.DataFrame): DataFrame containing the price data.
        column (str): Column name for which to calculate RSI. Default is 'close'.
        period (int): Period for RSI calculation. Default is 14.
        
    Returns:
        pandas.Series: Series containing the RSI values.
    """
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data")
    
    # Calculate price changes
    delta = data[column].diff()
    
    # Separate gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Calculate average gain and average loss
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # Calculate relative strength (RS)
    rs = avg_gain / avg_loss
    
    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def macd(data, column='close', fast_period=12, slow_period=26, signal_period=9):
    """
    Calculate the Moving Average Convergence Divergence (MACD).
    
    Args:
        data (pandas.DataFrame): DataFrame containing the price data.
        column (str): Column name for which to calculate MACD. Default is 'close'.
        fast_period (int): Period for the fast EMA. Default is 12.
        slow_period (int): Period for the slow EMA. Default is 26.
        signal_period (int): Period for the signal line. Default is 9.
        
    Returns:
        pandas.DataFrame: DataFrame containing 'macd', 'signal', and 'histogram' columns.
    """
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data")
    
    # Calculate EMAs
    fast_ema = data[column].ewm(span=fast_period, adjust=False).mean()
    slow_ema = data[column].ewm(span=slow_period, adjust=False).mean()
    
    # Calculate MACD line
    macd_line = fast_ema - slow_ema
    
    # Calculate signal line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    
    # Calculate histogram
    histogram = macd_line - signal_line
    
    # Create DataFrame with results
    result = pd.DataFrame({
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }, index=data.index)
    
    return result

def stochastic_oscillator(data, k_period=14, d_period=3, slowing=3):
    """
    Calculate the Stochastic Oscillator.
    
    Args:
        data (pandas.DataFrame): DataFrame containing OHLC data.
        k_period (int): Lookback period for %K. Default is 14.
        d_period (int): Smoothing period for %D. Default is 3.
        slowing (int): Slowing period. Default is 3.
        
    Returns:
        pandas.DataFrame: DataFrame containing '%K' and '%D' columns.
    """
    # Check if required columns exist
    required_columns = ['high', 'low', 'close']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    # Calculate %K
    lowest_low = data['low'].rolling(window=k_period).min()
    highest_high = data['high'].rolling(window=k_period).max()
    
    k_fast = 100 * ((data['close'] - lowest_low) / (highest_high - lowest_low))
    
    # Apply slowing if specified
    if slowing > 1:
        k = k_fast.rolling(window=slowing).mean()
    else:
        k = k_fast
    
    # Calculate %D (SMA of %K)
    d = k.rolling(window=d_period).mean()
    
    # Create DataFrame with results
    result = pd.DataFrame({
        '%K': k,
        '%D': d
    }, index=data.index)
    
    return result

def add_momentum_indicators(data, rsi_period=14, macd_fast=12, macd_slow=26, macd_signal=9, 
                           stoch_k=14, stoch_d=3, stoch_slowing=3):
    """
    Add momentum indicators to the input DataFrame.
    
    Args:
        data (pandas.DataFrame): DataFrame containing OHLC data.
        rsi_period (int): Period for RSI calculation. Default is 14.
        macd_fast (int): Fast period for MACD. Default is 12.
        macd_slow (int): Slow period for MACD. Default is 26.
        macd_signal (int): Signal period for MACD. Default is 9.
        stoch_k (int): %K period for Stochastic Oscillator. Default is 14.
        stoch_d (int): %D period for Stochastic Oscillator. Default is 3.
        stoch_slowing (int): Slowing period for Stochastic Oscillator. Default is 3.
        
    Returns:
        pandas.DataFrame: DataFrame with added momentum indicator columns.
    """
    result = data.copy()
    
    # Add RSI
    result['rsi'] = relative_strength_index(data, period=rsi_period)
    
    # Add MACD
    macd_result = macd(data, fast_period=macd_fast, slow_period=macd_slow, signal_period=macd_signal)
    result['macd'] = macd_result['macd']
    result['macd_signal'] = macd_result['signal']
    result['macd_histogram'] = macd_result['histogram']
    
    # Add Stochastic Oscillator
    stoch_result = stochastic_oscillator(data, k_period=stoch_k, d_period=stoch_d, slowing=stoch_slowing)
    result['stoch_k'] = stoch_result['%K']
    result['stoch_d'] = stoch_result['%D']
    
    return result

def detect_overbought_oversold(data, rsi_column='rsi', stoch_k_column='stoch_k', stoch_d_column='stoch_d',
                             rsi_upper=70, rsi_lower=30, stoch_upper=80, stoch_lower=20):
    """
    Detect overbought and oversold conditions using RSI and Stochastic Oscillator.
    
    Args:
        data (pandas.DataFrame): DataFrame containing the indicator data.
        rsi_column (str): Column name for RSI. Default is 'rsi'.
        stoch_k_column (str): Column name for Stochastic %K. Default is 'stoch_k'.
        stoch_d_column (str): Column name for Stochastic %D. Default is 'stoch_d'.
        rsi_upper (int): Upper threshold for RSI. Default is 70.
        rsi_lower (int): Lower threshold for RSI. Default is 30.
        stoch_upper (int): Upper threshold for Stochastic. Default is 80.
        stoch_lower (int): Lower threshold for Stochastic. Default is 20.
        
    Returns:
        pandas.DataFrame: DataFrame with added columns for overbought/oversold signals.
    """
    result = data.copy()
    
    # RSI conditions
    if rsi_column in result.columns:
        result['rsi_overbought'] = (result[rsi_column] > rsi_upper).astype(int)
        result['rsi_oversold'] = (result[rsi_column] < rsi_lower).astype(int)
    
    # Stochastic conditions
    if stoch_k_column in result.columns and stoch_d_column in result.columns:
        result['stoch_overbought'] = ((result[stoch_k_column] > stoch_upper) & 
                                    (result[stoch_d_column] > stoch_upper)).astype(int)
        result['stoch_oversold'] = ((result[stoch_k_column] < stoch_lower) & 
                                  (result[stoch_d_column] < stoch_lower)).astype(int)
    
    return result 