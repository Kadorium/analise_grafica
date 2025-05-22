import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
from concurrent.futures import ProcessPoolExecutor
import joblib
import traceback
from pathlib import Path
import time

# Import from project modules
from backtesting.backtester import Backtester
from strategies import create_strategy, get_default_parameters
from signals.log_utils import setup_file_logger
from optimization.file_manager import load_optimization_results

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Define lookback periods in days
LOOKBACK_PERIODS = {
    "1 Year": 365,
    "3 Years": 365 * 3,
    "5 Years": 365 * 5
}

# Default weight factors for custom weighting
DEFAULT_WEIGHT_FACTORS = {
    "sharpe_ratio": 0.4,
    "total_return": 0.3,
    "max_drawdown": 0.2,  # Note: will be used as negative factor
    "win_rate": 0.1
}

def setup_backtest_logger() -> logging.Logger:
    """
    Set up a dedicated file logger for weight calculation backtests.
    
    Returns:
        logging.Logger: Configured logger
    """
    log_dir = os.path.join('results', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'screening_log.txt')
    
    return setup_file_logger(log_file)

def apply_lookback_filter(df: pd.DataFrame, lookback_period: str) -> pd.DataFrame:
    """
    Filter dataframe to only include data within the specified lookback period.
    
    Args:
        df: DataFrame with financial data including a 'date' column
        lookback_period: String representing the lookback period ("1 Year", "3 Years", "5 Years")
        
    Returns:
        Filtered DataFrame
    """
    if 'date' not in df.columns:
        logger.warning("DataFrame doesn't have a 'date' column. Cannot apply lookback filter.")
        return df
    
    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    
    # Get days to look back
    days_to_lookback = LOOKBACK_PERIODS.get(lookback_period, LOOKBACK_PERIODS["1 Year"])  # Default to 1 Year
    
    # Calculate the cutoff date
    latest_date = df['date'].max()
    cutoff_date = latest_date - pd.Timedelta(days=days_to_lookback)
    
    # Filter the dataframe
    filtered_df = df[df['date'] >= cutoff_date].copy()
    
    # If the filtered dataframe is too small, warn but return it anyway
    if len(filtered_df) < 50:  # Minimum data points needed
        logger.warning(f"Filtered data has only {len(filtered_df)} rows after applying {lookback_period} lookback.")
    
    return filtered_df

def get_optimized_parameters(strategy_type: str) -> Optional[Dict[str, Any]]:
    """
    Load optimized parameters for a strategy from saved optimization results.
    
    Args:
        strategy_type: Type of strategy
    
    Returns:
        Dictionary of optimized parameters or None if not found
    """
    try:
        # Load the latest optimization results for the strategy type
        optimization_results = load_optimization_results(strategy_type)
        
        if optimization_results and 'optimized_params' in optimization_results:
            return optimization_results['optimized_params']
        elif optimization_results and 'top_results' in optimization_results and optimization_results['top_results']:
            # Get the parameters from the best result
            return optimization_results['top_results'][0]['params']
        
        logger.info(f"No optimization results found for strategy {strategy_type}, will use default parameters")
        return None
    except Exception as e:
        logger.error(f"Error loading optimized parameters for {strategy_type}: {str(e)}")
        return None

def get_cached_backtest_file(asset: str, strategy_type: str, param_type: str) -> Optional[str]:
    """
    Check if a cached backtest file exists for the given asset and strategy.
    
    Args:
        asset: Asset name
        strategy_type: Strategy type
        param_type: 'original' or 'optimized'
        
    Returns:
        Path to the cached file or None if not found
    """
    cache_dir = os.path.join('results', 'backtesting')
    os.makedirs(cache_dir, exist_ok=True)
    
    # List all files in the cache directory
    files = os.listdir(cache_dir)
    
    # Look for matching files
    pattern = f"backtest_{asset}_{strategy_type}_{param_type}"
    matching_files = [f for f in files if f.startswith(pattern) and f.endswith('.parquet')]
    
    if matching_files:
        # Sort by timestamp (assuming files have timestamp in the name)
        matching_files.sort(reverse=True)
        return os.path.join(cache_dir, matching_files[0])
    
    return None

