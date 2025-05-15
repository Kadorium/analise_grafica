import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import io
import base64
import logging

logger = logging.getLogger(__name__)

def combine_indicators(data, indicators_config=None):
    """
    Combine multiple indicators based on configuration.
    
    Args:
        data (pandas.DataFrame): DataFrame containing the price data.
        indicators_config (dict): Configuration for indicators to include.
            Example: {
                'moving_averages': {'sma_window': 50, 'ema_window': 20},
                'rsi': {'period': 14},
                'macd': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
                'bollinger_bands': {'window': 20, 'num_std': 2}
            }
    
    Returns:
        pandas.DataFrame: DataFrame with all requested indicators added.
    """
    from indicators.moving_averages import add_moving_averages
    from indicators.momentum import add_momentum_indicators
    from indicators.volume import add_volume_indicators
    from indicators.volatility import add_volatility_indicators
    from indicators.adx import add_adx_indicator
    from indicators.supertrend import add_supertrend_indicator
    from indicators.cci import add_cci_indicator
    from indicators.williams_r import add_williams_r_indicator
    from indicators.chaikin_money_flow import add_chaikin_money_flow_indicator
    from indicators.donchian_channels import add_donchian_channels_indicator
    from indicators.keltner_channels import add_keltner_channels_indicator
    from indicators.accumulation_distribution import add_accumulation_distribution_indicator
    from indicators.candlestick_patterns import add_candlestick_patterns
    
    if indicators_config is None:
        indicators_config = {
            'moving_averages': {'sma_periods': [20, 50, 200], 'ema_periods': [12, 26, 50]},
            'rsi': {'period': 14},
            'macd': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
            'bollinger_bands': {'window': 20, 'num_std': 2}
        }
    
    result = data.copy()
    
    # Track existing and new indicators
    existing_indicators = [col for col in result.columns 
                         if col not in ['date', 'open', 'high', 'low', 'close', 'volume']]
    print(f"Existing indicators: {existing_indicators}")
    
    # Add Moving Averages
    if 'moving_averages' in indicators_config:
        config = indicators_config['moving_averages']
        
        # Handle the case where we have separate sma_periods and ema_periods
        sma_periods = config.get('sma_periods', [20, 50, 200])
        ema_periods = config.get('ema_periods', [12, 26, 50])
        
        # For backward compatibility, check if 'periods' key exists
        if 'periods' in config:
            periods = config['periods']
            if 'sma' in config.get('types', []):
                sma_periods = periods
            if 'ema' in config.get('types', []):
                ema_periods = periods
        
        # Only include the types that are selected
        types = config.get('types', [])
        if 'sma' not in types:
            sma_periods = []
        if 'ema' not in types:
            ema_periods = []
            
        # Check if indicators already exist before adding
        expected_sma_columns = [f'sma_{period}' for period in sma_periods]
        expected_ema_columns = [f'ema_{period}' for period in ema_periods]
        
        # Filter out periods that already have indicators
        sma_periods_to_add = [period for period in sma_periods 
                            if f'sma_{period}' not in existing_indicators]
        ema_periods_to_add = [period for period in ema_periods 
                            if f'ema_{period}' not in existing_indicators]
        
        print(f"Adding SMA periods: {sma_periods_to_add} (requested: {sma_periods})")
        print(f"Adding EMA periods: {ema_periods_to_add} (requested: {ema_periods})")
        
        if sma_periods_to_add or ema_periods_to_add:
            result = add_moving_averages(result, 
                                      sma_periods=sma_periods_to_add,
                                      ema_periods=ema_periods_to_add)
    
    # Add Momentum Indicators
    if any(k in indicators_config for k in ['rsi', 'macd', 'stochastic']):
        momentum_params = {}
        
        # Only add RSI if it doesn't already exist
        if 'rsi' in indicators_config and 'rsi' not in existing_indicators:
            momentum_params['rsi_period'] = indicators_config['rsi'].get('period', 14)
            
        # Only add MACD if it doesn't already exist
        if 'macd' in indicators_config and not all(col in existing_indicators for col in ['macd', 'macd_signal', 'macd_histogram']):
            macd_config = indicators_config['macd']
            momentum_params['macd_fast'] = macd_config.get('fast_period', 12)
            momentum_params['macd_slow'] = macd_config.get('slow_period', 26)
            momentum_params['macd_signal'] = macd_config.get('signal_period', 9)
            
        # Only add Stochastic if it doesn't already exist
        if 'stochastic' in indicators_config and not all(col in existing_indicators for col in ['stoch_k', 'stoch_d']):
            stoch_config = indicators_config['stochastic']
            momentum_params['stoch_k'] = stoch_config.get('k_period', 14)
            momentum_params['stoch_d'] = stoch_config.get('d_period', 3)
            momentum_params['stoch_slowing'] = stoch_config.get('slowing', 3)
        
        print(f"Adding momentum indicators with params: {momentum_params}")
        
        # Only call the function if we have parameters to process
        if momentum_params:
            result = add_momentum_indicators(result, **momentum_params)
    
    # Add Volume Indicators
    if 'volume' in indicators_config and not any(col in existing_indicators for col in ['obv', 'vpt']):
        print("Adding volume indicators")
        result = add_volume_indicators(result)
    
    # Add Volatility Indicators
    if any(k in indicators_config for k in ['atr', 'bollinger_bands']):
        volatility_params = {}
        
        # Only add ATR if it doesn't already exist
        if 'atr' in indicators_config and 'atr' not in existing_indicators:
            volatility_params['atr_period'] = indicators_config['atr'].get('period', 14)
            
        # Only add Bollinger Bands if they don't already exist
        bb_columns = ['bb_upper', 'bb_middle', 'bb_lower']
        if 'bollinger_bands' in indicators_config and not all(col in existing_indicators for col in bb_columns):
            bb_config = indicators_config['bollinger_bands']
            volatility_params['bollinger_window'] = bb_config.get('window', 20)
            volatility_params['bollinger_std'] = bb_config.get('num_std', 2)
        
        print(f"Adding volatility indicators with params: {volatility_params}")
        
        # Only call the function if we have parameters to process
        if volatility_params:
            result = add_volatility_indicators(result, **volatility_params)
    
    # Add ADX Indicator
    if 'adx' in indicators_config and not all(col in existing_indicators for col in ['adx', 'plus_di', 'minus_di']):
        adx_config = indicators_config['adx']
        adx_period = adx_config.get('period', 14)
        print(f"Adding ADX indicator with period: {adx_period}")
        result = add_adx_indicator(result, period=adx_period)
    
    # Add SuperTrend Indicator
    if 'supertrend' in indicators_config and not all(col in existing_indicators for col in ['supertrend', 'supertrend_direction', 'supertrend_signal']):
        supertrend_config = indicators_config['supertrend']
        atr_period = supertrend_config.get('atr_period', 10)
        multiplier = supertrend_config.get('multiplier', 3)
        print(f"Adding SuperTrend indicator with ATR period: {atr_period}, multiplier: {multiplier}")
        result = add_supertrend_indicator(result, atr_period=atr_period, multiplier=multiplier)
    
    # Add CCI Indicator
    if 'cci' in indicators_config and 'cci' not in existing_indicators:
        cci_config = indicators_config['cci']
        cci_period = cci_config.get('period', 20)
        print(f"Adding CCI indicator with period: {cci_period}")
        result = add_cci_indicator(result, period=cci_period)
    
    # Add Williams %R Indicator
    if 'williams_r' in indicators_config and 'williams_r' not in existing_indicators:
        williams_config = indicators_config['williams_r']
        williams_period = williams_config.get('period', 14)
        print(f"Adding Williams %R indicator with period: {williams_period}")
        result = add_williams_r_indicator(result, period=williams_period)
    
    # Add Chaikin Money Flow Indicator
    if 'cmf' in indicators_config and 'cmf' not in existing_indicators:
        cmf_config = indicators_config['cmf']
        cmf_period = cmf_config.get('period', 20)
        print(f"Adding Chaikin Money Flow indicator with period: {cmf_period}")
        result = add_chaikin_money_flow_indicator(result, period=cmf_period)
    
    # Add Donchian Channels Indicator
    if 'donchian_channels' in indicators_config and not all(col in existing_indicators for col in ['dc_upper', 'dc_middle', 'dc_lower']):
        donchian_config = indicators_config['donchian_channels']
        donchian_period = donchian_config.get('period', 20)
        print(f"Adding Donchian Channels indicator with period: {donchian_period}")
        result = add_donchian_channels_indicator(result, period=donchian_period)
    
    # Add Keltner Channels Indicator
    if 'keltner_channels' in indicators_config and not all(col in existing_indicators for col in ['kc_upper', 'kc_middle', 'kc_lower']):
        keltner_config = indicators_config['keltner_channels']
        ema_period = keltner_config.get('ema_period', 20)
        atr_period = keltner_config.get('atr_period', 10)
        multiplier = keltner_config.get('multiplier', 1.5)
        print(f"Adding Keltner Channels indicator with EMA period: {ema_period}, ATR period: {atr_period}, multiplier: {multiplier}")
        result = add_keltner_channels_indicator(result, ema_period=ema_period, atr_period=atr_period, multiplier=multiplier)
    
    # Add Accumulation Distribution Line Indicator
    if 'ad_line' in indicators_config and 'ad_line' not in existing_indicators:
        print("Adding Accumulation Distribution Line indicator")
        result = add_accumulation_distribution_indicator(result)
    
    # Add Candlestick Patterns
    if 'candlestick_patterns' in indicators_config:
        pattern_columns = ['doji', 'bullish_engulfing', 'bearish_engulfing', 'hammer', 'inverted_hammer', 'morning_star', 'evening_star']
        
        # Check if any of the patterns already exist
        if not any(col in existing_indicators for col in pattern_columns):
            print("Adding Candlestick Pattern indicators")
            result = add_candlestick_patterns(result)
    
    # List new indicators added
    new_indicators = [col for col in result.columns 
                    if col not in existing_indicators and 
                       col not in ['date', 'open', 'high', 'low', 'close', 'volume']]
    print(f"New indicators added: {new_indicators}")
    
    return result

