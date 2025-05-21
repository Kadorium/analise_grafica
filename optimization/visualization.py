import os
import json
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64
import time
import traceback

logger = logging.getLogger(__name__)

def plot_optimization_comparison(default_signals, optimized_signals, strategy_type, initial_capital=100.0):
    """
    Generate a comparison chart of default vs optimized strategy performance.
    
    Args:
        default_signals (pd.DataFrame): DataFrame with default strategy signals
        optimized_signals (pd.DataFrame): DataFrame with optimized strategy signals
        strategy_type (str): The type of strategy being compared
        initial_capital (float): Initial capital for Buy & Hold calculation.
        
    Returns:
        tuple: (chart_html, chart_path)
            chart_html (str): HTML for the interactive Chart.js chart
            chart_path (str): Path to the backup PNG chart
    """
    try:
        logger.info(f"[PLOT] Entered plot_optimization_comparison for {strategy_type}.")
        logger.info(f"[PLOT] Initial capital: {initial_capital}")
        logger.info(f"[PLOT] Default signals DF shape: {default_signals.shape}, Columns: {default_signals.columns.tolist()}")
        if not default_signals.empty and 'date' in default_signals.columns:
            logger.info(f"[PLOT] Default signals date range: {default_signals['date'].min()} to {default_signals['date'].max()}")
        logger.info(f"[PLOT] Optimized signals DF shape: {optimized_signals.shape}, Columns: {optimized_signals.columns.tolist()}")
        if not optimized_signals.empty and 'date' in optimized_signals.columns:
            logger.info(f"[PLOT] Optimized signals date range: {optimized_signals['date'].min()} to {optimized_signals['date'].max()}")
        logger.info(f"[PLOT] 'cumulative_market_return' in default_signals: {'cumulative_market_return' in default_signals.columns}")

        timestamp = int(time.time())
        # Use underscores for JS compatibility in variable names
        equity_chart_id = f"equity_comparison_chart_{timestamp}" # Renamed for clarity
        signals_chart_id = f"signals_chart_{timestamp}" # ID for the new chart
        results_dir = os.path.join("results", "optimization")
        
        # Create directory if it doesn't exist
        os.makedirs(results_dir, exist_ok=True)
        
        # Convert dates to string format for JSON
        default_signals_dates = default_signals['date'].dt.strftime('%Y-%m-%d').tolist()
        # Ensure 'equity' is float and handle NaNs for default signals
        default_equity_series = pd.to_numeric(default_signals['equity'], errors='coerce')
        default_equity_series = default_equity_series.ffill().fillna(initial_capital)
        default_equity = default_equity_series.tolist()

        optimized_signals_dates = optimized_signals['date'].dt.strftime('%Y-%m-%d').tolist()
        # Ensure 'equity' is float and handle NaNs for optimized signals
        optimized_equity_series = pd.to_numeric(optimized_signals['equity'], errors='coerce')
        optimized_equity_series = optimized_equity_series.ffill().fillna(initial_capital)
        optimized_equity = optimized_equity_series.tolist()
        
        buy_and_hold_equity = []
        if 'cumulative_market_return' in default_signals.columns:
            # Calculate Buy & Hold equity
            bnh_series = default_signals['cumulative_market_return'] * initial_capital
            # Handle potential NaNs in Buy & Hold equity, e.g., fill with initial capital or ffill
            bnh_series = pd.to_numeric(bnh_series, errors='coerce').ffill().fillna(initial_capital)
            buy_and_hold_equity = bnh_series.tolist()
            logger.info(f"[PLOT] Buy & Hold equity calculated. Length: {len(buy_and_hold_equity)}. Sample (first 5): {buy_and_hold_equity[:5]}, Sample (last 5): {buy_and_hold_equity[-5:]}")
        else:
            logger.warning("[PLOT] 'cumulative_market_return' column not found in default_signals. Buy & Hold curve will be omitted.")
            
        # Log sample of the data for debugging
        logger.info(f"Chart data prepared - dates: {len(default_signals_dates)} points, equity: {len(default_equity)} points")
        logger.info(f"Sample date: {default_signals_dates[0]} to {default_signals_dates[-1]}")
        logger.info(f"Sample equity range: {min(default_equity)} to {max(default_equity)}")
        
        # Create a backup matplotlib chart
        fig, axs = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [2, 1]}) # 2 rows for two charts

        # Equity curve plot (top subplot)
        axs[0].plot(default_signals['date'], default_signals['equity'], label='Default', color='red')
        axs[0].plot(optimized_signals['date'], optimized_signals['equity'], label='Optimized', color='green')
        if buy_and_hold_equity:
            axs[0].plot(default_signals['date'], buy_and_hold_equity, label='Buy & Hold', color='blue', linestyle='--')
        axs[0].set_xlabel('Date')
        axs[0].set_ylabel('Equity')
        axs[0].set_title('Equity Curve Comparison')
        axs[0].legend()
        axs[0].grid(True)

        # Prepare data for signals chart (using default_signals for price and signals)
        # Ensure required columns are present
        required_cols = ['date', 'close', 'signal', 'position']
        missing_cols = [col for col in required_cols if col not in default_signals.columns]
        if missing_cols:
            logger.warning(f"[PLOT] Missing required columns for signals chart in default_signals: {missing_cols}. Signals chart will be omitted.")
            signals_chart_html_part = "<!-- Signals chart omitted due to missing data -->"
        else:
            price_data_dates = default_signals['date'].dt.strftime('%Y-%m-%d').tolist()
            price_data_close = pd.to_numeric(default_signals['close'], errors='coerce').fillna(method='ffill').fillna(0).tolist()

            buy_entry_points = []
            short_entry_points = []
            exit_points = []
            
            # Ensure 'position' is numeric and handle NaNs; shift requires a default for the first element
            positions = pd.to_numeric(default_signals['position'], errors='coerce').fillna(0)
            prev_positions = positions.shift(1).fillna(0) # fillna(0) for the first row's prev_position

            for i in range(len(default_signals)):
                row_date_str = default_signals['date'].iloc[i].strftime('%Y-%m-%d')
                row_close = default_signals['close'].iloc[i]
                row_signal = default_signals['signal'].iloc[i]
                current_pos = positions.iloc[i]
                prev_pos = prev_positions.iloc[i]

                if pd.notna(row_close): # Only add points if price is valid
                    if row_signal == 1 and prev_pos != 1: # Buy to open long or buy to close short
                        if current_pos == 1 : # Specifically buy to open long
                             buy_entry_points.append({'x': row_date_str, 'y': row_close})
                        elif current_pos == 0 and prev_pos == -1: # Buy to close short (exit)
                             exit_points.append({'x': row_date_str, 'y': row_close})
                    elif row_signal == -1 and prev_pos != -1: # Sell to open short or sell to close long
                        if current_pos == -1: # Specifically sell to open short
                            short_entry_points.append({'x': row_date_str, 'y': row_close})
                        elif current_pos == 0 and prev_pos == 1: # Sell to close long (exit)
                            exit_points.append({'x': row_date_str, 'y': row_close})
            
            logger.info(f"[PLOT] Buy entry points: {len(buy_entry_points)}, Short entry points: {len(short_entry_points)}, Exit points: {len(exit_points)}")

            # Signals plot (bottom subplot) for backup image
            axs[1].plot(default_signals['date'], default_signals['close'], label='Close Price', color='black', alpha=0.7)
            # For matplotlib scatter, we need to extract x and y from the dicts
            if buy_entry_points:
                buy_dates_mpl = [pd.to_datetime(p['x']) for p in buy_entry_points]
                buy_prices_mpl = [p['y'] for p in buy_entry_points]
                axs[1].scatter(buy_dates_mpl, buy_prices_mpl, label='Buy Entry', marker='^', color='green', s=100, zorder=5)
            if short_entry_points:
                short_dates_mpl = [pd.to_datetime(p['x']) for p in short_entry_points]
                short_prices_mpl = [p['y'] for p in short_entry_points]
                axs[1].scatter(short_dates_mpl, short_prices_mpl, label='Short Entry', marker='v', color='red', s=100, zorder=5)
            if exit_points:
                exit_dates_mpl = [pd.to_datetime(p['x']) for p in exit_points]
                exit_prices_mpl = [p['y'] for p in exit_points]
                axs[1].scatter(exit_dates_mpl, exit_prices_mpl, label='Exit', marker='o', color='blue', s=100, zorder=5)
            
            axs[1].set_xlabel('Date')
            axs[1].set_ylabel('Price')
            axs[1].set_title('Price and Trade Signals')
            axs[1].legend()
            axs[1].grid(True)
        
        # Save to optimization folder
        backup_chart_path = os.path.join(results_dir, f"chart_backup_{strategy_type}_{timestamp}.png")
        plt.tight_layout()
        plt.savefig(backup_chart_path)
        plt.close()
        
        logger.info(f"Saved backup chart image to {backup_chart_path}")
        
        # Also save a text file with the chart data for debugging
        debug_data_path = os.path.join(results_dir, f"chart_data_{strategy_type}_{timestamp}.json")
        with open(debug_data_path, 'w') as f:
            json.dump({
                "chart_id": equity_chart_id,
                "dates": default_signals_dates[:10] + ["..."] + default_signals_dates[-10:],
                "default_equity_sample": default_equity[:10] + ["..."] + default_equity[-10:],
                "optimized_equity_sample": optimized_equity[:10] + ["..."] + optimized_equity[-10:],
                "buy_and_hold_equity_sample": buy_and_hold_equity[:10] + ["..."] + buy_and_hold_equity[-10:],
                "date_count": len(default_signals_dates),
                "equity_count": len(default_equity)
            }, f, indent=2)
        
        logger.info(f"Saved chart debug data to {debug_data_path}")
        
        # Generate the Chart.js HTML with more robust initialization
        chart_html = f"""
        <div class="chart-container" style="position: relative; height:400px; width:100%; margin-bottom: 20px;">
            <canvas id="{equity_chart_id}" width="800" height="400"></canvas>
        </div>
        <script>
        console.log("Chart script for {equity_chart_id} loaded and executing");
        
        // Properly construct JavaScript string
        console.log("[PLOT SCRIPT] Equity Chart - Checking to add Buy & Hold. buy_and_hold_equity is not empty: " + String({json.dumps(bool(buy_and_hold_equity))}).toLowerCase());
        
        (function() {{
            // Store chart config for later use if needed
            var equityChartId = "{equity_chart_id}";
            window["chartConfig_" + equityChartId] = {{
                type: 'line',
                data: {{
                    labels: {json.dumps(default_signals_dates)},
                    datasets: [
                        {{
                            label: 'Default Strategy',
                            data: {json.dumps(default_equity)},
                            borderColor: 'rgb(255, 99, 132)',
                            backgroundColor: 'rgba(255, 99, 132, 0.1)',
                            tension: 0.1,
                            fill: false
                        }},
                        {{
                            label: 'Optimized Strategy',
                            data: {json.dumps(optimized_equity)},
                            borderColor: 'rgb(54, 162, 235)',
                            backgroundColor: 'rgba(54, 162, 235, 0.1)',
                            tension: 0.1,
                            fill: false
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        intersect: false,
                        mode: 'index'
                    }},
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Strategy Performance Comparison'
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    let label = context.dataset.label || '';
                                    if (label) {{
                                        label += ': ';
                                    }}
                                    if (context.parsed.y !== null) {{
                                        label += new Intl.NumberFormat('en-US', {{ 
                                            style: 'currency', 
                                            currency: 'USD',
                                            minimumFractionDigits: 2
                                        }}).format(context.parsed.y);
                                    }}
                                    return label;
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            display: true,
                            title: {{
                                display: true,
                                text: 'Date'
                            }}
                        }},
                        y: {{
                            display: true,
                            title: {{
                                display: true,
                                text: 'Equity ($)'
                            }}
                        }}
                    }}
                }}
            }};
            
            // Properly access the config object using bracket notation
            console.log("[PLOT SCRIPT] Equity Chart - Adding Buy & Hold dataset. Condition: window['chartConfig_' + equityChartId].data.datasets.length < 3 && " + String({json.dumps(bool(buy_and_hold_equity))}).toLowerCase());
            if (window["chartConfig_" + equityChartId].data.datasets.length < 3 && {json.dumps(bool(buy_and_hold_equity))}) {{
                console.log("[PLOT SCRIPT] Equity Chart - Actually pushing Buy & Hold dataset to chart " + equityChartId); 
                window["chartConfig_" + equityChartId].data.datasets.push({{
                    label: 'Buy & Hold',
                    data: {json.dumps(buy_and_hold_equity)},
                    borderColor: 'rgb(75, 192, 192)', // Teal color for Buy & Hold
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    borderDash: [5, 5], // Dashed line
                    tension: 0.1,
                    fill: false
                }});
            }}
            
            // Function to render chart
            function renderEquityChart() {{
                var ctx = document.getElementById(equityChartId);
                if (ctx) {{
                    new Chart(ctx, window["chartConfig_" + equityChartId]);
                    console.log("Chart " + equityChartId + " rendered successfully");
                }} else {{
                    console.error("Could not find canvas element " + equityChartId);
                }}
            }}
            
            // Check if Chart.js is loaded
            if (typeof Chart !== 'undefined') {{
                // If Chart.js is already loaded, render immediately
                renderEquityChart();
            }} else {{
                // If Chart.js isn't loaded yet, listen for window load
                window.addEventListener('load', function() {{
                    // Small delay to ensure Chart.js is loaded
                    setTimeout(renderEquityChart, 100);
                }});
            }}
        }})();
        </script>
        """

        # Generate HTML for the signals chart if data is available
        if not missing_cols:
            signals_chart_html_part = f"""
        <div class="chart-container" style="position: relative; height:300px; width:100%; margin-top: 30px; margin-bottom: 20px;">
            <canvas id="{signals_chart_id}" width="800" height="300"></canvas>
        </div>
        <script>
        console.log("Chart script for {signals_chart_id} loaded and executing");
        (function() {{
            var signalsChartId = "{signals_chart_id}";
            window["chartConfig_" + signalsChartId] = {{
                type: 'line', // Base type is line for price
                data: {{
                    labels: {json.dumps(price_data_dates)},
                    datasets: [
                        {{
                            label: 'Close Price',
                            data: {json.dumps(price_data_close)},
                            borderColor: 'rgb(0, 0, 0)', // Black for price
                            backgroundColor: 'rgba(0, 0, 0, 0.05)',
                            tension: 0.1,
                            fill: false,
                            pointRadius: 0, // No points on the price line itself
                            yAxisID: 'yPrice'
                        }},
                        {{
                            label: 'Buy Entry',
                            data: {json.dumps(buy_entry_points)},
                            type: 'scatter',
                            pointStyle: 'triangle',
                            radius: 8,
                            rotation: 0, // Pointing up
                            backgroundColor: 'rgba(0, 255, 0, 0.7)', // Green
                            borderColor: 'rgb(0, 128, 0)',
                            showLine: false,
                            yAxisID: 'yPrice'
                        }},
                        {{
                            label: 'Short Entry',
                            data: {json.dumps(short_entry_points)},
                            type: 'scatter',
                            pointStyle: 'triangle',
                            radius: 8,
                            rotation: 180, // Pointing down
                            backgroundColor: 'rgba(255, 0, 0, 0.7)', // Red
                            borderColor: 'rgb(128, 0, 0)',
                            showLine: false,
                            yAxisID: 'yPrice'
                        }},
                        {{
                            label: 'Exit Signal',
                            data: {json.dumps(exit_points)},
                            type: 'scatter',
                            pointStyle: 'circle',
                            radius: 7,
                            backgroundColor: 'rgba(0, 0, 255, 0.7)', // Blue
                            borderColor: 'rgb(0, 0, 128)',
                            showLine: false,
                            yAxisID: 'yPrice'
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        intersect: false,
                        mode: 'index'
                    }},
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Asset Price and Trade Signals'
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    let label = context.dataset.label || '';
                                    if (label === 'Close Price') {{
                                        if (context.parsed.y !== null) {{
                                            label += ': ' + new Intl.NumberFormat('en-US', {{ style: 'currency', currency: 'USD', minimumFractionDigits: 2 }}).format(context.parsed.y);
                                        }}
                                    }} else if (context.dataset.type === 'scatter') {{
                                        // For scatter points, just show the type and price
                                        label += ' at ' + new Intl.NumberFormat('en-US', {{ style: 'currency', currency: 'USD', minimumFractionDigits: 2 }}).format(context.parsed.y);
                                    }}
                                    return label;
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            display: true,
                            title: {{
                                display: true,
                                text: 'Date'
                            }}
                        }},
                        yPrice: {{ // Define y-axis for price
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {{
                                display: true,
                                text: 'Price ($)'
                            }}
                        }}
                    }}
                }}
            }};

            function renderSignalsChart() {{
                var ctxSignals = document.getElementById(signalsChartId);
                if (ctxSignals) {{
                    new Chart(ctxSignals, window["chartConfig_" + signalsChartId]);
                    console.log("Chart " + signalsChartId + " rendered successfully");
                }} else {{
                    console.error("Could not find canvas element " + signalsChartId);
                }}
            }}

            if (typeof Chart !== 'undefined') {{
                renderSignalsChart();
            }} else {{
                window.addEventListener('load', function() {{ setTimeout(renderSignalsChart, 100); }});
            }}
        }})();
        </script>
            """
            chart_html += signals_chart_html_part
        else: # If missing_cols is true, append the comment placeholder
            chart_html += "<!-- Signals chart omitted due to missing data in default_signals -->"
        
        return chart_html, backup_chart_path
        
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error creating optimization comparison chart: {str(e)}\nTraceback:\n{error_details}")
        return None, None