def run_backtest_for_asset(
    asset_name: str,
    asset_data: pd.DataFrame,
    strategy_type: str,
    param_type: str,
    lookback_period: str,
    file_logger: logging.Logger
) -> Dict[str, Any]:
    """
    Run a backtest for a single asset with a specific strategy.
    
    Args:
        asset_name: Name of the asset
        asset_data: DataFrame with price data
        strategy_type: Type of strategy to use
        param_type: 'original' or 'optimized'
        lookback_period: Lookback period to use for backtesting
        file_logger: Logger for detailed logging
        
    Returns:
        Dictionary with backtest results
    """
    try:
        # Check if we have a cached result
        cached_file = get_cached_backtest_file(asset_name, strategy_type, param_type)
        if cached_file and os.path.exists(cached_file):
            try:
                # Load cached results
                cached_results = pd.read_parquet(cached_file)
                file_logger.info(f"Loaded cached backtest results for {asset_name} with {strategy_type} ({param_type})")
                
                # For now, return both the DataFrame and a flag indicating it's from cache
                return {
                    'asset': asset_name,
                    'strategy': strategy_type,
                    'parameters': param_type,
                    'results_df': cached_results,
                    'from_cache': True
                }
            except Exception as cache_error:
                file_logger.warning(f"Error loading cached backtest: {str(cache_error)}. Running new backtest.")
        
        # Apply lookback filter
        filtered_data = apply_lookback_filter(asset_data, lookback_period)
        
        if len(filtered_data) < 50:
            file_logger.warning(f"Insufficient data for {asset_name} with lookback {lookback_period}. Skipping.")
            return {
                'asset': asset_name,
                'strategy': strategy_type,
                'parameters': param_type,
                'error': f"Insufficient data (only {len(filtered_data)} rows after applying lookback)"
            }
        
        # Get strategy parameters
        if param_type == 'optimized':
            params = get_optimized_parameters(strategy_type)
            if params is None:
                param_type = 'original'  # Fall back to original
                params = get_default_parameters(strategy_type)
        else:
            params = get_default_parameters(strategy_type)
            
        # Create strategy
        strategy = create_strategy(strategy_type, **params)
        
        # Initialize backtester
        backtester = Backtester(data=filtered_data, initial_capital=100.0, commission=0.001)
        
        # Run backtest
        backtest_result = backtester.run_backtest(strategy)
        
        # Get the signals DataFrame
        signals_df = backtest_result['signals']
        
        # Add metrics to the result
        metrics = backtest_result['performance_metrics']
        
        # Save results to cache
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        cache_dir = os.path.join('results', 'backtesting')
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"backtest_{asset_name}_{strategy_type}_{param_type}_{timestamp}.parquet")
        signals_df.to_parquet(cache_file)
        
        return {
            'asset': asset_name,
            'strategy': strategy_type,
            'parameters': param_type,
            'results_df': signals_df,
            'metrics': metrics,
            'from_cache': False
        }
    except Exception as e:
        file_logger.error(f"Error in backtest for {asset_name} with {strategy_type}: {str(e)}\n{traceback.format_exc()}")
        return {
            'asset': asset_name,
            'strategy': strategy_type,
            'parameters': param_type,
            'error': f"Backtest failed: {str(e)}"
        }

