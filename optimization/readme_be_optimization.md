# Backend Optimization Module Guide

> **Note:** This file (`readme_be_optimization.md`) supersedes the old `optimization/README.md`. All references to the old file should be removed. In the near future, `optimization/README.md` will be deleted. Use this file as the single source of truth for backend optimization documentation, developer instructions, and integration details.

## Overview

This document provides a comprehensive guide to the **backend optimization system** in the AI-Powered Trading Analysis System. It is intended for developers and maintainers who need to understand, extend, or modify the optimization workflow, its integration with strategies and backtesting, and its connection to the frontend UI.

---

## 1. Module Purpose & High-Level Flow

The optimization module enables **parameter optimization** for trading strategies using grid search and other algorithms. It is responsible for:
- Accepting optimization requests (via API or direct function call)
- Running parameter sweeps (grid search)
- Backtesting each parameter set using the core backtesting engine
- Comparing default vs. optimized strategy performance
- Storing results and generating visualizations
- Reporting status and results to the frontend

**Key Backend Flow:**
1. **Frontend** sends an optimization request (strategy, parameter ranges, metric, date range)
2. **API endpoint** (`/api/optimize-strategy`) receives the request and starts a background task
3. **Background task** (in `task.py`) runs the optimization using `optimizer.py`
4. For each parameter combination:
    - A strategy instance is created (via `strategies/`)
    - The strategy is backtested (via `backtesting/backtester.py`)
    - Performance metrics are calculated
5. The best parameters and all results are saved (via `file_manager.py`)
6. Status and results are made available to the frontend via API endpoints

---

## 2. File & Module Structure

```
optimization/
├── __init__.py                # Exposes main functions/classes
├── models.py                  # Pydantic models for config/validation
├── status.py                  # Status tracking, logging
├── metrics.py                 # Advanced performance metrics
├── visualization.py           # Chart/visualization generation
├── file_manager.py            # File I/O for results
├── task.py                    # Background optimization task logic
├── routes.py                  # FastAPI endpoints for optimization
├── optimizer.py               # Core optimization logic (grid search, etc.)
├── README.md                  # (To be deleted; see note above)
├── readme_be_optimization.md  # (This file: backend-focused, dev/maintainer guide)
```

**Key Connections:**
- `optimizer.py` is the core: runs grid search, calls strategies and backtester
- `task.py` wraps optimizer, handles default/optimized comparison, charting, saving
- `routes.py` exposes endpoints, launches background tasks, returns status/results
- `file_manager.py` handles saving/loading results
- `status.py` tracks progress and logs requests
- `visualization.py` generates comparison charts for results
- `models.py` defines request/response/config schemas

---

## 3. Backend Optimization Workflow

### a. API Layer (`routes.py`)
- **POST `/api/optimize-strategy`**: Starts an optimization job (calls `run_optimization_task` in background)
- **GET `/api/optimization-status`**: Returns current status (in progress, completed, etc.)
- **GET `/api/optimization-results/{strategy_type}`**: Returns results for a given strategy
- **GET `/api/check-optimization-directory`**: Checks if results directory exists
- **GET `/api/optimization-chart/{strategy_type}/{timestamp}`**: Returns chart image for results

### b. Task Layer (`task.py`)
- Receives config, data, and current app config
- Calls `optimize_strategy` (from `optimizer.py`) with parameter grid
- Runs a **default** backtest (using default parameters) for comparison
- Runs an **optimized** backtest (using best found parameters)
- Calculates advanced metrics (via `metrics.py`)
- Generates comparison chart (via `visualization.py`)
- Saves all results (via `file_manager.py`)
- Updates status (via `status.py`)

### c. Optimization Logic (`optimizer.py`)
- **`grid_search`**: Iterates over all parameter combinations (parallelized)
- For each combination:
    - Creates a strategy instance (via `strategies.create_strategy`)
    - Runs backtest (via `backtesting.Backtester`)
    - Collects performance metrics
- Returns best parameters, all results, and debug info

### d. Strategy & Backtesting Integration
- **Strategies** are defined in `strategies/` and must implement a standard interface (see `readmeLLM.md`)
- **Backtester** (`backtesting/backtester.py`) runs the strategy on the data, calculates equity, trades, and metrics
- The optimizer is agnostic to the strategy logic: it only requires the standard interface

