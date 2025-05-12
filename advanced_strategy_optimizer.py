#!/usr/bin/env python3
"""
Advanced Strategy Optimizer

This script provides a simple way to compare and optimize the advanced trading strategies
added to the trading analysis system:
1. Adaptive Trend Following
2. Hybrid Momentum-Volatility
3. Chart Pattern Recognition

The script allows:
- Running individual backtests of each strategy
- Comparing all strategies side by side
- Optimizing strategy parameters
- Visualizing results

Usage:
    python advanced_strategy_optimizer.py --data <csv_file> [options]

Options:
    --data <file>           CSV file with price data (required)
    --strategy <name>       Strategy to test/optimize (default: all)
                            Options: adaptive_trend, hybrid_momentum_volatility, pattern_recognition, all
    --optimize              Run parameter optimization
    --initial_capital <num> Initial capital (default: 10000)
    --commission <num>      Commission rate (default: 0.001)
    --start_date <date>     Start date (YYYY-MM-DD)
    --end_date <date>       End date (YYYY-MM-DD)
    --metric <name>         Optimization metric (default: sharpe_ratio)
                            Options: sharpe_ratio, total_return, max_drawdown, win_rate
    --output <file>         Save results to file
    --no_plots              Disable plotting
"""

import os
import sys
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Add the current directory to the path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules from the trading analysis system
from data.data_loader import DataLoader
from backtesting.backtester import Backtester
from optimization.optimizer import optimize_strategy
from strategies import get_default_parameters, get_strategy_function
from indicators.indicator_utils import add_technical_indicators


def load_data(data_file):
    """Load and prepare data for analysis"""
    print(f"Loading data from {data_file}...")
    
    # Load data
    data_loader = DataLoader(data_file)
    data = data_loader.load_csv()
    
    # Clean data
    data = data_loader.clean_data()
    
    # Make sure we have all required columns
    required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Missing required column: {col}")
    
    print(f"Loaded {len(data)} price records from {data['date'].min()} to {data['date'].max()}")
    return data


def run_backtest(data, strategy_type, params=None, initial_capital=10000.0, 
               commission=0.001, start_date=None, end_date=None, add_indicators=True):
    """Run a backtest for a specific strategy"""
    # Create a copy of the data to avoid modifying the original
    data_copy = data.copy()
    
    # Add all technical indicators that might be needed by the strategies
    if add_indicators:
        print("Adding technical indicators...")
        data_copy = add_technical_indicators(data_copy, 
                                           sma_periods=[20, 50, 200],
                                           ema_periods=[12, 26],
                                           rsi=True,
                                           macd=True,
                                           bollinger_bands=True,
                                           atr=True,
                                           adx=True)
    
    # Get strategy function and parameters
    strategy_func = get_strategy_function(strategy_type)
    if params is None:
        params = get_default_parameters(strategy_type)
    
    # Create backtester
    backtester = Backtester(data_copy, initial_capital, commission)
    
    # Run backtest
    print(f"Running backtest for {strategy_type} strategy...")
    result = backtester.run_backtest_functional(strategy_type, params, start_date, end_date)
    
    return backtester, result


def compare_strategies(data, strategy_types, initial_capital=10000.0, commission=0.001, 
                     start_date=None, end_date=None):
    """Compare multiple strategies"""
    print("Comparing strategies...")
    
    # Add all technical indicators once
    print("Adding technical indicators...")
    data_with_indicators = add_technical_indicators(data.copy(), 
                                                  sma_periods=[20, 50, 200],
                                                  ema_periods=[12, 26],
                                                  rsi=True,
                                                  macd=True,
                                                  bollinger_bands=True,
                                                  atr=True,
                                                  adx=True)
    
    # Create backtester
    backtester = Backtester(data_with_indicators, initial_capital, commission)
    
    # Run backtest for each strategy
    results = {}
    for strategy_type in strategy_types:
        print(f"Running backtest for {strategy_type} strategy...")
        params = get_default_parameters(strategy_type)
        result = backtester.run_backtest_functional(strategy_type, params, start_date, end_date)
        results[strategy_type] = result
    
    # Generate equity curve
    if results:
        print("Generating equity curve plot...")
        equity_curve = backtester.plot_equity_curves()
        
        # Save the plot to file
        from io import BytesIO
        import base64
        
        # Convert base64 to image
        image_data = base64.b64decode(equity_curve)
        
        # Create the results directory if it doesn't exist
        os.makedirs('results', exist_ok=True)
        
        # Save the image
        with open(os.path.join('results', 'equity_curve_comparison.png'), 'wb') as f:
            f.write(image_data)
        
        print("Equity curve saved to results/equity_curve_comparison.png")
    
    return backtester, results