def plot_indicators_comparison(default_signals, optimized_signals, strategy_type, default_params, optimized_params):
    """
    Generate a comparison chart of default vs optimized strategy indicators.
    
    Args:
        default_signals (pd.DataFrame): DataFrame with default strategy signals
        optimized_signals (pd.DataFrame): DataFrame with optimized strategy signals
        strategy_type (str): The type of strategy being compared
        default_params (dict): Parameters used for the default strategy
        optimized_params (dict): Parameters used for the optimized strategy
        
    Returns:
        str: HTML representation of the chart
    """
    try:
        if default_signals is None or optimized_signals is None:
            logger.error("Missing signals data for indicator comparison")
            return ""
            
        if len(default_signals) == 0 or len(optimized_signals) == 0:
            logger.error("Empty signals data for indicator comparison")
            return ""
        
        # Ensure we have the close price for plotting
        if 'close' not in default_signals.columns or 'close' not in optimized_signals.columns:
            logger.error("Missing 'close' column in signals data")
            return ""
            
        # Create figure for the chart
        plt.figure(figsize=(12, 8))
        
        # Plot price data as the baseline
        plt.subplot(2, 1, 1)
        plt.plot(default_signals.index, default_signals['close'], color='black', linewidth=1.5, label='Price')
        
        # Plot indicators based on strategy type
        has_indicators = False
        
        if strategy_type == 'trend_following' or strategy_type == 'sma_crossover':
            # Get parameters
            fast_period_default = default_params.get('fast_period', 20)
            slow_period_default = default_params.get('slow_period', 50)
            fast_period_opt = optimized_params.get('fast_period', 20)
            slow_period_opt = optimized_params.get('slow_period', 50)
            
            # Plot default SMAs
            fast_col = f'sma{fast_period_default}'
            slow_col = f'sma{slow_period_default}'
            if fast_col in default_signals.columns:
                plt.plot(default_signals.index, default_signals[fast_col], 
                        label=f'Default SMA({fast_period_default})', color='blue', linewidth=1.5)
                has_indicators = True
            if slow_col in default_signals.columns:
                plt.plot(default_signals.index, default_signals[slow_col], 
                        label=f'Default SMA({slow_period_default})', color='darkblue', linewidth=1.5)
                has_indicators = True
            
            # Plot optimized SMAs
            fast_col_opt = f'sma{fast_period_opt}'
            slow_col_opt = f'sma{slow_period_opt}'
            if fast_col_opt in optimized_signals.columns:
                plt.plot(optimized_signals.index, optimized_signals[fast_col_opt], 
                        label=f'Optimized SMA({fast_period_opt})', color='red', linestyle='--', linewidth=1.5)
                has_indicators = True
            if slow_col_opt in optimized_signals.columns:
                plt.plot(optimized_signals.index, optimized_signals[slow_col_opt], 
                        label=f'Optimized SMA({slow_period_opt})', color='darkred', linestyle='--', linewidth=1.5)
                has_indicators = True
        
        elif strategy_type == 'mean_reversion' or strategy_type == 'rsi':
            # For RSI strategy
            if 'rsi' in default_signals.columns and 'rsi' in optimized_signals.columns:
                rsi_period_default = default_params.get('rsi_period', 14)
                rsi_period_opt = optimized_params.get('rsi_period', 14)
                
                # Plot RSI lines
                plt.plot(default_signals.index, default_signals['rsi'], 
                        label=f'Default RSI({rsi_period_default})', color='blue', linewidth=1.5)
                plt.plot(optimized_signals.index, optimized_signals['rsi'], 
                        label=f'Optimized RSI({rsi_period_opt})', color='red', linestyle='--', linewidth=1.5)
                has_indicators = True
                
                # Plot threshold lines
                oversold_default = default_params.get('oversold', 30)
                overbought_default = default_params.get('overbought', 70)
                oversold_opt = optimized_params.get('oversold', 30)
                overbought_opt = optimized_params.get('overbought', 70)
                
                plt.axhline(y=oversold_default, color='blue', linestyle=':', label=f'Default Oversold ({oversold_default})')
                plt.axhline(y=overbought_default, color='blue', linestyle=':', label=f'Default Overbought ({overbought_default})')
                plt.axhline(y=oversold_opt, color='red', linestyle=':', label=f'Optimized Oversold ({oversold_opt})')
                plt.axhline(y=overbought_opt, color='red', linestyle=':', label=f'Optimized Overbought ({overbought_opt})')
        
        elif strategy_type == 'breakout':
            # For breakout strategy
            window_default = default_params.get('window', 20)
            window_opt = optimized_params.get('window', 20)
            
            if 'upper_band' in default_signals.columns and 'lower_band' in default_signals.columns:
                plt.plot(default_signals.index, default_signals['upper_band'], 
                        label=f'Default Upper Band ({window_default})', color='blue', linewidth=1.5)
                plt.plot(default_signals.index, default_signals['lower_band'], 
                        label=f'Default Lower Band ({window_default})', color='darkblue', linewidth=1.5)
                has_indicators = True
            
            if 'upper_band' in optimized_signals.columns and 'lower_band' in optimized_signals.columns:
                plt.plot(optimized_signals.index, optimized_signals['upper_band'], 
                        label=f'Optimized Upper Band ({window_opt})', color='red', linestyle='--', linewidth=1.5)
                plt.plot(optimized_signals.index, optimized_signals['lower_band'], 
                        label=f'Optimized Lower Band ({window_opt})', color='darkred', linestyle='--', linewidth=1.5)
                has_indicators = True
        
        if not has_indicators:
            logger.warning(f"No indicators found for strategy type: {strategy_type}")
            return ""
            
        plt.title(f"Indicators Comparison: Default vs Optimized ({strategy_type.replace('_', ' ').title()})")
        plt.ylabel('Price/Indicator Value')
        plt.grid(True, alpha=0.3)
        plt.legend(loc='best')
        
        # Plot the signals in the second subplot
        plt.subplot(2, 1, 2)
        
        # Plot positions or signals
        position_found = False
        for pos_col in ['position', 'signal', 'trade_signal']:
            if pos_col in default_signals.columns and pos_col in optimized_signals.columns:
                plt.plot(default_signals.index, default_signals[pos_col], 
                        label=f'Default {pos_col.title()}', color='blue', linewidth=1.5)
                plt.plot(optimized_signals.index, optimized_signals[pos_col], 
                        label=f'Optimized {pos_col.title()}', color='red', linestyle='--', linewidth=1.5)
                position_found = True
                break
        
        if not position_found:
            # Just show price changes if no position/signal column found
            plt.plot(default_signals.index, default_signals['close'].pct_change(), 
                    label='Price Change', color='green', linewidth=1)
        
        plt.title('Trading Signals: Default vs Optimized')
        plt.ylabel('Signal Value')
        plt.grid(True, alpha=0.3)
        plt.legend(loc='best')
        
        # Adjust layout and save
        plt.tight_layout()
        
        # Save to a buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        
        # Convert to base64 for embedding in HTML
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        # Create HTML for the chart
        html = f'''
        <div class="mt-4">
            <h6 class="mb-3">Indicators Comparison: Default vs Optimized</h6>
            <div class="text-center">
                <img src="data:image/png;base64,{img_str}" class="img-fluid" alt="Indicators Comparison" />
            </div>
            <div class="mt-2 text-center">
                <small class="text-muted">
                    Default parameters: {', '.join([f"{k}={v}" for k, v in default_params.items()])} <br>
                    Optimized parameters: {', '.join([f"{k}={v}" for k, v in optimized_params.items()])}
                </small>
            </div>
        </div>
        '''
        
        return html
    except Exception as e:
        logger.error(f"Error generating indicators comparison chart: {str(e)}")
        logger.error(traceback.format_exc())
        return ""

