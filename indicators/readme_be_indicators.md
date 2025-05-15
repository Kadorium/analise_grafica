# Backend Indicators Developer Guide

**Location:** `indicators/`  
**Purpose:** This document explains the architecture, workflow, and extension guidelines for the backend indicators system in the AI-Powered Trading Analysis System. It is intended for developers who need to understand, modify, or extend the technical indicators functionality, and describes how the backend and frontend interact, especially via the Indicators tab in the UI.

---

## Table of Contents
- [Overview](#overview)
- [Backend Indicators Architecture](#backend-indicators-architecture)
- [How Indicators Are Added and Used](#how-indicators-are-added-and-used)
- [API and Data Flow: Backend <-> Frontend](#api-and-data-flow-backend-frontend)
- [How to Add or Modify an Indicator](#how-to-add-or-modify-an-indicator)
- [Indicator Utility Functions](#indicator-utility-functions)
- [Frontend Integration: UI and Workflow](#frontend-integration-ui-and-workflow)
- [Best Practices & Update Policy](#best-practices--update-policy)
- [Checklist for Contributors](#checklist-for-contributors)
- [Plotting Indicators: Frontend-Backend Workflow](#plotting-indicators-frontend-backend-workflow)

---

## Overview

The `indicators/` module contains all technical indicator logic for the backend. Indicators are used to enrich price data with additional columns (e.g., moving averages, RSI, MACD, volatility bands) and are a core part of the system's analysis, backtesting, and visualization features.

- **All indicator logic is written in Python and designed for vectorized, efficient computation using pandas.**
- **Indicators are exposed to the frontend via FastAPI endpoints in `app.py`.**
- **The frontend (see `frontend/index.html` and `frontend/js/app.js`) allows users to select, configure, and visualize indicators.**
- **When plotting indicators, the backend now automatically saves the filtered data (CSV, semicolon-separated), the chart (PNG), and a TXT log file with key information to `results/indicators/`.**

---

## Backend Indicators Architecture

- **Each indicator or indicator family is implemented in its own file:**
  - E.g., `moving_averages.py`, `momentum.py`, `volatility.py`, `adx.py`, `supertrend.py`, etc.
- **All indicator functions are imported and exposed in `indicators/__init__.py`.**
- **The main entry point for combining indicators is `combine_indicators` in `indicator_utils.py`.**
- **Indicator utility functions (plotting, summaries, normalization) are also in `indicator_utils.py`.**

### Key Files
- `indicator_utils.py`: Combines indicators, plots, creates summaries, normalizes signals.
- `moving_averages.py`, `momentum.py`, `volume.py`, `volatility.py`, etc.: Implement specific indicator families.
- `__init__.py`: Exposes all public indicator functions for import elsewhere.

---

## How Indicators Are Added and Used

1. **User selects indicators in the frontend (Indicators tab).**
2. **Frontend sends a POST request to `/api/add-indicators` with the selected configuration.**
3. **Backend receives the config, calls `combine_indicators(data, indicators_config)` to add the requested indicators to the DataFrame.**
4. **The processed DataFrame is used for further analysis, plotting, backtesting, and is available for download/export.**

### Example: Adding Indicators
- The frontend sends a config like:
  ```json
  {
    "moving_averages": {"types": ["sma", "ema"], "sma_periods": [20, 50], "ema_periods": [12, 26]},
    "rsi": {"period": 14},
    "macd": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
    "bollinger_bands": {"window": 20, "num_std": 2}
  }
  ```
- The backend parses this and calls the relevant `add_*_indicator` or `add_*_indicators` functions for each family.

---

## API and Data Flow: Backend <-> Frontend

- **Main endpoints for indicators:**
  - `POST /api/add-indicators` — Adds indicators to the processed data.
  - `POST /api/plot-indicators` — Plots price and selected indicators, returns a base64 image.
- **Data flow:**
  1. User configures indicators in the UI.
  2. Frontend sends config to backend.
  3. Backend updates the DataFrame and returns available indicators and a summary.
  4. Frontend updates dropdowns, checkboxes, and chart options accordingly.

---

## How to Add or Modify an Indicator

**Follow these steps to add a new indicator:**

1. **Create a new file or add to an existing family file in `indicators/`.**
   - E.g., `indicators/my_indicator.py`
2. **Implement the indicator as a vectorized pandas function:**
   - Use the pattern: `def calculate_<indicator_name>(df, period=14, ...) -> pd.Series:`
   - Add a docstring explaining the formula and parameters.
3. **Add an `add_<indicator_name>_indicator(df, ...)` function that adds the result as a new column.**
4. **Import your function in `indicators/__init__.py` and add it to `__all__`.**
5. **Update `combine_indicators` in `indicator_utils.py` to support your indicator (if not already handled generically).**
6. **Test your indicator by adding it via the frontend and checking the results.**
7. **Update this file (`readme_be_indicators.md`) to document your new indicator and any new parameters.**

**If you change indicator parameters, config structure, or add/remove indicators, you MUST update this file and the frontend documentation (`frontend/README_frontend.md`).**

---

## Indicator Utility Functions

- **`combine_indicators(data, indicators_config)`**: Main entry point. Adds all requested indicators to the DataFrame.
- **`plot_price_with_indicators(data, plot_config)`**: Plots price and selected indicators, returns a base64 image for the frontend.
- **`create_indicator_summary(data, last_n_periods=1)`**: Returns a summary dict of indicator values and signals for the last N periods.
- **`normalize_signals_column(df)`**: Ensures the 'signal' column is standardized ("buy", "sell", "hold").

---

## Frontend Integration: UI and Workflow

- **Frontend UI (Indicators tab) is defined in `frontend/index.html`.**
- **Frontend logic for indicators is in `frontend/js/app.js` (and may be modularized in `frontend/js/modules/indicatorPanel.js`).**
- **Workflow:**
  1. User selects indicators and parameters in the UI.
  2. On submit, frontend sends config to `/api/add-indicators`.
  3. Backend processes and returns available indicators and a summary.
  4. Frontend updates indicator dropdowns, checkboxes, and chart options.
  5. User can then plot selected indicators via `/api/plot-indicators`.

---

## Best Practices & Update Policy

- **All indicator code must be vectorized and use pandas/numpy for performance.**
- **Every indicator function must have a clear docstring with parameter and return value descriptions.**
- **If you add, remove, or change any indicator or its parameters/config structure:**
  - Update this file (`readme_be_indicators.md`) with details.
  - Update the frontend documentation (`frontend/README_frontend.md`) and, if needed, the main `README.md`.
  - Ensure the indicator is exposed in `__init__.py` and handled in `combine_indicators`.
  - Test the full workflow via the UI.
- **When plotting indicators, always check that the CSV, PNG, and TXT log files are being saved in `results/indicators/` for traceability and reproducibility.**
- **Document any new indicator in the section below.**

---

## Checklist for Contributors

- [ ] Indicator implemented in its own file or appropriate family file.
- [ ] Docstring and parameter documentation provided.
- [ ] `add_<indicator>_indicator` function adds the indicator to the DataFrame.
- [ ] Imported and exposed in `__init__.py` and `__all__`.
- [ ] Supported in `combine_indicators`.
- [ ] Tested via the frontend UI.
- [ ] This file updated with indicator details and config structure.
- [ ] Frontend documentation updated if config or UI changes.

---

## Example: Documenting a New Indicator

> ### My Custom Oscillator
> - **File:** `indicators/my_custom_oscillator.py`
> - **Function:** `calculate_my_custom_oscillator(df, period=10)`
> - **Config Example:** `{ "my_custom_oscillator": { "period": 10 } }`
> - **Description:** Calculates ... (formula/logic here)
> - **Added to:** `__init__.py`, `combine_indicators`, and this file.

---

**If you make any change to indicators, you MUST update this file and the frontend documentation.**

---

## Plotting Indicators: Frontend-Backend Workflow

- **User selects indicators in the UI:**
  - The UI provides two multi-select lists: one for `main_indicators` (overlays on price) and one for `subplot_indicators` (separate subplots below price).
  - All available indicators (e.g., `sma_20`, `ema_12`, `bb_upper`, `rsi`, `macd`, etc.) are shown as options. The user can select any combination.
- **When the user clicks 'Plot Chart':**
  - The frontend gathers the selected `main_indicators` and `subplot_indicators` and sends them in a POST request to `/api/plot-indicators` as part of the `plot_config` JSON:
    ```json
    {
      "main_indicators": ["sma_20", "bb_upper", ...],
      "subplot_indicators": ["rsi", "macd", ...],
      "title": "Price Chart with Selected Indicators",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD"
    }
    ```
- **Backend processing:**
  - The backend receives the config and calls `plot_price_with_indicators`, which generates a matplotlib chart with the requested overlays and subplots.
  - The chart is returned as a base64-encoded PNG image in the response.
  - **New: The backend also automatically saves:**
    - The filtered data as a semicolon-separated CSV file in `results/indicators/`.
    - The chart as a PNG file in `results/indicators/`.
    - A TXT log file with the plot config, file paths, data shape, columns, and timestamp in `results/indicators/`.
- **Frontend display:**
  - The frontend receives the base64 image and displays it in the chart area.
  - All selected indicators should be plotted as requested. If you add new indicators, ensure they are available in the UI and handled in the backend plotting logic.

**If you change the indicator plotting logic, indicator selection UI, or the API contract, update this section and the frontend documentation accordingly.** 