def optimize_strategies(data, strategy_types, metric='sharpe_ratio', initial_capital=10000.0,
                      commission=0.001, start_date=None, end_date=None):
    """Optimize multiple strategies"""
    print("Running optimization...")
    
    # Add all technical indicators once
    print("Adding technical indicators...")
    data_with_indicators = add_technical_indicators(data.copy(), 
                                                  sma_periods=[20, 50, 200],
                                                  ema_periods=[12, 26],
                                                  rsi=True,
                                                  macd=True,
                                                  bollinger_bands=True,
                                                  atr=True,
                                                  adx=True)
    
    optimization_results = {}
    
    for strategy_type in strategy_types:
        print(f"Optimizing {strategy_type} strategy...")
        
        # Define parameter ranges based on strategy type
        if strategy_type == 'adaptive_trend':
            param_ranges = {
                'fast_period': [5, 10, 15, 20],
                'slow_period': [20, 30, 40, 50],
                'adx_threshold': [15, 20, 25, 30],
                'volatility_factor': [0.3, 0.5, 0.7, 1.0]
            }
        elif strategy_type == 'hybrid_momentum_volatility':
            param_ranges = {
                'rsi_period': [7, 14, 21],
                'bb_window': [15, 20, 25],
                'rsi_oversold': [20, 25, 30, 35],
                'rsi_overbought': [65, 70, 75, 80],
                'volume_factor': [1.2, 1.5, 2.0]
            }
        elif strategy_type == 'pattern_recognition':
            param_ranges = {
                'pattern_window': [15, 20, 25, 30],
                'confirmation_length': [2, 3, 4],
                'volume_factor': [1.3, 1.5, 1.7, 2.0],
                'breakout_pct': [0.5, 1.0, 1.5, 2.0]
            }
        else:
            print(f"Warning: No predefined parameter ranges for {strategy_type}. Using defaults.")
            param_ranges = None
            continue
        
        # Run optimization
        best_params, best_performance, all_results = optimize_strategy(
            data=data_with_indicators,
            strategy_type=strategy_type,
            param_ranges=param_ranges,
            initial_capital=initial_capital,
            commission=commission,
            metric=metric,
            start_date=start_date,
            end_date=end_date
        )
        
        # Store results
        optimization_results[strategy_type] = {
            'best_params': best_params,
            'best_performance': best_performance,
            'all_results': all_results[:5]  # Store only top 5 results to keep output manageable
        }
        
        print(f"Best {metric} for {strategy_type}: {best_performance:.4f}")
        print(f"Best parameters: {best_params}")
        print("-" * 50)
    
    return optimization_results


def print_results_table(results):
    """Print a formatted table of strategy performance metrics"""
    if not results:
        print("No results to display")
        return
    
    headers = ["Strategy", "Total Return (%)", "Sharpe Ratio", "Max Drawdown (%)", "Win Rate (%)", "Trades"]
    
    # Calculate the width for each column
    col_widths = [max(len(h), 20) for h in headers]
    
    # Print header
    header_row = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print("\n" + "=" * len(header_row))
    print(header_row)
    print("=" * len(header_row))
    
    # Print each strategy's results
    for strategy_name, result in results.items():
        metrics = result['performance_metrics']
        
        # Format metrics
        total_return = f"{metrics['total_return']:.2f}"
        sharpe_ratio = f"{metrics['sharpe_ratio']:.2f}"
        max_drawdown = f"{metrics['max_drawdown']:.2f}"
        win_rate = f"{metrics['win_rate']:.2f}"
        trades = str(metrics['trades'])
        
        # Create row values
        row_values = [
            strategy_name,
            total_return,
            sharpe_ratio,
            max_drawdown,
            win_rate,
            trades
        ]
        
        # Print row
        row = " | ".join(str(v).ljust(w) for v, w in zip(row_values, col_widths))
        print(row)
    
    print("=" * len(header_row) + "\n")


def print_optimization_results(optimization_results):
    """Print optimization results in a formatted table"""
    if not optimization_results:
        print("No optimization results to display")
        return
    
    for strategy_type, results in optimization_results.items():
        print(f"\n{strategy_type.upper()} OPTIMIZATION RESULTS")
        print("=" * 50)
        
        best_params = results['best_params']
        best_performance = results['best_performance']
        
        print(f"Best Performance: {best_performance:.4f}")
        print("Best Parameters:")
        for param, value in best_params.items():
            print(f"  - {param}: {value}")
        
        print("\nTop Parameter Combinations:")
        for i, result in enumerate(results['all_results'][:5]):
            print(f"{i+1}. Performance: {result['value']:.4f}")
            for param, value in result['params'].items():
                print(f"   - {param}: {value}")
        
        print("-" * 50)


