import pandas as pd
import numpy as np

def detect_doji(data, tolerance=0.05):
    """
    Detect Doji candlestick patterns, where opening and closing prices are very close.
    
    Args:
        data (pandas.DataFrame): DataFrame containing 'open', 'high', 'low', 'close' columns.
        tolerance (float): Maximum percentage difference between open and close to be considered a doji.
                           Default is 0.05 (5%).
        
    Returns:
        pandas.Series: Boolean series where True indicates a Doji pattern.
    """
    # Check if required columns exist
    required_columns = ['open', 'high', 'low', 'close']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    # Calculate body size as percentage of the range
    body_size = abs(data['close'] - data['open'])
    candle_range = data['high'] - data['low']
    
    # Avoid division by zero
    valid_range = candle_range > 0
    body_to_range_ratio = pd.Series(np.nan, index=data.index)
    body_to_range_ratio[valid_range] = body_size[valid_range] / candle_range[valid_range]
    
    # Identify Doji (very small body compared to the range)
    is_doji = body_to_range_ratio <= tolerance
    
    return is_doji

def detect_engulfing(data):
    """
    Detect Bullish and Bearish Engulfing candlestick patterns.
    
    Args:
        data (pandas.DataFrame): DataFrame containing 'open', 'high', 'low', 'close' columns.
        
    Returns:
        pandas.DataFrame: DataFrame with 'bullish_engulfing' and 'bearish_engulfing' columns
                          where True indicates the respective pattern.
    """
    # Check if required columns exist
    required_columns = ['open', 'high', 'low', 'close']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    # Calculate body sizes
    current_body_size = abs(data['close'] - data['open'])
    prev_body_size = abs(data['close'].shift(1) - data['open'].shift(1))
    
    # Determine if current candle is bullish (close > open) or bearish (close < open)
    current_bullish = data['close'] > data['open']
    current_bearish = data['close'] < data['open']
    prev_bullish = data['close'].shift(1) > data['open'].shift(1)
    prev_bearish = data['close'].shift(1) < data['open'].shift(1)
    
    # Bullish Engulfing: Current bullish candle completely engulfs previous bearish candle
    bullish_engulfing = (current_bullish & 
                         prev_bearish & 
                         (data['open'] <= data['close'].shift(1)) & 
                         (data['close'] >= data['open'].shift(1)) &
                         (current_body_size > prev_body_size))
    
    # Bearish Engulfing: Current bearish candle completely engulfs previous bullish candle
    bearish_engulfing = (current_bearish & 
                         prev_bullish & 
                         (data['open'] >= data['close'].shift(1)) & 
                         (data['close'] <= data['open'].shift(1)) &
                         (current_body_size > prev_body_size))
    
    # Create result DataFrame
    result = pd.DataFrame({
        'bullish_engulfing': bullish_engulfing,
        'bearish_engulfing': bearish_engulfing
    }, index=data.index)
    
    return result

def detect_hammer(data, body_ratio_threshold=0.3, tail_ratio_threshold=2.0):
    """
    Detect Hammer and Inverted Hammer (Shooting Star) candlestick patterns.
    
    Args:
        data (pandas.DataFrame): DataFrame containing 'open', 'high', 'low', 'close' columns.
        body_ratio_threshold (float): Maximum ratio of body to total candle size to be considered 
                                     a hammer. Default is 0.3 (30%).
        tail_ratio_threshold (float): Minimum ratio of tail to body to be considered a hammer.
                                     Default is 2.0 (tail should be at least 2x the body).
        
    Returns:
        pandas.DataFrame: DataFrame with 'hammer' and 'inverted_hammer' columns
                         where True indicates the respective pattern.
    """
    # Check if required columns exist
    required_columns = ['open', 'high', 'low', 'close']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    # Determine if candle is bullish or bearish
    bullish = data['close'] > data['open']
    
    # Calculate body and candle size
    body_size = abs(data['close'] - data['open'])
    candle_size = data['high'] - data['low']
    
    # Avoid division by zero
    valid_candle = candle_size > 0
    body_to_candle_ratio = pd.Series(np.nan, index=data.index)
    body_to_candle_ratio[valid_candle] = body_size[valid_candle] / candle_size[valid_candle]
    
    # Calculate upper shadow (wick)
    upper_shadow = pd.Series(np.nan, index=data.index)
    upper_shadow[bullish] = data['high'][bullish] - data['close'][bullish]
    upper_shadow[~bullish] = data['high'][~bullish] - data['open'][~bullish]
    
    # Calculate lower shadow (tail)
    lower_shadow = pd.Series(np.nan, index=data.index)
    lower_shadow[bullish] = data['open'][bullish] - data['low'][bullish]
    lower_shadow[~bullish] = data['close'][~bullish] - data['low'][~bullish]
    
    # Calculate shadow to body ratios (avoid division by zero)
    valid_body = body_size > 0
    upper_shadow_ratio = pd.Series(np.nan, index=data.index)
    lower_shadow_ratio = pd.Series(np.nan, index=data.index)
    
    upper_shadow_ratio[valid_body] = upper_shadow[valid_body] / body_size[valid_body]
    lower_shadow_ratio[valid_body] = lower_shadow[valid_body] / body_size[valid_body]
    
    # Hammer: Small body, insignificant upper shadow, long lower shadow
    hammer = ((body_to_candle_ratio <= body_ratio_threshold) & 
              (lower_shadow_ratio >= tail_ratio_threshold) & 
              (upper_shadow_ratio <= 0.5))
    
    # Inverted Hammer: Small body, long upper shadow, insignificant lower shadow
    inverted_hammer = ((body_to_candle_ratio <= body_ratio_threshold) & 
                       (upper_shadow_ratio >= tail_ratio_threshold) & 
                       (lower_shadow_ratio <= 0.5))
    
    # Create result DataFrame
    result = pd.DataFrame({
        'hammer': hammer,
        'inverted_hammer': inverted_hammer
    }, index=data.index)
    
    return result

