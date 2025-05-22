import os
import pandas as pd
import numpy as np
import logging
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional, Union
from concurrent.futures import ProcessPoolExecutor, as_completed
import joblib
import traceback
from pathlib import Path

# Import strategy factory functions
from strategies import create_strategy, get_default_parameters, AVAILABLE_STRATEGIES
from optimization.file_manager import load_optimization_results, get_latest_optimization_file
# Import logging utility
from signals.log_utils import setup_file_logger
# Import weighting engine for accessing weights
from signals.weighting_engine import load_cached_weights

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_optimized_parameters(strategy_type: str) -> Optional[Dict[str, Any]]:
    """
    Load optimized parameters for a strategy type from optimization results.
    
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

def process_single_asset(
    asset_data: Tuple[str, pd.DataFrame], 
    strategy_config: Tuple[str, str],
    file_logger: logging.Logger,
    weights_dict: Optional[Dict[str, Dict[str, float]]] = None
) -> Dict[str, Any]:
    """
    Process a single asset with a strategy to generate trading signals.
    
    Args:
        asset_data: Tuple of (asset_name, asset_dataframe)
        strategy_config: Tuple of (strategy_type, param_type) where param_type is 'original' or 'optimized'
        file_logger: Logger for detailed logging
        weights_dict: Optional dictionary with weights for each asset-strategy pair
    
    Returns:
        Dictionary with signal information including raw and weighted signals
    """
    asset_name, df = asset_data
    strategy_type, param_type = strategy_config
    
    try:
        # Make a clean copy of the data to avoid potential side effects
        df = df.copy()
        
        # Ensure all required columns exist with the right types
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        
        # Check if all required columns exist
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            file_logger.warning(f"Missing columns for {asset_name}: {missing_cols}. Adding dummy data.")
            # Add missing columns with dummy data
            for col in missing_cols:
                if col == 'date':
                    if len(df) > 0 and 'date' not in df.columns:
                        # Create a date range starting from today and going backwards
                        end_date = datetime.now()
                        start_date = end_date - pd.Timedelta(days=len(df)-1)
                        df['date'] = pd.date_range(start=start_date, end=end_date, periods=len(df))
                elif col in ['open', 'high', 'low', 'close']:
                    # For price columns, use a default value or calculate from other columns
                    if 'close' in df.columns and col != 'close':
                        df[col] = df['close']
                    else:
                        df[col] = 100.0  # Default price
                elif col == 'volume':
                    df[col] = 1000.0  # Default volume
        
        # Ensure data types are correct
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Ensure we have enough data (at least 50 rows)
        if len(df) < 50:
            file_logger.warning(f"Insufficient data for {asset_name} (only {len(df)} rows). Skipping.")
            return {
                'asset': asset_name,
                'strategy': strategy_type,
                'parameters': param_type,
                'signal': 'insufficient_data',
                'weighted_signal_score': 0.0,
                'date': None,
                'error': f"Insufficient data (only {len(df)} rows)"
            }
        
        # Fill any NaN values to prevent calculation errors
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                # Forward fill, then backward fill, then fill with sensible defaults
                df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
                if df[col].isna().any():
                    if col == 'volume':
                        df[col] = df[col].fillna(1000.0)
                    else:
                        df[col] = df[col].fillna(100.0)
        
        # Make sure data is sorted by date
        if 'date' in df.columns:
            df = df.sort_values('date')
        
        # Get the parameters based on parameter type
        try:
            if param_type == 'optimized':
                params = get_optimized_parameters(strategy_type)
                if params is None:
                    param_type = 'original'  # Fall back to original if optimized not available
                    params = get_default_parameters(strategy_type)
            else:
                params = get_default_parameters(strategy_type)
        except Exception as param_error:
            file_logger.error(f"Error getting parameters for {strategy_type}: {str(param_error)}")
            params = {}  # Use empty parameters as fallback
        
        # Prepare data specifically for certain strategies that need additional preprocessing
        try:
            # Add common indicators that strategies might need
            if strategy_type in ['bollinger_breakout', 'atr_breakout', 'donchian_breakout', 'keltner_reversal',
                                'supertrend', 'cci', 'williams_r', 'cmf', 'accum_dist', 'obv_trend', 'vpt_signal']:
                
                # For volatility-based strategies, ensure we have volatility indicators
                if strategy_type in ['bollinger_breakout', 'atr_breakout', 'keltner_reversal', 'supertrend']:
                    from indicators.volatility import add_volatility_indicators
                    df = add_volatility_indicators(df)
                
                # For moving average-based strategies, ensure we have MA calculations
                if strategy_type in ['sma_crossover', 'ema_crossover', 'adaptive_trend', 'supertrend']:
                    from indicators.moving_averages import add_moving_averages
                    df = add_moving_averages(df)
                
                # For momentum-based strategies, ensure we have momentum indicators
                if strategy_type in ['rsi', 'macd_crossover', 'stochastic', 'adx', 'cci', 'williams_r']:
                    from indicators.momentum import add_momentum_indicators
                    df = add_momentum_indicators(df)
                
                # For volume-based strategies, ensure we have volume indicators
                if strategy_type in ['volume_ratio', 'obv_trend', 'vpt_signal', 'cmf', 'accum_dist']:
                    from indicators.volume import add_volume_indicators
                    df = add_volume_indicators(df)
                
                # For candlestick patterns
                if strategy_type in ['candlestick', 'pattern_recognition']:
                    from indicators.candlestick_patterns import add_candlestick_patterns
                    df = add_candlestick_patterns(df)
                
            # For hybrid strategies, ensure all necessary indicators are calculated
            if strategy_type == 'hybrid_momentum_volatility':
                from indicators.volatility import add_volatility_indicators
                from indicators.momentum import add_momentum_indicators
                df = add_volatility_indicators(df)
                df = add_momentum_indicators(df)
                
        except Exception as indicator_error:
            file_logger.warning(f"Error adding indicators for {strategy_type} on {asset_name}: {str(indicator_error)}")
            # Continue anyway, the strategy will add indicators if needed
        
        # Create strategy using the factory
        try:
            strategy = create_strategy(strategy_type, **params)
        except Exception as strategy_error:
            file_logger.error(f"Error creating strategy {strategy_type}: {str(strategy_error)}")
            return {
                'asset': asset_name,
                'strategy': strategy_type,
                'parameters': param_type,
                'signal': 'error',
                'weighted_signal_score': 0.0,
                'date': None,
                'error': f"Strategy creation failed: {str(strategy_error)}"
            }
        
        # Generate signals with timeout protection
        try:
            signals_df = strategy.generate_signals(df)
        except Exception as signals_error:
            file_logger.error(f"Error generating signals for {asset_name} with {strategy_type}: {str(signals_error)}")
            return {
                'asset': asset_name,
                'strategy': strategy_type,
                'parameters': param_type,
                'signal': 'error',
                'weighted_signal_score': 0.0,
                'date': None,
                'error': f"Signal generation failed: {str(signals_error)}"
            }
        
        # Ensure we have a date column
        if 'date' not in signals_df.columns:
            file_logger.error(f"Missing 'date' column in signals_df for {asset_name} with {strategy_type}")
            return {
                'asset': asset_name,
                'strategy': strategy_type,
                'parameters': param_type,
                'signal': 'error',
                'weighted_signal_score': 0.0,
                'date': None,
                'error': "Missing 'date' column in signals_df"
            }
        
        # Get the latest date and signal
        latest_date = signals_df['date'].max()
        latest_row = signals_df[signals_df['date'] == latest_date]
        
        if latest_row.empty:
            file_logger.error(f"No rows found for latest date {latest_date} in signals_df for {asset_name} with {strategy_type}")
            return {
                'asset': asset_name,
                'strategy': strategy_type,
                'parameters': param_type,
                'signal': 'error',
                'weighted_signal_score': 0.0,
                'date': None,
                'error': f"No rows found for latest date {latest_date}"
            }
        
        if 'signal' not in latest_row.columns:
            if 'position' in latest_row.columns:
                # Derive signal from position (0 = no position, 1 = long position)
                if len(signals_df) > 1:
                    prev_position = signals_df.iloc[-2]['position'] if 'position' in signals_df.columns else 0
                    current_position = latest_row['position'].iloc[0]
                    
                    if current_position == 1 and prev_position == 0:
                        latest_signal = 'buy'
                    elif current_position == 0 and prev_position == 1:
                        latest_signal = 'sell'
                    else:
                        latest_signal = 'hold'
                else:
                    latest_signal = 'hold'
            else:
                latest_signal = 'no_signal'  # Unable to determine signal
        else:
            latest_signal = latest_row['signal'].iloc[0]
        
        # Normalize signal
        if latest_signal in [1, '1', 'buy', 'Buy', 'BUY']:
            normalized_signal = 'buy'
        elif latest_signal in [-1, '-1', 'sell', 'Sell', 'SELL']:
            normalized_signal = 'sell'
        else:
            normalized_signal = 'hold'
        
        # Convert signal to numeric value for weighting
        signal_value = 1.0 if normalized_signal == 'buy' else (-1.0 if normalized_signal == 'sell' else 0.0)
        
        # Check if we have weights for this asset and strategy
        weighted_signal_score = 0.0
        weight = 0.0
        
        if weights_dict is not None and asset_name in weights_dict:
            strategy_key = f"{strategy_type}_{param_type}"
            if strategy_key in weights_dict[asset_name]:
                weight = weights_dict[asset_name][strategy_key]
                weighted_signal_score = signal_value * weight
                file_logger.info(f"Applied weight {weight:.4f} to {asset_name} with {strategy_type} ({param_type})")
        
        # Get metrics if available in weights_dict
        metrics = {}
        if weights_dict is not None and asset_name in weights_dict:
            strategy_key = f"{strategy_type}_{param_type}"
            if '_metrics' in weights_dict and asset_name in weights_dict['_metrics'] and strategy_key in weights_dict['_metrics'][asset_name]:
                metrics = weights_dict['_metrics'][asset_name][strategy_key]
                file_logger.info(f"Found metrics for {asset_name} with {strategy_type} ({param_type})")
        
        file_logger.info(f"Generated {normalized_signal} signal for {asset_name} using {strategy_type} ({param_type} parameters) as of {latest_date}, weighted score: {weighted_signal_score:.4f}")
        
        result = {
            'asset': asset_name,
            'strategy': strategy_type,
            'parameters': param_type,
            'signal': normalized_signal,
            'weighted_signal_score': weighted_signal_score,
            'weight': weight,
            'date': latest_date
        }
        
        # Add metrics if available
        if metrics:
            result.update({
                'total_return': metrics.get('total_return', 0.0),
                'sharpe_ratio': metrics.get('sharpe_ratio', 0.0),
                'max_drawdown': metrics.get('max_drawdown', 0.0),
                'win_rate': metrics.get('win_rate', 0.0),
                'num_trades': metrics.get('num_trades', 0)
            })
        
        return result
    except Exception as e:
        error_msg = f"Error processing {asset_name} with {strategy_type}: {str(e)}"
        file_logger.error(error_msg)
        file_logger.error(traceback.format_exc())
        
        return {
            'asset': asset_name,
            'strategy': strategy_type,
            'parameters': param_type,
            'signal': 'error',
            'weighted_signal_score': 0.0,
            'date': None,
            'error': str(e)
        }

def generate_signals_for_assets(
    asset_data_dict: Dict[str, pd.DataFrame],
    strategies: List[Tuple[str, str]],
    max_workers: int = None,
    cache_file: str = None,
    weights_file: str = None
) -> pd.DataFrame:
    """
    Generate signals for multiple assets using multiple strategies in parallel.
    
    Args:
        asset_data_dict: Dictionary with asset names as keys and dataframes as values
        strategies: List of tuples (strategy_type, param_type) to apply
        max_workers: Maximum number of worker processes (defaults to CPU count - 1)
        cache_file: Path to cache results (if None, results are not cached)
        weights_file: Path to weights file (if None, no weights will be applied)
    
    Returns:
        DataFrame with signal information for all assets and strategies
    """
    # Set up logging
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_dir = os.path.join('results', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'screening_log_{timestamp}.txt')
    file_logger = setup_file_logger(log_file)
    
    # Log the request details
    file_logger.info(f"Starting signal generation for {len(asset_data_dict)} assets with {len(strategies)} strategies")
    file_logger.info(f"Strategies requested: {strategies}")
    
    # Load weights if a weights file is provided
    weights_dict = None
    if weights_file:
        file_logger.info(f"Weights file provided: {weights_file}")
        try:
            # Handle different path formats - convert backslashes to forward slashes
            normalized_weights_file = weights_file.replace('\\', '/')
            file_logger.info(f"Normalized weights file path: {normalized_weights_file}")
            
            # If the file doesn't exist as-is, try to find it in the results/signals directory
            if not os.path.exists(normalized_weights_file):
                # Extract filename and look in results/signals
                weights_filename = os.path.basename(normalized_weights_file)
                weights_in_signals_dir = os.path.join('results', 'signals', weights_filename)
                file_logger.info(f"Trying alternative path: {weights_in_signals_dir}")
                
                if os.path.exists(weights_in_signals_dir):
                    normalized_weights_file = weights_in_signals_dir
                    file_logger.info(f"Found weights file at: {normalized_weights_file}")
                else:
                    file_logger.error(f"Weights file not found at either location: {weights_file} or {weights_in_signals_dir}")
                    normalized_weights_file = None
            
            if normalized_weights_file:
                weights_df = load_cached_weights(normalized_weights_file)
                if weights_df is not None:
                    # Convert DataFrame to dictionary for faster lookups
                    file_logger.info(f"Successfully loaded weights from {normalized_weights_file} with {len(weights_df)} rows")
                    
                    # Create a dictionary structure for easy lookup
                    weights_dict = {}
                    # Initialize _metrics key for metrics storage
                    weights_dict['_metrics'] = {}
                    
                    for _, row in weights_df.iterrows():
                        asset = row['asset']
                        strategy = row['strategy']
                        parameters = row['parameters']
                        weight = row['weight']
                        strategy_key = f"{strategy}_{parameters}"
                        
                        # Initialize asset entries if needed
                        if asset not in weights_dict:
                            weights_dict[asset] = {}
                        if asset not in weights_dict['_metrics']:
                            weights_dict['_metrics'][asset] = {}
                        
                        # Store the weight
                        weights_dict[asset][strategy_key] = weight
                        file_logger.info(f"Added weight for {asset} - {strategy_key}: {weight}")
                        
                        # Store metrics if available
                        metrics = {}
                        for metric in ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'num_trades']:
                            if metric in row and not pd.isna(row[metric]):
                                metrics[metric] = row[metric]
                        
                        if metrics:
                            weights_dict['_metrics'][asset][strategy_key] = metrics
                    
                    file_logger.info(f"Prepared weights for {len(weights_dict) - 1} assets")  # -1 for _metrics key
                    file_logger.info(f"Weights dictionary keys: {list(weights_dict.keys())}")
                else:
                    file_logger.warning(f"No weights loaded from {normalized_weights_file}. Will use unweighted signals.")
        except Exception as e:
            file_logger.error(f"Error loading weights from {weights_file}: {str(e)}")
            file_logger.error(traceback.format_exc())
            weights_dict = None
    else:
        file_logger.info("No weights file provided. Using unweighted signals.")
    
    # Strategy performance tracking
    strategy_stats = {s[0]: {'total': 0, 'success': 0, 'error': 0} for s in strategies}
    
    # Process in smaller batches to prevent overwhelming the system
    # Split strategies into manageable chunks (max 3 per batch)
    strategy_batches = [strategies[i:i+3] for i in range(0, len(strategies), 3)]
    file_logger.info(f"Processing strategies in {len(strategy_batches)} batches")
    
    # If max_workers is not specified, use a more conservative number
    # to prevent system overload (min of 2, max of CPU count / 2)
    if max_workers is None:
        max_workers = max(2, min(4, joblib.cpu_count() // 2))
    
    file_logger.info(f"Using {max_workers} worker processes")
    
    # Initialize all_results list
    all_results = []
    
    # Process each batch of strategies
    for batch_idx, strategy_batch in enumerate(strategy_batches):
        file_logger.info(f"Processing batch {batch_idx+1}/{len(strategy_batches)}: {strategy_batch}")
        
        # Prepare tasks list for this batch
        tasks = []
        for asset_name, asset_df in asset_data_dict.items():
            for strategy_config in strategy_batch:
                strategy_type = strategy_config[0]
                strategy_stats[strategy_type]['total'] += 1
                tasks.append((
                    (asset_name, asset_df),
                    strategy_config,
                    file_logger,
                    weights_dict
                ))
        
        batch_results = []
        
        try:
            # Use joblib for parallel processing with a timeout
            batch_results = joblib.Parallel(n_jobs=max_workers, timeout=300, verbose=10)(
                joblib.delayed(process_single_asset)(*task_args)
                for task_args in tasks
            )
            
        except Exception as e:
            file_logger.error(f"Error in parallel processing batch {batch_idx+1}: {str(e)}")
            file_logger.error(traceback.format_exc())
            
            # Fall back to sequential processing for this batch
            file_logger.info(f"Falling back to sequential processing for batch {batch_idx+1}")
            for task_args in tasks:
                try:
                    result = process_single_asset(*task_args)
                    batch_results.append(result)
                except Exception as item_error:
                    file_logger.error(f"Error in sequential processing: {str(item_error)}")
                    strategy_type = task_args[1][0]
                    strategy_stats[strategy_type]['error'] += 1
                    
                    # Add error result
                    batch_results.append({
                        'asset': task_args[0][0],
                        'strategy': task_args[1][0],
                        'parameters': task_args[1][1],
                        'signal': 'error',
                        'weighted_signal_score': 0.0,
                        'date': None,
                        'error': str(item_error)
                    })
        
        # Update strategy statistics
        for result in batch_results:
            strategy = result['strategy']
            if result['signal'] not in ['error', 'insufficient_data', 'no_signal']:
                strategy_stats[strategy]['success'] += 1
            else:
                strategy_stats[strategy]['error'] += 1
        
        # Add batch results to all results
        all_results.extend(batch_results)
        file_logger.info(f"Completed batch {batch_idx+1} with {len(batch_results)} results")
        
        # Print interim strategy statistics
        _log_strategy_statistics(file_logger, strategy_stats)
    
    # Create DataFrame from all results
    signals_df = pd.DataFrame(all_results)
    
    # Cache results if cache_file is specified
    if cache_file and not signals_df.empty:
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            
            # Save to parquet file
            signals_df.to_parquet(cache_file, index=False)
            file_logger.info(f"Cached results to {cache_file}")
        except Exception as e:
            file_logger.error(f"Error caching results: {str(e)}")
    
    # Log summary
    _log_signals_summary(file_logger, signals_df, strategy_stats)
    
    return signals_df

def _log_strategy_statistics(logger, strategy_stats):
    """Log statistics about each strategy's performance"""
    logger.info("=" * 50)
    logger.info("STRATEGY STATISTICS:")
    logger.info("-" * 50)
    
    # Calculate total stats
    total_runs = sum(stats['total'] for stats in strategy_stats.values())
    total_success = sum(stats['success'] for stats in strategy_stats.values())
    total_error = sum(stats['error'] for stats in strategy_stats.values())
    success_rate = (total_success / total_runs * 100) if total_runs > 0 else 0
    
    # Format as a table with success rates
    logger.info(f"{'Strategy':<25} {'Success':<10} {'Error':<10} {'Total':<10} {'Rate %':<10}")
    logger.info("-" * 65)
    
    # Sort strategies by success rate (descending)
    sorted_strategies = sorted(
        strategy_stats.items(),
        key=lambda x: (x[1]['success'] / x[1]['total'] if x[1]['total'] > 0 else 0),
        reverse=True
    )
    
    for strategy, stats in sorted_strategies:
        success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        logger.info(f"{strategy:<25} {stats['success']:<10} {stats['error']:<10} {stats['total']:<10} {success_rate:.1f}%")
    
    logger.info("-" * 65)
    logger.info(f"{'TOTAL':<25} {total_success:<10} {total_error:<10} {total_runs:<10} {success_rate:.1f}%")
    logger.info("=" * 50)

