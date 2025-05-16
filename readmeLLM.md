# AI-Powered Trading Analysis System - LLM Guide

This document provides structured guidance for LLMs and AI models interacting with the AI-Powered Trading Analysis System. It outlines the system's architecture, components, and guidelines for contributing code.

## System Overview

The AI-Powered Trading Analysis System is a modular trading analysis platform built with a Python backend (FastAPI) and HTML frontend. It enables users to analyze stocks, implement technical indicators, backtest trading strategies, and optimize parameters without writing code.

### Primary Capabilities

- Data processing (CSV uploads with historical stock data)
- Technical indicator implementation (Moving Averages, RSI, MACD, Bollinger Bands)
- Trading strategy execution (Trend Following, Mean Reversion, Breakout)
- Backtesting against historical data
- Parameter optimization for strategies
- Results visualization and export (PDF/Excel)

## Architecture for AI Interaction

```
+-------------------+      API Endpoints       +-------------------+
|    Frontend       | <----------------------> |    Backend        |
| (HTML/CSS/JS)     |                          | (FastAPI/Python)  |
+-------------------+                          +-------------------+
                                                      |
                              +-------------------+   |   +-------------------+
                              | Data Management   |<--+-->| Indicators        |
                              | (CSV Processing)  |       | (Technical Tools) |
                              +-------------------+       +-------------------+
                                                              |
                              +-------------------+       +-------------------+
                              | Backtesting       |<----->| Strategies        |
                              | (Performance)     |       | (Signal Gen)      |
                              +-------------------+       +-------------------+
                                      |
                              +-------------------+
                              | Optimization      |
                              | (Parameter Tuning)|
                              +-------------------+
```

## Key File Structure

```
app.py                   # Main FastAPI application with API endpoints
backtesting/             # Backtesting implementation
└── backtester.py        # Core backtesting engine
data/                    # Data management
└── sample/              # Sample datasets
indicators/              # Technical indicators implementation
└── indicator_utils.py   # Contains indicator combination logic and utility functions for indicator processing. Includes `normalize_signals_column(df)` utility to standardize signal columns in strategies.
optimization/            # Strategy optimization modules
strategies/              # Trading strategy implementations
frontend/                # UI files
```

## Module Interaction Guidelines for LLMs

When providing modifications or extensions to this system, follow these interaction patterns:

### 1. Data Processing Flow

```python
# Data loading pattern
from data.data_loader import load_and_validate_csv

def process_data(file_path):
    data = load_and_validate_csv(file_path)
    # Perform cleaning and validation
    return processed_data
```

### 2. Adding New Indicators

```python
# Indicator implementation pattern
def calculate_new_indicator(df, period=14, column='close'):
    """
    Calculate a new technical indicator
    
    Args:
        df (pd.DataFrame): Price data with OHLCV columns
        period (int): Lookback period
        column (str): Column name to use in calculation
        
    Returns:
        pd.Series: Calculated indicator values
    """
    result = df[column].rolling(period).some_operation()
    return result
```

### 3. Creating New Strategies

```python
# Strategy implementation pattern
class NewStrategy:
    def __init__(self, parameters=None):
        self.parameters = parameters or {'param1': 10, 'param2': 20}
        
    def generate_signals(self, data):
        """Generate buy/sell signals
        
        Args:
            data (pd.DataFrame): Price and indicator data
            
        Returns:
            pd.DataFrame: DataFrame with 'signal' column (1=buy, -1=sell, 0=hold)
        """
        signals = data.copy()
        # Strategy logic implementation
        signals['signal'] = 0
        # Example: Buy condition
        buy_condition = (data['indicator1'] > data['indicator2'])
        signals.loc[buy_condition, 'signal'] = 1
        # Example: Sell condition
        sell_condition = (data['indicator1'] < data['indicator2'])
        signals.loc[sell_condition, 'signal'] = -1
        
        return signals
        
    def get_parameters(self):
        return self.parameters
```

