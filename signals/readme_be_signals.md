# Signals Module Documentation

## Overview

The signals module handles signal generation for trading strategies, including both rule-based and machine learning approaches. It provides a unified interface for generating, weighting, and managing trading signals across multiple assets.

## Module Structure

```
signals/
├── signal_generator.py      # Rule-based signal generation
├── ml_signal_generator.py   # Machine learning signal generation  
├── weighting_engine.py      # Performance-based signal weighting
└── log_utils.py            # Shared logging utilities
```

## Core Components

### 1. Rule-Based Signal Generation (`signal_generator.py`)

Generates signals using traditional technical analysis strategies:

- **Function**: `generate_signals_for_assets()`
- **Input**: Multi-asset data, strategy configurations
- **Output**: Pandas DataFrame with signals for all assets
- **Features**: 
  - Parallel processing for scalability
  - Caching for performance
  - Integration with weighting engine
  - Support for multiple strategies simultaneously

### 2. ML Signal Generation (`ml_signal_generator.py`)

Generates signals using machine learning models:

- **Model Type**: Logistic Regression per asset
- **Features**: 
  - Lagged returns (1-5 days)
  - Technical indicators (RSI, MACD, Bollinger Bands, etc.)
  - Volume indicators
  - Moving averages
- **Training**: 70/30 time-aware train-test split
- **Output**: Buy/Sell/Hold signals with accuracy scores
- **Caching**: Models and signals cached for performance

#### Feature Engineering

The ML signal generator creates features from:
1. **Price Features**: Lagged returns for 1-5 days
2. **Technical Indicators**: All indicators from `indicators/` module
3. **Volume Features**: Volume changes and patterns
4. **Moving Averages**: Multiple timeframes

#### Signal Generation Logic

```python
# Signal probability thresholds
if signal_proba[1] > 0.6:  # High confidence buy
    signal = 'buy'
elif signal_proba[0] > 0.6:  # High confidence sell  
    signal = 'sell'
else:
    signal = 'hold'
```

### 3. Performance-Based Weighting (`weighting_engine.py`)

Calculates performance-based weights for signal optimization:

- **Metrics**: Sharpe ratio, total return, max drawdown, win rate
- **Goal-Seek**: Optimize weights based on selected metric
- **Custom Weights**: Support for user-defined metric combinations
- **ML Integration**: Incorporates ML model accuracy as weighting factor

#### Weighting Formula for ML Signals

```python
# For ML signals, weight is enhanced by accuracy
final_weight = base_weight * (accuracy_factor ** accuracy_scaling)
```

## API Integration

### Endpoints

#### `POST /api/generate-signals`
- **Parameters**: 
  - `strategies`: List of strategy configurations
  - `include_ml`: Boolean to include ML signals
  - `weights_file`: Optional weights file for weighted signals
  - `refresh_cache`: Force regeneration of signals
- **Response**: Signal counts, cached file path, ML metrics

#### `POST /api/update-weights`
- **Parameters**: 
  - `strategies`: Strategy configurations for weight calculation
  - `goal_seek_metric`: Target optimization metric
  - `lookback_period`: Historical period for backtesting
- **Response**: Weight calculations and cached file path

## Usage Patterns

### Generate Rule-Based Signals Only

```python
from signals.signal_generator import generate_signals_for_assets

signals = generate_signals_for_assets(
    multi_asset_data=data,
    strategies=[('trend_following', 'default')],
    max_workers=4
)
```

### Generate ML Signals

```python
from signals.ml_signal_generator import generate_ml_signals

ml_signals = generate_ml_signals(
    multi_asset_data=data,
    max_workers=4,
    cache_models=True
)
```

### Calculate Performance Weights

```python
from signals.weighting_engine import calculate_and_store_weights

weights = calculate_and_store_weights(
    strategies=[('trend_following', 'optimized')],
    goal_seek_metric='sharpe_ratio',
    lookback_period='1 Year'
)
```

## Frontend Integration

The signals module integrates with the screener panel in the frontend:

- **ML Toggle**: `Include ML Signals` checkbox enables/disables ML signal generation
- **Weighted Signals**: Performance-based weighting with goal-seek optimization
- **Accuracy Column**: Displays ML model accuracy for LogisticRegression signals
- **Signal Distribution Chart**: Updates to show ML signals when enabled

## Performance Considerations

1. **Parallel Processing**: Uses `joblib` for multi-asset processing
2. **Caching**: Models and signals cached to avoid recomputation
3. **Memory Management**: Efficient handling of large datasets
4. **Error Handling**: Graceful handling of insufficient data or model failures

## Error Handling

Common error scenarios:

1. **Insufficient Data**: < 100 data points for ML training
2. **Feature Generation Failures**: Missing indicators or price data
3. **Model Training Failures**: Convergence issues or data quality problems
4. **File I/O Errors**: Caching or logging failures

All errors are logged to `results/logs/screening_log.txt` with detailed context.

## File Formats

### Signal Output Format

```python
{
    'asset': str,           # Asset symbol
    'strategy': str,        # Strategy name ('LogisticRegression' for ML)
    'parameters': str,      # Parameter type ('ML' for ML signals)
    'signal': str,          # 'buy', 'sell', 'hold'
    'date': datetime,       # Signal date
    'accuracy': float,      # Model accuracy (ML only)
    'weighted_signal_score': float,  # Weighted signal score
    'weight': float         # Performance-based weight
}
```

### Cached Files

- **Signals**: `results/signals/signals_{timestamp}.parquet`
- **Weights**: `results/signals/weights_{timestamp}.parquet`
- **ML Models**: `results/signals/ml_models_{asset}_{timestamp}.pkl`

## Development Guidelines

1. **Consistency**: Follow existing patterns for new signal generators
2. **Documentation**: Include detailed docstrings and type hints
3. **Testing**: Ensure proper handling of edge cases
4. **Performance**: Use vectorized operations where possible
5. **Logging**: Comprehensive error and progress logging
6. **Caching**: Implement appropriate caching strategies for performance 