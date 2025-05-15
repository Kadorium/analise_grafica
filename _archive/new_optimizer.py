import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime
import traceback
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
import matplotlib.pyplot as plt
import io
import base64
import itertools
import sys

from strategies import create_strategy, get_default_parameters, STRATEGY_REGISTRY
from backtesting.backtester import Backtester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("optimizer")

# Add a file handler for the optimization log
file_handler = logging.FileHandler('optimization_requests.log', mode='a')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Status tracking
OPTIMIZATION_STATUS = {
    "in_progress": False,
    "strategy_type": None,
    "start_time": None,
    "completion_time": None,
    "comparison_data": None,
    "error": None
}

def convert_to_serializable(obj):
    """
    Convert objects to JSON serializable formats
    
    Args:
        obj: Any object to convert
        
    Returns:
        JSON serializable version of the object
    """
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(i) for i in obj]
    elif pd.isna(obj):
        return None
    return obj

def log_message(message, data=None, level="INFO", to_console=False):
    """
    Log a message with optional data to the log file and console
    
    Args:
        message (str): The message to log
        data (dict, optional): Additional data to include in the log
        level (str): Log level (INFO, DEBUG, WARNING, ERROR)
        to_console (bool): Whether to also log to console
    """
    if level == "INFO":
        logger.info(message) 
    elif level == "DEBUG":
        logger.debug(message)
    elif level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)
    
    # Also log to the optimization_requests.log in a structured format
    try:
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": message,
            "level": level
        }
        
        if data:
            # Convert to JSON serializable format
            log_entry["data"] = convert_to_serializable(data)
            
        with open("optimization_requests.log", "a") as f:
            f.write(json.dumps(log_entry, indent=2) + "\n\n")
    except Exception as e:
        logger.error(f"Failed to write to log file: {str(e)}")
        
    # Also print to console if requested
    if to_console:
        print(f"{level} - {message}")
        if data:
            # Convert to JSON serializable format for printing
            serializable_data = convert_to_serializable(data)
            print(f"Data: {json.dumps(serializable_data, indent=2)}")