### 4. API Endpoint Pattern

```python
# FastAPI endpoint pattern
@app.post("/api/run-strategy")
async def run_strategy(request: dict):
    strategy_type = request.get("strategy_type")
    parameters = request.get("parameters", {})
    
    # Create strategy instance
    strategy = create_strategy(strategy_type, parameters)
    
    # Apply to data
    signals = strategy.generate_signals(data)
    
    # Return results
    return {
        "success": True,
        "signals": signals.to_dict(),
        "metrics": calculate_metrics(signals)
    }
```

## Development Guidelines for LLMs

### Code Structure

1. **Modularity**: Add new functionality as separate modules in the appropriate directory
2. **Docstrings**: Include detailed docstrings with parameter descriptions and return values
3. **Type Hints**: Use Python type hints for improved code clarity
4. **Error Handling**: Implement proper error handling with informative messages

### Version Control

1. **Committing Changes**: When the user indicates that the code is working correctly, perform a commit with a descriptive message.
   - **Correction Commits**: If a correction you made is confirmed by the user as working, even partially (e.g., user says "great", "it's working", "perfect", "that's it", "exactly", "nice", or similar affirmations), you MUST immediately perform a commit and then push the changes. This action takes precedence; complete the commit and push *before* proceeding with any other requests or tasks, even if they are part of the same user message.
2. **Pushing to Remote**: After committing, push the changes to the GitHub repository.
3. **Tagging Major Releases**: After completing a significant set of changes or a major feature (and after the above committing and pushing steps):
    *   Update the `version` field (e.g., from "1.0" to "1.1" or "2.0") within the `AUTO_UPDATE_CONFIG` JSON block in this `readmeLLM.md` file. Also update the `last_updated` field.
    *   Create a new Git tag for the release (e.g., `v1.1`, `v2.0`).
    *   Push the new tag to the GitHub repository.

### Strategy Development

When creating trading strategies:

1. Follow the strategy interface pattern (implement `generate_signals` method)
2. Document parameter ranges and descriptions
3. Include basic validation of inputs
4. Return standardized signal format (DataFrame with 'signal' column)

### Indicator Development

When implementing technical indicators:

1. Place in the appropriate category file in the `indicators/` directory
2. Document the mathematical formula being implemented
3. Handle edge cases (insufficient data points, NaN values)
4. Optimize for performance with vectorized operations

## Testing Methods

1. **Quick Strategy Testing**: Use `run_advanced_backtest.py` with sample data
2. **API Testing**: Test new endpoints with sample JSON payloads
3. **Integration Testing**: Verify that new components work with existing modules

## Common Tasks for LLMs

### Task: Add a New Technical Indicator

```python
# Add to indicators/oscillators.py
def calculate_williams_r(df, period=14):
    """
    Calculate Williams %R oscillator
    
    Formula: %R = (Highest High - Close)/(Highest High - Lowest Low) * -100
    
    Args:
        df (pd.DataFrame): Price data with 'high', 'low', 'close' columns
        period (int): Lookback period
        
    Returns:
        pd.Series: Williams %R values (-100 to 0)
    """
    highest_high = df['high'].rolling(window=period).max()
    lowest_low = df['low'].rolling(window=period).min()
    
    williams_r = ((highest_high - df['close']) / (highest_high - lowest_low)) * -100
    
    return williams_r
```

### Task: Create a New Trading Strategy

```python
# Create strategies/volatility_breakout.py
class VolatilityBreakoutStrategy:
    def __init__(self, parameters=None):
        """
        Volatility Breakout trading strategy
        
        Args:
            parameters (dict): Strategy parameters
                - atr_period (int): ATR calculation period
                - multiplier (float): Volatility multiplier
        """
        self.parameters = parameters or {'atr_period': 14, 'multiplier': 2.0}
        
    def generate_signals(self, data):
        """Generate buy/sell signals based on volatility breakouts
        
        Args:
            data (pd.DataFrame): Price data with OHLCV columns
            
        Returns:
            pd.DataFrame: DataFrame with signals
        """
        # Implementation details here
        # ...
        
        return signals
```

