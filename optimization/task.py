import logging
import os
import json
import time
from datetime import datetime

from strategies import create_strategy, get_default_parameters
from backtesting.backtester import Backtester
from optimization.optimizer import optimize_strategy
from optimization.status import set_optimization_status, log_optimization_request
from optimization.metrics import calculate_advanced_metrics
from optimization.visualization import plot_optimization_comparison
from optimization.file_manager import save_optimization_results

logger = logging.getLogger(__name__)

def run_optimization_task(data, optimization_config, current_config):
    """
    Run a strategy optimization task in the background
    
    Args:
        data (pd.DataFrame): The data to use for optimization
        optimization_config (dict): The optimization configuration
        current_config (dict): The current application configuration
        
    Returns:
        dict: Result summary
    """
    error_message = None
    result_file_path = None

    try:
        # 1. Run optimization
        params_for_optimizer = optimization_config['param_ranges']
        logger.info(f"[TASK] Calling optimize_strategy with param_ranges: {params_for_optimizer}")
        
        best_params, best_performance, all_results_raw = optimize_strategy(
            data=data,
            strategy_type=optimization_config['strategy_type'],
            param_ranges=optimization_config['param_ranges'],
            metric=optimization_config.get('metric', 'sharpe_ratio'),
            start_date=optimization_config.get('start_date'),
            end_date=optimization_config.get('end_date')
        )
        
        logger.info(f"[TASK] optimize_strategy returned - best_params: {best_params}, best_performance (snippet): {{ 'sharpe_ratio': {best_performance.get('sharpe_ratio', 'N/A')} }}")
        
        # Create the best strategy object using the best parameters
        best_strategy = create_strategy(optimization_config['strategy_type'], **best_params)

        # Update the current configuration with best parameters
        if 'strategies' not in current_config:
            current_config['strategies'] = {}
        if optimization_config['strategy_type'] not in current_config['strategies']:
            current_config['strategies'][optimization_config['strategy_type']] = {}
        current_config['strategies'][optimization_config['strategy_type']].update(best_params)
        
        # 2. Get default parameters and run backtest for default
        default_params = get_default_parameters(optimization_config['strategy_type'])
        backtester = Backtester(data, 10000.0, 0.001)
        default_strategy = create_strategy(optimization_config['strategy_type'], **default_params)
        default_result = backtester.run_backtest(
            default_strategy, 
            optimization_config.get('start_date'), 
            optimization_config.get('end_date')
        )
        default_performance = default_result['performance_metrics']
        default_signals = default_result.get('signals', None)
        
        # Calculate additional metrics for default strategy
        if default_signals is not None:
            additional_metrics = calculate_advanced_metrics(default_signals)
            default_performance.update(additional_metrics)

        # 3. Run backtest for optimized parameters
        # Start with default parameters
        final_optimized_params = default_params.copy()
        # Update with the parameters found by the optimization
        final_optimized_params.update(best_params) 

        logger.info(f"[TASK] Merged optimized params for backtest: {final_optimized_params}")
        log_optimization_request(
            optimization_config, 
            params_to_optimizer=params_for_optimizer,
            final_params_backtest=final_optimized_params
        )

        # Now use the correctly merged parameters
        optimized_strategy = create_strategy(optimization_config['strategy_type'], **final_optimized_params)
        optimized_result = backtester.run_backtest(
            optimized_strategy, 
            optimization_config.get('start_date'), 
            optimization_config.get('end_date')
        )
        optimized_performance = optimized_result['performance_metrics']
        optimized_signals = optimized_result.get('signals', None)
        
        # Calculate additional metrics for optimized strategy
        if optimized_signals is not None:
            additional_metrics = calculate_advanced_metrics(optimized_signals)
            optimized_performance.update(additional_metrics)

        # 4. Generate comparison chart (equity curve)
        chart_html = None
        chart_path = None
        if default_signals is not None and optimized_signals is not None:
            # Check if signal arrays have data
            logger.info(f"Generating chart with default signals shape {default_signals.shape} and optimized signals shape {optimized_signals.shape}")
            
            # Make sure both dataframes have the necessary columns for plotting
            for df_name, df in [("default", default_signals), ("optimized", optimized_signals)]:
                if 'equity' not in df.columns:
                    logger.warning(f"Missing 'equity' column in {df_name} signals dataframe for chart generation")
                    df['equity'] = 10000.0  # Default fallback
                if 'date' not in df.columns:
                    logger.warning(f"Missing 'date' column in {df_name} signals dataframe for chart generation")
                    continue
            
            chart_html, chart_path = plot_optimization_comparison(
                default_signals, 
                optimized_signals, 
                optimization_config['strategy_type']
            )
        
        # 5. Prepare and save results
        chart_timestamp = os.path.basename(chart_path).split('_')[-1].replace('.png', '') if chart_path else None
        
        # Sanitize performance metrics to ensure JSON compatibility
        sanitized_default_performance = _sanitize_dict(default_performance)
        sanitized_optimized_performance = _sanitize_dict(optimized_performance)
        
        results = {
            "strategy_type": optimization_config['strategy_type'],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "default_params": default_params,
            "optimized_params": final_optimized_params,
            "default_performance": sanitized_default_performance,
            "optimized_performance": sanitized_optimized_performance,
            "chart_timestamp": chart_timestamp,
            "top_results": [],
            "all_results": _sanitize_list(all_results_raw)
        }
        
        # Add top results in a more accessible format
        if all_results_raw:
            for i, result in enumerate(all_results_raw[:10]):  # Top 10 results
                results["top_results"].append({
                    "params": result.get('params', {}),
                    "score": _sanitize_value(result.get('value', 0)),
                    "metrics": _sanitize_dict(result.get('performance', {}))
                })
        
        # Save the results
        result_file_path = save_optimization_results(optimization_config['strategy_type'], results)
        
        # Log the optimization results for reference
        log_optimization_request(
            optimization_config, 
            extra_info={
                'default_params': default_params,
                'optimized_params': final_optimized_params,
                'default_performance': sanitized_default_performance,
                'optimized_performance': sanitized_optimized_performance,
                'all_results': _sanitize_list(all_results_raw[:3] if all_results_raw else [])
            }
        )
        
        # Update optimization status with results path and comparison data
        comparison_data = {
            "default_params": default_params,
            "optimized_params": final_optimized_params,
            "default_performance": sanitized_default_performance,
            "optimized_performance": sanitized_optimized_performance
        }
        
        set_optimization_status({
            "in_progress": False,
            "latest_result_file": result_file_path,
            "comparison_data": comparison_data
        })
        
        return {
            "status": "success",
            "message": f"Optimization for {optimization_config['strategy_type']} completed successfully",
            "file_path": result_file_path,
            "strategy_type": optimization_config['strategy_type']
        }
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error in optimization task: {error_message}")
        log_optimization_request(optimization_config, error=e)
        
        # Update optimization status with error
        set_optimization_status({
            "in_progress": False,
            "error": error_message
        })
        
        return {
            "status": "error",
            "message": f"Optimization failed: {error_message}",
            "strategy_type": optimization_config.get('strategy_type', "unknown")
        }

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
 