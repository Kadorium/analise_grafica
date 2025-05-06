import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import io
import base64

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
        
        # Determine how many subplots to create
        n_subplots = 1 + len(subplot_indicators)
        
        # Create figure and gridspec
        fig = plt.figure(figsize=(12, 8))
        gs = fig.add_gridspec(n_subplots, 1, height_ratios=[3] + [1] * (n_subplots - 1))
        
        # Main price plot - Create twin axis for indicators
        ax_main = fig.add_subplot(gs[0])
        ax_main.plot(temp_data['date'], temp_data['close'], label='Close Price', color='blue', linewidth=2)
        ax_main.set_ylabel('Price', color='blue')
        ax_main.tick_params(axis='y', labelcolor='blue')
        
        # Separate price-scale indicators from other indicators
        price_scale_indicators = [ind for ind in main_indicators if any(ind.startswith(prefix) for prefix in ['bb_', 'sma_', 'ema_'])]
        other_indicators = [ind for ind in main_indicators if ind not in price_scale_indicators]
        
        # For debugging
        print(f"Main indicators: {main_indicators}")
        print(f"Price scale indicators: {price_scale_indicators}")
        print(f"Other indicators: {other_indicators}")
        
        # Plot price-scale indicators on the same axis as price
        bb_colors = {'bb_upper': 'red', 'bb_lower': 'green', 'bb_middle': 'purple'}
        ma_colors = {'sma': 'orange', 'ema': 'magenta'}
        
        for indicator in price_scale_indicators:
            if indicator in temp_data.columns:  # Make sure the indicator exists in the data
                # Special colors for Bollinger Bands
                if indicator in bb_colors:
                    ax_main.plot(temp_data['date'], temp_data[indicator], 
                                 label=indicator, color=bb_colors[indicator], alpha=0.7, linestyle='--')
                # Colors for Moving Averages
                elif indicator.startswith('sma_'):
                    ax_main.plot(temp_data['date'], temp_data[indicator], 
                                 label=indicator, color='orange', alpha=0.7)
                elif indicator.startswith('ema_'):
                    ax_main.plot(temp_data['date'], temp_data[indicator], 
                                 label=indicator, color='magenta', alpha=0.7)
                else:
                    ax_main.plot(temp_data['date'], temp_data[indicator], 
                                 label=indicator, alpha=0.7)
        
        # Create a twin axis for non-price-scale indicators if there are any
        if other_indicators:
            ax_indicators = ax_main.twinx()
            
            # Determine a good color map for the indicators
            colors = plt.cm.tab10(np.linspace(0, 1, max(1, len(other_indicators))))
            
            # Plot other indicators on the twin axis
            for i, indicator in enumerate(other_indicators):
                if indicator in temp_data.columns:  # Make sure the indicator exists in the data
                    ax_indicators.plot(temp_data['date'], temp_data[indicator], 
                                     label=indicator, color=colors[i % len(colors)], alpha=0.7)
            
            ax_indicators.set_ylabel('Indicator Values', color='gray')
            ax_indicators.tick_params(axis='y', labelcolor='gray')
            
            # Create a combined legend for both axes
            lines1, labels1 = ax_main.get_legend_handles_labels()
            lines2, labels2 = ax_indicators.get_legend_handles_labels()
            
            # Only add legend if we have indicators
            if lines1 or lines2:
                ax_main.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        else:
            # Only add legend if we have something to show
            if ax_main.get_legend_handles_labels()[0]:
                ax_main.legend(loc='upper left')
        
        ax_main.set_title(plot_config.get('title', 'Price Chart with Indicators'))
        ax_main.grid(True)
        
        # Create subplots for additional indicators
        for i, indicator in enumerate(subplot_indicators, 1):
            ax_sub = fig.add_subplot(gs[i], sharex=ax_main)
            ax_sub.plot(temp_data['date'], temp_data[indicator], label=indicator)
            ax_sub.set_ylabel(indicator)
            ax_sub.grid(True)
            ax_sub.legend(loc='upper left')
        
        # Format x-axis date
        date_format = DateFormatter('%Y-%m-%d')
        ax_main.xaxis.set_major_formatter(date_format)
        
        # Remove main x-axis labels to avoid overlap
        if n_subplots > 1:
            plt.setp(ax_main.get_xticklabels(), visible=False)
        
        plt.tight_layout()
        
        # Convert plot to base64 encoded string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return image_base64
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in plot_price_with_indicators: {str(e)}\n{error_trace}")
        
        # Create an error message plot
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f"Error creating chart: {str(e)}", 
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
        except:
            # If even error plot fails, return a minimal encoded empty image
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="

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