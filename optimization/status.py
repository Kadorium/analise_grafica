from datetime import datetime
import logging
import json
import traceback

logger = logging.getLogger(__name__)

# Global status tracking for optimizations
OPTIMIZATION_STATUS = {
    "in_progress": False,
    "strategy_type": None,
    "start_time": None,
    "latest_result_file": None,
    "comparison_data": {}
}

def get_optimization_status():
    """
    Get the current optimization status.
    
    Returns:
        dict: The current optimization status
    """
    global OPTIMIZATION_STATUS
    return OPTIMIZATION_STATUS

def set_optimization_status(status_update):
    """
    Update the optimization status.
    
    Args:
        status_update (dict): The status update to apply
    """
    global OPTIMIZATION_STATUS
    OPTIMIZATION_STATUS.update(status_update)

def reset_optimization_status():
    """Reset the optimization status to its default state"""
    global OPTIMIZATION_STATUS
    OPTIMIZATION_STATUS.update({
        "in_progress": False,
        "strategy_type": None,
        "start_time": None,
        "latest_result_file": None,
        "comparison_data": {}
    })

def log_optimization_request(request_data, extra_info=None, error=None, traceback_info=None, 
                             params_to_optimizer=None, final_params_backtest=None,
                             api_request_details: dict = None):
    """
    Appends optimization request data, extra info, and errors to a log file for debugging and traceability.
    
    Args:
        request_data (dict): The request data
        extra_info (dict, optional): Additional information to log
        error (Exception, optional): Error that occurred, if any
        traceback_info (str, optional): Traceback information for the error
        params_to_optimizer (dict, optional): Parameters sent to the optimizer
        final_params_backtest (dict, optional): Parameters used for the final backtest
        api_request_details (dict, optional): API request details
    """
    log_file = 'optimization_requests.log'
    
    # Create basic log entry
    log_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'strategy_type': request_data.get('strategy_type', 'unknown')
    }
    
    # Add API request details if provided (e.g., initial call parameters)
    if api_request_details:
        log_entry['api_request_details'] = api_request_details
    
    # Add request parameters with better formatting
    if 'param_ranges' in request_data:
        formatted_params = {}
        for param_name, param_values in request_data['param_ranges'].items():
            # If the parameter has many values, just show count and range
            if isinstance(param_values, list) and len(param_values) > 10:
                formatted_params[param_name] = f"{len(param_values)} values from {min(param_values)} to {max(param_values)}"
            else:
                formatted_params[param_name] = param_values
        log_entry['param_ranges_request'] = formatted_params # Renamed for clarity
    
    # Add other request fields
    for key, value in request_data.items():
        if key != 'param_ranges' and key != 'strategy_type':
            log_entry[key] = value
            
    # Add parameters actually sent to the optimizer
    if params_to_optimizer is not None:
        log_entry['params_sent_to_optimizer'] = params_to_optimizer

    # Add parameters used for the final optimized backtest
    if final_params_backtest is not None:
        log_entry['final_params_for_optimized_backtest'] = final_params_backtest
            
    # Add extra info if provided (Performance, Parameter Changes, Top Results)
    if extra_info is not None:
        # Format optimization results for better readability
        if 'default_performance' in extra_info and 'optimized_performance' in extra_info:
            perf_comparison = {}
            # Log the full performance dictionaries for completeness
            log_entry['full_default_performance'] = extra_info['default_performance']
            log_entry['full_optimized_performance'] = extra_info['optimized_performance']

            # Keep the summary comparison for quick view
            comparison_metrics_keys = ['sharpe_ratio', 'total_return', 'max_drawdown', 'win_rate', 'profit_factor', 'percent_profitable_days', 'calmar_ratio']
            for metric in comparison_metrics_keys:
                if metric in extra_info['default_performance'] and metric in extra_info['optimized_performance']:
                    default_val = extra_info['default_performance'][metric]
                    opt_val = extra_info['optimized_performance'][metric]
                    perf_comparison[metric] = {
                        'default': round(default_val, 4) if isinstance(default_val, (int, float)) else default_val,
                        'optimized': round(opt_val, 4) if isinstance(opt_val, (int, float)) else opt_val,
                        'improvement': f"{round((opt_val - default_val) / abs(default_val) * 100, 2)}%" 
                            if isinstance(default_val, (int, float)) and default_val != 0 else "N/A"
                    }
            log_entry['performance_comparison'] = perf_comparison
        
        # Add parameter comparison
        if 'default_params' in extra_info and 'optimized_params' in extra_info:
            param_comparison = {}
            # Get all unique parameter names
            all_params = set(list(extra_info['default_params'].keys()) + list(extra_info['optimized_params'].keys()))
            for param in all_params:
                default_val = extra_info['default_params'].get(param, "N/A")
                opt_val = extra_info['optimized_params'].get(param, "N/A")
                if default_val != opt_val:
                    param_comparison[param] = {
                        'default': default_val,
                        'optimized': opt_val
                    }
            log_entry['parameter_changes'] = param_comparison
        
        # Add summary of all results (already uses 'all_results_summary' from task.py if available)
        if 'all_results_summary' in extra_info: # Changed from 'all_results' to match task.py
            log_entry['top_results_summary'] = extra_info['all_results_summary']

        # Add the collected debug logs from metric calculations
        if 'default_base_debug_logs' in extra_info:
            log_entry['default_base_metric_debug_logs'] = extra_info['default_base_debug_logs']
        if 'default_advanced_debug_logs' in extra_info:
            log_entry['default_advanced_metric_debug_logs'] = extra_info['default_advanced_debug_logs']
        if 'optimized_base_debug_logs' in extra_info:
            log_entry['optimized_base_metric_debug_logs'] = extra_info['optimized_base_debug_logs']
        if 'optimized_advanced_debug_logs' in extra_info:
            log_entry['optimized_advanced_metric_debug_logs'] = extra_info['optimized_advanced_debug_logs']
    
    # Add error if any
    if error is not None:
        log_entry['error'] = str(error)
        
        # Add traceback info if available
        if traceback_info is not None:
            log_entry['traceback'] = traceback_info
        # If traceback not provided, try to get current exception traceback
        elif error:
            current_tb = traceback.format_exc()
            if current_tb and 'NoneType' not in current_tb:
                log_entry['traceback'] = current_tb
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False, indent=2) + '\n\n')
    except Exception as e:
        logger.error(f"Failed to write optimization request log: {e}") 