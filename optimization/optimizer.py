import pandas as pd
import numpy as np
import itertools
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
from strategies import create_strategy, get_default_parameters
from backtesting.backtester import Backtester

def grid_search(data, strategy_type, param_grid, initial_capital=10000.0, commission=0.001, 
               metric='sharpe_ratio', start_date=None, end_date=None, max_workers=None):
    """
    Perform a grid search to find the optimal parameters for a strategy.
    
    Args:
        data (pandas.DataFrame): DataFrame containing the price data.
        strategy_type (str): Type of strategy ('trend_following', 'mean_reversion', or 'breakout').
        param_grid (dict): Dictionary mapping parameter names to lists of values to try.
        initial_capital (float, optional): Initial capital for backtesting. Defaults to 10000.0.
        commission (float, optional): Commission rate per trade. Defaults to 0.001 (0.1%).
        metric (str, optional): The metric to optimize for. Defaults to 'sharpe_ratio'.
        start_date (str, optional): Start date for backtesting. Format: 'YYYY-MM-DD'.
        end_date (str, optional): End date for backtesting. Format: 'YYYY-MM-DD'.
        max_workers (int, optional): Maximum number of worker processes. Defaults to None (auto).
        
    Returns:
        tuple: (best_params, best_value, all_results)
            best_params (dict): Dictionary containing the best parameters.
            best_value (float): The best value of the metric.
            all_results (list): List of all results, sorted by the metric.
    """
    # Create parameter combinations
    param_names = list(param_grid.keys())
    param_values = [param_grid[name] for name in param_names]
    param_combinations = list(itertools.product(*param_values))
    
    # If max_workers is not specified, use the number of CPU cores
    if max_workers is None:
        max_workers = multiprocessing.cpu_count()
    
    # Run the optimization in parallel
    results = []
    
    if max_workers > 1:
        # Parallel execution
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            for params in param_combinations:
                param_dict = dict(zip(param_names, params))
                futures.append(executor.submit(_evaluate_params, 
                                              data=data,
                                              strategy_type=strategy_type,
                                              params=param_dict,
                                              initial_capital=initial_capital,
                                              commission=commission,
                                              metric=metric,
                                              start_date=start_date,
                                              end_date=end_date))
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"An error occurred: {str(e)}")
    else:
        # Sequential execution
        for params in param_combinations:
            param_dict = dict(zip(param_names, params))
            try:
                result = _evaluate_params(
                    data=data,
                    strategy_type=strategy_type,
                    params=param_dict,
                    initial_capital=initial_capital,
                    commission=commission,
                    metric=metric,
                    start_date=start_date,
                    end_date=end_date
                )
                results.append(result)
            except Exception as e:
                print(f"An error occurred: {str(e)}")
    
    # Sort results by the metric (higher is better, except for max_drawdown)
    if metric == 'max_drawdown':
        results.sort(key=lambda x: x['value'])
    else:
        results.sort(key=lambda x: x['value'], reverse=True)
    
    # Get the best parameters
    if results:
        best_result = results[0]
        best_params = best_result['params']
        best_value = best_result['value']
    else:
        best_params = {}
        best_value = None
    
    return best_params, best_value, results

def _evaluate_params(data, strategy_type, params, initial_capital, commission, metric, start_date, end_date):
    """
    Evaluate a set of parameters for a strategy.
    
    Args:
        data (pandas.DataFrame): DataFrame containing the price data.
        strategy_type (str): Type of strategy.
        params (dict): Dictionary containing the parameters to evaluate.
        initial_capital (float): Initial capital for backtesting.
        commission (float): Commission rate per trade.
        metric (str): The metric to optimize for.
        start_date (str, optional): Start date for backtesting.
        end_date (str, optional): End date for backtesting.
        
    Returns:
        dict: Dictionary containing the parameters, the value of the metric, and other performance metrics.
    """
    # Get default parameters and update with the provided parameters
    all_params = get_default_parameters(strategy_type)
    all_params.update(params)
    
    # Create the strategy
    strategy = create_strategy(strategy_type, **all_params)
    
    # Create a backtester
    backtester = Backtester(data, initial_capital, commission)
    
    # Run the backtest
    result = backtester.run_backtest(strategy, start_date, end_date)
    performance = result['performance_metrics']
    
    return {
        'params': params,
        'value': performance[metric],
        'performance': performance
    }

