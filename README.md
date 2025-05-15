# AI-Powered Trading Analysis System

**GitHub Repository:** [https://github.com/Kadorium/analise_grafica](https://github.com/Kadorium/analise_grafica)

A comprehensive modular trading analysis platform with Python backend and HTML frontend that enables users to analyze stocks, implement technical indicators, backtest trading strategies, and optimize parameters without writing any code.

## 📋 Table of Contents

- [Features](#-features)
- [Project Overview](#-project-overview)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Running the Application](#-running-the-application)
- [Using the Application](#-using-the-application)
- [System Architecture](#-system-architecture)
- [Directory Structure](#-directory-structure)
- [Backend Workflow](#-backend-workflow)
- [Frontend-Backend Integration](#-frontend-backend-integration)
- [API Reference](#-api-reference)
- [Deployment Guide](#-deployment-guide)
- [Development & Contribution](#-development--contribution)
- [Extending the System](#-extending-the-system)
- [Advanced Configuration](#-advanced-configuration)
- [Autonomy for AI Tools](#-autonomy-for-ai-tools)
- [License](#-license)

## 🚀 Features

- **Data Loading & Cleaning**: Upload and process CSV files with historical stock data
- **Technical Indicators**: Apply various indicators (Moving Averages, RSI, MACD, Bollinger Bands, etc.)
- **Trading Strategies**: Choose from pre-built strategies (Trend Following, Mean Reversion, Breakout)
- **Backtesting Engine**: Test strategies against historical data
- **Optimization**: Find optimal parameters for your strategies
- **User-Friendly Interface**: Control everything through an intuitive HTML interface
- **Export Results**: Download analysis as PDF/Excel documents
- **Configuration Management**: Save and load analysis setups

## 🧭 Project Overview

### Purpose

The **AI-Powered Trading Analysis System** empowers traders, investors and financial analysts by providing a comprehensive platform for stock analysis and strategy testing without requiring programming skills. It bridges the gap between sophisticated trading algorithms and user-friendly interfaces.

### Target Users

- **Financial analysts** who need to quickly test trading hypotheses
- **Retail traders** looking to backtest strategies before live trading
- **Investment researchers** analyzing historical market behavior
- **Trading educators** demonstrating technical analysis concepts
- **Non-programmers** who need professional-grade trading analysis tools

### Core Technologies

- **Backend**:
  - Python 3.8+
  - FastAPI for web framework
  - Pandas & NumPy for data manipulation
  - Scikit-learn for optimization components
  - Matplotlib & Seaborn for data visualization
- **Frontend**:
  - HTML/CSS/JavaScript for user interface
  - Chart.js for interactive charts and visualization
- **Other Tools**:
  - ReportLab & OpenPyXL for exporting results

## 📋 Requirements

- Python 3.8 or higher
- Web browser (Chrome, Firefox, Edge recommended)
- 4GB+ RAM for larger datasets or intensive optimization
- 50MB+ disk space (excluding virtual environment)

## 💻 Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd trading-analysis-system
   ```

2. **Create a virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 🏃‍♂️ Running the Application

1. **Start the application:**
   ```bash
   # Using the provided script
   python start.py
   
   # Or directly with uvicorn
   python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Access the application:**
   ```
   http://localhost:8000
   ```

## 📊 Using the Application

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

## 🧱 System Architecture

### High-Level Architecture

The system follows a client-server model with clear separation between components:

```
+-------------------+       HTTP Requests       +-------------------+
|    Frontend       | <-----------------------> |    Backend        |
| (HTML/CSS/JS)     |                           | (FastAPI/Python)  |
| - UI Interaction  |                           | - API Endpoints   |
| - Chart.js Charts |                           | - Data Processing |
+-------------------+                           | - Analysis Logic  |
                                                +-------------------+
                                                      |
                                                      v
+-------------------+  +-------------------+  +-------------------+
| Data Management   |  | Indicators        |  | Strategies        |
| - CSV Loading     |  | - RSI, MACD, etc. |  | - Trend Following |
| - Cleaning        |  | - Visualization   |  | - Signal Gen      |
+-------------------+  +-------------------+  +-------------------+
                                                      |
                                                      v
+-------------------+  +-------------------+
| Backtesting       |  | Optimization      |
| - Performance     |  | - Parameter Tuning|
| - Equity Curves   |  | - Background Tasks|
+-------------------+  +-------------------+
```

### Key Architectural Patterns

1. **Frontend-Backend Separation**: The system uses a client-server model where the frontend (HTML/CSS/JavaScript) is served by a FastAPI backend, communicating via RESTful API endpoints.

2. **Modular Backend Structure**: The backend is organized into distinct modules for data handling, indicators, strategies, backtesting, and optimization, promoting maintainability and scalability.

3. **Factory Pattern**: Used in strategy creation (`strategies/__init__.py`) to instantiate strategy objects based on type.

4. **Singleton Pattern**: Applied in configuration management (`config.py`) to ensure a single configuration instance across the application.

5. **Observer Pattern**: For status updates during optimization tasks.

6. **Adapter Pattern**: Used in `StrategyAdapter` class to make function-based strategies compatible with the backtesting engine.

## 🗂️ Directory Structure

### High-Level Directory Structure

```
Analise_Grafica/
├── _archive/                # Archived code and data
│   └── debug/               # Debugging files
├── app.py                   # Main FastAPI application file
├── backtesting/             # Backtesting modules
│   └── backtester.py        # Core backtesting implementation
├── config.py                # Application configuration settings
├── data/                    # Data management modules
│   └── sample/              # Sample CSV datasets
├── frontend/                # User interface files
│   ├── css/                 # CSS stylesheets
│   └── js/                  # JavaScript files
│       ├── modules/         # JS modules
│       └── utils/           # JS utility functions
├── indicators/              # Technical indicators implementation
├── optimization/            # Strategy optimization modules
├── results/                 # Output storage
│   ├── configs/             # Saved configurations
│   └── optimization/        # Optimization results
├── strategies/              # Trading strategy implementations
├── requirements.txt         # Python dependencies
├── start.py                 # Application startup script
├── run_advanced_backtest.py # Advanced backtesting script
├── .gitignore               # Git ignore rules
├── LICENSE                  # License information
└── *.bat                    # Windows batch scripts
```

### Detailed Structure

#### Core Files
- **`app.py`**: Main backend application file using FastAPI. It defines API endpoints, serves the frontend, and orchestrates data processing, strategy application, and result generation.
- **`config.py`**: Manages application configuration settings, providing default parameters for indicators, strategies, and backtesting.
- **`start.py`**: A script to start the FastAPI backend server, with options to configure host, port, and auto-open a browser.
- **`run_advanced_backtest.py`**: Script for executing advanced backtesting scenarios, allowing quick testing of strategies with minimal configuration.

#### Data Management (`data/`)
- **`sample/`**: Contains sample CSV datasets for testing and demonstration purposes.
- **`data_loader.py`**: Handles loading and cleaning of CSV data files, ensuring proper formatting for analysis.

#### Technical Analysis (`indicators/`)
- **`indicator_utils.py`**: Utility functions to combine and plot various indicators like Moving Averages, RSI, etc.
- **Module files for each indicator type**: Separate modules for different indicator categories (moving averages, momentum indicators, volatility indicators, etc.)

#### Trading Strategies (`strategies/`)
- **`__init__.py`**: Registers all available strategies and provides a factory function to create strategy instances.
- **Strategy implementation files**: Individual files for each strategy (e.g., `trend_following.py`, `mean_reversion.py`).

#### Backtesting Engine (`backtesting/`)
- **`backtester.py`**: Core backtesting class to simulate trading strategies on historical data, calculating performance metrics like returns and drawdowns.

#### Parameter Optimization (`optimization/`)
- **`optimizer.py`**: Implements grid search and other optimization techniques to find the best strategy parameters.
- **`status.py`**: Tracks the status of optimization tasks.
- **`charts.py`**, **`metrics.py`**, **`results.py`**: Handle visualization, metric calculation, and result storage for optimization.

#### Output Storage (`results/`)
- **`configs/`**: Stores configuration files related to specific analysis runs.
- **`optimization/`**: Contains detailed logs and outputs from optimization processes.

## 🔄 Backend Workflow

### Data Processing Pipeline

1. **Data Upload**
   - User uploads CSV via `/api/upload` endpoint
   - Backend validates file format and required columns

2. **Data Processing**
   - `/api/process-data` endpoint cleans and prepares data
   - Ensures Date, Open, High, Low, Close, Volume columns exist
   - Converts data types and handles missing values

3. **Indicator Application**
   - `/api/add-indicators` applies selected technical indicators
   - Computes indicator values using functions from `indicators/` module
   - Merges results with original data

4. **Strategy Selection & Backtesting**
   - `/api/run-backtest` instantiates selected strategy with parameters
   - `Backtester` class simulates trading on historical data
   - Generates buy/sell signals and calculates performance metrics

5. **Results & Export**
   - Performance metrics returned to frontend
   - `/api/export-results/{format}` generates PDF or Excel reports

### Optimization Workflow

1. **Optimization Request**
   - User submits request via `/api/optimize-strategy`
   - Request logged and background task created

2. **Parameter Search**
   - `optimizer.py` iterates through parameter combinations
   - Each combination evaluated by running a backtest
   - Performance metrics calculated for each parameter set

3. **Status Tracking & Results**
   - `status.py` tracks optimization progress
   - `/api/optimization-status` reports current status
   - Results saved to `results/optimization/` directory
   - Optimal parameters returned to frontend

## 📡 Frontend-Backend Integration

### Communication Flow

- Frontend makes asynchronous HTTP requests to backend endpoints using JavaScript's `fetch` API
- Backend responds with JSON data containing results
- Frontend parses JSON and updates UI accordingly (charts, tables, metrics)

### Key Integration Points

1. **Data Upload**
   - Frontend sends CSV file using FormData
   - Backend processes and responds with success/error message

2. **Chart Rendering**
   - Backend sends processed data and indicators
   - Frontend renders charts using Chart.js

3. **Backtesting Results**
   - Backend sends performance metrics and trade signals
   - Frontend displays metrics and renders equity curve

4. **Optimization Status**
   - Frontend polls `/api/optimization-status` for updates
   - Backend responds with current progress percentage

## 📡 API Reference

### Key API Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/upload` | POST | Upload CSV file | File upload |
| `/api/process-data` | POST | Process raw data | Data cleaning options |
| `/api/add-indicators` | POST | Apply technical indicators | Indicator types, parameters |
| `/api/run-backtest` | POST | Execute backtest | Strategy, parameters, capital |
| `/api/optimize-strategy` | POST | Begin optimization process | Strategy, parameter ranges, objective |
| `/api/optimization-status` | GET | Check optimization status | Task ID |
| `/api/export-results/{format}` | GET | Generate and download results | Format (PDF/Excel) |

### Example API Usage

#### Backtest Request/Response

**Request (POST /api/run-backtest)**:
```json
{
  "strategy_config": {
    "strategy_type": "sma_crossover_strategy",
    "parameters": { 
      "fast_period": 20, 
      "slow_period": 50 
    }
  },
  "backtest_config": {
    "initial_capital": 10000.0,
    "commission": 0.001,
    "start_date": "2020-01-01",
    "end_date": "2022-12-31"
  }
}
```

**Response**:
```json
{
  "success": true,
  "strategy_name": "SMA Crossover Strategy",
  "performance_metrics": {
    "total_return": 0.1523,
    "sharpe_ratio": 1.25,
    "max_drawdown": -0.087
  },
  "signals": [
    {"date": "2020-01-15", "price": 125.30, "action": "BUY", "quantity": 80},
    {"date": "2020-03-22", "price": 105.75, "action": "SELL", "quantity": 80}
  ]
}
```

#### Optimization Request/Response

**Request (POST /api/optimize-strategy)**:
```json
{
  "strategy_type": "mean_reversion",
  "param_ranges": {
    "rsi_period": [7, 14, 21],
    "oversold": [20, 30]
  },
  "metric": "sharpe_ratio"
}
```

**Response**:
```json
{
  "status": "running",
  "task_id": "opt_20230510_143022"
}
```

**Status Check Request/Response**:
```json
// GET /api/optimization-status?task_id=opt_20230510_143022

{
  "status": "completed",
  "best_params": { 
    "rsi_period": 14, 
    "oversold": 20 
  },
  "best_value": 1.8
}
```

## 📦 Deployment Guide

### Local Development

Follow the [Installation](#-installation) and [Running the Application](#-running-the-application) sections.

### Production Deployment

#### Using Gunicorn

For production deployment with multiple workers:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:8000
```

#### Docker Deployment

1. **Create a Dockerfile**:
   ```dockerfile
   FROM python:3.8-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app:app", "--bind", "0.0.0.0:8000"]
   ```

2. **Build and run**:
   ```bash
   docker build -t trading-system .
   docker run -p 8000:8000 trading-system
   ```

#### Nginx Configuration

Set up Nginx as a reverse proxy:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### Performance Considerations

- Use asynchronous tasks for optimization to prevent blocking
- Configure proper logging for debugging
- Set up multiple backend instances behind a load balancer for high traffic
- Log rotation should be configured for `optimization_requests.log`
- Consider using Redis for caching frequently accessed data

## 👨‍💻 Development & Contribution

### Code Organization

- **File Naming**: 
  - Python files use lowercase with underscores (snake_case) (e.g., `data_loader.py`)
  - Strategy and indicator files follow descriptive naming patterns (e.g., `trend_following.py`, `moving_averages.py`)

- **Module Structure**: 
  - Group related functionality in dedicated modules
  - Include docstrings and type hints in Python code

### Adding New Components

#### Adding a New Indicator

1. Create a new file in `indicators/` or add to an existing one based on category
2. Define the indicator calculation function:
   ```python
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
3. Update `combine_indicators` in `indicators/indicator_utils.py` to include the new indicator
4. Update default configurations in `config.py` if necessary

#### Adding a New Strategy

1. Create a new file in `strategies/` (e.g., `new_strategy.py`)
2. Define a `generate_signals` function or class with required methods:
   ```python
   class NewStrategy:
       def __init__(self, parameters=None):
           self.parameters = parameters or {}
       
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
           
       def get_parameters(self):
           """Return the strategy parameters"""
           return self.parameters
   ```
3. It will be automatically registered by `strategies/__init__.py` if it follows the naming convention
4. Test the strategy using `run_advanced_backtest.py`

### Testing Guidelines

- Use `run_advanced_backtest.py` for quick strategy testing
- Test API endpoints with tools like Postman or curl
- Verify frontend-backend integration with browser developer tools

## 🔧 Extending the System

### Adding a New Optimization Algorithm

1. Create a file in `optimization/algorithms/` (e.g., `optimization/algorithms/genetic_algorithm.py`)
2. Implement the optimization algorithm:
   ```python
   def optimize_genetic(strategy_class, data, param_ranges, objective_function, **kwargs):
       """
       Perform genetic algorithm optimization for strategy parameters.
       
       Args:
           strategy_class: Strategy class to optimize
           data (pd.DataFrame): Historical price data
           param_ranges (dict): Dictionary mapping parameter names to ranges
           objective_function (callable): Function to maximize/minimize
           **kwargs: Additional parameters for the genetic algorithm
           
       Returns:
           dict: Best parameters found
           float: Best objective value
       """
       # Implementation of genetic algorithm
       # ...
       return best_params, best_value
   ```
3. Register the algorithm in the optimization controller
4. Add UI options if applicable

### Advanced Strategy Development

For more complex strategies, consider:

1. Inheriting from a base strategy class:
   ```python
   from strategies.base_strategy import BaseStrategy
   
   class AdvancedStrategy(BaseStrategy):
       def __init__(self, **kwargs):
           super().__init__()
           self.params = kwargs
           
       def generate_signals(self, data):
           # Advanced logic
           return signals
   ```

2. Combining multiple indicators:
   ```python
   from indicators.moving_averages import calculate_sma
   from indicators.oscillators import calculate_rsi
   
   def setup_indicators(data, params):
       data['sma'] = calculate_sma(data, period=params['sma_period'])
       data['rsi'] = calculate_rsi(data, period=params['rsi_period'])
       return data
   ```

## 🔧 Advanced Configuration

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

### Custom Configurations

Save and load custom configurations through the UI, which are stored in `results/configs/` directory.

## 🔍 Autonomy for AI Tools

If you are an LLM or AI tool reading this:

- ✅ **Indicator Development**: You can generate new indicators inside `indicators/` by adding logic to existing files or creating new ones following the structure.
- ✅ **Strategy Creation**: You can create new strategies under `strategies/` by defining a `generate_signals` function or class with necessary methods.
- ✅ **Testing Methods**: Use `run_advanced_backtest.py` for quick testing or the full UI workflow for comprehensive evaluation.
- ✅ **Integration Requirements**: Use `app.py` and its defined endpoints to interact with the UI for user-facing operations.
- ✅ **Output Storage**: Store optimization results using the `optimization/results.py` interface to maintain consistency with existing workflows.
- ✅ **Code Standards**: Ensure any new code adheres to the modular structure and uses existing utility functions where applicable.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
