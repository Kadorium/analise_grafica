import os
import pandas as pd
import numpy as np
import logging
import pickle
import joblib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings
from pathlib import Path

# Machine learning imports
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.exceptions import ConvergenceWarning

# Import indicators modules
from indicators.momentum import add_momentum_indicators
from indicators.moving_averages import add_moving_averages  
from indicators.volatility import add_volatility_indicators
from indicators.volume import add_volume_indicators

# Import logging utility
from signals.log_utils import setup_file_logger

# Suppress sklearn convergence warnings for cleaner logs
warnings.filterwarnings('ignore', category=ConvergenceWarning)

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_features(df: pd.DataFrame, file_logger: logging.Logger) -> pd.DataFrame:
    """
    Create features for ML model including lagged returns and technical indicators.
    
    Args:
        df: DataFrame with OHLCV data
        file_logger: Logger for detailed logging
        
    Returns:
        DataFrame with features added
    """
    try:
        # Make a copy to avoid modifying original data
        df = df.copy()
        
        # Ensure we have the required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                file_logger.warning(f"Missing column {col}, filling with close price")
                df[col] = df.get('close', 100.0)
        
        # Sort by date to ensure correct order
        if 'date' in df.columns:
            df = df.sort_values('date').reset_index(drop=True)
        
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        
        # Create lagged returns (1-5 days)
        for lag in range(1, 6):
            df[f'returns_lag_{lag}'] = df['returns'].shift(lag)
        
        # Add technical indicators
        try:
            df = add_momentum_indicators(df)
            file_logger.info("Added momentum indicators")
        except Exception as e:
            file_logger.warning(f"Error adding momentum indicators: {str(e)}")
        
        try:
            df = add_moving_averages(df)
            file_logger.info("Added moving average indicators")
        except Exception as e:
            file_logger.warning(f"Error adding moving average indicators: {str(e)}")
        
        try:
            df = add_volatility_indicators(df)
            file_logger.info("Added volatility indicators")
        except Exception as e:
            file_logger.warning(f"Error adding volatility indicators: {str(e)}")
        
        try:
            df = add_volume_indicators(df)
            file_logger.info("Added volume indicators")
        except Exception as e:
            file_logger.warning(f"Error adding volume indicators: {str(e)}")
        
        # Add additional derived features
        try:
            # Price change features
            df['price_change'] = df['close'] - df['open']
            df['price_change_pct'] = df['price_change'] / df['open']
            
            # High-Low range
            df['hl_range'] = (df['high'] - df['low']) / df['close']
            
            # Volume change
            df['volume_change'] = df['volume'].pct_change()
            
            # Moving averages of volume
            df['volume_sma_5'] = df['volume'].rolling(window=5).mean()
            df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma_20']
            
            file_logger.info("Added derived features")
        except Exception as e:
            file_logger.warning(f"Error adding derived features: {str(e)}")
        
        return df
        
    except Exception as e:
        file_logger.error(f"Error creating features: {str(e)}")
        return df

def create_target_variable(df: pd.DataFrame, file_logger: logging.Logger, 
                          lookback_days: int = 5, threshold: float = 0.02) -> pd.DataFrame:
    """
    Create target variable for ML model based on future returns.
    
    Args:
        df: DataFrame with price data
        file_logger: Logger for detailed logging
        lookback_days: Number of days to look ahead for target
        threshold: Minimum return threshold for buy/sell signals
        
    Returns:
        DataFrame with target variable added
    """
    try:
        # Calculate future returns
        df['future_returns'] = df['close'].shift(-lookback_days) / df['close'] - 1
        
        # Create target variable (0 = sell/hold, 1 = buy)
        # Buy signal if future return > threshold
        # Sell signal if future return < -threshold  
        # Hold otherwise
        df['target'] = 0  # Default to hold/sell
        df.loc[df['future_returns'] > threshold, 'target'] = 1  # Buy signal
        
        # Remove rows where we can't calculate future returns
        df = df.dropna(subset=['future_returns'])
        
        file_logger.info(f"Created target variable with {df['target'].sum()} buy signals out of {len(df)} samples")
        
        return df
        
    except Exception as e:
        file_logger.error(f"Error creating target variable: {str(e)}")
        return df

def select_features(df: pd.DataFrame, file_logger: logging.Logger) -> List[str]:
    """
    Select relevant features for ML model, excluding non-predictive columns.
    
    Args:
        df: DataFrame with all features
        file_logger: Logger for detailed logging
        
    Returns:
        List of feature column names
    """
    try:
        # Exclude non-predictive columns
        exclude_cols = [
            'date', 'open', 'high', 'low', 'close', 'volume', 
            'returns', 'future_returns', 'target'
        ]
        
        # Get all numeric columns that aren't excluded
        feature_cols = [col for col in df.columns 
                       if col not in exclude_cols and df[col].dtype in ['float64', 'int64']]
        
        # Remove columns with too many NaN values (>50%)
        valid_features = []
        for col in feature_cols:
            nan_pct = df[col].isna().sum() / len(df)
            if nan_pct < 0.5:  # Keep columns with <50% NaN
                valid_features.append(col)
            else:
                file_logger.warning(f"Excluding feature {col} due to {nan_pct:.1%} NaN values")
        
        file_logger.info(f"Selected {len(valid_features)} features: {valid_features[:10]}...")
        return valid_features
        
    except Exception as e:
        file_logger.error(f"Error selecting features: {str(e)}")
        return []

