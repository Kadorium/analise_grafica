# AI-Powered Trading Analysis System

A comprehensive trading analysis platform with Python backend and HTML frontend enabling users to analyze stocks, implement technical indicators, backtest trading strategies, and optimize parameters without writing any code.

## 📋 Table of Contents

- [Features](#-features)
- [Project Overview](#-project-overview)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Deployment Guide](#-deployment-guide)
- [Using the Application](#-using-the-application)
- [System Architecture](#-system-architecture)
- [Directory Structure](#-directory-structure)
- [Module Details](#-module-details)
- [API Reference](#-api-reference)
- [Extending the System](#-extending-the-system)
- [Development Guide](#-development-guide)
- [Configuration Options](#-configuration-options)
- [License](#-license)

## 🚀 Features

- **Data Loading & Cleaning**: Upload CSV files with historical stock data
- **Technical Indicators**: Apply various indicators (Moving Averages, RSI, MACD, Bollinger Bands, etc.)
- **Trading Strategies**: Choose from pre-built strategies (Trend Following, Mean Reversion, Breakout)
- **Backtesting Engine**: Test strategies against historical data
- **Optimization**: Find the best parameters for your strategies
- **User-Friendly Interface**: Control everything through an intuitive HTML interface
- **Export Results**: Download analysis as PDF/Excel documents
- **Configuration Management**: Save and load your analysis setups

## 🧭 Project Overview

### Purpose
This system provides a complete trading analysis platform for financial analysts, traders, and investors who need technical analysis capabilities without programming knowledge. It bridges the gap between sophisticated trading algorithms and user-friendly interfaces.

### Target Users
- **Financial analysts** who need to quickly test trading hypotheses
- **Retail traders** looking to backtest strategies before live trading
- **Investment researchers** analyzing historical market behavior
- **Trading educators** demonstrating technical analysis concepts
- **Non-programmers** who need professional-grade trading analysis tools

### Core Technologies
- **Backend**: Python 3.8+, FastAPI, Pandas, NumPy, scikit-learn
- **Data Processing**: Pandas, NumPy
- **Technical Analysis**: Custom indicators module
- **Visualization**: Chart.js, Matplotlib, Seaborn
- **Frontend**: HTML, CSS, JavaScript
- **API**: FastAPI with asynchronous endpoints
- **Document Generation**: ReportLab, OpenPyXL
- **Optimization**: Integrated parameter optimization using scikit-learn

## 📋 Requirements

- Python 3.8+
- Web browser (Chrome, Firefox, Edge recommended)
- 4GB+ RAM for larger datasets or intensive optimization
- 50MB+ disk space (excluding virtual environment)

## 💻 Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd trading-analysis-system
   ```

2. Create a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 📦 Deployment Guide

### Local Development
```bash
# Using the start script
python start.py

# Or directly with uvicorn
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment

1. **Using Gunicorn (Linux/macOS)**:
   ```bash
   gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   ```

2. **Using Docker**:
   ```bash
   # Build the image
   docker build -t trading-analysis-system .

   # Run the container
   docker run -p 8000:8000 trading-analysis-system
   ```

3. **With Nginx (as reverse proxy)**:
   - Configure Nginx to forward requests to the application
   - Set up SSL for secure connections
   - Consider using supervisor or systemd for process management

4. **Performance Considerations**:
   - For heavy optimization workloads, consider increasing worker count
   - Log rotation should be configured for `optimization_requests.log`
   - Consider using Redis for caching frequently accessed data

## 🏃‍♂️ Using the Application

### Step-by-Step Guide

1. **Upload Data**
   - Click on the "Upload Data" tab
   - Select your CSV file (must include columns: Date, Open, High, Low, Close, Volume)
   - Click "Upload" and then "Process Data"

2. **Add Indicators**
   - Navigate to the "Indicators" tab
   - Select desired indicators and set parameters
   - Click "Apply Indicators"
   - View the chart with indicators

3. **Choose a Strategy**
   - Go to the "Strategy" tab
   - Select a trading strategy
   - Customize parameters or use defaults
   - Click "Apply Strategy"

4. **Run Backtest**
   - Go to the "Backtest" tab
   - Set initial capital and commission rate
   - Click "Run Backtest"
   - View performance metrics and trade history

5. **Optimize Strategy (Optional)**
   - Navigate to the "Optimization" tab
   - Set parameter ranges and optimization metric
   - Click "Optimize Strategy"
   - View and apply optimized parameters

6. **Export Results**
   - Go to the "Results" tab
   - Choose export format (PDF or Excel)
   - Click "Export"

### API Usage Examples

#### Backtesting a Moving Average Crossover Strategy

**API Request:**
```json
POST /api/backtest
{
  "strategy": "ma_crossover",
  "parameters": {
    "short_period": 10,
    "long_period": 50
  },
  "initial_capital": 10000,
  "commission": 0.001
}
```

**API Response:**
```json
{
  "status": "success",
  "metrics": {
    "total_return": 0.34,
    "sharpe_ratio": 0.78,
    "max_drawdown": 0.15,
    "win_rate": 0.56
  },
  "trades": [...],
  "equity_curve": [...],
  "chart_url": "/results/charts/backtest_12345.png"
}
```

#### Optimizing an RSI Strategy

**API Request:**
```json
POST /api/optimize
{
  "strategy": "rsi_reversal",
  "parameters": {
    "rsi_period": {"min": 7, "max": 21, "step": 2},
    "overbought": {"min": 70, "max": 80, "step": 1},
    "oversold": {"min": 20, "max": 30, "step": 1}
  },
  "optimization_target": "sharpe_ratio",
  "max_iterations": 100
}
```

**API Response:**
```json
{
  "status": "queued",
  "job_id": "opt_789102",
  "estimated_time": "120 seconds"
}
```

**Retrieving Results:**
```json
GET /api/optimize/status/opt_789102

Response:
{
  "status": "completed",
  "best_parameters": {
    "rsi_period": 14,
    "overbought": 76,
    "oversold": 24
  },
  "best_value": 1.23,
  "result_chart_url": "/results/optimization/opt_789102.png",
  "all_results": [...]
}
```

## 🧱 System Architecture

### High-Level Architecture

```
┌───────────────────────┐     ┌───────────────────────────────────────────┐
│                       │     │                                           │
│     Web Browser       │     │                 Backend                   │
│                       │     │                                           │
│  ┌─────────────────┐  │     │  ┌───────────┐        ┌───────────────┐  │
│  │                 │  │     │  │           │        │               │  │
│  │  HTML/CSS/JS    │◄─┼─────┼──┤  FastAPI  │◄───────┤  Core Modules │  │
│  │  Frontend       │  │     │  │  Routes   │        │               │  │
│  │                 │  │     │  │           │        │               │  │
│  └────────┬────────┘  │     │  └───────────┘        └───────┬───────┘  │
│           │           │     │                               │          │
│           │           │     │                               │          │
│  ┌────────▼────────┐  │     │  ┌───────────┐        ┌───────▼───────┐  │
│  │                 │  │     │  │           │        │               │  │
│  │  Chart.js       │◄─┼─────┼──┤  Results  │◄───────┤  Processing   │  │
│  │  Visualization  │  │     │  │  API      │        │  Pipeline     │  │
│  │                 │  │     │  │           │        │               │  │
│  └─────────────────┘  │     │  └───────────┘        └───────────────┘  │
│                       │     │                                           │
└───────────────────────┘     └───────────────────────────────────────────┘
```

### Key Architectural Patterns

1. **Client-Server Architecture**
   - Clear separation between frontend (client) and backend (server)
   - Communication via RESTful API endpoints
   - Stateless interactions with state maintained in session storage or database

2. **Modular Design**
   - Each major function (indicators, strategies, backtesting) is in its own module
   - Clear interfaces between components
   - Minimal dependencies between modules

3. **Processing Pipeline**
   - Data flows through distinct processing stages:
     - Data loading → Preprocessing → Indicator calculation → Strategy application → Backtest execution → Results analysis
   - Each stage has well-defined inputs and outputs

4. **Factory Pattern**
   - Used for creating indicators and strategies dynamically
   - Allows for registration of new components without modifying core code

5. **Observer Pattern**
   - Used for status updates during long-running operations
   - Allows frontend to receive progress updates during optimization

6. **Repository Pattern**
   - Used for data access and results storage
   - Abstracts storage mechanisms from business logic

## 🗂️ Directory Structure

### High-Level Structure

```
trading-analysis-system/
├── app.py                 # Main FastAPI application
├── start.py               # Startup script
├── config.py              # Global configuration
├── requirements.txt       # Python dependencies
├── data/                  # Data handling modules
├── frontend/              # UI files (HTML, CSS, JS)
├── indicators/            # Technical indicators implementation
├── strategies/            # Trading strategies implementation
├── backtesting/           # Backtesting engine
├── optimization/          # Strategy optimization modules
├── results/               # Output and reports storage
└── _archive/              # Legacy code
```

### Detailed Structure

#### Core Files
- **`app.py`**: Main application entry point using FastAPI
- **`start.py`**: Convenience script for starting the application
- **`config.py`**: Global configuration settings
- **`run_advanced_backtest.py`**: CLI script for running backtests directly
- **`advanced_strategy_optimizer.py`**: CLI script for advanced optimization

#### Data Management (`data/`)
- **Data loaders** for different file formats
- **Data cleaning** and normalization utilities
- **Price data validation** and error correction
- **Historical data caching** mechanisms
- **Sample data** files for testing and demonstration

#### User Interface (`frontend/`)
- **`css/`**: Stylesheet files
- **`js/`**: Client-side JavaScript
  - **`modules/`**: Chart rendering, form handling, API communication
  - **`utils/`**: Data formatting, validation, UI helpers

#### Technical Analysis (`indicators/`)
- **Moving averages** (Simple, Exponential, Weighted)
- **Oscillators** (RSI, Stochastic, MACD)
- **Volume indicators** (OBV, Volume Profile)
- **Volatility indicators** (Bollinger Bands, ATR)
- **Trend indicators** (ADX, Ichimoku)

#### Trading Strategies (`strategies/`)
- **Trend following** strategies
- **Mean reversion** patterns
- **Breakout detection** algorithms
- **Volatility-based** strategies
- **Multi-indicator** composite strategies

#### Backtesting Engine (`backtesting/`)
- **Position sizing** and risk management
- **Trade execution** simulation
- **Performance metrics** calculation
- **Trade logging** and analysis
- **Simulation parameters** and environment settings

#### Parameter Optimization (`optimization/`)
- **Optimization algorithms** (Grid Search, Bayesian, Genetic)
- **Objective function** definitions
- **Parallel processing** for performance
- **Results persistence** and comparison
- **Visualization** of optimization landscapes

#### Output Storage (`results/`)
- **Saved configurations** for reproducible results
- **Optimization results** and parameter studies

## 📊 Module Details

### Data Processing Flow

1. **Data Acquisition**:
   - User uploads CSV or specifies a data source
   - Data is validated and processed
   - Raw data is converted to pandas DataFrame with proper datetime indexing

2. **Data Preprocessing**:
   - Missing values are handled according to configuration
   - Timestamps are normalized
   - Optional resampling to different timeframes
   - Data is cached for performance

3. **Indicator Application**:
   - User selects indicators and parameters
   - Indicators are calculated based on the price data
   - Results are merged into the main DataFrame

4. **Strategy Selection**:
   - User chooses a trading strategy and sets parameters
   - Strategy generates entry/exit signals based on indicators and price data

5. **Backtesting Execution**:
   - Simulates trades based on strategy signals
   - Position sizing and risk management rules are applied
   - Trades are logged with entry/exit prices, timestamps, and results
   - Performance metrics are calculated

6. **Results Processing**:
   - Performance statistics are calculated
   - Visualizations are generated
   - Results are stored and prepared for the frontend

7. **Optimization Flow** (when triggered):
   - User defines parameter ranges and optimization target
   - Parameters are systematically varied according to the algorithm
   - Each parameter set is evaluated through backtesting
   - Results are compared to find optimal settings
   - Best parameters and visualizations are sent to the frontend

## 📡 API Reference

### Key API Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/data/upload` | POST | Upload and process price data | File upload |
| `/api/data/available` | GET | List available data sources | None |
| `/api/indicators/list` | GET | Get available indicators | None |
| `/api/indicators/apply` | POST | Calculate and apply indicators | Indicator type, parameters |
| `/api/strategies/list` | GET | Get available strategies | None |
| `/api/strategies/apply` | POST | Apply strategy to data | Strategy type, parameters |
| `/api/backtest/run` | POST | Execute backtest | Strategy, parameters, capital |
| `/api/optimize/start` | POST | Begin optimization process | Strategy, parameter ranges, objective |
| `/api/optimize/status/{job_id}` | GET | Check optimization status | Job ID |
| `/api/results/export` | POST | Generate and download results | Format (PDF/Excel) |

### API Communication

- All endpoints use JSON for request/response
- Authentication is handled via API key or session cookie
- Long-running operations return a job ID for status polling
- Error responses include descriptive messages and error codes

## 🔧 Extending the System

### Adding a New Indicator

1. Create a new file in `indicators/` (e.g., `indicators/custom_indicator.py`)
2. Implement the indicator calculation function:

```python
# indicators/custom_indicator.py
import pandas as pd
import numpy as np

def calculate_custom_indicator(df, period=14, column='close'):
    """
    Calculate a custom indicator based on price data.
    
    Args:
        df (pd.DataFrame): Price data with OHLCV columns
        period (int): Lookback period
        column (str): Column to use for calculation
        
    Returns:
        pd.Series: Calculated indicator values
    """
    # Implementation logic here
    values = df[column].rolling(period).mean() / df[column].rolling(period).std()
    return values
```

3. Register the indicator in `indicators/__init__.py` or `indicators/factory.py`
4. Update the UI options in the frontend

### Adding a New Strategy

1. Create a new file in `strategies/` (e.g., `strategies/custom_strategy.py`)
2. Implement the strategy class:

```python
# strategies/custom_strategy.py
from strategies.base_strategy import BaseStrategy

class CustomStrategy(BaseStrategy):
    """
    Custom trading strategy implementation.
    
    Args:
        param1 (int): First parameter description
        param2 (float): Second parameter description
    """
    
    def __init__(self, param1=10, param2=0.5):
        super().__init__()
        self.param1 = param1
        self.param2 = param2
        
    def generate_signals(self, data):
        """
        Generate buy/sell signals based on the strategy logic.
        
        Args:
            data (pd.DataFrame): Price and indicator data
            
        Returns:
            pd.DataFrame: DataFrame with buy/sell signals
        """
        signals = data.copy()
        # Strategy logic implementation
        signals['signal'] = 0
        # Buy/sell conditions
        # ...
        return signals
```

3. Register the strategy in `strategies/__init__.py` or `strategies/factory.py`
4. Update the UI options in the frontend

### Adding a New Optimization Algorithm

1. Create a file in `optimization/algorithms/` 
2. Implement the algorithm interface
3. Register it in the algorithm factory

## 👨‍💻 Development Guide

### Code Structure Conventions

1. **File Naming**:
   - Modules: `snake_case.py` (e.g., `moving_average.py`)
   - Classes: `PascalCase` (e.g., `class RSIStrategy`)
   - Constants: `UPPER_CASE` (e.g., `DEFAULT_PERIOD`)

2. **Module Organization**:
   - Each technical indicator goes in `indicators/`
   - Each trading strategy goes in `strategies/`
   - Common utilities belong in respective module's `utils.py`

### Programmatic Integration

```python
# Example programmatic usage of the system
from data.loader import load_data
from indicators.factory import create_indicator
from strategies.factory import create_strategy
from backtesting.engine import backtest
from optimization.controller import OptimizationController

# Load data
df = load_data('/path/to/data.csv')

# Apply indicators
rsi = create_indicator('rsi', period=14)
df['rsi'] = rsi.calculate(df)

# Create strategy
strategy = create_strategy('ma_crossover', short_period=10, long_period=50)

# Run backtest
results = backtest(df, strategy, initial_capital=10000)

# Optimize strategy
controller = OptimizationController(
    strategy_name='ma_crossover',
    param_ranges={'short_period': range(5, 20), 'long_period': range(30, 100)},
    objective='sharpe_ratio'
)
best_params = controller.optimize(df)
```

## 🔧 Configuration Options

### Environment Variables

The system supports the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATA_DIR` | Override default data directory | `./data` |
| `PORT` | Change default port | `8000` |
| `LOG_LEVEL` | Set logging verbosity | `INFO` |
| `OPTIMIZATION_WORKERS` | Number of parallel workers | `4` |

### Configuration File

The `config.py` file contains default settings that can be modified:

```python
# Key configuration options
DEFAULT_INDICATORS = ['sma', 'ema', 'rsi', 'macd']
DEFAULT_COMMISSION = 0.001
DEFAULT_SLIPPAGE = 0.0005
DEFAULT_RISK_PER_TRADE = 0.02  # 2% risk per trade
```

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
