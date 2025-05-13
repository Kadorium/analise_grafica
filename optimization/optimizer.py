import pandas as pd
import numpy as np
import itertools
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
from strategies import create_strategy, get_default_parameters, STRATEGY_REGISTRY
from backtesting.backtester import Backtester
import logging

logger = logging.getLogger(__name__)

# Define parameter ranges for optimization for all strategies
PARAM_RANGES = {
    'trend_following': {
        'fast_ma_type': ['sma', 'ema'],
        'fast_ma_period': [5, 10, 15, 20, 25],
        'slow_ma_type': ['sma', 'ema'],
        'slow_ma_period': [30, 50, 100, 200]
    },
    'mean_reversion': {
        'rsi_period': [7, 14, 21],
        'oversold': [20, 25, 30, 35],
        'overbought': [65, 70, 75, 80],
        'exit_middle': [45, 50, 55]
    },
    'breakout': {
        'lookback_period': [10, 20, 30],
        'volume_threshold': [1.2, 1.5, 2.0],
        'price_threshold': [0.01, 0.02, 0.03],
        'volatility_exit': [True, False],
        'atr_multiplier': [1.5, 2.0, 2.5]
    },
    'sma_crossover': {
        'short_period': [10, 20, 50, 100],
        'long_period': [50, 100, 200]
    },
    'ema_crossover': {
        'short_period': [5, 10, 20, 50],
        'long_period': [20, 50, 100, 200]
    },
    'supertrend': {
        'period': [7, 10, 14],
        'multiplier': [1.5, 2.0, 2.5, 3.0]
    },
    'adx': {
        'period': [7, 14, 21],
        'threshold': [20, 25, 30]
    },
    'bollinger_breakout': {
        'period': [10, 20, 30],
        'std_dev': [1.5, 2.0, 2.5]
    },
    'atr_breakout': {
        'period': [7, 14, 21],
        'multiplier': [1.0, 1.5, 2.0, 2.5]
    },
    'donchian_breakout': {
        'period': [10, 20, 30, 40]
    },
    'keltner_reversal': {
        'period': [10, 20, 30],
        'multiplier': [1.5, 2.0, 2.5]
    },
    'rsi': {
        'period': [7, 14, 21],
        'buy_level': [20, 25, 30],
        'sell_level': [70, 75, 80]
    },
    'macd_crossover': {
        'fast_period': [8, 12, 16],
        'slow_period': [21, 26, 30],
        'signal_period': [5, 9, 13]
    },
    'stochastic': {
        'k_period': [5, 9, 14],
        'd_period': [3, 5, 7]
    },
    'cci': {
        'period': [14, 20, 30],
        'overbought': [100, 150, 200],
        'oversold': [-100, -150, -200]
    },
    'williams_r': {
        'period': [7, 14, 21],
        'buy_level': [-80, -75, -70],
        'sell_level': [-30, -25, -20]
    },
    'obv_trend': {
        'period': [10, 20, 30]
    },
    'vpt_signal': {
        'period': [10, 20, 30]
    },
    'volume_ratio': {
        'period': [10, 20, 30],
        'threshold': [1.5, 2.0, 2.5]
    },
    'cmf': {
        'period': [10, 20, 30]
    },
    'accum_dist': {
        'period': [10, 20, 30]
    },
    'candlestick': {
        'confirmation_period': [1, 2, 3]
    },
    'adaptive_trend': {
        'fast_period': [5, 10, 15],
        'slow_period': [20, 30, 40],
        'signal_period': [5, 9, 13]
    },
    'hybrid_momentum_volatility': {
        'rsi_period': [7, 14, 21],
        'bb_period': [10, 20, 30],
        'std_dev': [1.5, 2.0, 2.5]
    },
    'pattern_recognition': {
        'lookback': [3, 5, 7, 10]
    }
}