def _log_signals_summary(logger, signals_df, strategy_stats):
    """Log a summary of the generated signals"""
    if signals_df.empty:
        logger.error("No signals were generated!")
        return
    
    # Count signals by type
    buy_count = len(signals_df[signals_df['signal'] == 'buy'])
    sell_count = len(signals_df[signals_df['signal'] == 'sell'])
    hold_count = len(signals_df[signals_df['signal'] == 'hold'])
    error_count = len(signals_df[signals_df['signal'].isin(['error', 'insufficient_data', 'no_signal'])])
    
    # Count successful strategies
    successful_strategies = signals_df[~signals_df['signal'].isin(['error', 'insufficient_data', 'no_signal'])]['strategy'].nunique()
    total_strategies = len(strategy_stats)
    
    # Count signals by weighted score
    if 'weighted_signal_score' in signals_df.columns:
        weighted_buy_count = len(signals_df[signals_df['weighted_signal_score'] > 0.5])
        weighted_sell_count = len(signals_df[signals_df['weighted_signal_score'] < -0.5])
        weighted_hold_count = len(signals_df[(signals_df['weighted_signal_score'] >= -0.5) & (signals_df['weighted_signal_score'] <= 0.5)])
        
        logger.info(f"Weighted Buy signals: {weighted_buy_count}")
        logger.info(f"Weighted Sell signals: {weighted_sell_count}")
        logger.info(f"Weighted Hold signals: {weighted_hold_count}")
    
    logger.info("=" * 50)
    logger.info("SIGNAL GENERATION SUMMARY")
    logger.info("-" * 50)
    logger.info(f"Total signals: {len(signals_df)}")
    logger.info(f"Buy signals: {buy_count}")
    logger.info(f"Sell signals: {sell_count}")
    logger.info(f"Hold signals: {hold_count}")
    logger.info(f"Error signals: {error_count}")
    logger.info(f"Successful strategies: {successful_strategies} out of {total_strategies}")
    
    # If there are errors, log the most common error types
    if error_count > 0 and 'error' in signals_df.columns:
        error_df = signals_df[signals_df['signal'] == 'error']
        if not error_df.empty:
            common_errors = error_df['error'].value_counts().head(5)
            logger.info("-" * 50)
            logger.info("MOST COMMON ERRORS:")
            for error, count in common_errors.items():
                logger.info(f"{count} occurrences: {error}")
    
    logger.info("=" * 50)

