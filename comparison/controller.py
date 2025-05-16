import pandas as pd
import logging
import traceback
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import json

from .comparator import StrategyComparator, run_comparison

logger = logging.getLogger("trading-app.comparison.controller")

async def run_comparison_controller(
    processed_data,
    strategy_configs,
    backtest_config=None,
    optimize=False,
    optimization_metric='sharpe_ratio'
):
    """
    Controller function to handle strategy comparison requests.
    
    Args:
        processed_data (pd.DataFrame): The processed price data
        strategy_configs (list): List of strategy configuration dictionaries
        backtest_config (dict, optional): Configuration for backtesting (capital, commission, etc.)
        optimize (bool): Whether to optimize strategies before comparison
        optimization_metric (str): Metric to optimize for if optimize=True
        
    Returns:
        dict: Comparison results with metrics and visualizations
    """
    if processed_data is None:
        return {"success": False, "message": "No processed data available."}
    
    if not strategy_configs:
        return {"success": False, "message": "No strategy configurations provided."}
    
    try:
        # Set up backtest configuration
        if backtest_config is None:
            backtest_config = {}
            
        initial_capital = backtest_config.get('initial_capital', 100.0)
        commission = backtest_config.get('commission', 0.001)
        start_date = backtest_config.get('start_date')
        end_date = backtest_config.get('end_date')
        
        # Run comparison
        comparison_results = run_comparison(
            data=processed_data,
            strategy_configs=strategy_configs,
            initial_capital=initial_capital,
            commission=commission,
            start_date=start_date,
            end_date=end_date,
            optimize=optimize,
            optimization_metric=optimization_metric
        )
        
        # Get table data for display
        comparator = StrategyComparator(processed_data, initial_capital, commission)
        comparator.results = comparison_results['results']
        table_data = comparator.get_comparison_table_data()
        
        # Combine results
        response = {
            "success": True,
            "message": "Comparison completed successfully.",
            "comparison_metrics": table_data['metrics'],
            "best_strategies": table_data['best_strategies'],
            "parameters": table_data['parameters'],
            "trades": table_data['trades'],
            "chart_image": comparison_results['chart_base64']
        }
        
        # Add optimization information if applicable
        if optimize:
            response["optimization"] = {
                "metric": optimization_metric,
                "strategies": [
                    {
                        "strategy_id": config.get('strategy_id'),
                        "optimized": config.get('optimized', False),
                        "optimization_score": config.get('optimization_score', None),
                        "optimization_error": config.get('optimization_error', None)
                    }
                    for config in strategy_configs if 'optimized' in config
                ]
            }
        
        # Save comparison results
        save_comparison_results(response)
        
        return response
        
    except Exception as e:
        error_msg = f"Error in strategy comparison: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return {"success": False, "message": error_msg}

def save_comparison_results(results):
    """
    Save comparison results to a file.
    
    Args:
        results (dict): Comparison results
    """
    try:
        # Create directory if it doesn't exist
        results_dir = os.path.join("results", "comparison")
        os.makedirs(results_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comparison_{timestamp}.json"
        filepath = os.path.join(results_dir, filename)
        
        # Save as JSON
        with open(filepath, 'w') as f:
            # Create a copy without the large image data
            results_to_save = results.copy()
            results_to_save.pop('chart_image', None)
            json.dump(results_to_save, f, indent=2)
            
        logger.info(f"Comparison results saved to {filepath}")
        
    except Exception as e:
        logger.error(f"Error saving comparison results: {str(e)}")

def load_recent_comparisons(limit=5):
    """
    Load recent comparison results.
    
    Args:
        limit (int): Maximum number of results to return
        
    Returns:
        list: List of recent comparison results
    """
    try:
        results_dir = os.path.join("results", "comparison")
        if not os.path.exists(results_dir):
            return []
            
        # Get all JSON files in the directory
        files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(results_dir, x)), reverse=True)
        
        # Load the most recent ones
        recent_results = []
        for f in files[:limit]:
            filepath = os.path.join(results_dir, f)
            with open(filepath, 'r') as file:
                result = json.load(file)
                # Add filename and timestamp
                result['filename'] = f
                result['timestamp'] = datetime.fromtimestamp(
                    os.path.getmtime(filepath)
                ).strftime("%Y-%m-%d %H:%M:%S")
                recent_results.append(result)
                
        return recent_results
        
    except Exception as e:
        logger.error(f"Error loading recent comparisons: {str(e)}")
        return [] 