def grid_search(data, strategy_type, param_grid, initial_capital=10000.0, commission=0.001, 
               metric='sharpe_ratio', start_date=None, end_date=None, max_workers=None):
    """
    Perform a grid search to find the optimal parameters for a strategy.
    
    Args:
        data (pandas.DataFrame): DataFrame containing the price data.
        strategy_type (str): Type of strategy.
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
    logger.info(f"[grid_search] Received param_grid: {param_grid}, metric: {metric}, start_date: {start_date}, end_date: {end_date}")
    
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
    # Filter data by date range if specified
    filtered_data = data.copy()
    
    if start_date:
        start_date = pd.to_datetime(start_date)
        filtered_data = filtered_data[filtered_data['date'] >= start_date]
        
    if end_date:
        end_date = pd.to_datetime(end_date)
        filtered_data = filtered_data[filtered_data['date'] <= end_date]
    
    # Create the strategy object (either legacy or modular via adapter)
    # Get default parameters and update with the provided parameters
    all_params = get_default_parameters(strategy_type)
    all_params.update(params)
    
    # Create the strategy using the factory function
    strategy = create_strategy(strategy_type, **all_params)
    
    # Create a backtester
    backtester = Backtester(filtered_data, initial_capital, commission)
    
    # Run the backtest
    result = backtester.run_backtest(strategy)
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
        strategy_type (str): Type of strategy.
        param_ranges (dict, optional): Dictionary mapping parameter names to lists of values to try.
                                    If None, default ranges are used.
        initial_capital (float, optional): Initial capital for backtesting. Defaults to 10000.0.
        commission (float, optional): Commission rate per trade. Defaults to 0.001 (0.1%).
        metric (str, optional): The metric to optimize for. Defaults to 'sharpe_ratio'.
        start_date (str, optional): Start date for backtesting. Format: 'YYYY-MM-DD'.
        end_date (str, optional): End date for backtesting. Format: 'YYYY-MM-DD'.
        max_workers (int, optional): Maximum number of worker processes. Defaults to None (auto).
        
    Returns:
        tuple: (best_params, best_performance, all_results)
            best_params (dict): Dictionary containing the best parameters.
            best_performance (dict): Dictionary containing the performance metrics of the best strategy.
            all_results (list): List of all results, sorted by the metric.
    """
    logger.info(f"[optimize_strategy] Received strategy_type: {strategy_type}, param_ranges: {param_ranges}, metric: {metric}, start_date: {start_date}, end_date: {end_date}")
    
    # Use predefined parameter ranges if none provided
    if param_ranges is None or not param_ranges:
        if strategy_type in PARAM_RANGES:
            param_ranges = PARAM_RANGES[strategy_type]
        else:
            raise ValueError(f"No default parameter ranges for strategy type: {strategy_type}. Please provide param_ranges.")
    
    # Run the grid search
    logger.info(f"[optimize_strategy] Calling grid_search with param_grid: {param_ranges}")
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
    
    # If no good parameters found
    if not best_params:
        return {}, {}, []
    
    # Filter data by date range if specified
    filtered_data = data.copy()
    
    if start_date:
        start_date = pd.to_datetime(start_date)
        filtered_data = filtered_data[filtered_data['date'] >= start_date]
        
    if end_date:
        end_date = pd.to_datetime(end_date)
        filtered_data = filtered_data[filtered_data['date'] <= end_date]
    
    # Get default parameters and update with the best parameters
    all_params = get_default_parameters(strategy_type)
    all_params.update(best_params)
    
    # Create the best strategy with all parameters
    best_strategy = create_strategy(strategy_type, **all_params)
    
    # Create a backtester
    backtester = Backtester(filtered_data, initial_capital, commission)
    
    # Run a backtest with the best strategy
    result = backtester.run_backtest(best_strategy, start_date, end_date)
    performance = result['performance_metrics']
    
    return best_params, performance, all_results

def compare_optimized_strategies(data, strategy_types=None, param_ranges=None, initial_capital=10000.0, 
                               commission=0.001, metric='sharpe_ratio', start_date=None, end_date=None,
                               max_workers=None):
    """
    Compare optimized strategies.
    
    Args:
        data (pandas.DataFrame): DataFrame containing the price data.
        strategy_types (list, optional): List of strategy types to compare.
                                      If None, all available strategies are used.
        param_ranges (dict, optional): Dictionary mapping strategy types to parameter ranges.
                                    If None, default ranges are used.
        initial_capital (float, optional): Initial capital for backtesting. Defaults to 10000.0.
        commission (float, optional): Commission rate per trade. Defaults to 0.001 (0.1%).
        metric (str, optional): The metric to optimize for. Defaults to 'sharpe_ratio'.
        start_date (str, optional): Start date for backtesting. Format: 'YYYY-MM-DD'.
        end_date (str, optional): End date for backtesting. Format: 'YYYY-MM-DD'.
        max_workers (int, optional): Maximum number of worker processes. Defaults to None (auto).
        
    Returns:
        dict: Dictionary mapping strategy types to (best_params, best_performance).
    """
    # If no strategy types specified, use all available
    if strategy_types is None:
        strategy_types = list(PARAM_RANGES.keys())
    
    # If no parameter ranges specified, use defaults
    if param_ranges is None:
        param_ranges = {strategy_type: PARAM_RANGES.get(strategy_type, None) for strategy_type in strategy_types}
    
    # Optimize each strategy
    results = {}
    
    for strategy_type in strategy_types:
        try:
            # Skip if no parameter ranges available
            if strategy_type not in param_ranges or not param_ranges[strategy_type]:
                print(f"Skipping {strategy_type}: No parameter ranges defined.")
                continue
            
            print(f"Optimizing {strategy_type}...")
            
            # Optimize the strategy
            best_params, best_performance, _ = optimize_strategy(
                data=data,
                strategy_type=strategy_type,
                param_ranges=param_ranges[strategy_type],
                initial_capital=initial_capital,
                commission=commission,
                metric=metric,
                start_date=start_date,
                end_date=end_date,
                max_workers=max_workers
            )
            
            # Add to results
            results[strategy_type] = {
                'params': best_params,
                'performance': best_performance
            }
            
            print(f"Done optimizing {strategy_type}.")
        except Exception as e:
            print(f"Error optimizing {strategy_type}: {str(e)}")
    
    return results