def calculate_performance_metrics(signals_df, initial_capital=10000.0, commission=0.001):
    """
    Calculate comprehensive performance metrics from signals DataFrame
    
    Args:
        signals_df (pd.DataFrame): DataFrame with signal column ('buy', 'sell', 'hold')
        initial_capital (float): Initial capital for the backtest
        commission (float): Commission rate per trade
        
    Returns:
        dict: Performance metrics dictionary with standardized keys
    """
    # Create a copy to avoid modifying the original
    df = signals_df.copy()
    
    # Ensure we have the required columns
    required_cols = ['date', 'close', 'signal']
    if not all(col in df.columns for col in required_cols):
        log_message(f"Missing required columns in signals DataFrame", {
            "required": required_cols,
            "available": df.columns.tolist()
        }, "ERROR")
        return {
            "total_return": 0.0,
            "annual_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "trades": 0
        }
    
    # Initialize tracking variables
    position = 0
    equity = initial_capital
    entry_price = 0.0
    trades = 0
    wins = 0
    losses = 0
    total_win_amount = 0.0
    total_loss_amount = 0.0
    
    # Add columns to track equity and trade performance
    df['position'] = 0
    df['equity'] = initial_capital
    df['trade_profit'] = 0.0
    df['trade_return'] = 0.0
    
    # Process each row to simulate trading
    for i in range(len(df)):
        if df.iloc[i]['signal'] == 'buy' and position == 0:
            # Enter long position
            position = 1
            entry_price = df.iloc[i]['close'] * (1 + commission)  # Include commission
            df.at[df.index[i], 'position'] = position
        elif df.iloc[i]['signal'] == 'sell' and position == 1:
            # Exit long position
            position = 0
            exit_price = df.iloc[i]['close'] * (1 - commission)  # Include commission
            trade_profit = exit_price - entry_price
            trade_return = trade_profit / entry_price
            
            # Update equity
            equity += trade_profit
            
            # Record trade details
            df.at[df.index[i], 'position'] = position
            df.at[df.index[i], 'trade_profit'] = trade_profit
            df.at[df.index[i], 'trade_return'] = trade_return
            
            # Update trade statistics
            trades += 1
            if trade_profit > 0:
                wins += 1
                total_win_amount += trade_profit
            else:
                losses += 1
                total_loss_amount += abs(trade_profit)
        
        # Update equity for each row
        df.at[df.index[i], 'equity'] = equity if position == 0 else equity + position * (df.iloc[i]['close'] - entry_price)
    
    # Calculate market returns for comparison
    df['market_return'] = df['close'].pct_change().fillna(0)
    df['cumulative_market_return'] = (1 + df['market_return']).cumprod()
    
    # Calculate strategy returns
    df['equity_return'] = df['equity'].pct_change().fillna(0)
    
    # Calculate time-related metrics
    if len(df) > 0:
        start_date = df['date'].min()
        end_date = df['date'].max()
        days = (end_date - start_date).days
        years = max(days / 365.25, 0.01)  # Avoid division by zero
        
        # Calculate key performance metrics
        total_return = (df['equity'].iloc[-1] / initial_capital) - 1
        annual_return = ((1 + total_return) ** (1 / years)) - 1
        
        # Calculate drawdown
        df['high_watermark'] = df['equity'].cummax()
        df['drawdown'] = (df['high_watermark'] - df['equity']) / df['high_watermark']
        max_drawdown = df['drawdown'].max()
        
        # Calculate volatility and Sharpe ratio
        daily_returns = df['equity_return']
        annual_volatility = daily_returns.std() * np.sqrt(252)  # Annualized
        risk_free_rate = 0.0  # Simplification
        sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
        
        # Calculate additional metrics
        win_rate = wins / trades if trades > 0 else 0
        avg_win = total_win_amount / wins if wins > 0 else 0
        avg_loss = total_loss_amount / losses if losses > 0 else 0
        profit_factor = total_win_amount / total_loss_amount if total_loss_amount > 0 else float('inf')
        
        # Calculate consecutive wins/losses
        trade_results = df[df['trade_profit'] != 0]['trade_profit'].reset_index(drop=True)
        
        max_consecutive_wins = 0
        current_consecutive_wins = 0
        max_consecutive_losses = 0
        current_consecutive_losses = 0
        
        for trade in trade_results:
            if trade > 0:
                current_consecutive_wins += 1
                current_consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_consecutive_wins)
            else:
                current_consecutive_losses += 1
                current_consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_consecutive_losses)
        
        # Create the metrics dictionary with standardized keys
        metrics = {
            # Core metrics
            "total_return": total_return * 100,  # Convert to percentage
            "annual_return": annual_return * 100,  # Convert to percentage
            "max_drawdown": max_drawdown * 100,  # Convert to percentage
            "sharpe_ratio": sharpe_ratio,
            "volatility": annual_volatility * 100,  # Convert to percentage
            
            # Trade statistics
            "trades": trades,
            "win_rate": win_rate * 100,  # Convert to percentage
            "profit_factor": profit_factor,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "max_consecutive_wins": max_consecutive_wins,
            "max_consecutive_losses": max_consecutive_losses,
            
            # Capital metrics
            "initial_capital": initial_capital,
            "final_capital": df['equity'].iloc[-1],
            
            # Time metrics
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "days": days,
            "years": years,
            
            # Derived metrics
            "risk_reward_ratio": (avg_win / avg_loss) if avg_loss > 0 else 0,
            "calmar_ratio": (annual_return / max_drawdown) if max_drawdown > 0 else 0,
            "recovery_factor": (total_return / max_drawdown) if max_drawdown > 0 else 0,
            "expectancy": (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        }
    else:
        # Default metrics if no data
        metrics = {
            "total_return": 0.0,
            "annual_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "volatility": 0.0,
            "trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "initial_capital": initial_capital,
            "final_capital": initial_capital,
            "risk_reward_ratio": 0.0,
            "calmar_ratio": 0.0,
            "recovery_factor": 0.0,
            "expectancy": 0.0
        }
    
    return metrics

def grid_search(data, strategy_type, param_grid, metric='sharpe_ratio', initial_capital=10000.0, 
               commission=0.001, max_workers=None):
    """
    Perform a grid search to find optimal parameters for a strategy
    
    Args:
        data (pd.DataFrame): The price data for backtesting
        strategy_type (str): The type of strategy to optimize
        param_grid (dict): Dictionary of parameter names to lists of values to try
        metric (str): The performance metric to optimize for
        initial_capital (float): Initial capital for backtesting
        commission (float): Commission rate per trade
        max_workers (int): Number of workers for parallel processing, None for auto
        
    Returns:
        tuple: (best_params, best_performance, all_results)
    """
    log_message(f"Starting grid search for {strategy_type}", {
        "param_grid": param_grid,
        "metric": metric,
        "num_combinations": np.prod([len(values) for values in param_grid.values()])
    })
    
    # Create parameter combinations
    param_names = list(param_grid.keys())
    param_values = [param_grid[name] for name in param_names]
    param_combinations = list(itertools.product(*param_values))
    
    # Set up parallel processing
    if max_workers is None:
        max_workers = max(1, multiprocessing.cpu_count() - 1)
    
    # Run the optimization
    results = []
    
    # Function to evaluate a single parameter set
    def evaluate_params(params_dict):
        try:
            log_message(f"Evaluating parameters", {
                "strategy": strategy_type,
                "params": params_dict
            }, "DEBUG")
            
            # For function-based strategies like RSI, directly generate signals
            if strategy_type in STRATEGY_REGISTRY:
                strategy_func = STRATEGY_REGISTRY[strategy_type]
                
                # Make a copy of the data to avoid modification
                data_copy = data.copy()
                
                # Get default parameters and update with our test params
                all_params = get_default_parameters(strategy_type).copy()
                all_params.update(params_dict)
                
                log_message(f"Running strategy with params", {
                    "strategy": strategy_type,
                    "combined_params": all_params
                }, "DEBUG")
                
                # Generate signals
                signals_df = strategy_func(data_copy, **all_params)
                
                # Calculate performance metrics
                performance = calculate_performance_metrics(signals_df, initial_capital, commission)
            else:
                # For class-based strategies, use the backtester
                all_params = get_default_parameters(strategy_type).copy()
                all_params.update(params_dict)
                
                strategy = create_strategy(strategy_type, **all_params)
                backtester = Backtester(data.copy(), initial_capital, commission)
                result = backtester.run_backtest(strategy)
                performance = result.get('performance_metrics', {})
            
            # Check if the target metric exists
            if metric not in performance:
                log_message(f"Metric {metric} not found in performance metrics", {
                    "params": params_dict,
                    "available_metrics": list(performance.keys())
                }, "WARNING")
                performance[metric] = 0.0
            
            # Return the result
            return {
                'params': params_dict,
                'performance': performance,
                'value': performance[metric]
            }
        except Exception as e:
            log_message(f"Error evaluating parameters", {
                "params": params_dict,
                "error": str(e),
                "traceback": traceback.format_exc()
            }, "ERROR")
            
            # Return a valid result with -inf value (or +inf for metrics where lower is better)
            return {
                'params': params_dict,
                'performance': {
                    metric: float('-inf') if metric != 'max_drawdown' else float('inf')
                },
                'value': float('-inf') if metric != 'max_drawdown' else float('inf'),
                'error': str(e)
            }
    
    # Run evaluations in parallel or sequentially
    if max_workers > 1:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for params in param_combinations:
                param_dict = dict(zip(param_names, params))
                futures.append(executor.submit(evaluate_params, param_dict))
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    log_message(f"Error in parameter evaluation", {
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }, "ERROR")
    else:
        for params in param_combinations:
            param_dict = dict(zip(param_names, params))
            result = evaluate_params(param_dict)
            results.append(result)
    
    # Sort results by the metric (higher is better, except for drawdown)
    results = [r for r in results if r['value'] is not None]  # Filter out failures
    
    if not results:
        log_message("No valid results found in grid search", level="WARNING")
        return {}, {}, []
    
    if metric == 'max_drawdown':
        # For drawdown, lower is better
        results.sort(key=lambda x: x['value'])
    else:
        # For other metrics, higher is better
        results.sort(key=lambda x: x['value'], reverse=True)
    
    # Get the best result
    best_result = results[0]
    best_params = best_result['params']
    best_performance = best_result['performance']
    
    log_message(f"Grid search completed. Best {metric}: {best_result['value']}", {
        "best_params": best_params,
        "best_value": best_result['value'],
        "num_results": len(results)
    })
    
    return best_params, best_performance, results 

def run_optimization(data, strategy_type, param_ranges, metric='sharpe_ratio', 
                    initial_capital=10000.0, commission=0.001, max_workers=None):
    """
    Run a complete optimization process for a strategy
    
    Args:
        data (pd.DataFrame): The price data for backtesting
        strategy_type (str): The type of strategy to optimize
        param_ranges (dict): Dictionary of parameter names to lists of values to try
        metric (str): The performance metric to optimize for
        initial_capital (float): Initial capital for backtesting
        commission (float): Commission rate per trade
        max_workers (int): Number of workers for parallel processing, None for auto
        
    Returns:
        dict: Complete optimization results
    """
    global OPTIMIZATION_STATUS
    
    try:
        # Update status
        OPTIMIZATION_STATUS["in_progress"] = True
        OPTIMIZATION_STATUS["strategy_type"] = strategy_type
        OPTIMIZATION_STATUS["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        OPTIMIZATION_STATUS["error"] = None
        
        log_message(f"Starting optimization for {strategy_type}", {
            "param_ranges": param_ranges,
            "metric": metric,
            "data_shape": data.shape
        }, "INFO", True)
        
        # Run the grid search
        best_params, best_performance, all_results = grid_search(
            data, 
            strategy_type, 
            param_ranges,
            metric=metric,
            initial_capital=initial_capital,
            commission=commission,
            max_workers=max_workers
        )
        
        if not best_params:
            log_message(f"Optimization failed for {strategy_type}: No valid parameters found", level="ERROR")
            OPTIMIZATION_STATUS["in_progress"] = False
            OPTIMIZATION_STATUS["completion_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            OPTIMIZATION_STATUS["error"] = "No valid parameters found"
            return {
                "status": "failed",
                "error": "No valid parameters found"
            }
        
        # Get default parameters and run backtest with them
        default_params = get_default_parameters(strategy_type)
        
        log_message(f"Running backtest with default parameters for {strategy_type}", {
            "default_params": default_params
        })
        
        # Run backtest with default parameters
        default_performance = {}
        try:
            if strategy_type in STRATEGY_REGISTRY:
                # For function-based strategies
                strategy_func = STRATEGY_REGISTRY[strategy_type]
                default_signals = strategy_func(data.copy(), **default_params)
                default_performance = calculate_performance_metrics(
                    default_signals, 
                    initial_capital=initial_capital,
                    commission=commission
                )
            else:
                # For class-based strategies
                default_strategy = create_strategy(strategy_type, **default_params)
                backtester = Backtester(data.copy(), initial_capital, commission)
                default_result = backtester.run_backtest(default_strategy)
                if 'performance_metrics' in default_result:
                    default_performance = default_result['performance_metrics']
                else:
                    log_message("Default backtest didn't return performance metrics", level="WARNING")
                    default_performance = {}
        except Exception as e:
            log_message(f"Error running default backtest", {
                "error": str(e),
                "traceback": traceback.format_exc()
            }, "ERROR")
            default_performance = {}
        
        # Make sure we have all required metrics in default_performance
        if not default_performance:
            default_performance = {
                "total_return": 0.0,
                "annual_return": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "volatility": 0.0,
                "trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "initial_capital": initial_capital,
                "final_capital": initial_capital
            }
        
        # Create a comprehensive results structure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Format the top results
        top_results = []
        for i, result in enumerate(all_results[:min(10, len(all_results))]):
            top_results.append({
                "rank": i + 1,
                "params": result["params"],
                "performance": result["performance"],
                "score": result["value"]
            })
        
        # Calculate improvement percentages
        improvement_data = {}
        for metric_key in best_performance:
            if metric_key in default_performance:
                default_val = default_performance[metric_key]
                optimized_val = best_performance[metric_key]
                
                if default_val != 0:
                    # For metrics where lower is better, invert the calculation
                    if metric_key in ['max_drawdown', 'volatility'] or 'drawdown' in metric_key:
                        improvement = ((default_val - optimized_val) / abs(default_val)) * 100
                    else:
                        improvement = ((optimized_val - default_val) / abs(default_val)) * 100
                    
                    improvement_data[metric_key] = round(improvement, 2)
                else:
                    improvement_data[metric_key] = "N/A"
            else:
                improvement_data[metric_key] = "N/A"
        
        # Create the complete results object
        optimization_results = {
            "status": "completed",
            "strategy_type": strategy_type,
            "timestamp": timestamp,
            "metric_optimized": metric,
            "default_params": default_params,
            "default_performance": default_performance,
            "best_params": best_params,
            "best_performance": best_performance,
            "improvement_data": improvement_data,
            "top_results": top_results
        }
        
        # Save results to file
        results_dir = os.path.join("results", "optimization")
        os.makedirs(results_dir, exist_ok=True)
        
        results_file = os.path.join(results_dir, f"optimization_{strategy_type}_{timestamp}.json")
        
        with open(results_file, 'w') as f:
            json.dump(optimization_results, f, indent=2)
        
        log_message(f"Optimization completed for {strategy_type}", {
            "results_file": results_file,
            "best_params": best_params,
            "best_score": top_results[0]["score"] if top_results else "N/A"
        }, "INFO", True)
        
        # Update status
        OPTIMIZATION_STATUS["in_progress"] = False
        OPTIMIZATION_STATUS["completion_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        OPTIMIZATION_STATUS["comparison_data"] = {
            "default_params": default_params,
            "default_performance": default_performance,
            "best_params": best_params,
            "best_performance": best_performance,
            "improvement_data": improvement_data
        }
        
        return optimization_results
    
    except Exception as e:
        log_message(f"Error in optimization process", {
            "strategy_type": strategy_type,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, "ERROR", True)
        
        # Update status
        OPTIMIZATION_STATUS["in_progress"] = False
        OPTIMIZATION_STATUS["completion_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        OPTIMIZATION_STATUS["error"] = str(e)
        
        return {
            "status": "failed",
            "error": str(e),
            "traceback": traceback.format_exc()
        } 

def get_optimization_status():
    """
    Get the current status of the optimization process
    
    Returns:
        dict: Current optimization status
    """
    global OPTIMIZATION_STATUS
    return OPTIMIZATION_STATUS

def get_latest_optimization_results(strategy_type=None):
    """
    Get the latest optimization results for a strategy
    
    Args:
        strategy_type (str, optional): Strategy type to get results for. If None, uses the last optimized strategy.
        
    Returns:
        dict: Latest optimization results
    """
    global OPTIMIZATION_STATUS
    
    # If no strategy specified, use the last one
    if strategy_type is None:
        strategy_type = OPTIMIZATION_STATUS.get("strategy_type")
    
    if not strategy_type:
        return {
            "status": "error",
            "message": "No strategy type specified and no optimization history"
        }
    
    # Check for in-progress optimization
    if OPTIMIZATION_STATUS["in_progress"] and OPTIMIZATION_STATUS["strategy_type"] == strategy_type:
        return {
            "status": "in_progress",
            "message": f"Optimization for {strategy_type} is still in progress",
            "start_time": OPTIMIZATION_STATUS["start_time"]
        }
    
    # Look for the latest result file
    results_dir = os.path.join("results", "optimization")
    
    if not os.path.exists(results_dir):
        log_message(f"Results directory not found: {results_dir}", level="WARNING")
        return {
            "status": "not_found",
            "message": "No optimization results directory found"
        }
    
    try:
        # Find files for this strategy
        files = [f for f in os.listdir(results_dir) 
                if f.startswith(f"optimization_{strategy_type}_") and f.endswith(".json")]
        
        if not files:
            log_message(f"No optimization files found for strategy: {strategy_type}", level="WARNING")
            return {
                "status": "not_found",
                "message": f"No optimization results found for {strategy_type}"
            }
        
        # Get the latest file
        latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(results_dir, f)))
        file_path = os.path.join(results_dir, latest_file)
        
        log_message(f"Found latest optimization results file: {file_path}")
        
        # Load the results
        with open(file_path, 'r') as f:
            results = json.load(f)
        
        return {
            "status": "success",
            "results": results,
            "file_path": file_path,
            "timestamp": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
        }
    
    except Exception as e:
        log_message(f"Error getting optimization results", {
            "strategy_type": strategy_type,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, "ERROR")
        
        return {
            "status": "error",
            "message": f"Error retrieving optimization results: {str(e)}"
        }

def format_optimization_results_for_frontend(results):
    """
    Format optimization results for the frontend display
    
    Args:
        results (dict): Raw optimization results
        
    Returns:
        dict: Formatted results for frontend consumption
    """
    if not results or "status" not in results or results["status"] != "success" or "results" not in results:
        return results
    
    raw_results = results["results"]
    
    # Create a standardized format for the frontend
    formatted = {
        "top_results": raw_results.get("top_results", []),
        "default_params": raw_results.get("default_params", {}),
        "optimized_params": raw_results.get("best_params", {}),
        "default_performance": raw_results.get("default_performance", {}),
        "optimized_performance": raw_results.get("best_performance", {}),
        "improvement_data": raw_results.get("improvement_data", {}),
        "status": "completed",
        "timestamp": raw_results.get("timestamp", "")
    }
    
    # Add metric descriptions for better interpretation
    formatted["metric_descriptions"] = {
        "total_return": "Total return percentage over the period",
        "annual_return": "Annualized return percentage",
        "max_drawdown": "Maximum percentage decline (lower is better)",
        "sharpe_ratio": "Risk-adjusted return (higher is better)",
        "volatility": "Annualized volatility percentage",
        "trades": "Total number of trades executed",
        "win_rate": "Percentage of winning trades",
        "profit_factor": "Ratio of gross profit to gross loss",
        "avg_win": "Average profit per winning trade",
        "avg_loss": "Average loss per losing trade (absolute value)",
        "initial_capital": "Initial capital amount",
        "final_capital": "Final capital amount",
        "risk_reward_ratio": "Ratio of average win to average loss",
        "calmar_ratio": "Ratio of annual return to maximum drawdown",
        "recovery_factor": "Ratio of total return to maximum drawdown",
        "expectancy": "Expected profit/loss per trade"
    }
    
    return formatted

def run_optimization_task(data, optimization_config, current_config=None):
    """
    Run an optimization task based on a configuration
    
    Args:
        data (pd.DataFrame): The price data for backtesting
        optimization_config (dict): Configuration for the optimization
        current_config (dict, optional): Current application configuration
        
    Returns:
        dict: Optimization results or status
    """
    # Extract configuration
    strategy_type = optimization_config.get("strategy_type")
    if not strategy_type:
        return {
            "status": "failed",
            "error": "No strategy type specified in optimization configuration"
        }
    
    param_ranges = optimization_config.get("param_ranges", {})
    if not param_ranges:
        return {
            "status": "failed", 
            "error": "No parameter ranges specified for optimization"
        }
    
    # Get other configuration parameters
    metric = optimization_config.get("metric", "sharpe_ratio")
    initial_capital = optimization_config.get("initial_capital", 10000.0)
    commission = optimization_config.get("commission", 0.001)
    max_workers = optimization_config.get("max_workers", None)
    
    # Check if an optimization is already in progress
    if OPTIMIZATION_STATUS["in_progress"]:
        return {
            "status": "in_progress",
            "message": f"Optimization for {OPTIMIZATION_STATUS['strategy_type']} is already in progress",
            "start_time": OPTIMIZATION_STATUS["start_time"]
        }
    
    # Log the optimization request
    log_message(f"Starting optimization task for {strategy_type}", {
        "param_ranges": param_ranges,
        "metric": metric,
        "initial_capital": initial_capital,
        "data_shape": data.shape if hasattr(data, 'shape') else None
    }, "INFO", True)
    
    # Run the optimization in a new thread
    import threading
    
    def run_in_background():
        try:
            # Run the optimization
            results = run_optimization(
                data,
                strategy_type,
                param_ranges,
                metric=metric,
                initial_capital=initial_capital,
                commission=commission,
                max_workers=max_workers
            )
            
            # Update the current config if provided
            if current_config is not None and results["status"] == "completed":
                if 'strategies' not in current_config:
                    current_config['strategies'] = {}
                if strategy_type not in current_config['strategies']:
                    current_config['strategies'][strategy_type] = {}
                current_config['strategies'][strategy_type].update(results["best_params"])
                log_message(f"Updated current config with best parameters for {strategy_type}")
        
        except Exception as e:
            log_message(f"Error in optimization background task", {
                "strategy_type": strategy_type,
                "error": str(e),
                "traceback": traceback.format_exc()
            }, "ERROR", True)
    
    # Start the background thread
    thread = threading.Thread(target=run_in_background)
    thread.daemon = True
    thread.start()
    
    return {
        "status": "started",
        "message": f"Optimization for {strategy_type} started in the background",
        "strategy_type": strategy_type
    }

# Replace the entire if __name__ == "__main__" section at the end of the file
if __name__ == "__main__":
    print("===== TESTING OPTIMIZATION MODULE =====")
    
    # Try to load test data
    try:
        if os.path.exists("../data/teste_arranged.csv"):
            data_path = "../data/teste_arranged.csv"
        elif os.path.exists("data/teste_arranged.csv"):
            data_path = "data/teste_arranged.csv"
        else:
            print("Test data file not found. Creating synthetic data.")
            # Create synthetic data
            dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
            data = pd.DataFrame({
                'date': dates,
                'open': [100 + i * 0.5 + ((-1) ** i) * i * 0.1 for i in range(100)],
                'high': [102 + i * 0.5 + ((-1) ** i) * i * 0.1 for i in range(100)],
                'low': [98 + i * 0.5 + ((-1) ** i) * i * 0.1 for i in range(100)],
                'close': [101 + i * 0.5 + ((-1) ** i) * i * 0.2 for i in range(100)],
                'volume': [1000000 * (1 + 0.1 * (i % 10)) for i in range(100)]
            })
            data_path = None
        
        # Load data if path was found
        if data_path:
            print(f"Loading test data from: {data_path}")
            data = pd.read_csv(data_path)
            if 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'])
        
        print(f"Data loaded, shape: {data.shape}")
        
        # Test RSI strategy directly first
        print("\n===== TESTING RSI STRATEGY DIRECTLY =====")
        strategy_type = "rsi"
        
        if strategy_type in STRATEGY_REGISTRY:
            try:
                # Get the strategy function
                strategy_func = STRATEGY_REGISTRY[strategy_type]
                
                # Get default parameters
                default_params = get_default_parameters(strategy_type)
                print(f"Default parameters: {default_params}")
                
                # Generate signals
                signals = strategy_func(data.copy(), **default_params)
                print(f"Generated signals shape: {signals.shape}")
                print(f"Signal counts: {signals['signal'].value_counts().to_dict()}")
                
                # Calculate metrics
                metrics = calculate_performance_metrics(signals, 10000.0, 0.001)
                print(f"Performance metrics sharpe ratio: {metrics['sharpe_ratio']}")
                print(f"Total trades: {metrics['trades']}")
                print(f"Win rate: {metrics['win_rate']}%")
                
                print("\n===== RSI STRATEGY TEST PASSED =====")
            except Exception as e:
                print(f"\n===== RSI STRATEGY TEST FAILED =====")
                print(f"Error: {str(e)}")
                traceback.print_exc()
        
        # Test the performance metrics calculation with a simple strategy
        print("\n===== TESTING PERFORMANCE METRICS CALCULATION =====")
        try:
            # Create a simple signals dataframe
            test_signals = data.copy()
            test_signals['signal'] = 'hold'
            
            # Add some buy/sell signals
            for i in range(10, len(test_signals), 20):
                test_signals.loc[test_signals.index[i], 'signal'] = 'buy'
                if i + 10 < len(test_signals):
                    test_signals.loc[test_signals.index[i + 10], 'signal'] = 'sell'
            
            # Calculate metrics
            metrics = calculate_performance_metrics(test_signals, 10000.0, 0.001)
            print(f"Test metrics calculation passed. Trades: {metrics['trades']}")
        except Exception as e:
            print(f"Error in metrics calculation: {str(e)}")
            traceback.print_exc()
        
        # Test a simple grid search with just a few parameters
        print("\n===== TESTING LIMITED GRID SEARCH =====")
        try:
            # Create a very limited parameter grid for quick testing
            param_grid = {
                "period": [14],  # Just one value
                "buy_level": [30],  # Just one value
                "sell_level": [70]  # Just one value
            }
            
            # Run grid search with detailed logging
            best_params, best_performance, results = grid_search(
                data, 
                "rsi", 
                param_grid,
                metric="sharpe_ratio",
                initial_capital=10000.0,
                commission=0.001,
                max_workers=1  # Use sequential processing for easier debugging
            )
            
            if best_params:
                print(f"Grid search successful. Best parameters: {best_params}")
                print(f"Best sharpe ratio: {best_performance.get('sharpe_ratio', 'N/A')}")
            else:
                print("Grid search returned no valid parameters")
        except Exception as e:
            print(f"Error in grid search: {str(e)}")
            traceback.print_exc()
        
        print("\n===== TESTING COMPLETE =====")
    
    except Exception as e:
        print(f"Error in test: {str(e)}")
        traceback.print_exc() 