import pandas as pd
import numpy as np

def simple_moving_average(data, column='close', window=20):
    """
    Calculate the Simple Moving Average (SMA).
    
    Args:
        data (pandas.DataFrame): DataFrame containing the price data.
        column (str): Column name for which to calculate SMA. Default is 'close'.
        window (int): Window size for the moving average. Default is 20.
        
    Returns:
        pandas.Series: Series containing the SMA values.
    """
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data")
    
    return data[column].rolling(window=window).mean()

def exponential_moving_average(data, column='close', window=20):
    """
    Calculate the Exponential Moving Average (EMA).
    
    Args:
        data (pandas.DataFrame): DataFrame containing the price data.
        column (str): Column name for which to calculate EMA. Default is 'close'.
        window (int): Window size for the moving average. Default is 20.
        
    Returns:
        pandas.Series: Series containing the EMA values.
    """
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data")
    
    return data[column].ewm(span=window, adjust=False).mean()

def detect_ma_crossover(data, fast_ma, slow_ma):
    """
    Detect crossovers between two moving averages.
    
    Args:
        data (pandas.DataFrame): DataFrame containing the price data.
        fast_ma (pandas.Series): Faster moving average (shorter period).
        slow_ma (pandas.Series): Slower moving average (longer period).
        
    Returns:
        pandas.DataFrame: DataFrame with added columns for crossover signals:
                         - 'golden_cross': 1 when fast_ma crosses above slow_ma, 0 otherwise
                         - 'death_cross': 1 when fast_ma crosses below slow_ma, 0 otherwise
    """
    # Create a copy of the input data to avoid modifying the original
    result = data.copy()
    
    # Calculate crossover conditions
    result['golden_cross'] = 0
    result['death_cross'] = 0
    
    # Previous day fast_ma was below slow_ma and current day fast_ma is above slow_ma
    golden_cross = (fast_ma.shift(1) < slow_ma.shift(1)) & (fast_ma > slow_ma)
    result.loc[golden_cross, 'golden_cross'] = 1
    
    # Previous day fast_ma was above slow_ma and current day fast_ma is below slow_ma
    death_cross = (fast_ma.shift(1) > slow_ma.shift(1)) & (fast_ma < slow_ma)
    result.loc[death_cross, 'death_cross'] = 1
    
    return result

def add_moving_averages(data, sma_periods=None, ema_periods=None, column='close'):
    """
    Add multiple moving averages to the input DataFrame.
    
    Args:
        data (pandas.DataFrame): DataFrame containing the price data.
        sma_periods (list, optional): List of periods for SMAs. Default is [20, 50, 200].
        ema_periods (list, optional): List of periods for EMAs. Default is [12, 26, 50].
        column (str): Column name for which to calculate the moving averages. Default is 'close'.
        
    Returns:
        pandas.DataFrame: DataFrame with added columns for each moving average.
    """
    if sma_periods is None:
        sma_periods = [20, 50, 200]
        
    if ema_periods is None:
        ema_periods = [12, 26, 50]
    
    result = data.copy()
    
    # Add SMAs
    for period in sma_periods:
        result[f'sma_{period}'] = simple_moving_average(data, column, period)
        
    # Add EMAs
    for period in ema_periods:
        result[f'ema_{period}'] = exponential_moving_average(data, column, period)
        
    return result

def add_crossover_signals(data, fast_ma_col, slow_ma_col):
    """
    Add crossover signals between two moving averages.
    
    Args:
        data (pandas.DataFrame): DataFrame containing the moving averages.
        fast_ma_col (str): Column name of the faster moving average.
        slow_ma_col (str): Column name of the slower moving average.
        
    Returns:
        pandas.DataFrame: DataFrame with added crossover signal columns.
    """
    if fast_ma_col not in data.columns:
        raise ValueError(f"Column '{fast_ma_col}' not found in data")
        
    if slow_ma_col not in data.columns:
        raise ValueError(f"Column '{slow_ma_col}' not found in data")
    
    return detect_ma_crossover(data, data[fast_ma_col], data[slow_ma_col]) 