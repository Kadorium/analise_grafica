# Backend Strategies Guide for AI-Powered Trading Analysis System

## Overview

This document provides a comprehensive guide to the backend strategies system in the `strategies/` directory of the AI-Powered Trading Analysis System. It explains how strategies are structured, how they interact with the rest of the backend (including optimization and backtesting), and how they connect to the frontend UI. It also provides clear instructions for extending, modifying, and documenting changes to strategies, as well as guidance on updating this file when changes are made.

---

## 1. Directory and File Structure

```
Analise_Grafica/
├── strategies/
│   ├── __init__.py
│   ├── <strategy_name>.py
│   └── readme_be_strategies.md   # <--- THIS FILE
├── backtesting/
│   └── backtester.py
├── optimization/
│   └── optimizer.py
├── indicators/
├── app.py
├── frontend/
│   ├── index.html
│   └── js/
│       ├── main.js
│       └── modules/
│           └── strategySelector.js
```

- **`strategies/`**: Contains all backend trading strategy implementations.
- **`__init__.py`**: Registers and exposes all available strategies, provides the factory for creating strategy instances, and manages default parameters.
- **`<strategy_name>.py`**: Each file implements a specific strategy, following the required interface.
- **`readme_be_strategies.md`**: (This file) Documentation and instructions for backend strategies.

---

## 2. Strategy Architecture & Patterns

### 2.1. Strategy Interface

Each strategy must implement a `generate_signals(data: pd.DataFrame) -> pd.DataFrame` method. The returned DataFrame **must** include a normalized `'signal'` column (values: `'buy'`, `'sell'`, `'hold'`).

- **Class-based pattern:**
    ```python
    class MyStrategy:
        def __init__(self, parameters=None):
            self.parameters = parameters or { ... }
        def generate_signals(self, data):
            # ... logic ...
            return signals_df
        def get_parameters(self):
            return self.parameters
    ```
- **Function-based pattern:**
    ```python
    def generate_signals(data, param1=..., param2=...):
        # ... logic ...
        return signals_df
    ```

### 2.2. Registration and Factory

- All strategies following the `*_strategy.py` naming convention are auto-registered in `__init__.py` using dynamic import.
- The `create_strategy(strategy_type, **parameters)` factory returns a strategy instance or adapter for use in backtesting and optimization.
- Default parameters for each strategy are managed in `get_default_parameters(strategy_type)`.

### 2.3. Adapter Pattern

- Function-based strategies are wrapped in a `StrategyAdapter` class to provide a unified interface for backtesting and metrics calculation.

---

## 3. Backend Integration

### 3.1. Backtesting

- The `Backtester` class (`backtesting/backtester.py`) expects a strategy instance with a `backtest` or `generate_signals` method.
- The backtest process:
    1. Calls `generate_signals` to get signals DataFrame.
    2. Calculates positions, equity, and performance metrics.
    3. Returns results for further analysis and visualization.

### 3.2. Optimization

- The optimization module (`optimization/optimizer.py`) uses the strategy factory to instantiate strategies with different parameter sets.
- It runs backtests for each parameter combination and selects the best according to the chosen metric (e.g., Sharpe ratio).
- Results are saved to `results/optimization/` and can be visualized in the UI.

### 3.3. API and FastAPI Endpoints

- The main API (`app.py`) exposes endpoints for running backtests, optimizations, and retrieving available strategies and parameters.
- Endpoints:
    - `/api/available-strategies`: Lists all registered strategies.
    - `/api/strategy-parameters/{strategy_type}`: Returns default parameters for a strategy.
    - `/api/run-backtest`: Runs a backtest with the selected strategy and parameters.
    - `/api/optimize-strategy`: Runs parameter optimization for a strategy.

---

## 4. Frontend Integration

### 4.1. UI Structure