def calculate_weights_for_goal(
    backtest_results: List[Dict[str, Any]],
    goal_seek_metric: str,
    custom_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Dict[str, float]]:
    """
    Calculate weights for each asset-strategy pair based on the goal-seek metric.
    
    Args:
        backtest_results: List of dictionaries with backtest results
        goal_seek_metric: Metric to use for weighting ('total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'custom')
        custom_weights: Dictionary with custom weight factors (used when goal_seek_metric is 'custom')
        
    Returns:
        Dictionary with asset-strategy pairs as keys and weights as values
    """
    # Filter out failed backtests
    valid_results = [result for result in backtest_results if 'error' not in result]
    
    if not valid_results:
        logger.warning("No valid backtest results to calculate weights")
        return {}
    
    # Extract metrics for weighting
    metrics_data = []
    for result in valid_results:
        # Check if this is an ML signal result
        is_ml_signal = result.get('strategy') == 'LogisticRegression'
        
        # Get metrics either from the metrics key or calculate from results_df
        if 'metrics' in result:
            metrics = result['metrics']
        elif 'results_df' in result and not is_ml_signal:
            # Calculate basic metrics from the results DataFrame (for rule-based strategies)
            df = result['results_df']
            if 'equity' in df.columns:
                total_return = (df['equity'].iloc[-1] / df['equity'].iloc[0]) - 1
                # Simple approximation for other metrics
                max_drawdown = df['drawdown'].max() if 'drawdown' in df.columns else 0.0
                win_count = len(df[df['trade_profit'] > 0]) if 'trade_profit' in df.columns else 0
                total_trades = len(df[df['trade_profit'] != 0]) if 'trade_profit' in df.columns else 1
                win_rate = win_count / total_trades if total_trades > 0 else 0.0
                
                # Simple Sharpe approximation
                if 'equity' in df.columns and len(df) > 1:
                    returns = df['equity'].pct_change().dropna()
                    sharpe_ratio = returns.mean() / returns.std() if returns.std() > 0 else 0.0
                else:
                    sharpe_ratio = 0.0
                
                metrics = {
                    'total_return': total_return,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'win_rate': win_rate
                }
            else:
                # Default metrics if we can't calculate
                metrics = {
                    'total_return': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'win_rate': 0.0
                }
        elif is_ml_signal:
            # For ML signals, use accuracy and create pseudo-metrics
            accuracy = result.get('accuracy', 0.0)
            
            # Convert accuracy to metrics for consistent processing
            # Use accuracy as a proxy for performance
            metrics = {
                'total_return': accuracy * 0.5,  # Scale accuracy to reasonable return range
                'sharpe_ratio': accuracy * 2.0,   # Scale accuracy to reasonable Sharpe range
                'max_drawdown': (1 - accuracy) * 0.1,  # Lower accuracy = higher drawdown
                'win_rate': accuracy,  # Direct mapping
                'accuracy': accuracy  # Keep original accuracy for ML-specific weighting
            }
        else:
            # Skip this result if we can't get metrics
            continue
        
        metrics_data.append({
            'asset': result['asset'],
            'strategy': result['strategy'],
            'parameters': result['parameters'],
            'total_return': metrics.get('total_return', 0.0),
            'sharpe_ratio': metrics.get('sharpe_ratio', 0.0),
            'max_drawdown': metrics.get('max_drawdown', 0.0),
            'win_rate': metrics.get('win_rate', 0.0),
            'num_trades': metrics.get('total_trades', 0),
            'accuracy': metrics.get('accuracy', None),  # For ML signals
            'is_ml': is_ml_signal
        })
    
    # Create DataFrame for easier manipulation
    metrics_df = pd.DataFrame(metrics_data)
    
    if metrics_df.empty:
        logger.warning("No metrics data available for weight calculation")
        return {}
    
    # Calculate weights based on the goal-seek metric
    if goal_seek_metric == 'total_return':
        # Normalize total returns for weighting
        metrics_df['weight'] = metrics_df['total_return']
        
    elif goal_seek_metric == 'sharpe_ratio':
        # Normalize Sharpe ratios for weighting
        metrics_df['weight'] = metrics_df['sharpe_ratio']
        
    elif goal_seek_metric == 'max_drawdown':
        # Inverse max drawdown (lower is better)
        metrics_df['weight'] = 1 / (metrics_df['max_drawdown'] + 1e-6)
        
    elif goal_seek_metric == 'win_rate':
        # Normalize win rates for weighting
        metrics_df['weight'] = metrics_df['win_rate']
        
    elif goal_seek_metric == 'custom':
        # Use custom weighting formula
        weight_factors = custom_weights if custom_weights else DEFAULT_WEIGHT_FACTORS
        
        # Normalize each metric first
        for metric in ['sharpe_ratio', 'total_return', 'win_rate']:
            max_val = metrics_df[metric].max()
            if max_val > 0:
                metrics_df[f'{metric}_norm'] = metrics_df[metric] / max_val
            else:
                metrics_df[f'{metric}_norm'] = 0.0
        
        # For max_drawdown, lower is better, so invert
        max_dd = metrics_df['max_drawdown'].max()
        if max_dd > 0:
            metrics_df['max_drawdown_norm'] = 1 - (metrics_df['max_drawdown'] / max_dd)
        else:
            metrics_df['max_drawdown_norm'] = 1.0
        
        # Apply custom formula
        metrics_df['weight'] = (
            weight_factors.get('sharpe_ratio', 0.4) * metrics_df['sharpe_ratio_norm'] +
            weight_factors.get('total_return', 0.3) * metrics_df['total_return_norm'] +
            weight_factors.get('max_drawdown', 0.2) * metrics_df['max_drawdown_norm'] +
            weight_factors.get('win_rate', 0.1) * metrics_df['win_rate_norm']
        )
    else:
        # Default to equal weighting
        logger.warning(f"Unknown goal-seek metric: {goal_seek_metric}. Using equal weights.")
        metrics_df['weight'] = 1.0
    
    # Apply ML accuracy multiplier for ML signals
    ml_mask = metrics_df['is_ml'] == True
    if ml_mask.any():
        # For ML signals, multiply the base weight by accuracy to give higher weight to more accurate models
        metrics_df.loc[ml_mask, 'weight'] = metrics_df.loc[ml_mask, 'weight'] * metrics_df.loc[ml_mask, 'accuracy']
        logger.info(f"Applied accuracy multiplier to {ml_mask.sum()} ML signal weights")
    
    # Handle negative weights (make them small positive values)
    metrics_df.loc[metrics_df['weight'] < 0, 'weight'] = 1e-6
    
    # Normalize weights per asset to sum to 1
    asset_weights = {}
    for asset in metrics_df['asset'].unique():
        asset_df = metrics_df[metrics_df['asset'] == asset].copy()
        
        # Skip assets with all zero weights
        if asset_df['weight'].sum() <= 0:
            # Assign equal weights in this case
            asset_df['normalized_weight'] = 1.0 / len(asset_df)
        else:
            # Normalize to sum to 1
            asset_df['normalized_weight'] = asset_df['weight'] / asset_df['weight'].sum()
        
        # Create a dictionary for this asset
        asset_weights[asset] = {}
        for _, row in asset_df.iterrows():
            strategy_key = f"{row['strategy']}_{row['parameters']}"
            asset_weights[asset][strategy_key] = row['normalized_weight']
    
    return asset_weights