### Task: Optimize a Strategy

```python
# Example parameter optimization
from optimization.optimizer import grid_search_optimization

def optimize_strategy(strategy_class, data, param_ranges, metric='sharpe_ratio'):
    """
    Find optimal parameters for a strategy
    
    Args:
        strategy_class: Strategy class to optimize
        data (pd.DataFrame): Historical price data
        param_ranges (dict): Dictionary mapping parameter names to ranges
        metric (str): Metric to optimize ('sharpe_ratio', 'total_return', etc.)
        
    Returns:
        dict: Best parameters found
        float: Best metric value
    """
    best_params, best_value = grid_search_optimization(
        strategy_class, data, param_ranges, metric)
    
    return best_params, best_value
```

## Extending Functionality

### Example: Add Machine Learning Support

```python
# Machine learning integration pattern
from sklearn.ensemble import RandomForestClassifier

def create_ml_features(data, feature_columns):
    """Create features for ML model"""
    X = data[feature_columns].copy()
    # Handle NaN values, normalization, etc.
    return X

def train_ml_strategy(data, feature_columns, target='signal'):
    """Train ML model for trading signals
    
    Args:
        data (pd.DataFrame): Historical data with indicators
        feature_columns (list): Features to use for prediction
        target (str): Target column name
        
    Returns:
        object: Trained model
    """
    X = create_ml_features(data, feature_columns)
    y = data[target]
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    return model

class MLStrategy:
    def __init__(self, model, feature_columns):
        self.model = model
        self.feature_columns = feature_columns
        
    def generate_signals(self, data):
        X = create_ml_features(data, self.feature_columns)
        data['signal'] = self.model.predict(X)
        return data
```

## System Limitations to Consider

1. **Data Format Requirements**: CSV files must have Date, Open, High, Low, Close, Volume columns
2. **Backtesting Assumptions**: Perfect execution at close prices without slippage
3. **Optimization Constraints**: Grid search can be computationally intensive on large parameter spaces
4. **Frontend-Backend Communication**: All data passes through RESTful API endpoints

## LLM Update Parameters

### AUTO_UPDATE_CONFIG

```json
{
  "version": "1.0",
  "last_updated": "2025-05-13",
  "update_triggers": [
    "new_module_added",
    "api_change",
    "core_structure_change",
    "strategy_pattern_change"
  ],
  "system_components": [
    "data_processing",
    "indicators",
    "strategies",
    "backtesting",
    "optimization",
    "api",
    "frontend"
  ],
  "code_examples": {
    "refresh_frequency": "on_change",
    "include_patterns": true
  },
  "architecture_diagram": {
    "update_on_structure_change": true
  }
}
```

### LLM Interaction Guidelines

When working with this codebase, LLMs should:

1. **Prioritize Understanding**: Read this document first for system architecture and patterns
2. **Use Example Patterns**: Reference provided code patterns when creating new components
3. **Respect Module Boundaries**: Add functionality to appropriate directories/modules
4. **Follow Naming Conventions**: Use snake_case for functions and files
5. **Update Documentation**: Maintain this LLM guide when significant changes are made

### Document Auto-Update Triggers

This readmeLLM.md should be updated when:

1. New modules or major components are added to the system
2. API endpoint patterns change
3. Strategy or indicator interfaces are modified
4. Core architecture is restructured
5. New development guidelines are established

### Version Control

Changes to this document should include:
- Updated version number
- Last modified date
- Summary of changes
- Author or source of changes (if applicable)

## Strategy Pattern

Each strategy class (in `strategies/`) should implement a `generate_signals(data: pd.DataFrame) -> pd.DataFrame` method. The returned DataFrame must include a normalized 'signal' column using `normalize_signals_column` from `indicators/indicator_utils.py`.
