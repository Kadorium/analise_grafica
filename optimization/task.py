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
from optimization.visualization import plot_optimization_comparison
from optimization.file_manager import save_optimization_results, ensure_optimization_directory, load_optimization_results, get_latest_optimization_file
from optimization.models import OptimizationConfig

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
        
        best_params, optimized_base_metrics, all_results_raw, optimized_base_debug_logs, optimized_signals_df = optimize_strategy(
            data=data,
            strategy_type=optimization_config['strategy_type'],
            param_ranges=optimization_config['param_ranges'],
            metric=optimization_config.get('metric', 'sharpe_ratio'),
            start_date=optimization_config.get('start_date'),
            end_date=optimization_config.get('end_date')
        )
        
        logger.info(f"[TASK] optimize_strategy returned - best_params: {best_params}, optimized_base_metrics (snippet): {{ 'sharpe_ratio': {optimized_base_metrics.get('sharpe_ratio', 'N/A')} }}")
        
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
        
        # Initialize Backtester for default run, passing the main data to its constructor
        # The Backtester.run_backtest method will handle date filtering internally.
        backtester_default = Backtester(data=data, # Pass main data here
                                      initial_capital=optimization_config.get('initial_capital', 10000.0), 
                                      commission=optimization_config.get('commission', 0.001))
        default_strategy = create_strategy(optimization_config['strategy_type'], **default_params)
        
        # Run backtest for default strategy. run_backtest will use its self.data and filter it.
        # Backtester.run_backtest returns a dictionary: {'strategy_name', 'performance_metrics', 'signals'}
        default_run_results_dict = backtester_default.run_backtest(
            default_strategy, 
            start_date=optimization_config.get('start_date'), 
            end_date=optimization_config.get('end_date')
        )
        # Base metrics are already computed by Backtester.run_backtest
        default_base_metrics = default_run_results_dict['performance_metrics']
        # Ensure default_base_metrics is a dictionary
        if not isinstance(default_base_metrics, dict):
            logger.warning(f"default_base_metrics was expected to be a dict but got {type(default_base_metrics)}. Re-initializing as empty dict. Investigate Backtester.run_backtest.")
            default_base_metrics = {}
        # The DataFrame for signals/further calculations is under the 'signals' key
        default_signals_df = default_run_results_dict['signals'] 
        
        # Get debug logs from the default run
        default_base_debug_logs = default_run_results_dict.get('debug_logs', [])
        
        # Calculate additional metrics for default strategy
        adv_default_metrics = None
        default_advanced_debug_logs = []
        if default_signals_df is not None and not default_signals_df.empty:
            adv_default_metrics, default_advanced_debug_logs = calculate_advanced_metrics(default_signals_df, base_metrics=default_base_metrics.copy())
            if isinstance(adv_default_metrics, dict):
                default_base_metrics.update(adv_default_metrics)
            elif adv_default_metrics is not None: # Log if it's not a dict but also not None
                logger.warning(f"adv_default_metrics was not a dict, but {type(adv_default_metrics)}. Skipping update.")
        else:
            logger.warning("Default signals are None or empty, skipping advanced metrics for default.")
        final_default_performance = default_base_metrics

        # 3. Optimized parameters run (metrics and signals already obtained from optimize_strategy)
        # final_optimized_params already includes merged default and best_params
        final_optimized_params = get_default_parameters(optimization_config['strategy_type']).copy()
        final_optimized_params.update(best_params)

        logger.info(f"[TASK] Merged optimized params for display/logging: {final_optimized_params}")
        
        # The optimized_base_metrics and optimized_base_debug_logs are from optimize_strategy's final run.
        # The optimized_signals_df is also from optimize_strategy.
        if not isinstance(optimized_base_metrics, dict):
            logger.warning(f"optimized_base_metrics was expected to be a dict but got {type(optimized_base_metrics)}. Re-initializing as empty dict. Investigate optimize_strategy.")
            optimized_base_metrics = {}
        
        # Calculate additional metrics for optimized strategy
        adv_optimized_metrics = None
        optimized_advanced_debug_logs = []
        if optimized_signals_df is not None and not optimized_signals_df.empty:
            adv_optimized_metrics, optimized_advanced_debug_logs = calculate_advanced_metrics(optimized_signals_df, base_metrics=optimized_base_metrics.copy())
            if isinstance(adv_optimized_metrics, dict):
                optimized_base_metrics.update(adv_optimized_metrics)
            elif adv_optimized_metrics is not None: # Log if it's not a dict but also not None
                logger.warning(f"adv_optimized_metrics was not a dict, but {type(adv_optimized_metrics)}. Skipping update.")
        else:
            logger.warning("Optimized signals_df is None or empty, skipping advanced metrics for optimized.")
        final_optimized_performance = optimized_base_metrics

        # 4. Generate comparison chart (equity curve)
        chart_html = None
        chart_path = None
        if default_signals_df is not None and optimized_signals_df is not None:
            logger.info(f"Generating chart with default signals shape {default_signals_df.shape} and optimized signals shape {optimized_signals_df.shape}")
            # ... (chart generation logic using default_signals_df and optimized_signals_df) ...
            chart_html, chart_path = plot_optimization_comparison(
                default_signals_df, 
                optimized_signals_df, 
                optimization_config['strategy_type'],
                initial_capital=optimization_config.get('initial_capital', 10000.0)
            )
        
        # 5. Prepare and save results
        chart_timestamp = os.path.basename(chart_path).split('_')[-1].replace('.png', '') if chart_path else None
        
        # Sanitize performance metrics to ensure JSON compatibility
        sanitized_default_performance = _sanitize_dict(final_default_performance)
        sanitized_optimized_performance = _sanitize_dict(final_optimized_performance)
        
        results = {
            "strategy_type": optimization_config['strategy_type'],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "default_params": default_params,
            "optimized_params": final_optimized_params,
            "default_performance": sanitized_default_performance,
            "optimized_performance": sanitized_optimized_performance,
            "chart_timestamp": chart_timestamp,
            "chart_html": chart_html,
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
        
        # Log the results dictionary before saving to check for chart_html
        logger.info(f"[TASK] Results to be saved (checking for chart_html):")
        logger.info(f"  chart_html is present: {'chart_html' in results}")
        if 'chart_html' in results and results['chart_html'] is not None:
            logger.info(f"  chart_html content (first 100 chars): {results['chart_html'][:100]}...")
        else:
            logger.info(f"  chart_html is None or not present.")

        # Save the results
        result_file_path = save_optimization_results(optimization_config['strategy_type'], results)
        
        # Log the optimization results for reference
        # This call will be updated to include debug logs and API request details
        
        # Retrieve initial API request details from global status
        current_status = get_optimization_status()
        api_request_details_from_status = current_status.get('current_optimization_api_request')
        
        log_optimization_request(
            request_data=optimization_config, # Pass the original optimization_config 
            api_request_details=api_request_details_from_status, # Pass the retrieved API details
            extra_info={
                'default_params': default_params,
                'optimized_params': final_optimized_params,
                'default_performance': sanitized_default_performance,
                'optimized_performance': sanitized_optimized_performance,
                'all_results_summary': _sanitize_list(all_results_raw[:3] if all_results_raw else []),
                'default_base_debug_logs': default_base_debug_logs,
                'default_advanced_debug_logs': default_advanced_debug_logs,
                'optimized_base_debug_logs': optimized_base_debug_logs,
                'optimized_advanced_debug_logs': optimized_advanced_debug_logs
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
            "strategy_type": optimization_config['strategy_type'],
            "chart_html": chart_html
        }
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error in optimization task: {error_message}")
        # log_optimization_request(optimization_config, error=e) # Original error logging
        # Enhance error logging with API details if available
        current_status_for_error_log = get_optimization_status()
        api_request_details_for_error = current_status_for_error_log.get('current_optimization_api_request')
        log_optimization_request(
            request_data=optimization_config, 
            error=e, 
            traceback_info=traceback.format_exc(),
            api_request_details=api_request_details_for_error
        )
        
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
 