def train_ml_model(asset_name: str, df: pd.DataFrame, file_logger: logging.Logger) -> Dict[str, Any]:
    """
    Train logistic regression model for a single asset.
    
    Args:
        asset_name: Name of the asset
        df: DataFrame with features and target
        file_logger: Logger for detailed logging
        
    Returns:
        Dictionary with model, scaler, accuracy, and signal information
    """
    try:
        file_logger.info(f"Training ML model for {asset_name}")
        
        # Create features and target
        df = create_features(df, file_logger)
        df = create_target_variable(df, file_logger)
        
        # Check if we have enough data
        if len(df) < 100:
            file_logger.warning(f"Insufficient data for {asset_name}: only {len(df)} samples")
            return {
                'asset': asset_name,
                'strategy': 'LogisticRegression',
                'parameters': 'ML',
                'signal': 'insufficient_data',
                'date': None,
                'accuracy': 0.0,
                'error': 'Insufficient data for training'
            }
        
        # Select features
        feature_cols = select_features(df, file_logger)
        if not feature_cols:
            file_logger.error(f"No valid features found for {asset_name}")
            return {
                'asset': asset_name,
                'strategy': 'LogisticRegression', 
                'parameters': 'ML',
                'signal': 'no_features',
                'date': None,
                'accuracy': 0.0,
                'error': 'No valid features available'
            }
        
        # Prepare data
        X = df[feature_cols].fillna(0)  # Fill remaining NaN with 0
        y = df['target']
        
        # Check target distribution
        target_dist = y.value_counts()
        if len(target_dist) < 2:
            file_logger.warning(f"Insufficient target diversity for {asset_name}: {target_dist.to_dict()}")
            return {
                'asset': asset_name,
                'strategy': 'LogisticRegression',
                'parameters': 'ML', 
                'signal': 'insufficient_diversity',
                'date': None,
                'accuracy': 0.0,
                'error': 'Insufficient target diversity'
            }
        
        # Split data (70/30 train/test) - use time series split to avoid lookahead bias
        split_idx = int(len(X) * 0.7)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train logistic regression model
        model = LogisticRegression(
            random_state=42,
            max_iter=1000,
            class_weight='balanced'  # Handle class imbalance
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Calculate accuracy
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Generate signal for the latest date
        latest_idx = len(df) - 1
        latest_features = X.iloc[latest_idx:latest_idx+1]
        latest_features_scaled = scaler.transform(latest_features)
        
        signal_prob = model.predict_proba(latest_features_scaled)[0]
        signal_pred = model.predict(latest_features_scaled)[0]
        
        # Convert to buy/sell/hold signal
        if signal_pred == 1 and signal_prob[1] > 0.6:  # High confidence buy
            signal = 'buy'
        elif signal_pred == 0 and signal_prob[0] > 0.6:  # High confidence sell/hold
            signal = 'sell'
        else:
            signal = 'hold'  # Low confidence
        
        # Get latest date
        latest_date = df['date'].iloc[-1] if 'date' in df.columns else datetime.now().date()
        
        file_logger.info(f"ML model for {asset_name}: signal={signal}, accuracy={accuracy:.3f}")
        
        return {
            'asset': asset_name,
            'strategy': 'LogisticRegression',
            'parameters': 'ML',
            'signal': signal,
            'date': latest_date,
            'accuracy': accuracy,
            'model': model,
            'scaler': scaler,
            'feature_cols': feature_cols,
            'signal_probability': signal_prob.tolist()
        }
        
    except Exception as e:
        error_msg = f"Error training ML model for {asset_name}: {str(e)}"
        file_logger.error(error_msg)
        return {
            'asset': asset_name,
            'strategy': 'LogisticRegression',
            'parameters': 'ML',
            'signal': 'error',
            'date': None,
            'accuracy': 0.0,
            'error': str(e)
        }

def generate_ml_signals(asset_data_dict: Dict[str, pd.DataFrame], 
                       max_workers: int = None,
                       cache_models: bool = True) -> pd.DataFrame:
    """
    Generate ML signals for multiple assets using parallel processing.
    
    Args:
        asset_data_dict: Dictionary with asset names as keys and dataframes as values
        max_workers: Maximum number of worker processes
        cache_models: Whether to cache trained models
        
    Returns:
        DataFrame with ML signals for all assets
    """
    # Set up logging
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_dir = os.path.join('results', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'ml_signals_log_{timestamp}.txt')
    file_logger = setup_file_logger(log_file)
    
    file_logger.info(f"Starting ML signal generation for {len(asset_data_dict)} assets")
    
    # Set up parallel processing
    if max_workers is None:
        max_workers = max(2, min(4, joblib.cpu_count() // 2))
    
    file_logger.info(f"Using {max_workers} worker processes")
    
    # Process assets in parallel
    results = []
    
    # For now, let's use sequential processing to avoid pickling issues
    # Can be optimized later with proper multiprocessing setup
    for asset_name, asset_df in asset_data_dict.items():
        try:
            result = train_ml_model(asset_name, asset_df.copy(), file_logger)
            results.append(result)
            
            # Cache model if requested and training was successful
            if cache_models and 'model' in result and result['signal'] not in ['error', 'insufficient_data']:
                try:
                    model_dir = os.path.join('results', 'signals')
                    os.makedirs(model_dir, exist_ok=True)
                    
                    model_data = {
                        'model': result['model'],
                        'scaler': result['scaler'], 
                        'feature_cols': result['feature_cols'],
                        'asset': asset_name,
                        'timestamp': timestamp,
                        'accuracy': result['accuracy']
                    }
                    
                    model_file = os.path.join(model_dir, f'ml_model_{asset_name}_{timestamp}.pkl')
                    with open(model_file, 'wb') as f:
                        pickle.dump(model_data, f)
                    
                    file_logger.info(f"Cached model for {asset_name} to {model_file}")
                    
                except Exception as cache_error:
                    file_logger.warning(f"Failed to cache model for {asset_name}: {str(cache_error)}")
            
        except Exception as e:
            file_logger.error(f"Error processing {asset_name}: {str(e)}")
            results.append({
                'asset': asset_name,
                'strategy': 'LogisticRegression',
                'parameters': 'ML',
                'signal': 'error',
                'date': None,
                'accuracy': 0.0,
                'error': str(e)
            })
    
    # Create DataFrame from results
    signals_df = pd.DataFrame(results)
    
    # Remove model objects from DataFrame for caching
    signals_for_cache = signals_df.copy()
    columns_to_remove = ['model', 'scaler', 'feature_cols', 'signal_probability']
    for col in columns_to_remove:
        if col in signals_for_cache.columns:
            signals_for_cache = signals_for_cache.drop(columns=[col])
    
    # Cache signals
    try:
        signals_dir = os.path.join('results', 'signals')
        os.makedirs(signals_dir, exist_ok=True)
        signals_file = os.path.join(signals_dir, f'ml_signals_{timestamp}.parquet')
        signals_for_cache.to_parquet(signals_file, index=False)
        file_logger.info(f"Cached ML signals to {signals_file}")
    except Exception as e:
        file_logger.error(f"Error caching ML signals: {str(e)}")
    
    # Log summary
    success_count = len(signals_df[~signals_df['signal'].isin(['error', 'insufficient_data', 'no_features', 'insufficient_diversity'])])
    error_count = len(signals_df[signals_df['signal'].isin(['error', 'insufficient_data', 'no_features', 'insufficient_diversity'])])
    
    buy_count = len(signals_df[signals_df['signal'] == 'buy'])
    sell_count = len(signals_df[signals_df['signal'] == 'sell'])
    hold_count = len(signals_df[signals_df['signal'] == 'hold'])
    
    avg_accuracy = signals_df[signals_df['accuracy'] > 0]['accuracy'].mean() if success_count > 0 else 0
    
    file_logger.info("=" * 50)
    file_logger.info("ML SIGNAL GENERATION SUMMARY")
    file_logger.info("-" * 50)
    file_logger.info(f"Total assets: {len(asset_data_dict)}")
    file_logger.info(f"Successful models: {success_count}")
    file_logger.info(f"Failed models: {error_count}")
    file_logger.info(f"Buy signals: {buy_count}")
    file_logger.info(f"Sell signals: {sell_count}")
    file_logger.info(f"Hold signals: {hold_count}")
    file_logger.info(f"Average accuracy: {avg_accuracy:.3f}")
    file_logger.info("=" * 50)
    
    return signals_df

def load_latest_ml_signals() -> Optional[pd.DataFrame]:
    """
    Load the most recent ML signals from cache.
    
    Returns:
        DataFrame with ML signals or None if not found
    """
    try:
        signals_dir = os.path.join('results', 'signals')
        if not os.path.exists(signals_dir):
            return None
        
        # Find most recent ML signals file
        ml_files = [f for f in os.listdir(signals_dir) 
                   if f.startswith('ml_signals_') and f.endswith('.parquet')]
        
        if not ml_files:
            return None
        
        # Sort by timestamp (newest first)
        ml_files.sort(reverse=True)
        latest_file = os.path.join(signals_dir, ml_files[0])
        
        return pd.read_parquet(latest_file)
        
    except Exception as e:
        logger.error(f"Error loading latest ML signals: {str(e)}")
        return None

if __name__ == "__main__":
    # Example usage
    from data.data_loader import DataLoader
    
    # Load multi-asset data
    data_loader = DataLoader("data/test multidata.xlsx")
    multi_asset_data = data_loader.load_multi_asset_excel()
    
    # Generate ML signals for subset of assets (for testing)
    test_assets = dict(list(multi_asset_data.items())[:5])
    
    ml_signals = generate_ml_signals(test_assets, max_workers=2)
    
    print("ML Signals Generated:")
    print(ml_signals[['asset', 'signal', 'accuracy']].head(10)) 