#!/usr/bin/env python3
"""
Quick Advanced Strategy Backtest Runner

A simple helper script to run a backtest with the advanced trading strategies
and visualize the results with minimal configuration.

This is a more straightforward version of the advanced_strategy_optimizer.py script,
designed for quick testing rather than comprehensive optimization.

Usage:
    python run_advanced_backtest.py
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import base64
from io import BytesIO
import webbrowser
import tempfile
import json
import platform
import subprocess

# Add the current directory to the path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules from the trading analysis system
from data.data_loader import DataLoader
from backtesting.backtester import Backtester
from strategies import get_default_parameters, get_strategy_function
from indicators.indicator_utils import add_technical_indicators

def select_data_file():
    """Prompt the user to select a data file from the data directory"""
    data_dir = 'data'
    
    # List available CSV files in the data directory
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in the data directory. Please add data files.")
        return None
    
    print("\nAvailable data files:")
    for i, file in enumerate(csv_files, 1):
        print(f"{i}. {file}")
    
    try:
        choice = int(input("\nSelect a file number (or 0 to cancel): "))
        if choice == 0:
            return None
        
        selected_file = csv_files[choice - 1]
        return os.path.join(data_dir, selected_file)
    except (ValueError, IndexError):
        print("Invalid selection.")
        return None

def select_strategy():
    """Prompt the user to select a strategy"""
    strategies = [
        {
            'type': 'adaptive_trend',
            'name': 'Adaptive Trend Following',
            'description': 'Dynamically adjusts moving average periods based on market volatility and uses ADX to confirm trend strength.'
        },
        {
            'type': 'hybrid_momentum_volatility',
            'name': 'Hybrid Momentum-Volatility',
            'description': 'Combines RSI (momentum), Bollinger Bands (volatility), and volume confirmation for robust entry and exit signals.'
        },
        {
            'type': 'pattern_recognition',
            'name': 'Chart Pattern Recognition',
            'description': 'Identifies common chart patterns like double tops/bottoms, flags and pennants, with volume confirmation for entries and exits.'
        },
        {
            'type': 'all',
            'name': 'All Advanced Strategies',
            'description': 'Run a comparison of all three advanced strategies.'
        }
    ]
    
    print("\nAvailable strategies:")
    for i, strategy in enumerate(strategies, 1):
        print(f"{i}. {strategy['name']}")
        print(f"   {strategy['description']}")
    
    try:
        choice = int(input("\nSelect a strategy number: "))
        return strategies[choice - 1]['type']
    except (ValueError, IndexError):
        print("Invalid selection. Using Adaptive Trend Following as default.")
        return 'adaptive_trend'

def get_date_range(data):
    """Get date range from user or use data's min/max dates"""
    min_date = data['date'].min().strftime('%Y-%m-%d')
    max_date = data['date'].max().strftime('%Y-%m-%d')
    
    print(f"\nData date range: {min_date} to {max_date}")
    use_range = input("Do you want to use a custom date range? (y/n): ").lower() == 'y'
    
    if use_range:
        try:
            start_date = input(f"Enter start date (YYYY-MM-DD) or press Enter for {min_date}: ")
            start_date = start_date if start_date else min_date
            
            end_date = input(f"Enter end date (YYYY-MM-DD) or press Enter for {max_date}: ")
            end_date = end_date if end_date else max_date
            
            return start_date, end_date
        except:
            print("Invalid date format. Using full data range.")
    
    return min_date, max_date