- **`frontend/index.html`**: Contains the main UI, including the "Strategy & Backtest" tab (formerly separate "Strategies" and "Backtest" tabs) for selecting, configuring strategies, and running backtests.
- **`frontend/js/main.js`**: Initializes the app, manages tab navigation (now with the merged "Strategy & Backtest" tab), and coordinates feature modules.
- **`frontend/js/modules/strategySelector.js`**: Handles strategy selection, parameter forms, and communication with the backend for strategies within the "Strategy & Backtest" tab. It now works alongside `backtestView.js` logic which is also triggered within this combined tab.
- **`frontend/js/modules/backtestView.js`**: Handles the backtesting execution and results display components, which are now part of the "Strategy & Backtest" tab UI. It is initialized by `main.js` and picks up strategy details from `appState`.

### 4.2. Workflow

1. **User navigates to the "Strategy & Backtest" tab** in the UI.
2. **Frontend fetches available strategies** and their parameters from `/api/available-strategies` and `/api/strategy-parameters/{strategy_type}` for the strategy selection part.
3. **User selects a strategy** and customizes its parameters.
4. **User configures backtest settings** (initial capital, commission, date range) within the same tab.
5. **User runs a backtest** or optimization, which sends a request to `/api/run-backtest` or `/api/optimize-strategy` respectively. The `/api/run-backtest` call will include both strategy configuration and backtest settings.
6. **Backend processes the request** using the selected strategy, runs the backtest/optimization, and returns results.
7. **Frontend displays results** (metrics, equity curve, trade history, etc.) within the "Strategy & Backtest" tab.

### 4.3. Strategy Comparison

The "Strategy & Backtest" tab now includes advanced strategy comparison functionality:

- **Multi-strategy Selection:** Users can select multiple strategies via checkboxes and customize parameters for each.
- **Parameter Configuration:** Each selected strategy displays its configurable parameters in a compact form.
- **Optimized Comparison:** Option to automatically optimize each strategy's parameters using grid search before comparison.
- **Comprehensive Results:** Comparison provides:
  - Performance metrics table comparing key metrics across strategies
  - Parameter values used for each strategy
  - Trade-by-trade breakdown for each strategy
  - Equity curve visualization
  - Identification of best strategy for each metric

The comparison feature helps traders rapidly evaluate multiple strategies to identify the most promising ones for their specific market conditions and trading goals.

### 4.4. API Endpoints

- **`/api/available-strategies`**: GET - Returns a list of available strategies.
- **`/api/strategy-parameters/{strategy_type}`**: GET - Returns the parameters for a specific strategy.
- **`/api/run-backtest`**: POST - Runs a backtest for a specific strategy configuration.
- **`/api/compare-strategies`**: POST - Enhanced endpoint that compares multiple strategies with optional optimization.
- **`/api/recent-comparisons`**: GET - Returns recent strategy comparison results.

### 4.5. Adding/Modifying Strategies and UI

- When a new strategy is added to the backend, it is automatically available in the UI (if it follows the naming convention and is registered in `__init__.py`).
- To customize how strategies appear in the UI, update the `strategy_descriptions` dictionary in `strategies/__init__.py`.
- The frontend dynamically builds strategy selection dropdowns and parameter forms based on backend responses.

---

## 5. Extending and Modifying Strategies

### 5.1. Adding a New Strategy

1. **Create a new file** in `strategies/` named `<strategy_name>_strategy.py`.
2. **Implement** a `generate_signals` function or class as described above.
3. **Document** all parameters and logic with clear docstrings and type hints.
4. **(Optional)** Add a description to the `strategy_descriptions` dictionary in `__init__.py` for better UI display.
5. **Test** the strategy using the UI or `run_advanced_backtest.py`.
6. **Update this file** (`readme_be_strategies.md`) to document the new strategy and any interface changes.

### 5.2. Modifying an Existing Strategy

- Update the relevant strategy file and its docstrings.
- If parameters or interface change, update `get_default_parameters` and the UI description.
- **Update this file** to reflect the changes.

### 5.3. Removing a Strategy

- Delete the strategy file and remove its entry from `strategy_descriptions` if present.
- **Update this file** to document the removal.

---

## 6. Best Practices & Requirements

- **Follow the interface**: All strategies must provide a `generate_signals` method/function.
- **Docstrings and type hints**: Document all parameters, return values, and logic.
- **Parameter validation**: Validate input parameters and handle edge cases.
- **Signal normalization**: Use the `normalize_signals_column` utility to ensure the 'signal' column is standardized.
- **Performance**: Use vectorized operations with pandas/numpy for efficiency.
- **Testing**: Use the provided backtesting and optimization tools to validate new strategies.

