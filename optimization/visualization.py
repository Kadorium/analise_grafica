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

def plot_optimization_comparison(default_signals, optimized_signals, strategy_type, initial_capital=10000.0):
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
        timestamp = int(time.time())
        chart_id = f"equity-comparison-chart-{timestamp}"
        results_dir = os.path.join("results", "optimization")
        
        # Create directory if it doesn't exist
        os.makedirs(results_dir, exist_ok=True)
        
        # Convert dates to string format for JSON
        default_signals_dates = default_signals['date'].dt.strftime('%Y-%m-%d').tolist()
        optimized_signals_dates = optimized_signals['date'].dt.strftime('%Y-%m-%d').tolist()
        
        # Ensure we have valid equity values for plotting
        default_equity = default_signals['equity'].tolist()
        optimized_equity = optimized_signals['equity'].tolist()
        
        buy_and_hold_equity = []
        if 'cumulative_market_return' in default_signals.columns:
            buy_and_hold_equity = (default_signals['cumulative_market_return'] * initial_capital).tolist()
        else:
            logger.warning("'cumulative_market_return' column not found in default_signals. Buy & Hold curve will be omitted.")
            # Ensure buy_and_hold_equity is an empty list of the same length for consistency if needed elsewhere, though Chart.js handles empty datasets.
            # buy_and_hold_equity = [initial_capital] * len(default_signals_dates) # Alternative: flat line at initial capital
        
        # Log sample of the data for debugging
        logger.info(f"Chart data prepared - dates: {len(default_signals_dates)} points, equity: {len(default_equity)} points")
        logger.info(f"Sample date: {default_signals_dates[0]} to {default_signals_dates[-1]}")
        logger.info(f"Sample equity range: {min(default_equity)} to {max(default_equity)}")
        
        # Create a backup matplotlib chart
        plt.figure(figsize=(10, 5))
        plt.plot(default_signals['date'], default_signals['equity'], label='Default', color='red')
        plt.plot(optimized_signals['date'], optimized_signals['equity'], label='Optimized', color='green')
        if buy_and_hold_equity:
            plt.plot(default_signals['date'], buy_and_hold_equity, label='Buy & Hold', color='blue', linestyle='--')
        plt.xlabel('Date')
        plt.ylabel('Equity')
        plt.title('Equity Curve Comparison')
        plt.legend()
        
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
                "chart_id": chart_id,
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
            <canvas id="{chart_id}" width="800" height="400"></canvas>
        </div>
        <script>
        console.log("Chart script for {chart_id} loaded and executing");
        
        // Create a safer wrapper to avoid global conflicts
        (function() {{
            // Store chart config for later use if needed
            window.chartConfig_{chart_id} = {{
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
            
            // Add Buy & Hold dataset only if data is available
            if (window.chartConfig_{chart_id}.data.datasets.length < 3 && {json.dumps(bool(buy_and_hold_equity))}) {{
                window.chartConfig_{chart_id}.data.datasets.push({{
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
            function renderChart() {{
                var ctx = document.getElementById('{chart_id}');
                if (ctx) {{
                    new Chart(ctx, window.chartConfig_{chart_id});
                    console.log("Chart {chart_id} rendered successfully");
                }} else {{
                    console.error("Could not find canvas element {chart_id}");
                }}
            }}
            
            // Check if Chart.js is loaded
            if (typeof Chart !== 'undefined') {{
                // If Chart.js is already loaded, render immediately
                renderChart();
            }} else {{
                // If Chart.js isn't loaded yet, listen for window load
                window.addEventListener('load', function() {{
                    // Small delay to ensure Chart.js is loaded
                    setTimeout(renderChart, 100);
                }});
            }}
        }})();
        </script>
        """
        
        return chart_html, backup_chart_path
        
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error creating optimization comparison chart: {str(e)}\nTraceback:\n{error_details}")
        return None, None

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