def create_html_report(strategy_type, results, equity_curve_img, drawdown_img, trade_stats):
    """Create an HTML report with the backtest results"""
    # Determine the proper title
    if strategy_type == 'all':
        title = "Advanced Strategies Comparison"
    else:
        title_map = {
            'adaptive_trend': 'Adaptive Trend Following Strategy',
            'hybrid_momentum_volatility': 'Hybrid Momentum-Volatility Strategy',
            'pattern_recognition': 'Chart Pattern Recognition Strategy'
        }
        title = title_map.get(strategy_type, f"{strategy_type} Strategy")
    
    # Create the HTML content
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - Backtest Results</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 20px; 
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
            }}
            h1, h2, h3 {{ 
                color: #2c3e50; 
            }}
            .report-header {{
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
                border-left: 5px solid #4CAF50;
            }}
            .metrics-container {{
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                margin-bottom: 20px;
            }}
            .metric-box {{
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 15px;
                flex: 1;
                min-width: 200px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .metric-value {{
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }}
            .metric-name {{
                font-size: 14px;
                color: #7f8c8d;
                margin-bottom: 5px;
            }}
            .positive {{
                color: #27ae60;
            }}
            .negative {{
                color: #e74c3c;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #f8f9fa;
                font-weight: bold;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            .chart-container {{
                margin: 30px 0;
                text-align: center;
            }}
            img {{
                max-width: 100%;
                height: auto;
                border-radius: 5px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.2);
            }}
            .footer {{
                margin-top: 40px;
                text-align: center;
                font-size: 12px;
                color: #7f8c8d;
                padding: 20px;
                border-top: 1px solid #eee;
            }}
        </style>
    </head>
    <body>
        <div class="report-header">
            <h1>{title}</h1>
            <p>Backtest results generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    """
    
    # Add performance metrics
    html += """
        <h2>Performance Metrics</h2>
        <div class="metrics-container">
    """
    
    # Create metric boxes for each strategy
    for strategy_name, result in results.items():
        metrics = result['performance_metrics']
        
        # Format the metrics with proper colors
        total_return_class = "positive" if metrics['total_return'] > 0 else "negative"
        annual_return_class = "positive" if metrics['annual_return'] > 0 else "negative"
        
        html += f"""
            <div class="metric-box">
                <h3>{strategy_name}</h3>
                <div class="metric-name">Total Return</div>
                <div class="metric-value {total_return_class}">{metrics['total_return']:.2f}%</div>
                
                <div class="metric-name">Annual Return</div>
                <div class="metric-value {annual_return_class}">{metrics['annual_return']:.2f}%</div>
                
                <div class="metric-name">Sharpe Ratio</div>
                <div class="metric-value">{metrics['sharpe_ratio']:.2f}</div>
                
                <div class="metric-name">Max Drawdown</div>
                <div class="metric-value negative">{metrics['max_drawdown']:.2f}%</div>
                
                <div class="metric-name">Win Rate</div>
                <div class="metric-value">{metrics['win_rate']:.2f}%</div>
                
                <div class="metric-name">Total Trades</div>
                <div class="metric-value">{metrics['trades']}</div>
            </div>
        """
    
    html += """
        </div>
    """
    
    # Add charts
    html += """
        <h2>Equity Curve</h2>
        <div class="chart-container">
            <img src="data:image/png;base64,""" + equity_curve_img + """" alt="Equity Curve">
        </div>
        
        <h2>Drawdown</h2>
        <div class="chart-container">
            <img src="data:image/png;base64,""" + drawdown_img + """" alt="Drawdown">
        </div>
    """
    
    # Add trade statistics if available
    if trade_stats:
        html += """
            <h2>Trade Statistics</h2>
            <table>
                <tr>
                    <th>Strategy</th>
                    <th>Total Trades</th>
                    <th>Winning Trades</th>
                    <th>Losing Trades</th>
                    <th>Win Rate</th>
                    <th>Avg. Trade Return</th>
                    <th>Avg. Winner</th>
                    <th>Avg. Loser</th>
                </tr>
        """
        
        for strategy_name, stats in trade_stats.items():
            html += f"""
                <tr>
                    <td>{strategy_name}</td>
                    <td>{stats['total_trades']}</td>
                    <td>{stats['winning_trades']}</td>
                    <td>{stats['losing_trades']}</td>
                    <td>{stats['win_rate']:.2f}%</td>
                    <td>{stats['average_return']:.2f}%</td>
                    <td class="positive">{stats['average_winning_return']:.2f}%</td>
                    <td class="negative">{stats['average_losing_return']:.2f}%</td>
                </tr>
            """
        
        html += """
            </table>
        """
    
    # Add footer and close HTML
    html += """
        <div class="footer">
            <p>Generated by Advanced Trading Analysis System</p>
        </div>
    </body>
    </html>
    """
    
    return html

def open_html_report(html_content):
    """Save the HTML content to a temporary file and open it in a browser"""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.html')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(html_content)
        
        # Open the HTML file in the browser
        if platform.system() == 'Windows':
            os.startfile(path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.call(['open', path])
        else:  # Linux
            subprocess.call(['xdg-open', path])
        
        print(f"\nBacktest report opened in your web browser.")
        print(f"Report saved temporarily at: {path}")
    except Exception as e:
        print(f"Error opening report: {e}")

def get_trade_statistics(backtester, backtest_results):
    """Get trade statistics for all strategies in the backtest results"""
    trade_stats = {}
    
    for strategy_name in backtest_results.keys():
        try:
            stats = backtester.get_trade_statistics(strategy_name)
            trade_stats[strategy_name] = stats
        except Exception as e:
            print(f"Warning: Could not get trade statistics for {strategy_name}: {e}")
    
    return trade_stats

def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("        ADVANCED TRADING STRATEGY BACKTEST RUNNER")
    print("=" * 70)
    
    # Step 1: Select data file
    print("\nStep 1: Select a data file")
    data_file = select_data_file()
    if not data_file:
        print("Exiting: No data file selected.")
        return
    
    # Load data
    try:
        print(f"\nLoading data from {data_file}...")
        data_loader = DataLoader(data_file)
        data = data_loader.load_csv()
        data = data_loader.clean_data()
        
        print(f"Loaded {len(data)} price records from {data['date'].min()} to {data['date'].max()}")
    except Exception as e:
        print(f"Error loading data: {e}")
        return
    
    # Step 2: Select strategy
    print("\nStep 2: Select a strategy")
    strategy_type = select_strategy()
    
    # Step 3: Set date range
    print("\nStep 3: Set date range")
    start_date, end_date = get_date_range(data)
    
    # Step 4: Set backtest parameters
    print("\nStep 4: Set backtest parameters")
    try:
        initial_capital = float(input("Enter initial capital (default: 100): ") or 100)
        commission = float(input("Enter commission rate (default: 0.001): ") or 0.001)
    except ValueError:
        print("Invalid input. Using default values.")
        initial_capital = 100
        commission = 0.001
    
    # Add technical indicators
    print("\nAdding technical indicators...")
    data_with_indicators = add_technical_indicators(data.copy(), 
                                                 sma_periods=[20, 50, 200],
                                                 ema_periods=[12, 26],
                                                 rsi=True,
                                                 macd=True,
                                                 bollinger_bands=True,
                                                 atr=True,
                                                 adx=True)
    
    # Step 5: Run backtest
    print("\nStep 5: Running backtest...")
    if strategy_type == 'all':
        strategy_types = ["adaptive_trend", "hybrid_momentum_volatility", "pattern_recognition"]
        
        # Create backtester
        backtester = Backtester(data_with_indicators, initial_capital, commission)
        
        # Run backtest for each strategy
        results = {}
        for st in strategy_types:
            print(f"Running backtest for {st} strategy...")
            params = get_default_parameters(st)
            result = backtester.run_backtest_functional(st, params, start_date, end_date)
            results[st] = result
    else:
        # Run backtest for a single strategy
        backtester = Backtester(data_with_indicators, initial_capital, commission)
        params = get_default_parameters(strategy_type)
        result = backtester.run_backtest_functional(strategy_type, params, start_date, end_date)
        results = {strategy_type: result}
    
    # Generate plots
    print("\nGenerating performance charts...")
    equity_curve_img = backtester.plot_equity_curves()
    drawdown_img = backtester.plot_drawdowns()
    
    # Get trade statistics
    trade_stats = get_trade_statistics(backtester, results)
    
    # Print summary
    print("\nBACKTEST SUMMARY")
    print("=" * 50)
    for strategy_name, result in results.items():
        metrics = result['performance_metrics']
        print(f"\n{strategy_name}:")
        print(f"  Total Return: {metrics['total_return']:.2f}%")
        print(f"  Annual Return: {metrics['annual_return']:.2f}%")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print(f"  Win Rate: {metrics['win_rate']:.2f}%")
        print(f"  Trades: {metrics['trades']}")
    
    # Generate and open HTML report
    print("\nGenerating HTML report...")
    html_content = create_html_report(strategy_type, results, equity_curve_img, drawdown_img, trade_stats)
    open_html_report(html_content)
    
    print("\nBacktest complete!")

if __name__ == "__main__":
    main() 