---

## 7. Updating This Documentation

**Whenever you add, modify, or remove a strategy, or change the interface or integration with other modules, you MUST:**

- Update this `readme_be_strategies.md` file to reflect:
    - The new/changed/removed strategy
    - Any changes to the interface, parameters, or workflow
    - Any changes to how strategies connect to optimization, backtesting, or the frontend
- Summarize the change at the top of the file (changelog section, if present)
- Ensure that instructions for future contributors remain clear and up to date

---

## 8. Example: Adding a New Strategy

1. **Create the file:** `strategies/my_new_strategy.py`
2. **Implement the function:**
    ```python
    def generate_signals(data, my_param=10):
        """
        My New Strategy
        Args:
            data (pd.DataFrame): Input price and indicator data
            my_param (int): Example parameter
        Returns:
            pd.DataFrame: DataFrame with 'signal' column
        """
        signals = data.copy()
        # ... strategy logic ...
        signals['signal'] = 'hold'  # or 'buy'/'sell' as appropriate
        return signals
    ```
3. **(Optional) Add description** to `strategy_descriptions` in `__init__.py`.
4. **Test** via UI or `run_advanced_backtest.py`.
5. **Update this file** with a summary of the new strategy and its parameters.

---

## 9. Troubleshooting

- If a strategy does not appear in the UI, ensure the file is named correctly and implements the required interface.
- Check logs for import errors in `__init__.py`.
- Ensure all required columns are present in the returned DataFrame.
- Use the provided utility functions for signal normalization and performance metrics.

---

## 10. Strategy Documentation

### Seasonality Strategy

The seasonality strategy (`strategies/seasonality_strategy.py`) is a calendar-based trading approach that automatically analyzes and trades based on historical seasonal patterns.

**Parameters:**

- `auto_optimize` (bool): When True, automatically analyzes historical data to determine optimal trading days/months
- `significance_threshold` (float): Minimum statistical significance level (0-1) for considering a pattern valid
- `return_threshold` (float): Minimum average return percentage for considering a pattern valid
- `day_of_week_filter` (list): Optional override to manually specify days to enter positions (0-6, where 0 is Monday)
- `month_of_year_filter` (list): Optional override to manually specify months to enter positions (1-12)
- `day_of_month_filter` (list): Optional override to manually specify days of month to enter positions (1-31)
- `exit_after_days` (int): Exit position after specified number of days
- `combined_seasonality` (bool): If True, all conditions must be met; if False, any condition can generate a signal

**Example Configuration:**
```python
{
    'auto_optimize': True,
    'significance_threshold': 0.6,
    'return_threshold': 0.1,
    'day_of_week_filter': None,  # Will be auto-determined
    'month_of_year_filter': None,  # Will be auto-determined
    'day_of_month_filter': None,
    'exit_after_days': 3,
    'combined_seasonality': False
}
```

**Implementation Details:**
- Automatically analyzes historical data using the built-in seasonality functions
- Identifies statistically significant positive and negative seasonal patterns
- Goes long (buy) on positive seasonality periods and short (sell) on negative seasonality periods
- Exits positions after a specified number of days or when the seasonal pattern ends
- Provides diagnostic information about discovered patterns during strategy execution

**How to Use:**
1. Simply select the Seasonality strategy in the UI
2. Use the default auto-optimize setting or adjust the significance and return thresholds
3. The strategy will automatically discover and trade the statistically significant seasonal patterns in your data

---

## 11. References

- [Project README.md](../README.md)
- [LLM Guide (readmeLLM.md)](../readmeLLM.md)
- [Strategy Registry and Factory (`__init__.py`)](./__init__.py)
- [Backtester (`backtesting/backtester.py`)](../backtesting/backtester.py)
- [Frontend UI (`frontend/index.html`)](../frontend/index.html)
- [Frontend JS (`frontend/js/main.js`)](../frontend/js/main.js)

---

**Keep this file up to date!** 