---

## 4. Frontend-Backend Integration

### a. Frontend Modules (Modular Structure)

> **Note:** The frontend is now fully modular. The main entry point is `frontend/js/main.js`, which imports and initializes all feature modules. All optimization UI logic, parameter selection, and results display are handled by dedicated modules. Do **not** reference or modify `frontend/js/app.js` (deprecated).

**Key frontend modules for optimization:**
- `frontend/js/main.js`: **Entry point**; initializes the app and all modules.
- `frontend/js/modules/optimizationPanel.js`: Main optimization UI logic (parameter selection, job submission, progress, results display).
- `frontend/js/modules/optimizationParamTable.js`: Renders the parameter selection table for optimization.
- `frontend/js/utils/api.js`: Defines all API calls to backend endpoints (including optimization).
- `frontend/js/utils/strategies-config.js`: Defines available strategies and parameter metadata for the UI.
- Other modules (e.g., `indicatorPanel.js`, `strategySelector.js`) are initialized by `main.js` and may interact with optimization as needed.

**How it works:**
- The user interacts with the optimization UI (rendered by `optimizationPanel.js` and `optimizationParamTable.js`).
- When the user submits an optimization job, the frontend collects the selected strategy, parameter ranges, and metric, and sends a POST request to `/api/optimize-strategy` using the API utility in `utils/api.js`.
- The backend runs the optimization and updates status/results, which are polled and displayed by the frontend modules.
- All strategy and parameter metadata for the UI is defined in `utils/strategies-config.js`.
- The modular structure allows for easy extension and maintenance; new features should be added as new modules or utilities.

**Maintainer Note:**
> If the frontend structure changes (e.g., new entry point, new modules, or major refactor), update this section to reflect the new architecture. Remove any outdated references and ensure all integration points are clearly documented.

### b. Data Flow
1. User selects strategy and parameter ranges in the UI
2. UI sends a POST to `/api/optimize-strategy` with config (via `utils/api.js`)
3. Backend runs optimization, updates status
4. UI polls `/api/optimization-status` and `/api/optimization-results/{strategy_type}`
5. Results (best params, metrics, charts) are displayed in the UI (via `optimizationPanel.js`)

---

## 4a. Usage Examples (Python)

### Start an Optimization

```python
from optimization import OptimizationConfig, run_optimization_task

# Create optimization configuration
optimization_config = OptimizationConfig(
    strategy_type="sma_crossover",
    param_ranges={
        "short_window": [5, 10, 15, 20],
        "long_window": [50, 100, 150, 200]
    },
    metric="sharpe_ratio",
    start_date="2020-01-01",
    end_date="2021-01-01"
)

# Run the optimization task
result = run_optimization_task(
    data=processed_data,
    optimization_config=optimization_config.dict(),
    current_config=app_config
)
```

### Check Optimization Status

```python
from optimization.status import get_optimization_status

# Get current status
status = get_optimization_status()
print(f"In progress: {status['in_progress']}")
print(f"Strategy type: {status['strategy_type']}")
```

### Retrieve Optimization Results

```python
from optimization.file_manager import load_optimization_results

# Load the latest optimization results for a strategy
results, timestamp, error = load_optimization_results("sma_crossover")
if error:
    print(f"Error: {error}")
else:
    print(f"Optimization results from {timestamp}")
    print(f"Default performance: {results['default_performance']}")
    print(f"Optimized performance: {results['optimized_performance']}")
```

---

## 4b. Integration with Main Application

There are two recommended ways to integrate this module with the main application:

### Method 1: Using the Router (Simpler, but may have issues with accessing global state)

```python
# In app.py
from optimization import optimization_router

# Add the optimization router to the FastAPI app
app.include_router(optimization_router)
```

### Method 2: Forwarding Endpoints (Recommended for accessing global variables)

If you encounter a "No processed data" error when using Method 1, this is because the router endpoints don't have access to the global `PROCESSED_DATA` variable. Instead, use this approach:

