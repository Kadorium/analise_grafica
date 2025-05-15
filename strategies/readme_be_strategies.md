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

- **`frontend/index.html`**: Contains the main UI, including the "Strategies" tab for selecting and configuring strategies.
- **`frontend/js/main.js`**: Initializes the app, manages tab navigation, and coordinates feature modules.
- **`frontend/js/modules/strategySelector.js`**: Handles strategy selection, parameter forms, and communication with the backend for strategies.

### 4.2. Workflow

1. **User selects a strategy** in the UI ("Strategies" tab).
2. **Frontend fetches available strategies** and their parameters from `/api/available-strategies` and `/api/strategy-parameters/{strategy_type}`.
3. **User customizes parameters** (if desired).
4. **User runs a backtest** or optimization, which sends a request to `/api/run-backtest` or `/api/optimize-strategy`.
5. **Backend processes the request** using the selected strategy, runs the backtest/optimization, and returns results.
6. **Frontend displays results** (metrics, equity curve, trade history, etc.).

### 4.3. Adding/Modifying Strategies and UI

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

## 10. References

- [Project README.md](../README.md)
- [LLM Guide (readmeLLM.md)](../readmeLLM.md)
- [Strategy Registry and Factory (`__init__.py`)](./__init__.py)
- [Backtester (`backtesting/backtester.py`)](../backtesting/backtester.py)
- [Frontend UI (`frontend/index.html`)](../frontend/index.html)
- [Frontend JS (`frontend/js/main.js`)](../frontend/js/main.js)

---

**Keep this file up to date!** 