# Helper function for calculating performance metrics from signals
def calculate_performance_metrics(signals_df, initial_capital=10000.0, commission=0.001):
    """
    Calculate performance metrics from signals DataFrame.
    
    Args:
        signals_df (pd.DataFrame): DataFrame with signal column ('buy', 'sell', 'hold')
        initial_capital (float): Initial capital for the backtest
        commission (float): Commission rate per trade
        
    Returns:
        dict: Performance metrics
    """
    df = signals_df.copy()
    
    # Ensure we have the right columns
    required_cols = ['date', 'close', 'signal']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Data must contain columns: {required_cols}")
    
    # Initialize position and equity columns
    df['position'] = 0
    df['entry_price'] = 0.0
    df['equity'] = initial_capital
    df['trade_profit'] = 0.0
    df['trade_returns'] = 0.0
    
    # Calculate positions
    position = 0
    entry_price = 0.0
    equity = initial_capital
    
    for i in range(len(df)):
        if df.iloc[i]['signal'] == 'buy' and position == 0:
            position = 1
            entry_price = df.iloc[i]['close'] * (1 + commission)  # Include commission
        elif df.iloc[i]['signal'] == 'sell' and position == 1:
            position = 0
            exit_price = df.iloc[i]['close'] * (1 - commission)  # Include commission
            trade_profit = exit_price - entry_price
            trade_return = trade_profit / entry_price
            equity += trade_profit
            df.at[df.index[i], 'trade_profit'] = trade_profit
            df.at[df.index[i], 'trade_returns'] = trade_return
        
        df.at[df.index[i], 'position'] = position
        df.at[df.index[i], 'equity'] = equity
        df.at[df.index[i], 'entry_price'] = entry_price
    
    # Calculate market returns for comparison
    df['market_return'] = df['close'].pct_change().fillna(0)
    df['cumulative_market_return'] = (1 + df['market_return']).cumprod()
    
    # Calculate strategy metrics
    start_date = df['date'].min()
    end_date = df['date'].max()
    days = (end_date - start_date).days
    years = days / 365.25
    
    total_return = (df['equity'].iloc[-1] / initial_capital) - 1
    annual_return = ((1 + total_return) ** (1 / max(years, 0.01))) - 1
    
    # Drawdown calculation
    df['drawdown'] = (df['equity'].cummax() - df['equity']) / df['equity'].cummax()
    max_drawdown = df['drawdown'].max()
    
    # Trade statistics
    winning_trades = df[df['trade_profit'] > 0]
    losing_trades = df[df['trade_profit'] < 0]
    
    total_trades = len(winning_trades) + len(losing_trades)
    win_rate = len(winning_trades) / max(total_trades, 1)
    
    avg_win = winning_trades['trade_profit'].mean() if len(winning_trades) > 0 else 0
    avg_loss = abs(losing_trades['trade_profit'].mean()) if len(losing_trades) > 0 else 0
    
    profit_factor = abs(winning_trades['trade_profit'].sum() / losing_trades['trade_profit'].sum()) if len(losing_trades) > 0 and losing_trades['trade_profit'].sum() != 0 else float('inf')
    
    # Calculate volatility and Sharpe ratio
    daily_returns = df['equity'].pct_change().fillna(0)
    annual_volatility = daily_returns.std() * (252 ** 0.5)  # Annualized
    sharpe_ratio = annual_return / max(annual_volatility, 0.0001)  # Avoid division by zero
    
    metrics = {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'initial_capital': initial_capital,
        'final_capital': df['equity'].iloc[-1],
        'total_return_percent': total_return * 100,
        'annual_return_percent': annual_return * 100,
        'max_drawdown_percent': max_drawdown * 100,
        'sharpe_ratio': sharpe_ratio,
        'total_trades': total_trades,
        'win_rate_percent': win_rate * 100,
        'profit_factor': profit_factor,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'annual_volatility_percent': annual_volatility * 100
    }
    
    return metrics 