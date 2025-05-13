# AI-Powered Trading Analysis System

A modular trading analysis system with a Python backend and HTML frontend that allows users to easily analyze stocks, implement technical indicators, backtest trading strategies, and optimize parameters without writing any code.

## 🚀 Features

- **Data Loading & Cleaning**: Upload CSV files with historical stock data
- **Technical Indicators**: Apply various indicators (Moving Averages, RSI, MACD, Bollinger Bands, etc.)
- **Trading Strategies**: Choose from pre-built strategies (Trend Following, Mean Reversion, Breakout)
- **Backtesting Engine**: Test strategies against historical data
- **Optimization**: Find the best parameters for your strategies
- **User-Friendly Interface**: Control everything through an intuitive HTML interface
- **Export Results**: Download analysis as PDF/Excel documents
- **Configuration Management**: Save and load your analysis setups

## 📋 Requirements

- Python 3.8+
- Web browser (Chrome, Firefox, Edge recommended)

## 💻 Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd trading-analysis-system
   ```

2. Create a virtual environment (recommended):
   ```
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## 🏃‍♂️ Running the Application

1. Start the application:
   ```
   # Using the provided script
   python start.py
   
   # Or directly with uvicorn
   python -m uvicorn app:app --reload
   ```

2. Open your browser and navigate to:
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

## 📂 Project Structure

- **data/**: Data loading and processing modules
- **indicators/**: Technical indicator implementations
- **strategies/**: Trading strategy modules
- **backtesting/**: Backtesting engine
- **optimization/**: Strategy optimization modules (see [Optimization README](optimization/README.md))
- **frontend/**: HTML, CSS, and JavaScript files
- **app.py**: FastAPI backend server
- **config.py**: Configuration management

## 🔧 Recent Improvements

### Modularized Optimization System

The optimization functionality has been refactored into a modular package structure:

- **Clean Separation of Concerns**: Optimization code is now organized in the `optimization/` directory
- **API Router**: All optimization endpoints are defined in a separate router
- **Background Processing**: Asynchronous optimization tasks run without blocking the main application
- **Status Tracking**: Improved status monitoring and error handling
- **Visualization**: Enhanced visualization capabilities for optimization results

See the [Optimization README](optimization/README.md) for detailed documentation.

## 🔧 Advanced Configuration

Edit the `config.py` file to change default parameters or create custom configuration files through the UI.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details. 