def get_strategy_indicators(strategy_type, default_signals, optimized_signals, default_params, optimized_params):
    """
    Get indicator columns based on strategy type.
    
    Args:
        strategy_type (str): Strategy type
        default_signals (pd.DataFrame): Default signals DataFrame
        optimized_signals (pd.DataFrame): Optimized signals DataFrame
        default_params (dict): Default parameters
        optimized_params (dict): Optimized parameters
    
    Returns:
        dict: Dictionary with default and optimized indicator columns
    """
    indicators = {'default': {}, 'optimized': {}}
    
    # Map strategy types to their indicator columns
    if strategy_type == 'trend_following' or strategy_type == 'sma_crossover' or strategy_type == 'ema_crossover':
        fast_period_default = default_params.get('fast_period', 20)
        slow_period_default = default_params.get('slow_period', 50)
        
        fast_period_opt = optimized_params.get('fast_period', 20)
        slow_period_opt = optimized_params.get('slow_period', 50)
        
        # Look for SMA or EMA columns
        prefix = 'sma' if strategy_type != 'ema_crossover' else 'ema'
        
        indicators['default'][f'{prefix}{fast_period_default}'] = {
            'label': f'{prefix.upper()}{fast_period_default}', 
            'color': 'blue', 
            'linestyle': '-'
        }
        indicators['default'][f'{prefix}{slow_period_default}'] = {
            'label': f'{prefix.upper()}{slow_period_default}', 
            'color': 'darkblue', 
            'linestyle': '-'
        }
        
        indicators['optimized'][f'{prefix}{fast_period_opt}'] = {
            'label': f'{prefix.upper()}{fast_period_opt}', 
            'color': 'red', 
            'linestyle': '--'
        }
        indicators['optimized'][f'{prefix}{slow_period_opt}'] = {
            'label': f'{prefix.upper()}{slow_period_opt}', 
            'color': 'darkred', 
            'linestyle': '--'
        }
    
    elif strategy_type == 'mean_reversion' or strategy_type == 'rsi':
        rsi_period_default = default_params.get('rsi_period', 14)
        oversold_default = default_params.get('oversold', 30)
        overbought_default = default_params.get('overbought', 70)
        
        rsi_period_opt = optimized_params.get('rsi_period', 14)
        oversold_opt = optimized_params.get('oversold', 30)
        overbought_opt = optimized_params.get('overbought', 70)
        
        indicators['default']['rsi'] = {
            'label': f'RSI({rsi_period_default})', 
            'color': 'blue', 
            'linestyle': '-'
        }
        
        indicators['optimized']['rsi'] = {
            'label': f'RSI({rsi_period_opt})', 
            'color': 'red', 
            'linestyle': '--'
        }
    
    elif strategy_type == 'breakout' or strategy_type == 'donchian_breakout':
        window_default = default_params.get('window', 20)
        window_opt = optimized_params.get('window', 20)
        
        indicators['default']['upper_band'] = {
            'label': f'Upper({window_default})', 
            'color': 'blue', 
            'linestyle': '-'
        }
        indicators['default']['lower_band'] = {
            'label': f'Lower({window_default})', 
            'color': 'darkblue', 
            'linestyle': '-'
        }
        
        indicators['optimized']['upper_band'] = {
            'label': f'Upper({window_opt})', 
            'color': 'red', 
            'linestyle': '--'
        }
        indicators['optimized']['lower_band'] = {
            'label': f'Lower({window_opt})', 
            'color': 'darkred', 
            'linestyle': '--'
        }
    
    elif strategy_type == 'bollinger_breakout':
        window_default = default_params.get('window', 20)
        std_dev_default = default_params.get('std_dev', 2)
        
        window_opt = optimized_params.get('window', 20)
        std_dev_opt = optimized_params.get('std_dev', 2)
        
        indicators['default']['upper_band'] = {
            'label': f'Upper BBand({window_default},{std_dev_default})', 
            'color': 'blue', 
            'linestyle': '-'
        }
        indicators['default']['middle_band'] = {
            'label': f'Middle BBand({window_default})', 
            'color': 'green', 
            'linestyle': '-'
        }
        indicators['default']['lower_band'] = {
            'label': f'Lower BBand({window_default},{std_dev_default})', 
            'color': 'darkblue', 
            'linestyle': '-'
        }
        
        indicators['optimized']['upper_band'] = {
            'label': f'Upper BBand({window_opt},{std_dev_opt})', 
            'color': 'red', 
            'linestyle': '--'
        }
        indicators['optimized']['middle_band'] = {
            'label': f'Middle BBand({window_opt})', 
            'color': 'darkgreen', 
            'linestyle': '--'
        }
        indicators['optimized']['lower_band'] = {
            'label': f'Lower BBand({window_opt},{std_dev_opt})', 
            'color': 'darkred', 
            'linestyle': '--'
        }
    
    elif strategy_type == 'macd_crossover':
        fast_period_default = default_params.get('fast_period', 12)
        slow_period_default = default_params.get('slow_period', 26)
        signal_period_default = default_params.get('signal_period', 9)
        
        fast_period_opt = optimized_params.get('fast_period', 12)
        slow_period_opt = optimized_params.get('slow_period', 26)
        signal_period_opt = optimized_params.get('signal_period', 9)
        
        indicators['default']['macd'] = {
            'label': f'MACD({fast_period_default},{slow_period_default})', 
            'color': 'blue', 
            'linestyle': '-'
        }
        indicators['default']['signal'] = {
            'label': f'Signal({signal_period_default})', 
            'color': 'darkblue', 
            'linestyle': '-'
        }
        
        indicators['optimized']['macd'] = {
            'label': f'MACD({fast_period_opt},{slow_period_opt})', 
            'color': 'red', 
            'linestyle': '--'
        }
        indicators['optimized']['signal'] = {
            'label': f'Signal({signal_period_opt})', 
            'color': 'darkred', 
            'linestyle': '--'
        }
    
    # Add more strategy types as needed...
    
    return indicators

def get_signal_column(signals_df):
    """Find the column that represents the trading signal in the DataFrame"""
    possible_cols = ['position', 'signal', 'trade_signal']
    
    for col in possible_cols:
        if col in signals_df.columns:
            return col
    
    return None

def format_params_for_display(params):
    """Format parameters as a readable string"""
    if not params:
        return "N/A"
    
    param_strs = []
    for k, v in params.items():
        param_strs.append(f"{k}={v}")
    
    return ", ".join(param_strs)

def plot_to_base64(plt_figure):
    """
    Convert a matplotlib figure to base64 encoded string
    
    Args:
        plt_figure: The matplotlib figure object
    
    Returns:
        str: Base64 encoded string of the figure image
    """
    buf = io.BytesIO()
    plt_figure.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    return f"data:image/png;base64,{img_str}"

def get_optimization_chart_path(strategy_type, timestamp):
    """
    Get the path to a specific optimization chart
    
    Args:
        strategy_type (str): The strategy type
        timestamp (str): The timestamp
    
    Returns:
        str: Path to the chart file
    """
    return os.path.join("results", "optimization", f"chart_backup_{strategy_type}_{timestamp}.png") 