def plot_price_with_indicators(data, plot_config=None):
    """
    Create a plot of price with selected indicators.
    
    Args:
        data (pandas.DataFrame): DataFrame containing price and indicator data.
        plot_config (dict): Configuration for what to plot.
            Example: {
                'main_indicators': ['sma_20', 'ema_20', 'bb_upper', 'bb_lower'],
                'subplot_indicators': ['rsi', 'macd', 'volume'],
                'title': 'Custom Chart Title',
                'start_date': '2020-01-01',
                'end_date': '2021-01-01'
            }
    
    Returns:
        str: Base64 encoded image.
    """
    try:
        if plot_config is None:
            plot_config = {
                'main_indicators': ['sma_50', 'ema_20'],
                'subplot_indicators': ['rsi', 'volume'],
                'title': 'Price Chart with Indicators'
            }
        
        # Filter data by date range if specified
        temp_data = data.copy()
        if 'start_date' in plot_config and plot_config['start_date']:
            start_date = pd.to_datetime(plot_config['start_date'])
            temp_data = temp_data[temp_data['date'] >= start_date]
            
        if 'end_date' in plot_config and plot_config['end_date']:
            end_date = pd.to_datetime(plot_config['end_date'])
            temp_data = temp_data[temp_data['date'] <= end_date]
        
        if len(temp_data) == 0:
            # Not enough data, create a simple message plot
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "No data available for the selected date range", 
                    horizontalalignment='center', verticalalignment='center', fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
            
            # Convert simple plot to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
            return image_base64
        
        # Check if we have any of the requested indicators
        main_indicators = [ind for ind in plot_config.get('main_indicators', []) if ind in temp_data.columns]
        subplot_indicators = [ind for ind in plot_config.get('subplot_indicators', []) if ind in temp_data.columns]
        
        # Determine how many subplots to create - group ADX indicators together
        adx_indicators = [ind for ind in subplot_indicators if ind in ['adx', 'plus_di', 'minus_di']]
        non_adx_indicators = [ind for ind in subplot_indicators if ind not in adx_indicators]
        
        # If any ADX indicator is selected, we'll plot all three (adx, plus_di, minus_di) in a single subplot
        n_adx_subplots = 1 if adx_indicators else 0
        n_subplots = 1 + len(non_adx_indicators) + n_adx_subplots
        
        # Create figure and gridspec
        fig = plt.figure(figsize=(12, 8))
        gs = fig.add_gridspec(n_subplots, 1, height_ratios=[3] + [1] * (n_subplots - 1))
        
        # Main price plot - Create twin axis for indicators
        ax_main = fig.add_subplot(gs[0])
        ax_main.plot(temp_data['date'], temp_data['close'], label='Close Price', color='blue', linewidth=2)
        ax_main.set_ylabel('Price', color='blue')
        ax_main.tick_params(axis='y', labelcolor='blue')
        
        # Separate price-scale indicators from other indicators
        overlay_indicators = []
        for ind in main_indicators:
            # Classify channel-type indicators that need special handling
            if any(ind.startswith(prefix) for prefix in ['bb_', 'dc_', 'kc_']):
                overlay_indicators.append(ind)
                
            # SuperTrend requires special coloring based on direction
            elif ind == 'supertrend':
                overlay_indicators.append(ind)
                
            # Candlestick pattern markers
            elif ind in ['doji', 'bullish_engulfing', 'bearish_engulfing', 'hammer', 'inverted_hammer', 'morning_star', 'evening_star']:
                # We'll handle these separately
                pass
            # Moving averages and other price-scale indicators
            elif any(ind.startswith(prefix) for prefix in ['sma_', 'ema_']):
                ax_main.plot(temp_data['date'], temp_data[ind], 
                             label=ind.replace('_', ' ').upper(), alpha=0.7,
                             linestyle='-', linewidth=1.5)
        
        # Bollinger Bands
        bb_upper = next((ind for ind in overlay_indicators if ind == 'bb_upper'), None)
        bb_lower = next((ind for ind in overlay_indicators if ind == 'bb_lower'), None)
        bb_middle = next((ind for ind in overlay_indicators if ind == 'bb_middle'), None)
        
        if bb_upper and bb_lower:
            ax_main.fill_between(temp_data['date'], temp_data[bb_upper], temp_data[bb_lower], 
                                 color='lightgrey', alpha=0.3, label='Bollinger Bands')
            if bb_middle:
                ax_main.plot(temp_data['date'], temp_data[bb_middle], color='grey', 
                             linestyle='--', alpha=0.7, label='BB Middle')
        
        # Donchian Channels
        donchian_high = next((ind for ind in overlay_indicators if ind == 'dc_upper'), None)
        donchian_low = next((ind for ind in overlay_indicators if ind == 'dc_lower'), None)
        donchian_mid = next((ind for ind in overlay_indicators if ind == 'dc_middle'), None)
        
        if donchian_high and donchian_low:
            ax_main.fill_between(temp_data['date'], temp_data[donchian_high], temp_data[donchian_low], 
                                 color='lightskyblue', alpha=0.2, label='Donchian Channels')
            if donchian_mid:
                ax_main.plot(temp_data['date'], temp_data[donchian_mid], color='blue', 
                             linestyle='--', alpha=0.5, label='Donchian Middle')
        
        # Keltner Channels
        keltner_high = next((ind for ind in overlay_indicators if ind == 'kc_upper'), None)
        keltner_low = next((ind for ind in overlay_indicators if ind == 'kc_lower'), None)
        keltner_mid = next((ind for ind in overlay_indicators if ind == 'kc_middle'), None)
        
        if keltner_high and keltner_low:
            ax_main.fill_between(temp_data['date'], temp_data[keltner_high], temp_data[keltner_low], 
                                 color='lightgreen', alpha=0.2, label='Keltner Channels')
            if keltner_mid:
                ax_main.plot(temp_data['date'], temp_data[keltner_mid], color='green', 
                             linestyle='--', alpha=0.5, label='Keltner Middle')
        
        # SuperTrend (colored by direction)
        if 'supertrend' in overlay_indicators and 'supertrend_direction' in temp_data.columns:
            # Create a mask for uptrend (1) and downtrend (-1)
            uptrend = temp_data['supertrend_direction'] == 1
            downtrend = temp_data['supertrend_direction'] == -1
            
            # Plot SuperTrend with color based on direction
            ax_main.plot(temp_data.loc[uptrend, 'date'], temp_data.loc[uptrend, 'supertrend'], 
                         color='green', label='SuperTrend (Up)', linewidth=1.5)
            ax_main.plot(temp_data.loc[downtrend, 'date'], temp_data.loc[downtrend, 'supertrend'], 
                         color='red', label='SuperTrend (Down)', linewidth=1.5)
        
        # Plot candlestick pattern markers
        pattern_markers = {
            'doji': ('o', 'purple', 'Doji'),
            'bullish_engulfing': ('^', 'green', 'Bullish Engulfing'),
            'bearish_engulfing': ('v', 'red', 'Bearish Engulfing'),
            'hammer': ('d', 'green', 'Hammer'),
            'inverted_hammer': ('d', 'red', 'Inverted Hammer'),
            'morning_star': ('*', 'green', 'Morning Star'),
            'evening_star': ('*', 'red', 'Evening Star')
        }
        
        for pattern in pattern_markers:
            if pattern in main_indicators and pattern in temp_data.columns:
                # Plot markers only where pattern is True
                pattern_dates = temp_data.loc[temp_data[pattern], 'date']
                pattern_prices = temp_data.loc[temp_data[pattern], 'close']
                
                if len(pattern_dates) > 0:
                    marker, color, label = pattern_markers[pattern]
                    ax_main.scatter(pattern_dates, pattern_prices, marker=marker, color=color, 
                                   s=80, label=label, alpha=0.8, zorder=5)
        
        # Get min/max y-values to adjust y-axis limits with some padding
        y_min = temp_data['low'].min()
        y_max = temp_data['high'].max()
        y_padding = (y_max - y_min) * 0.05
        ax_main.set_ylim(y_min - y_padding, y_max + y_padding)
        
        # Create subplots for additional indicators
        subplot_idx = 1
        
        # Handle ADX subplot if any ADX components are selected
        if adx_indicators:
            ax_adx = fig.add_subplot(gs[subplot_idx], sharex=ax_main)
            
            # Plot +DI, -DI, and ADX lines with appropriate colors
            if 'plus_di' in temp_data.columns:
                ax_adx.plot(temp_data['date'], temp_data['plus_di'], color='green', label='+DI')
            
            if 'minus_di' in temp_data.columns:
                ax_adx.plot(temp_data['date'], temp_data['minus_di'], color='red', label='-DI')
            
            if 'adx' in temp_data.columns:
                ax_adx.plot(temp_data['date'], temp_data['adx'], color='blue', label='ADX')
            
            ax_adx.set_ylabel('ADX')
            ax_adx.grid(True)
            ax_adx.legend(loc='upper left')
            
            # Draw threshold line at 25 (commonly used ADX threshold)
            ax_adx.axhline(y=25, color='grey', linestyle='--', alpha=0.5)
            
            subplot_idx += 1
        
        # Create subplots for remaining indicators
        for indicator in non_adx_indicators:
            ax_sub = fig.add_subplot(gs[subplot_idx], sharex=ax_main)
            
            color = 'blue'  # Default color
            
            # Special handling for certain indicators
            if indicator in ['macd', 'macd_signal', 'macd_histogram']:
                # MACD special handling
                if indicator == 'macd_histogram':
                    # For histogram, use bar chart with color based on value
                    for i in range(len(temp_data)):
                        color = 'green' if temp_data['macd_histogram'].iloc[i] >= 0 else 'red'
                        ax_sub.bar(temp_data['date'].iloc[i], temp_data['macd_histogram'].iloc[i], 
                                  color=color, alpha=0.6, width=2)
                    ax_sub.set_ylabel('MACD Histogram')
                else:
                    # For MACD and signal lines
                    color = 'blue' if indicator == 'macd' else 'red'
                    ax_sub.plot(temp_data['date'], temp_data[indicator], color=color, label=indicator)
                    ax_sub.set_ylabel('MACD')
            
            elif indicator == 'rsi':
                ax_sub.plot(temp_data['date'], temp_data[indicator], color='purple', label=indicator)
                # Add overbought/oversold lines
                ax_sub.axhline(y=70, color='red', linestyle='--', alpha=0.5)
                ax_sub.axhline(y=30, color='green', linestyle='--', alpha=0.5)
                ax_sub.set_ylabel('RSI')
                ax_sub.set_ylim(0, 100)
            
            elif indicator == 'williams_r':
                ax_sub.plot(temp_data['date'], temp_data[indicator], color='orange', label=indicator)
                # Add overbought/oversold lines (typical Williams %R thresholds)
                ax_sub.axhline(y=-20, color='red', linestyle='--', alpha=0.5)
                ax_sub.axhline(y=-80, color='green', linestyle='--', alpha=0.5)
                ax_sub.set_ylabel('Williams %R')
                ax_sub.set_ylim(-100, 0)
            
            elif indicator == 'cci':
                ax_sub.plot(temp_data['date'], temp_data[indicator], color='teal', label=indicator)
                # Add overbought/oversold lines
                ax_sub.axhline(y=100, color='red', linestyle='--', alpha=0.5)
                ax_sub.axhline(y=-100, color='green', linestyle='--', alpha=0.5)
                ax_sub.set_ylabel('CCI')
            
            elif indicator == 'cmf':
                # Color based on positive/negative values
                positive_cmf = temp_data['cmf'] >= 0
                negative_cmf = temp_data['cmf'] < 0
                
                ax_sub.plot(temp_data.loc[positive_cmf, 'date'], temp_data.loc[positive_cmf, 'cmf'], 
                           color='green', label='CMF +')
                ax_sub.plot(temp_data.loc[negative_cmf, 'date'], temp_data.loc[negative_cmf, 'cmf'], 
                           color='red', label='CMF -')
                
                # Add zero line
                ax_sub.axhline(y=0, color='grey', linestyle='-', alpha=0.5)
                ax_sub.set_ylabel('CMF')
            
            elif indicator == 'volume':
                # Plot volume as bars
                ax_sub.bar(temp_data['date'], temp_data[indicator], color='lightblue', alpha=0.7)
                ax_sub.set_ylabel('Volume')
            
            else:
                # Generic handling for other indicators
                ax_sub.plot(temp_data['date'], temp_data[indicator], color=color, label=indicator)
                ax_sub.set_ylabel(indicator)
            
            ax_sub.grid(True)
            ax_sub.legend(loc='upper left')
            
            subplot_idx += 1
        
        # Format x-axis date
        date_format = DateFormatter('%Y-%m-%d')
        ax_main.xaxis.set_major_formatter(date_format)
        
        # Remove main x-axis labels to avoid overlap
        if n_subplots > 1:
            plt.setp(ax_main.get_xticklabels(), visible=False)
        
        # Add title and legend
        ax_main.set_title(plot_config.get('title', 'Price Chart with Indicators'))
        ax_main.legend(loc='upper left')
        ax_main.grid(True)
        
        plt.tight_layout()
        
        # Convert plot to base64 encoded string
        buffer = io.BytesIO()
        plt.savefig(r'C:\\Users\\ricar\\Desktop\\Python Works\\Analise_Grafica\\test_chart.png', format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        logger.info("Saved test_chart.png to project root.")
        
        return image_base64
        
    except Exception as e:
        print(f"Error plotting indicators: {e}")
        # Create a simple error plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f"Error plotting indicators: {str(e)}", 
                horizontalalignment='center', verticalalignment='center', fontsize=12, color='red')
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Convert error plot to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return image_base64