```python
# In app.py

# Do NOT include the router directly
# app.include_router(optimization_router)  # <-- Comment out or remove

# Instead, create wrapper endpoints that forward to the modularized versions
@app.post("/api/optimize-strategy")
@endpoint_wrapper("POST /api/optimize-strategy")
async def optimize_strategy_endpoint(optimization_config: OptimizationConfig, background_tasks: BackgroundTasks, request: Request):
    """Forward the optimize-strategy endpoint to the modularized version with the proper dependencies"""
    global PROCESSED_DATA, CURRENT_CONFIG
    
    from optimization.routes import optimize_strategy_endpoint as modularized_endpoint
    return await modularized_endpoint(
        optimization_config=optimization_config,
        background_tasks=background_tasks,
        request=request,
        processed_data=PROCESSED_DATA,
        current_config=CURRENT_CONFIG
    )

# Add similar wrappers for the other endpoints
@app.get("/api/optimization-status")
@endpoint_wrapper("GET /api/optimization-status")
async def optimization_status_endpoint():
    from optimization.routes import get_optimization_status_endpoint
    return await get_optimization_status_endpoint()

# And so on for other endpoints...
```

---

## 5. How to Extend or Modify

### a. To Add/Change a Strategy
- Implement the strategy in `strategies/` (see `readmeLLM.md` for interface)
- Register it in the strategy factory (`strategies/__init__.py`)
- Add parameter ranges in `optimizer.py` (`PARAM_RANGES`)
- Update frontend config in `frontend/js/utils/strategies-config.js`

### b. To Add/Change Optimization Logic
- Edit or extend `optimizer.py` (e.g., add new search algorithms)
- Update `task.py` if new workflow steps are needed
- Update `visualization.py` for new result types or charts

### c. To Add/Change Metrics
- Add to `metrics.py` (for advanced metrics)
- Ensure new metrics are returned in results and displayed in the frontend

### d. To Add/Change API Endpoints
- Edit `routes.py` (follow FastAPI async conventions)
- Update frontend API calls in `frontend/js/utils/api.js`

---

## 6. File Storage

Optimization results are stored in the `results/optimization/` directory. The following files are created:

- **optimization_{strategy_type}_{timestamp}.json**: Optimization results
- **chart_backup_{strategy_type}_{timestamp}.png**: Backup chart image

---

## 7. Error Handling and Logging

The module includes comprehensive error handling and logging:

- All optimization requests are logged to `optimization_requests.log`
- Runtime errors are captured and reported
- Status updates are maintained throughout the optimization process

---

## 8. Update & Maintenance Instructions

**Whenever you make changes to the optimization backend or its integration:**
- **Update this file** (`readme_be_optimization.md`) with:
    - New/changed modules, files, or workflow steps
    - Any new strategy, parameter, or metric exposed to optimization
    - Any changes to API endpoints or their expected payloads
    - Any changes to the frontend-backend contract (data format, flow)
- **Update `optimizer.py` PARAM_RANGES** for new strategies/parameters
- **Update `frontend/js/utils/strategies-config.js`** for new strategies/parameters
- **Update `optimization/README.md`** if API usage or user-facing instructions change
- **Update `readmeLLM.md`** if architectural patterns or LLM guidelines change

---

## 9. References & Further Reading
- [optimization/README.md](./README.md) — User/API/usage guide
- [readmeLLM.md](../readmeLLM.md) — LLM and architecture patterns
- [README.md](../README.md) — Project overview and structure
- [frontend/js/utils/strategies-config.js](../../frontend/js/utils/strategies-config.js) — Frontend strategy config
- [strategies/](../../strategies/) — Strategy implementations
- [backtesting/backtester.py](../../backtesting/backtester.py) — Backtesting engine

---

## 10. FAQ & Troubleshooting

- **Q: Why does optimization fail with 'No processed data'?**
  - A: Ensure data is uploaded and processed before starting optimization. See API integration notes above.

- **Q: How do I add a new parameter to optimize?**
  - A: Add it to the strategy, update `PARAM_RANGES` in `optimizer.py`, and update the frontend config.

- **Q: How do I debug optimization runs?**
  - A: Check logs in `optimization_requests.log` and use debug info in results files. Use the `debug_logs` fields in results for step-by-step traces.

---

# Summary of Changes (2025-05-13)

- This file now **fully replaces** the old `optimization/README.md`.
- All unique content from the old README (usage examples, integration code, file storage, error handling/logging) has been merged here.
- The structure is unified for backend developers and maintainers.
- All future updates should be made **only in this file**.
- The old README will be deleted soon; do not reference it in code, docs, or comments.

# END OF FILE 