def load_cached_signals(cache_file: str) -> Optional[pd.DataFrame]:
    """
    Load signals from a cached parquet file.
    
    Args:
        cache_file: Path to the cached parquet file
        
    Returns:
        DataFrame with signals or None if file doesn't exist or cannot be read
    """
    if not os.path.exists(cache_file):
        return None
    
    try:
        signals_df = pd.read_parquet(cache_file)
        return signals_df
    except Exception as e:
        logger.error(f"Error loading cached signals: {str(e)}")
        return None

def get_latest_signals_file() -> Optional[str]:
    """
    Get the path to the latest signals file.
    
    Returns:
        Path to the latest signals file or None if no file exists
    """
    signals_dir = os.path.join('results', 'signals')
    if not os.path.exists(signals_dir):
        return None
    
    signal_files = [os.path.join(signals_dir, f) for f in os.listdir(signals_dir) 
                   if f.startswith('signals_') and f.endswith('.parquet')]
    
    if not signal_files:
        return None
    
    # Sort by modification time (newest first)
    signal_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    return signal_files[0]

if __name__ == "__main__":
    # Example usage
    from data.data_loader import DataLoader
    
    # Load multi-asset data
    data_loader = DataLoader("data/test multidata.xlsx")
    multi_asset_data = data_loader.load_multi_asset_excel()
    
    # Define strategies to apply
    strategies_to_apply = [
        ("trend_following", "original"),
        ("mean_reversion", "optimized"),
        ("breakout", "original")
    ]
    
    # Generate timestamp for the cache file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    cache_file = os.path.join('results', 'signals', f'signals_{timestamp}.parquet')
    
    # Get latest weights file
    from signals.weighting_engine import get_latest_weights_file
    weights_file = get_latest_weights_file()
    
    # Generate signals
    signals_df = generate_signals_for_assets(
        multi_asset_data,
        strategies_to_apply,
        max_workers=3,  # Use 3 worker processes
        cache_file=cache_file,
        weights_file=weights_file
    )
    
    print(signals_df.head(10)) 