def save_results_to_file(results, output_file):
    """Save results to CSV file"""
    if not results:
        print("No results to save")
        return
    
    # Create a DataFrame from the results
    data = []
    for strategy_name, result in results.items():
        metrics = result['performance_metrics']
        
        data.append({
            'Strategy': strategy_name,
            'Total Return (%)': metrics['total_return'],
            'Annual Return (%)': metrics['annual_return'],
            'Sharpe Ratio': metrics['sharpe_ratio'],
            'Max Drawdown (%)': metrics['max_drawdown'],
            'Win Rate (%)': metrics['win_rate'],
            'Trades': metrics['trades'],
            'Volatility (%)': metrics['volatility']
        })
    
    df = pd.DataFrame(data)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")


def main():
    """Main function to parse arguments and run the optimizer"""
    parser = argparse.ArgumentParser(description="Advanced Strategy Optimizer")
    
    parser.add_argument("--data", required=True, help="CSV file with price data")
    parser.add_argument("--strategy", default="all",
                      choices=["adaptive_trend", "hybrid_momentum_volatility", "pattern_recognition", "all"],
                      help="Strategy to test/optimize")
    parser.add_argument("--optimize", action="store_true", help="Run parameter optimization")
    parser.add_argument("--initial_capital", type=float, default=10000.0, help="Initial capital")
    parser.add_argument("--commission", type=float, default=0.001, help="Commission rate")
    parser.add_argument("--start_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--metric", default="sharpe_ratio",
                      choices=["sharpe_ratio", "total_return", "max_drawdown", "win_rate"],
                      help="Optimization metric")
    parser.add_argument("--output", help="Save results to file")
    parser.add_argument("--no_plots", action="store_true", help="Disable plotting")
    
    args = parser.parse_args()
    
    # Load data
    data = load_data(args.data)
    
    # Determine which strategies to test
    if args.strategy == "all":
        strategy_types = ["adaptive_trend", "hybrid_momentum_volatility", "pattern_recognition"]
    else:
        strategy_types = [args.strategy]
    
    # Run optimization if requested
    if args.optimize:
        opt_results = optimize_strategies(
            data=data,
            strategy_types=strategy_types,
            metric=args.metric,
            initial_capital=args.initial_capital,
            commission=args.commission,
            start_date=args.start_date,
            end_date=args.end_date
        )
        
        print_optimization_results(opt_results)
        
        # Run backtests with optimized parameters
        backtester, backtest_results = None, {}
        
        for strategy_type, results in opt_results.items():
            print(f"Running backtest with optimized parameters for {strategy_type}...")
            backtester, result = run_backtest(
                data=data,
                strategy_type=strategy_type,
                params=results['best_params'],
                initial_capital=args.initial_capital,
                commission=args.commission,
                start_date=args.start_date,
                end_date=args.end_date
            )
            backtest_results[strategy_type] = result
    else:
        # Run strategy comparison
        backtester, backtest_results = compare_strategies(
            data=data,
            strategy_types=strategy_types,
            initial_capital=args.initial_capital,
            commission=args.commission,
            start_date=args.start_date,
            end_date=args.end_date
        )
    
    # Print results table
    print("\nPERFORMANCE SUMMARY")
    print_results_table(backtest_results)
    
    # Save results if requested
    if args.output:
        save_results_to_file(backtest_results, args.output)
    
    # Generate plots unless disabled
    if not args.no_plots and backtester is not None:
        print("Generating plots...")
        
        # Generate equity curve
        equity_curve_img = backtester.plot_equity_curves()
        
        # Generate drawdown curves
        drawdown_img = backtester.plot_drawdowns()
        
        # Console can't display images, so we save them
        # Convert base64 to image
        import base64
        from io import BytesIO
        
        # Create the results directory if it doesn't exist
        os.makedirs('results', exist_ok=True)
        
        # Save equity curve
        image_data = base64.b64decode(equity_curve_img)
        with open(os.path.join('results', 'equity_curve.png'), 'wb') as f:
            f.write(image_data)
        
        # Save drawdown curve
        image_data = base64.b64decode(drawdown_img)
        with open(os.path.join('results', 'drawdowns.png'), 'wb') as f:
            f.write(image_data)
        
        print("Plots saved to results directory")
    
    print("\nOptimization and backtesting complete!")


if __name__ == "__main__":
    main() 