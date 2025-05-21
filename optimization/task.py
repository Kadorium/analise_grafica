import logging
import os
import json
import time
from datetime import datetime
import traceback
import pandas as pd

from strategies import create_strategy, get_default_parameters
from backtesting.backtester import Backtester
from optimization.optimizer import optimize_strategy
from optimization.status import set_optimization_status, log_optimization_request, get_optimization_status
from optimization.metrics import calculate_advanced_metrics
from optimization.visualization import plot_optimization_comparison, plot_indicators_comparison
from optimization.file_manager import save_optimization_results, ensure_optimization_directory, load_optimization_results, get_latest_optimization_file
from optimization.models import OptimizationConfig

logger = logging.getLogger(__name__)

def run_optimization_task(data, optimization_config, current_config=None):
    """
    Run the optimization task for the given configuration.
    
    Args:
        data (pd.DataFrame): The data to optimize on.
        optimization_config (dict): Configuration for optimization.
        current_config (dict, optional): Current application configuration.
        
    Returns:
        dict: Dictionary with optimization results.
    """
    try:
        # Log the optimization request with the complete API request details
        api_request_details = get_optimization_status().get('current_optimization_api_request', {})
        log_optimization_request(optimization_config, api_request_details=api_request_details)
        
        # Set optimization status to in-progress
        task_id = str(int(time.time()))
        set_optimization_status({
            "in_progress": True,
            "strategy_type": optimization_config.get('strategy_type'),
            "task_id": task_id
        })
        
        # Get data slice based on date range
        if optimization_config.get('start_date') and optimization_config.get('end_date'):
            data = data[(data['date'] >= optimization_config.get('start_date')) & 
                        (data['date'] <= optimization_config.get('end_date'))].copy()
        
        # Get default parameters for the strategy
        default_params = get_default_parameters(optimization_config.get('strategy_type'))
        
        # Initialize Backtester for default run, passing the main data to its constructor
        backtester_default = Backtester(
            data=data,
            initial_capital=optimization_config.get('initial_capital', 100.0), 
            commission=optimization_config.get('commission', 0.001)
        )
        default_strategy = create_strategy(optimization_config.get('strategy_type'), **default_params)
        
        # Run backtest for default strategy
        default_run_results_dict = backtester_default.run_backtest(
            default_strategy,
            start_date=optimization_config.get('start_date'),
            end_date=optimization_config.get('end_date')
        )
        
        # Get all metrics for default run
        default_performance_metrics = calculate_advanced_metrics(
            default_run_results_dict["signals"],
            default_run_results_dict["performance_metrics"]
        )
        
        # Run optimization
        set_optimization_status({
            "in_progress": True, 
            "strategy_type": optimization_config.get('strategy_type'),
            "status_message": 'Optimizing strategy parameters...'
        })
        optimization_results = optimize_strategy(
            data,
            optimization_config.get('strategy_type'),
            optimization_config.get('param_grid', {}),
            metric=optimization_config.get('metric'),
            start_date=optimization_config.get('start_date'),
            end_date=optimization_config.get('end_date'),
            initial_capital=optimization_config.get('initial_capital', 100.0),
            commission=optimization_config.get('commission', 0.001)
        )
        
        set_optimization_status({
            "in_progress": True, 
            "strategy_type": optimization_config.get('strategy_type'),
            "status_message": 'Running backtest with optimized parameters...'
        })
        
        # Get the best parameters from optimization
        optimized_params = optimization_results[0]['params']
        
        # Run backtest with optimized parameters
        backtester_optimized = Backtester(data=data, 
                                         initial_capital=optimization_config.get('initial_capital', 100.0), 
                                         commission=optimization_config.get('commission', 0.001))
        optimized_strategy = create_strategy(optimization_config.get('strategy_type'), **optimized_params)
        
        optimized_run_results_dict = backtester_optimized.run_backtest(
            optimized_strategy,
            start_date=optimization_config.get('start_date'),
            end_date=optimization_config.get('end_date')
        )
        
        # Get all metrics for optimized run
        optimized_performance_metrics = calculate_advanced_metrics(
            optimized_run_results_dict["signals"],
            optimized_run_results_dict["performance_metrics"]
        )
        
        set_optimization_status({
            "in_progress": True, 
            "strategy_type": optimization_config.get('strategy_type'),
            "status_message": 'Generating performance comparison...'
        })
        
        # Generate comparison chart between default and optimized runs
        chart_html = plot_optimization_comparison(
            default_run_results_dict["signals"],
            optimized_run_results_dict["signals"],
            optimization_config.get('strategy_type')
        )
        
        # Generate indicators comparison chart
        indicators_chart_html = plot_indicators_comparison(
            default_run_results_dict["signals"],
            optimized_run_results_dict["signals"],
            optimization_config.get('strategy_type'),
            default_params,
            optimized_params
        )
        
        # Prepare results object
        results = {
            "task_id": task_id,
            "strategy_type": optimization_config.get('strategy_type'),
            "top_results": optimization_results,
            "default_params": default_params,
            "optimized_params": optimized_params,
            "default_performance": default_performance_metrics,
            "optimized_performance": optimized_performance_metrics,
            "chart_html": chart_html,
            "indicators_chart_html": indicators_chart_html,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save results to file
        result_file = save_optimization_results(optimization_config.get('strategy_type'), results)
        logger.info(f"Optimization results saved to {result_file}")
        
        # Set optimization status to complete
        set_optimization_status({
            "in_progress": False, 
            "strategy_type": optimization_config.get('strategy_type'),
            "status_message": 'Optimization complete'
        })
        
        return results
    except Exception as e:
        error_msg = f"Error in optimization task: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        set_optimization_status({
            "in_progress": False, 
            "strategy_type": optimization_config.get('strategy_type'),
            "status_message": error_msg
        })
        return {"error": error_msg}

# Helper functions for JSON sanitization
def _sanitize_value(value):
    """Sanitize a single value for JSON compatibility"""
    import math
    import numpy as np
    
    if value is None:
        return None
    
    # Convert numpy types to Python types
    if isinstance(value, (np.integer, np.int64, np.int32)):
        return int(value)
    elif isinstance(value, (np.floating, np.float64, np.float32)):
        value = float(value)
    
    # Handle non-finite float values
    if isinstance(value, float):
        if math.isnan(value):
            return 0
        elif math.isinf(value):
            return 1.0e+308 if value > 0 else -1.0e+308
    
    return value

def _sanitize_dict(d):
    """Sanitize a dictionary for JSON compatibility"""
    if not isinstance(d, dict):
        return {}
    
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            result[k] = _sanitize_dict(v)
        elif isinstance(v, list):
            result[k] = _sanitize_list(v)
        else:
            result[k] = _sanitize_value(v)
    
    return result

def _sanitize_list(lst):
    """Sanitize a list for JSON compatibility"""
    if not isinstance(lst, list):
        return []
    
    result = []
    for item in lst:
        if isinstance(item, dict):
            result.append(_sanitize_dict(item))
        elif isinstance(item, list):
            result.append(_sanitize_list(item))
        else:
            result.append(_sanitize_value(item))
    
    return result
 