import pandas as pd
import numpy as np
from indicators.volume import add_volume_indicators
from indicators.volatility import add_volatility_indicators

def generate_signals(df: pd.DataFrame, pattern_window=20, confirmation_length=3, 
                    volume_factor=1.5, breakout_pct=1.0, **params) -> pd.DataFrame:
    """
    Generate buy/sell signals based on chart pattern recognition.
    Identifies common patterns like double tops/bottoms, flags, and triangles.
    
    Args:
        df (pd.DataFrame): DataFrame containing price data with indicators.
        pattern_window (int): Lookback window for pattern detection. Default is 20.
        confirmation_length (int): Number of bars to confirm a pattern. Default is 3.
        volume_factor (float): Volume increase factor for confirmation. Default is 1.5.
        breakout_pct (float): Percentage threshold for breakout confirmation. Default is 1.0.
        **params: Additional parameters.
        
    Returns:
        pd.DataFrame: DataFrame with added signal column.
    """
    # Create a copy of the dataframe
    result = df.copy()
    
    # Make sure we have volume indicators
    if 'volume_sma_20' not in result.columns:
        result = add_volume_indicators(result)
    
    # Make sure we have volatility indicators (ATR and Bollinger Bands)
    if 'atr' not in result.columns:
        result = add_volatility_indicators(result)
    
    # Calculate percentage change
    result['pct_change'] = result['close'].pct_change() * 100
    
    # Identify local extrema (peaks and troughs) within the window
    result['high_roll_max'] = result['high'].rolling(window=pattern_window, center=False).max()
    result['low_roll_min'] = result['low'].rolling(window=pattern_window, center=False).min()
    
    # 1. Double Top/Bottom Pattern Detection
    # -----------------------------------
    
    # Find potential tops (within 2% of recent high)
    result['top_signal'] = ((result['high'] >= result['high_roll_max'] * 0.98) & 
                           (result['high'] <= result['high_roll_max'] * 1.02))
    
    # Find potential bottoms (within 2% of recent low)
    result['bottom_signal'] = ((result['low'] <= result['low_roll_min'] * 1.02) & 
                              (result['low'] >= result['low_roll_min'] * 0.98))
    
    # Look for double tops/bottoms (two peaks/troughs with a valley/peak between)
    result['double_top'] = False
    result['double_bottom'] = False
    
    # Check each candle for pattern completion
    for i in range(pattern_window, len(result)):
        # Slice to look back at potential pattern formation
        window = result.iloc[i-pattern_window:i+1]
        
        # Find tops in this window
        tops = window[window['top_signal']].index
        
        # Find bottoms in this window
        bottoms = window[window['bottom_signal']].index
        
        # Double Top Pattern: Two tops with similar highs and a clear trough between
        if len(tops) >= 2:
            latest_tops = sorted(tops)[-2:]  # Get the latest two tops
            
            # Check if the two tops are similar in price
            top1_price = result.loc[latest_tops[0], 'high']
            top2_price = result.loc[latest_tops[1], 'high']
            
            price_diff_pct = abs(top2_price - top1_price) / top1_price * 100
            
            # Find the lowest point between the two tops
            between_idx = result[(result.index > latest_tops[0]) & 
                                (result.index < latest_tops[1])].index
            
            if len(between_idx) > 0:
                lowest_between = result.loc[between_idx, 'low'].min()
                
                # Calculate the trough depth as a percentage
                trough_depth = (top1_price - lowest_between) / top1_price * 100
                
                # Valid double top if tops are within 3% and trough is at least 3% deep
                if price_diff_pct < 3 and trough_depth > 3:
                    # The pattern completes when price breaks below the trough
                    neckline = lowest_between
                    
                    # If current close breaks below neckline with volume
                    if (result.iloc[i]['close'] < neckline and 
                        result.iloc[i]['volume'] > result.iloc[i]['volume_sma_20'] * volume_factor):
                        result.loc[result.index[i], 'double_top'] = True
        
        # Double Bottom Pattern: Two bottoms with similar lows and a clear peak between
        if len(bottoms) >= 2:
            latest_bottoms = sorted(bottoms)[-2:]  # Get the latest two bottoms
            
            # Check if the two bottoms are similar in price
            bottom1_price = result.loc[latest_bottoms[0], 'low']
            bottom2_price = result.loc[latest_bottoms[1], 'low']
            
            price_diff_pct = abs(bottom2_price - bottom1_price) / bottom1_price * 100
            
            # Find the highest point between the two bottoms
            between_idx = result[(result.index > latest_bottoms[0]) & 
                                (result.index < latest_bottoms[1])].index
            
            if len(between_idx) > 0:
                highest_between = result.loc[between_idx, 'high'].max()
                
                # Calculate the peak height as a percentage
                peak_height = (highest_between - bottom1_price) / bottom1_price * 100
                
                # Valid double bottom if bottoms are within 3% and peak is at least 3% high
                if price_diff_pct < 3 and peak_height > 3:
                    # The pattern completes when price breaks above the peak
                    neckline = highest_between
                    
                    # If current close breaks above neckline with volume
                    if (result.iloc[i]['close'] > neckline and 
                        result.iloc[i]['volume'] > result.iloc[i]['volume_sma_20'] * volume_factor):
                        result.loc[result.index[i], 'double_bottom'] = True
    
    # 2. Flag/Pennant Pattern Detection
    # --------------------------------
    
    # Find strong directional moves (poles)
    result['strong_uptrend'] = False
    result['strong_downtrend'] = False
    
    # Define strong trends (4 or more consecutive bars in same direction)
    for i in range(4, len(result)):
        # Bullish pole: 4+ consecutive up days with strong momentum
        if all(result.iloc[i-j]['close'] > result.iloc[i-j-1]['close'] for j in range(4)):
            result.loc[result.index[i], 'strong_uptrend'] = True
        
        # Bearish pole: 4+ consecutive down days with strong momentum
        if all(result.iloc[i-j]['close'] < result.iloc[i-j-1]['close'] for j in range(4)):
            result.loc[result.index[i], 'strong_downtrend'] = True
    
    # Find consolidation periods after strong moves (flag/pennant)
    result['bull_flag'] = False
    result['bear_flag'] = False
    
    for i in range(pattern_window, len(result)):
        # Check if there was a strong uptrend before
        uptrend_indices = result.iloc[i-pattern_window:i-3].index[result.iloc[i-pattern_window:i-3]['strong_uptrend']]
        
        if len(uptrend_indices) > 0:
            # Get the most recent strong uptrend
            latest_uptrend = max(uptrend_indices)
            
            # Check if we've been consolidating since the uptrend
            consolidation_period = result.loc[latest_uptrend:result.index[i]]
            
            # Calculate the price range during consolidation
            high_range = consolidation_period['high'].max()
            low_range = consolidation_period['low'].min()
            range_pct = (high_range - low_range) / low_range * 100
            
            # Flag pattern: consolidation in a small range (less than 10%)
            # followed by a breakout in the trend direction
            if range_pct < 10:
                # Breakout confirmation: price closes above the consolidation range
                # with increased volume
                if (result.iloc[i]['close'] > high_range and 
                    result.iloc[i]['close'] > result.iloc[i-1]['close'] * (1 + breakout_pct/100) and
                    result.iloc[i]['volume'] > result.iloc[i]['volume_sma_20'] * volume_factor):
                    result.loc[result.index[i], 'bull_flag'] = True
        
        # Check if there was a strong downtrend before
        downtrend_indices = result.iloc[i-pattern_window:i-3].index[result.iloc[i-pattern_window:i-3]['strong_downtrend']]
        
        if len(downtrend_indices) > 0:
            # Get the most recent strong downtrend
            latest_downtrend = max(downtrend_indices)
            
            # Check if we've been consolidating since the downtrend
            consolidation_period = result.loc[latest_downtrend:result.index[i]]
            
            # Calculate the price range during consolidation
            high_range = consolidation_period['high'].max()
            low_range = consolidation_period['low'].min()
            range_pct = (high_range - low_range) / low_range * 100
            
            # Flag pattern: consolidation in a small range (less than 10%)
            # followed by a breakout in the trend direction
            if range_pct < 10:
                # Breakout confirmation: price closes below the consolidation range
                # with increased volume
                if (result.iloc[i]['close'] < low_range and 
                    result.iloc[i]['close'] < result.iloc[i-1]['close'] * (1 - breakout_pct/100) and
                    result.iloc[i]['volume'] > result.iloc[i]['volume_sma_20'] * volume_factor):
                    result.loc[result.index[i], 'bear_flag'] = True
    
    # Initialize signal column
    result['signal'] = 'hold'
    
    # Generate buy signals
    buy_condition = (result['double_bottom'] | result['bull_flag'])
    result.loc[buy_condition, 'signal'] = 'buy'
    
    # Generate sell signals
    sell_condition = (result['double_top'] | result['bear_flag'])
    result.loc[sell_condition, 'signal'] = 'sell'
    
    return result 