def create_indicator_summary(data, last_n_periods=1):
    """
    Create a summary of technical indicators and their signals.
    
    Args:
        data (pandas.DataFrame): DataFrame containing price and indicator data.
        last_n_periods (int): Number of periods to consider for the summary. Default is 1.
    
    Returns:
        dict: Summary of technical indicators and their signals.
    """
    if len(data) < last_n_periods:
        raise ValueError("Not enough data for requested periods")
    
    # Get the last N periods of data
    recent_data = data.iloc[-last_n_periods:].copy()
    
    summary = {
        'date_range': f"{recent_data['date'].min().strftime('%Y-%m-%d')} to {recent_data['date'].max().strftime('%Y-%m-%d')}",
        'price_info': {
            'last_close': recent_data['close'].iloc[-1],
            'change': recent_data['close'].iloc[-1] - recent_data['close'].iloc[0],
            'change_pct': ((recent_data['close'].iloc[-1] / recent_data['close'].iloc[0]) - 1) * 100
        },
        'trend_indicators': {},
        'momentum_indicators': {},
        'volatility_indicators': {},
        'volume_indicators': {},
        'signals': {
            'bullish': [],
            'bearish': [],
            'neutral': []
        }
    }
    
    # Process trend indicators (Moving Averages)
    trend_cols = [col for col in recent_data.columns if col.startswith(('sma_', 'ema_'))]
    for col in trend_cols:
        if col in recent_data.columns:
            summary['trend_indicators'][col] = recent_data[col].iloc[-1]
            
            # Trend signals
            if recent_data['close'].iloc[-1] > recent_data[col].iloc[-1]:
                summary['signals']['bullish'].append(f"Price above {col}")
            else:
                summary['signals']['bearish'].append(f"Price below {col}")
    
    # Process momentum indicators
    momentum_map = {
        'rsi': 'RSI',
        'macd': 'MACD',
        'macd_signal': 'MACD Signal',
        'macd_histogram': 'MACD Histogram',
        'stoch_k': 'Stochastic %K',
        'stoch_d': 'Stochastic %D'
    }
    
    for col, name in momentum_map.items():
        if col in recent_data.columns:
            summary['momentum_indicators'][name] = recent_data[col].iloc[-1]
            
            # RSI signals
            if col == 'rsi':
                rsi_value = recent_data[col].iloc[-1]
                if rsi_value > 70:
                    summary['signals']['bearish'].append(f"RSI overbought ({rsi_value:.2f})")
                elif rsi_value < 30:
                    summary['signals']['bullish'].append(f"RSI oversold ({rsi_value:.2f})")
                else:
                    summary['signals']['neutral'].append(f"RSI neutral ({rsi_value:.2f})")
            
            # MACD signals
            if col == 'macd_histogram':
                hist_value = recent_data[col].iloc[-1]
                hist_prev = recent_data[col].iloc[-2] if len(recent_data) > 1 else 0
                
                if hist_value > 0 and hist_value > hist_prev:
                    summary['signals']['bullish'].append("MACD histogram increasing & positive")
                elif hist_value < 0 and hist_value < hist_prev:
                    summary['signals']['bearish'].append("MACD histogram decreasing & negative")
    
    # Process volatility indicators
    volatility_map = {
        'atr': 'ATR',
        'atr_pct': 'ATR %',
        'bb_upper': 'Bollinger Upper',
        'bb_middle': 'Bollinger Middle',
        'bb_lower': 'Bollinger Lower',
        'bb_bandwidth': 'Bollinger Bandwidth',
        'bb_percent_b': 'Bollinger %B'
    }
    
    for col, name in volatility_map.items():
        if col in recent_data.columns:
            summary['volatility_indicators'][name] = recent_data[col].iloc[-1]
            
            # Bollinger Band signals
            if col == 'bb_percent_b':
                bb_value = recent_data[col].iloc[-1]
                if bb_value > 1:
                    summary['signals']['bearish'].append(f"Price above upper Bollinger Band")
                elif bb_value < 0:
                    summary['signals']['bullish'].append(f"Price below lower Bollinger Band")
    
    # Process volume indicators
    volume_map = {
        'volume': 'Volume',
        'obv': 'OBV',
        'vpt': 'VPT',
        'volume_sma_20': 'Volume SMA(20)',
        'volume_ratio_20': 'Volume Ratio'
    }
    
    for col, name in volume_map.items():
        if col in recent_data.columns:
            summary['volume_indicators'][name] = recent_data[col].iloc[-1]
            
            # Volume signals
            if col == 'volume_ratio_20' and recent_data[col].iloc[-1] > 1.5:
                summary['signals']['neutral'].append(f"Above average volume ({recent_data[col].iloc[-1]:.2f}x)")
    
    # Crossover signals
    if 'golden_cross' in recent_data.columns and recent_data['golden_cross'].iloc[-1] == 1:
        summary['signals']['bullish'].append("Golden Cross detected")
        
    if 'death_cross' in recent_data.columns and recent_data['death_cross'].iloc[-1] == 1:
        summary['signals']['bearish'].append("Death Cross detected")
    
    # Overall signal summary
    bullish_count = len(summary['signals']['bullish'])
    bearish_count = len(summary['signals']['bearish'])
    
    if bullish_count > bearish_count + 2:
        summary['overall_signal'] = "Strong Bullish"
    elif bullish_count > bearish_count:
        summary['overall_signal'] = "Bullish"
    elif bearish_count > bullish_count + 2:
        summary['overall_signal'] = "Strong Bearish"
    elif bearish_count > bullish_count:
        summary['overall_signal'] = "Bearish"
    else:
        summary['overall_signal'] = "Neutral"
    
    return summary 

# Utility for strategies: Ensures the 'signal' column contains only 'buy', 'sell', or 'hold' as strings.
def normalize_signals_column(df):
    """
    Utility for strategies: Ensures the 'signal' column contains only 'buy', 'sell', or 'hold' as strings.
    If the column is numeric, converts to text. If missing, creates as 'hold'.
    Any unexpected value is coerced to 'hold'.
    """
    import numpy as np
    import pandas as pd
    df = df.copy()
    if 'signal' not in df.columns:
        df['signal'] = 'hold'
    if df['signal'].dtype in [np.int64, np.float64, 'int64', 'float64']:
        map_dict = {1: 'buy', -1: 'sell', 0: 'hold'}
        df['signal'] = df['signal'].map(map_dict).fillna('hold')
    valid_signals = {'buy', 'sell', 'hold'}
    df['signal'] = df['signal'].astype(str).str.lower()
    df.loc[~df['signal'].isin(valid_signals), 'signal'] = 'hold'
    df['signal'] = df['signal'].astype(object)
    return df 