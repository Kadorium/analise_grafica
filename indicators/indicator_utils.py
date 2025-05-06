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
    
    # Add Moving Averages
    if 'moving_averages' in indicators_config:
        config = indicators_config['moving_averages']
        result = add_moving_averages(result, 
                                   sma_periods=config.get('sma_periods', [20, 50, 200]),
                                   ema_periods=config.get('ema_periods', [12, 26, 50]))
    
    # Add Momentum Indicators
    if any(k in indicators_config for k in ['rsi', 'macd', 'stochastic']):
        momentum_params = {}
        
        if 'rsi' in indicators_config:
            momentum_params['rsi_period'] = indicators_config['rsi'].get('period', 14)
            
        if 'macd' in indicators_config:
            macd_config = indicators_config['macd']
            momentum_params['macd_fast'] = macd_config.get('fast_period', 12)
            momentum_params['macd_slow'] = macd_config.get('slow_period', 26)
            momentum_params['macd_signal'] = macd_config.get('signal_period', 9)
            
        if 'stochastic' in indicators_config:
            stoch_config = indicators_config['stochastic']
            momentum_params['stoch_k'] = stoch_config.get('k_period', 14)
            momentum_params['stoch_d'] = stoch_config.get('d_period', 3)
            momentum_params['stoch_slowing'] = stoch_config.get('slowing', 3)
            
        result = add_momentum_indicators(result, **momentum_params)
    
    # Add Volume Indicators
    if 'volume' in indicators_config:
        result = add_volume_indicators(result)
    
    # Add Volatility Indicators
    if any(k in indicators_config for k in ['atr', 'bollinger_bands']):
        volatility_params = {}
        
        if 'atr' in indicators_config:
            volatility_params['atr_period'] = indicators_config['atr'].get('period', 14)
            
        if 'bollinger_bands' in indicators_config:
            bb_config = indicators_config['bollinger_bands']
            volatility_params['bollinger_window'] = bb_config.get('window', 20)
            volatility_params['bollinger_std'] = bb_config.get('num_std', 2)
            
        result = add_volatility_indicators(result, **volatility_params)
    
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
        
        # Main price plot
        ax_main = fig.add_subplot(gs[0])
        ax_main.plot(temp_data['date'], temp_data['close'], label='Close Price')
        
        # Plot main indicators
        for indicator in main_indicators:
            ax_main.plot(temp_data['date'], temp_data[indicator], label=indicator)
        
        ax_main.set_title(plot_config.get('title', 'Price Chart with Indicators'))
        ax_main.set_ylabel('Price')
        ax_main.grid(True)
        ax_main.legend(loc='upper left')
        
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