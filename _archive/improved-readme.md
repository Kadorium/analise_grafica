# AI-Powered Trading Analysis System

A modular trading analysis system with a Python backend and HTML frontend that enables users to analyze stocks, implement technical indicators, backtest trading strategies, and optimize parameters without writing code.

## Table of Contents
- [Features](#-features)
- [Project Overview](#-project-overview)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Running the Application](#-running-the-application)
- [How to Use](#-how-to-use)
- [Directory Structure](#-directory-structure)
- [Architecture & Design](#-architecture--design)
- [Backend Workflow](#-backend-workflow)
- [Frontend-Backend Integration](#-frontend-backend-integration)
- [API Examples](#-api-examples)
- [Deployment Guide](#-deployment-guide)
- [Development & Contribution](#-development--contribution)
- [Autonomy for AI Tools](#-autonomy-for-ai-tools)
- [Advanced Configuration](#-advanced-configuration)
- [Contributing](#-contributing)
- [License](#-license)

## 🚀 Features

- **Data Loading & Cleaning**: Upload and process CSV files with historical stock data
- **Technical Indicators**: Apply indicators (Moving Averages, RSI, MACD, Bollinger Bands, etc.)
- **Trading Strategies**: Choose from pre-built strategies (Trend Following, Mean Reversion, Breakout)
- **Backtesting Engine**: Test strategies against historical data
- **Optimization**: Find optimal parameters for strategies
- **User-Friendly Interface**: Control everything through an intuitive HTML interface
- **Export Results**: Download analysis as PDF/Excel documents
- **Configuration Management**: Save and load analysis setups

## 🧭 Project Overview

The **AI-Powered Trading Analysis System** empowers traders and investors by providing a comprehensive platform for stock analysis and strategy testing without programming skills. It targets non-programmers and trading enthusiasts who want to leverage technical analysis through an intuitive user interface.

**Key Technologies:**
- **Python 3.8+**: Core backend language
- **FastAPI**: Web framework for APIs
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Matplotlib**: Visualization for charts
- **Chart.js**: Interactive frontend charts
- **HTML/CSS/JavaScript**: Frontend technologies

## 📋 Requirements

- Python 3.8+
- Web browser (Chrome, Firefox, Edge recommended)

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
   python -m uvicorn app:app --reload
   ```

2. **Access the application:**
   ```
   http://localhost:8000
   ```

## 📊 How to Use

### Step 1: Upload Data
1. Click on the "Upload Data" tab
2. Select your CSV file (must include columns: Date, Open, High, Low, Close, Volume)
3. Click "Upload" and then "Process Data"

### Step 2: Add Indicators
1. Navigate to the "Indicators" tab
2. Select desired indicators and set parameters
3. Click "Apply Indicators"
4. View the chart with indicators

### Step 3: Choose a Strategy
1. Go to the "Strategy" tab
2. Select a trading strategy
3. Customize parameters or use defaults
4. Click "Apply Strategy"

### Step 4: Run Backtest
1. Go to the "Backtest" tab
2. Set initial capital and commission rate
3. Click "Run Backtest"
4. View performance metrics and trade history

### Step 5: Optimize Strategy (Optional)
1. Navigate to the "Optimization" tab
2. Set parameter ranges and optimization metric
3. Click "Optimize Strategy"
4. View and apply optimized parameters

### Step 6: Export Results
1. Go to the "Results" tab
2. Choose export format (PDF or Excel)
3. Click "Export"

## 🗂️ Directory Structure

The project follows a modular structure with clear separation of concerns:

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
│   ├── optimizer.py         # Core optimization logic
│   ├── metrics.py           # Performance metrics calculation
│   ├── status.py            # Optimization task status tracking
│   ├── visualization.py     # Results visualization
│   ├── routes.py            # API endpoints for optimization
│   └── task.py              # Background task management
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

## 🧱 Architecture & Design

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

### Key Components

1. **Frontend Layer**
   - HTML/CSS for structure and styling
   - JavaScript for user interactions and API calls
   - Chart.js for interactive data visualization

2. **Backend Layer**
   - FastAPI framework handles HTTP requests
   - API endpoints for each functionality
   - Asynchronous processing for optimization tasks

3. **Core Modules**
   - **Data Module**: Handles CSV loading, cleaning and storage
   - **Indicators Module**: Implements technical indicators
   - **Strategies Module**: Defines trading strategies
   - **Backtesting Module**: Simulates trading on historical data
   - **Optimization Module**: Finds optimal strategy parameters

### Design Patterns

- **Factory Pattern**: Used in strategy creation for dynamic instantiation based on user selection
- **Singleton Pattern**: Used for configuration management
- **Observer Pattern**: For status updates during optimization tasks
- **Strategy Pattern**: For interchangeable trading strategies

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

- Frontend makes asynchronous HTTP requests to backend endpoints using `fetch` API
- Backend responds with JSON data containing results
- Frontend parses JSON and updates UI accordingly

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

## 🧪 API Examples

### Backtest Request/Response

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

### Optimization Request/Response

**Request (POST /api/optimize-strategy)**:
```json
{
  "strategy_type": "sma_crossover_strategy",
  "parameter_ranges": {
    "fast_period": [10, 30, 5],
    "slow_period": [40, 60, 5]
  },
  "optimization_metric": "sharpe_ratio",
  "max_iterations": 50
}
```

**Response**:
```json
{
  "success": true,
  "message": "Optimization started for SMA Crossover Strategy",
  "task_id": "opt_20230510_143022"
}
```

### Status Check Request/Response

**Request (GET /api/optimization-status?task_id=opt_20230510_143022)**

**Response**:
```json
{
  "status": "running",
  "progress": 65,
  "current_best": {
    "parameters": {
      "fast_period": 15,
      "slow_period": 50
    },
    "metrics": {
      "sharpe_ratio": 1.42
    }
  }
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

## 👨‍💻 Development & Contribution

### Code Organization

- **File Naming**: Use lowercase with underscores (snake_case) for Python files
- **Module Structure**: Group related functionality in dedicated modules
- **Documentation**: Include docstrings and type hints in Python code

### Adding New Components

#### Adding a New Strategy

1. Create a new file in `strategies/` (e.g., `new_strategy.py`)
2. Define the strategy class with required interface:
   ```python
   class NewStrategy:
       def __init__(self, parameters=None):
           self.parameters = parameters or {}
       
       def generate_signals(self, data):
           # Strategy logic here
           return signals
   ```
3. Register the strategy in `strategies/__init__.py`:
   ```python
   STRATEGY_REGISTRY["new_strategy"] = NewStrategy
   ```
4. Test using `run_advanced_backtest.py` or via the UI

#### Adding a New Indicator

1. Add logic in the appropriate file under `indicators/`
2. Update `indicators/__init__.py` to include the new indicator
3. Update API endpoint in `app.py` if necessary

### Testing Guidelines

- Use `run_advanced_backtest.py` for testing strategies
- Test API endpoints with tools like Postman or curl
- Verify frontend-backend integration with browser developer tools

## 🔍 Autonomy for AI Tools

If you are an LLM or AI agent working with this codebase:

- ✅ **Indicator Development**: You can generate new indicators in `indicators/` directory by adding functions to existing files or creating new ones
- ✅ **Strategy Creation**: You can create new strategies in `strategies/` by defining new classes and registering them in `STRATEGY_REGISTRY`
- ✅ **Testing Methods**: Use `run_advanced_backtest.py` for batch testing or API endpoints for real-time testing
- ✅ **Integration Requirements**: Use `app.py` and defined FastAPI endpoints for UI interaction
- ✅ **Output Storage**: Store optimization results in `results/optimization/` directory using the interfaces in `optimization/file_manager.py`

## 🔧 Advanced Configuration

### Configuration Options

Edit `config.py` to modify default settings such as:
- Indicator default parameters
- Strategy default parameters
- Backtesting settings
- Optimization parameters
- Visualization options

### Custom Configurations

Save and load custom configurations through the UI, which are stored in `results/configs/` directory.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