def process_asset_batch(
    asset_batch: List[Tuple[str, pd.DataFrame]],
    strategies: List[Tuple[str, str]],
    lookback_period: str,
    file_logger: logging.Logger
) -> List[Dict[str, Any]]:
    """
    Process a batch of assets with the specified strategies.
    
    Args:
        asset_batch: List of (asset_name, asset_data) tuples
        strategies: List of (strategy_type, param_type) tuples
        lookback_period: Lookback period for backtesting
        file_logger: Logger for detailed logging
        
    Returns:
        List of dictionaries with backtest results
    """
    results = []
    
    for asset_name, asset_data in asset_batch:
        for strategy_type, param_type in strategies:
            result = run_backtest_for_asset(
                asset_name=asset_name,
                asset_data=asset_data,
                strategy_type=strategy_type,
                param_type=param_type,
                lookback_period=lookback_period,
                file_logger=file_logger
            )
            results.append(result)
    
    return results

def calculate_asset_weights(
    asset_data_dict: Dict[str, pd.DataFrame],
    strategies: List[Tuple[str, str]],
    goal_seek_metric: str = 'sharpe_ratio',
    custom_weights: Optional[Dict[str, float]] = None,
    lookback_period: str = '1 Year',
    max_workers: int = None,
    cache_results: bool = True,
    return_metrics: bool = False
) -> Union[Dict[str, Dict[str, float]], Dict[str, Any]]:
    """
    Calculate performance-based weights for each asset-strategy pair.
    
    Args:
        asset_data_dict: Dictionary with asset names as keys and DataFrames as values
        strategies: List of (strategy_type, param_type) tuples to apply
        goal_seek_metric: Metric to use for weighting ('total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'custom')
        custom_weights: Dictionary with custom weight factors (used when goal_seek_metric is 'custom')
        lookback_period: Period to look back for backtesting ('1 Year', '3 Years', '5 Years')
        max_workers: Maximum number of worker processes (defaults to CPU count - 1)
        cache_results: Whether to cache backtest results to disk
        return_metrics: Whether to return metrics along with weights
        
    Returns:
        Dictionary with asset weights by strategy, or if return_metrics is True, a dictionary with weights and metrics
    """
    # Setup logger
    file_logger = setup_backtest_logger()
    file_logger.info(f"Starting weight calculation for {len(asset_data_dict)} assets with {len(strategies)} strategies")
    file_logger.info(f"Goal-seek metric: {goal_seek_metric}, Lookback period: {lookback_period}")
    
    # Validate inputs
    if not asset_data_dict:
        error_msg = "No asset data provided for weight calculation"
        file_logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not strategies:
        error_msg = "No strategies provided for weight calculation"
        file_logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Validate goal_seek_metric
    valid_metrics = ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'custom']
    if goal_seek_metric not in valid_metrics:
        error_msg = f"Invalid goal-seek metric: {goal_seek_metric}. Valid options are: {', '.join(valid_metrics)}"
        file_logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Validate custom weights if using custom metric
    if goal_seek_metric == 'custom':
        if not custom_weights:
            custom_weights = DEFAULT_WEIGHT_FACTORS
            file_logger.warning(f"No custom weights provided for 'custom' goal-seek metric. Using defaults: {custom_weights}")
        else:
            # Check if all required weights are present
            required_weights = ['sharpe_ratio', 'total_return', 'max_drawdown', 'win_rate']
            missing_weights = [w for w in required_weights if w not in custom_weights]
            
            if missing_weights:
                for missing in missing_weights:
                    custom_weights[missing] = DEFAULT_WEIGHT_FACTORS.get(missing, 0.0)
                file_logger.warning(f"Missing weights: {missing_weights}. Using defaults for these: {custom_weights}")
            
            # Check if weights sum to approximately 1
            weights_sum = sum(custom_weights.values())
            if abs(weights_sum - 1.0) > 0.01:  # Allow 1% tolerance
                # Normalize the weights
                for key in custom_weights:
                    custom_weights[key] = custom_weights[key] / weights_sum
                file_logger.warning(f"Custom weights did not sum to 1.0 (sum: {weights_sum}). Normalized to: {custom_weights}")
    
    # Validate lookback_period
    valid_lookbacks = ['1 Year', '3 Years', '5 Years']
    if lookback_period not in valid_lookbacks:
        error_msg = f"Invalid lookback period: {lookback_period}. Valid options are: {', '.join(valid_lookbacks)}"
        file_logger.error(error_msg)
        raise ValueError(error_msg)
    
    start_time = time.time()
    
    # If max_workers is not specified, use CPU count - 1 (leave one core free)
    if max_workers is None:
        max_workers = max(1, joblib.cpu_count() - 1)
    
    # Convert asset dictionary to list of tuples for processing
    asset_tuples = [(name, data) for name, data in asset_data_dict.items()]
    
    # For very large datasets, process in batches
    batch_size = 10  # Process 10 assets at a time
    asset_batches = [asset_tuples[i:i + batch_size] for i in range(0, len(asset_tuples), batch_size)]
    
    all_results = []
    
    try:
        # Process batches in parallel
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {
                executor.submit(
                    process_asset_batch, 
                    batch, 
                    strategies, 
                    lookback_period, 
                    file_logger
                ): i for i, batch in enumerate(asset_batches)
            }
            
            for i, future in enumerate(future_to_batch):
                try:
                    batch_results = future.result()
                    all_results.extend(batch_results)
                    
                    # Log progress
                    batch_idx = future_to_batch[future]
                    progress = (batch_idx + 1) / len(asset_batches) * 100
                    file_logger.info(f"Processed batch {batch_idx + 1}/{len(asset_batches)} ({progress:.1f}%)")
                    
                except Exception as e:
                    file_logger.error(f"Error processing batch: {str(e)}")
    except Exception as e:
        file_logger.error(f"Parallel processing failed: {str(e)}. Falling back to sequential processing.")
        
        # Fall back to sequential processing
        for batch in asset_batches:
            try:
                batch_results = process_asset_batch(batch, strategies, lookback_period, file_logger)
                all_results.extend(batch_results)
            except Exception as batch_error:
                file_logger.error(f"Error processing batch sequentially: {str(batch_error)}")
    
    # Calculate weights based on backtest results
    weights = calculate_weights_for_goal(all_results, goal_seek_metric, custom_weights)
    
    # Collect metrics for each asset-strategy pair
    metrics_data = {}
    for result in all_results:
        if 'error' in result:
            continue
            
        asset = result['asset']
        strategy = result['strategy']
        param_type = result['parameters']
        strategy_key = f"{strategy}_{param_type}"
        
        if asset not in metrics_data:
            metrics_data[asset] = {}
            
        if 'metrics' in result:
            # Get metrics from the backtest result
            metrics = result['metrics']
            metrics_data[asset][strategy_key] = {
                'total_return': metrics.get('total_return', 0.0),
                'sharpe_ratio': metrics.get('sharpe_ratio', 0.0),
                'max_drawdown': metrics.get('max_drawdown', 0.0),
                'win_rate': metrics.get('win_rate', 0.0),
                'num_trades': metrics.get('total_trades', 0)
            }
        elif 'results_df' in result:
            # Calculate basic metrics from the results DataFrame
            df = result['results_df']
            if 'equity' in df.columns:
                total_return = (df['equity'].iloc[-1] / df['equity'].iloc[0]) - 1
                # Simple approximation for other metrics
                max_drawdown = df['drawdown'].max() if 'drawdown' in df.columns else 0.0
                
                # Count trades accurately
                trade_count = 0
                if 'trade_profit' in df.columns:
                    # Count non-zero trade profits as completed trades
                    trade_count = len(df[df['trade_profit'] != 0])
                elif 'position' in df.columns:
                    # Count position changes as trades
                    position_changes = df['position'].diff().abs()
                    trade_count = int(position_changes.sum())
                
                win_count = len(df[df['trade_profit'] > 0]) if 'trade_profit' in df.columns else 0
                win_rate = win_count / trade_count if trade_count > 0 else 0.0
                
                # Simple Sharpe approximation
                if 'equity' in df.columns and len(df) > 1:
                    returns = df['equity'].pct_change().dropna()
                    sharpe_ratio = returns.mean() / returns.std() if returns.std() > 0 else 0.0
                else:
                    sharpe_ratio = 0.0
                
                metrics_data[asset][strategy_key] = {
                    'total_return': total_return,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'win_rate': win_rate,
                    'num_trades': trade_count
                }
    
    # Cache weights if requested
    if cache_results:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        cache_dir = os.path.join('results', 'signals')
        os.makedirs(cache_dir, exist_ok=True)
        
        # Convert weights to DataFrame for saving
        weights_rows = []
        for asset, strategy_weights in weights.items():
            for strategy, weight in strategy_weights.items():
                strategy_parts = strategy.split('_')
                strategy_type = '_'.join(strategy_parts[:-1])  # Join all parts except the last one
                param_type = strategy_parts[-1]
                
                # Add metrics if available
                metrics_dict = {}
                if asset in metrics_data and strategy in metrics_data[asset]:
                    metrics_dict = metrics_data[asset][strategy]
                
                row_data = {
                    'asset': asset,
                    'strategy': strategy_type,
                    'parameters': param_type,
                    'weight': weight,
                    'goal_metric': goal_seek_metric,
                    'lookback_period': lookback_period
                }
                
                # Add metrics to the row
                if metrics_dict:
                    row_data.update({
                        'total_return': metrics_dict.get('total_return', 0.0),
                        'sharpe_ratio': metrics_dict.get('sharpe_ratio', 0.0),
                        'max_drawdown': metrics_dict.get('max_drawdown', 0.0),
                        'win_rate': metrics_dict.get('win_rate', 0.0),
                        'num_trades': metrics_dict.get('num_trades', 0)
                    })
                
                weights_rows.append(row_data)
        
        weights_df = pd.DataFrame(weights_rows)
        weights_file = os.path.join(cache_dir, f"weights_{timestamp}.parquet")
        weights_df.to_parquet(weights_file)
        
        file_logger.info(f"Weights saved to {weights_file}")
    
    elapsed_time = time.time() - start_time
    file_logger.info(f"Weight calculation completed in {elapsed_time:.2f} seconds")
    
    if return_metrics:
        return {
            "weights": weights,
            "metrics": metrics_data
        }
    else:
        return weights

# Helper function to get cached weights
def get_latest_weights_file() -> Optional[str]:
    """
    Get the path to the most recent weights file.
    
    Returns:
        Path to the weights file or None if not found
    """
    cache_dir = os.path.join('results', 'signals')
    if not os.path.exists(cache_dir):
        return None
    
    # List all weight files
    files = [f for f in os.listdir(cache_dir) if f.startswith('weights_') and f.endswith('.parquet')]
    
    if not files:
        return None
    
    # Sort by timestamp (assuming files have timestamp in the name)
    files.sort(reverse=True)
    
    return os.path.join(cache_dir, files[0])

def load_cached_weights(file_path: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Load cached weights from a Parquet file.
    
    Args:
        file_path: Path to the weights file or None to use the latest file
        
    Returns:
        DataFrame with weights or None if file not found
    """
    if file_path is None:
        file_path = get_latest_weights_file()
    
    if not file_path or not os.path.exists(file_path):
        return None
    
    try:
        return pd.read_parquet(file_path)
    except Exception as e:
        logger.error(f"Error loading weights file {file_path}: {str(e)}")
        return None 