def detect_morning_star(data, body_ratio_threshold=0.3, body_size_ratio=2.0):
    """
    Detect Morning Star and Evening Star candlestick patterns.
    
    Args:
        data (pandas.DataFrame): DataFrame containing 'open', 'high', 'low', 'close' columns.
        body_ratio_threshold (float): Maximum ratio of middle candle body to its total size. 
                                    Default is 0.3 (30%).
        body_size_ratio (float): Minimum ratio of first/third candle body size relative to middle candle.
                               Default is 2.0 (first and third candles should have bodies at least 
                               twice as large as the middle candle).
        
    Returns:
        pandas.DataFrame: DataFrame with 'morning_star' and 'evening_star' columns
                         where True indicates the respective pattern.
    """
    # Check if required columns exist
    required_columns = ['open', 'high', 'low', 'close']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")
    
    # Calculate body sizes for 3 consecutive candles
    body_size = abs(data['close'] - data['open'])
    body_size_prev = body_size.shift(1)
    body_size_prev2 = body_size.shift(2)
    
    # Middle candle should have a small body
    candle_size_middle = data['high'].shift(1) - data['low'].shift(1)
    valid_middle_candle = candle_size_middle > 0
    
    body_to_candle_ratio_middle = pd.Series(np.nan, index=data.index)
    body_to_candle_ratio_middle[valid_middle_candle] = body_size_prev[valid_middle_candle] / candle_size_middle[valid_middle_candle]
    small_body_middle = body_to_candle_ratio_middle <= body_ratio_threshold
    
    # First and third candles should have larger bodies than middle candle
    valid_body_comparison = body_size_prev > 0
    first_larger_than_middle = pd.Series(False, index=data.index)
    third_larger_than_middle = pd.Series(False, index=data.index)
    
    first_larger_than_middle[valid_body_comparison] = body_size_prev2[valid_body_comparison] / body_size_prev[valid_body_comparison] >= body_size_ratio
    third_larger_than_middle[valid_body_comparison] = body_size[valid_body_comparison] / body_size_prev[valid_body_comparison] >= body_size_ratio
    
    # Determine candle directions
    bullish = data['close'] > data['open']
    bearish = data['close'] < data['open']
    bullish_prev2 = data['close'].shift(2) > data['open'].shift(2)
    bearish_prev2 = data['close'].shift(2) < data['open'].shift(2)
    
    # Gap between first and second candles
    gap_down = ((pd.DataFrame({'a': data['open'].shift(1), 'b': data['close'].shift(1)}).min(axis=1) < 
                pd.DataFrame({'a': data['open'].shift(2), 'b': data['close'].shift(2)}).min(axis=1)) & 
               (pd.DataFrame({'a': data['open'].shift(1), 'b': data['close'].shift(1)}).max(axis=1) < 
                pd.DataFrame({'a': data['open'].shift(2), 'b': data['close'].shift(2)}).max(axis=1)))
    
    gap_up = ((pd.DataFrame({'a': data['open'].shift(1), 'b': data['close'].shift(1)}).min(axis=1) > 
              pd.DataFrame({'a': data['open'].shift(2), 'b': data['close'].shift(2)}).min(axis=1)) & 
             (pd.DataFrame({'a': data['open'].shift(1), 'b': data['close'].shift(1)}).max(axis=1) > 
              pd.DataFrame({'a': data['open'].shift(2), 'b': data['close'].shift(2)}).max(axis=1)))
    
    # Morning Star: First bearish, small middle, third bullish
    morning_star = (bearish_prev2 & 
                    small_body_middle & 
                    bullish & 
                    first_larger_than_middle & 
                    third_larger_than_middle & 
                    gap_down & 
                    (data['close'] > (data['open'].shift(2) + data['close'].shift(2)) / 2))
    
    # Evening Star: First bullish, small middle, third bearish
    evening_star = (bullish_prev2 & 
                    small_body_middle & 
                    bearish & 
                    first_larger_than_middle & 
                    third_larger_than_middle & 
                    gap_up & 
                    (data['close'] < (data['open'].shift(2) + data['close'].shift(2)) / 2))
    
    # Create result DataFrame
    result = pd.DataFrame({
        'morning_star': morning_star,
        'evening_star': evening_star
    }, index=data.index)
    
    return result

def add_candlestick_patterns(data):
    """
    Add all candlestick pattern indicators to the input DataFrame.
    
    Args:
        data (pandas.DataFrame): DataFrame containing OHLC data.
        
    Returns:
        pandas.DataFrame: DataFrame with added candlestick pattern columns.
    """
    result = data.copy()
    
    # Add Doji pattern
    result['doji'] = detect_doji(data)
    
    # Add Engulfing patterns
    engulfing_patterns = detect_engulfing(data)
    result['bullish_engulfing'] = engulfing_patterns['bullish_engulfing']
    result['bearish_engulfing'] = engulfing_patterns['bearish_engulfing']
    
    # Add Hammer patterns
    hammer_patterns = detect_hammer(data)
    result['hammer'] = hammer_patterns['hammer']
    result['inverted_hammer'] = hammer_patterns['inverted_hammer']
    
    # Add Morning/Evening Star patterns
    star_patterns = detect_morning_star(data)
    result['morning_star'] = star_patterns['morning_star']
    result['evening_star'] = star_patterns['evening_star']
    
    return result 