def optimize_strategy(data, strategy_type, param_ranges=None, initial_capital=10000.0, commission=0.001,
                     metric='sharpe_ratio', start_date=None, end_date=None, max_workers=None):
    """
    Optimize a strategy's parameters.
    
    Args:
        data (pandas.DataFrame): DataFrame containing the price data.
        strategy_type (str): Type of strategy ('trend_following', 'mean_reversion', or 'breakout').
        param_ranges (dict, optional): Dictionary mapping parameter names to lists of values to try.
                                    If None, default ranges are used.
        initial_capital (float, optional): Initial capital for backtesting. Defaults to 10000.0.
        commission (float, optional): Commission rate per trade. Defaults to 0.001 (0.1%).
        metric (str, optional): The metric to optimize for. Defaults to 'sharpe_ratio'.
        start_date (str, optional): Start date for backtesting. Format: 'YYYY-MM-DD'.
        end_date (str, optional): End date for backtesting. Format: 'YYYY-MM-DD'.
        max_workers (int, optional): Maximum number of worker processes. Defaults to None (auto).
        
    Returns:
        tuple: (best_strategy, best_params, best_performance, all_results)
            best_strategy: The best strategy instance.
            best_params (dict): Dictionary containing the best parameters.
            best_performance (dict): Dictionary containing the performance metrics of the best strategy.
            all_results (list): List of all results, sorted by the metric.
    """
    # Define default parameter ranges based on strategy type
    if param_ranges is None:
        if strategy_type == 'trend_following':
            param_ranges = {
                'fast_ma_type': ['sma', 'ema'],
                'fast_ma_period': [5, 10, 15, 20, 25],
                'slow_ma_type': ['sma', 'ema'],
                'slow_ma_period': [30, 50, 100, 200]
            }
        elif strategy_type == 'mean_reversion':
            param_ranges = {
                'rsi_period': [7, 14, 21],
                'oversold': [20, 25, 30, 35],
                'overbought': [65, 70, 75, 80]
            }
        elif strategy_type == 'breakout':
            param_ranges = {
                'lookback_period': [10, 20, 30],
                'volume_threshold': [1.2, 1.5, 2.0],
                'price_threshold': [0.01, 0.02, 0.03]
            }
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    # Run the grid search
    best_params, best_value, all_results = grid_search(
        data=data,
        strategy_type=strategy_type,
        param_grid=param_ranges,
        initial_capital=initial_capital,
        commission=commission,
        metric=metric,
        start_date=start_date,
        end_date=end_date,
        max_workers=max_workers
    )
    
    # Create the best strategy
    if best_params:
        # Get default parameters and update with the best parameters
        all_params = get_default_parameters(strategy_type)
        all_params.update(best_params)
        
        best_strategy = create_strategy(strategy_type, **all_params)
        best_performance = all_results[0]['performance']
    else:
        best_strategy = None
        best_performance = None
    
    return best_strategy, best_params, best_performance, all_results

def compare_optimized_strategies(data, strategy_types=None, param_ranges=None, initial_capital=10000.0, 
                               commission=0.001, metric='sharpe_ratio', start_date=None, end_date=None,
                               max_workers=None):
    """
    Compare multiple optimized strategies.
    
    Args:
        data (pandas.DataFrame): DataFrame containing the price data.
        strategy_types (list, optional): List of strategy types to compare.
                                      If None, all available types are used.
        param_ranges (dict, optional): Dictionary mapping strategy types to parameter ranges.
                                    If None, default ranges are used.
        initial_capital (float, optional): Initial capital for backtesting. Defaults to 10000.0.
        commission (float, optional): Commission rate per trade. Defaults to 0.001 (0.1%).
        metric (str, optional): The metric to optimize for. Defaults to 'sharpe_ratio'.
        start_date (str, optional): Start date for backtesting. Format: 'YYYY-MM-DD'.
        end_date (str, optional): End date for backtesting. Format: 'YYYY-MM-DD'.
        max_workers (int, optional): Maximum number of worker processes. Defaults to None (auto).
        
    Returns:
        tuple: (best_strategy, all_strategies, backtest_results)
            best_strategy: The best strategy instance.
            all_strategies (dict): Dictionary mapping strategy types to the best strategy instances.
            backtest_results (dict): Dictionary mapping strategy types to backtest results.
    """
    if strategy_types is None:
        strategy_types = ['trend_following', 'mean_reversion', 'breakout']
    
    if param_ranges is None:
        param_ranges = {}
    
    # Optimize each strategy
    best_strategies = {}
    performances = {}
    
    for strategy_type in strategy_types:
        print(f"Optimizing {strategy_type} strategy...")
        
        param_range = param_ranges.get(strategy_type, None)
        
        best_strategy, best_params, best_performance, _ = optimize_strategy(
            data=data,
            strategy_type=strategy_type,
            param_ranges=param_range,
            initial_capital=initial_capital,
            commission=commission,
            metric=metric,
            start_date=start_date,
            end_date=end_date,
            max_workers=max_workers
        )
        
        best_strategies[strategy_type] = best_strategy
        performances[strategy_type] = best_performance
        
        print(f"Best parameters for {strategy_type}: {best_params}")
        print(f"Best {metric}: {best_performance[metric]}")
        print()
    
    # Compare the best strategies
    backtester = Backtester(data, initial_capital, commission)
    
    for strategy_type, strategy in best_strategies.items():
        backtester.run_backtest(strategy, start_date, end_date)
    
    # Get the best strategy based on the metric
    if metric == 'max_drawdown':
        best_strategy_type = min(performances.items(), key=lambda x: x[1][metric])[0]
    else:
        best_strategy_type = max(performances.items(), key=lambda x: x[1][metric])[0]
    
    best_strategy = best_strategies[best_strategy_type]
    
    return best_strategy, best_strategies, backtester.results 