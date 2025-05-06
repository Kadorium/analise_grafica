import os
import pandas as pd
import json
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import io
import base64
from datetime import datetime

# Import our modules
from data.data_loader import DataLoader
from indicators.indicator_utils import combine_indicators, plot_price_with_indicators, create_indicator_summary
from strategies import create_strategy, get_default_parameters, AVAILABLE_STRATEGIES
from backtesting.backtester import Backtester
from optimization.optimizer import optimize_strategy, compare_optimized_strategies
import config as cfg

# Create the FastAPI app
app = FastAPI(title="Trading Analysis API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Global state
UPLOADED_DATA = None
PROCESSED_DATA = None
BACKTESTER = None
CURRENT_CONFIG = cfg.get_all_config()

# Pydantic models for request/response validation
class IndicatorConfig(BaseModel):
    moving_averages: Optional[Dict[str, Any]] = None
    rsi: Optional[Dict[str, Any]] = None
    macd: Optional[Dict[str, Any]] = None
    bollinger_bands: Optional[Dict[str, Any]] = None
    stochastic: Optional[Dict[str, Any]] = None
    volume: Optional[bool] = None
    atr: Optional[Dict[str, Any]] = None

class StrategyConfig(BaseModel):
    strategy_type: str
    parameters: Dict[str, Any]

class BacktestConfig(BaseModel):
    initial_capital: float = 10000.0
    commission: float = 0.001
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class OptimizationConfig(BaseModel):
    strategy_type: str
    param_ranges: Dict[str, List[Any]]
    metric: str = "sharpe_ratio"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class PlotConfig(BaseModel):
    main_indicators: List[str] = []
    subplot_indicators: List[str] = []
    title: str = "Price Chart with Indicators"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

# Routes
@app.get("/")
async def read_root():
    return FileResponse("frontend/index.html")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    global UPLOADED_DATA
    
    # Read the uploaded file
    try:
        contents = await file.read()
        
        # Parse the CSV
        UPLOADED_DATA = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Check if the required columns exist
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col.lower() not in map(str.lower, UPLOADED_DATA.columns)]
        
        if missing_columns:
            return JSONResponse(
                status_code=400,
                content={"message": f"Missing required columns: {', '.join(missing_columns)}"}
            )
        
        # Return a sample of the data
        return {
            "message": "File uploaded successfully",
            "data_shape": UPLOADED_DATA.shape,
            "data_sample": UPLOADED_DATA.head().to_dict('records')
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error processing file: {str(e)}"}
        )

@app.post("/api/process-data")
async def process_data():
    global UPLOADED_DATA, PROCESSED_DATA
    
    if UPLOADED_DATA is None:
        return JSONResponse(
            status_code=400,
            content={"message": "No data uploaded. Please upload a CSV file first."}
        )
    
    try:
        # Create a DataLoader instance
        data_loader = DataLoader()
        
        # Set the data
        data_loader.data = UPLOADED_DATA.copy()
        
        # Clean the data
        cleaned_data = data_loader.clean_data()
        
        # Store the processed data
        PROCESSED_DATA = cleaned_data
        
        # Return a summary of the processed data
        return {
            "message": "Data processed successfully",
            "data_shape": PROCESSED_DATA.shape,
            "date_range": {
                "start": PROCESSED_DATA['date'].min().strftime('%Y-%m-%d'),
                "end": PROCESSED_DATA['date'].max().strftime('%Y-%m-%d')
            },
            "data_sample": PROCESSED_DATA.head().to_dict('records')
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error processing data: {str(e)}"}
        )

@app.post("/api/add-indicators")
async def add_indicators(indicator_config: IndicatorConfig):
    global PROCESSED_DATA
    
    if PROCESSED_DATA is None:
        return JSONResponse(
            status_code=400,
            content={"message": "No processed data available. Please upload and process data first."}
        )
    
    try:
        # Convert the indicator config to dict
        indicators_dict = indicator_config.dict(exclude_none=True)
        
        # Add indicators
        data_with_indicators = combine_indicators(PROCESSED_DATA, indicators_dict)
        
        # Update the processed data
        PROCESSED_DATA = data_with_indicators
        
        # Create a summary of the indicators
        summary = create_indicator_summary(PROCESSED_DATA, last_n_periods=1)
        
        # Get the list of all indicator columns
        indicator_columns = [col for col in PROCESSED_DATA.columns 
                           if col not in ['date', 'open', 'high', 'low', 'close', 'volume']]
        
        return {
            "message": "Indicators added successfully",
            "indicator_summary": summary,
            "available_indicators": indicator_columns
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error adding indicators: {str(e)}"}
        )

@app.post("/api/plot-indicators")
async def plot_indicators(plot_config: PlotConfig):
    global PROCESSED_DATA
    
    if PROCESSED_DATA is None:
        return JSONResponse(
            status_code=400,
            content={"message": "No processed data available. Please upload and process data first."}
        )
    
    try:
        # Convert the plot config to dict
        plot_dict = plot_config.dict(exclude_none=True)
        
        # Create the plot
        image_base64 = plot_price_with_indicators(PROCESSED_DATA, plot_dict)
        
        return {
            "message": "Plot created successfully",
            "image": image_base64
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error creating plot: {str(e)}"}
        )

@app.get("/api/available-strategies")
async def get_strategies():
    return {
        "strategies": AVAILABLE_STRATEGIES
    }

@app.get("/api/strategy-parameters/{strategy_type}")
async def get_strategy_parameters(strategy_type: str):
    try:
        # Get the default parameters for the strategy
        default_params = get_default_parameters(strategy_type)
        
        return {
            "parameters": default_params
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error getting strategy parameters: {str(e)}"}
        )

@app.post("/api/run-backtest")
async def run_backtest(strategy_config: StrategyConfig, backtest_config: BacktestConfig):
    global PROCESSED_DATA, BACKTESTER
    
    if PROCESSED_DATA is None:
        return JSONResponse(
            status_code=400,
            content={"message": "No processed data available. Please upload and process data first."}
        )
    
    try:
        # Create the strategy
        strategy = create_strategy(strategy_config.strategy_type, **strategy_config.parameters)
        
        # Create a backtester
        BACKTESTER = Backtester(
            data=PROCESSED_DATA,
            initial_capital=backtest_config.initial_capital,
            commission=backtest_config.commission
        )
        
        # Run the backtest
        backtest_result = BACKTESTER.run_backtest(
            strategy=strategy,
            start_date=backtest_config.start_date,
            end_date=backtest_config.end_date
        )
        
        # Get the equity curve plot
        equity_curve_image = BACKTESTER.plot_equity_curves([strategy.name])
        
        # Get the drawdown plot
        drawdown_image = BACKTESTER.plot_drawdowns([strategy.name])
        
        # Get trade statistics
        trade_stats = BACKTESTER.get_trade_statistics(strategy.name)
        
        return {
            "message": "Backtest completed successfully",
            "strategy_name": backtest_result["strategy_name"],
            "performance_metrics": backtest_result["performance_metrics"],
            "trade_statistics": trade_stats,
            "equity_curve": equity_curve_image,
            "drawdown_curve": drawdown_image
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error running backtest: {str(e)}"}
        )

@app.post("/api/optimize-strategy")
async def optimize_strategy_endpoint(optimization_config: OptimizationConfig, background_tasks: BackgroundTasks):
    global PROCESSED_DATA
    
    if PROCESSED_DATA is None:
        return JSONResponse(
            status_code=400,
            content={"message": "No processed data available. Please upload and process data first."}
        )
    
    # Define a background task for optimization (as it can take a long time)
    def run_optimization():
        global CURRENT_CONFIG
        
        try:
            # Run the optimization
            best_strategy, best_params, best_performance, all_results = optimize_strategy(
                data=PROCESSED_DATA,
                strategy_type=optimization_config.strategy_type,
                param_ranges=optimization_config.param_ranges,
                metric=optimization_config.metric,
                start_date=optimization_config.start_date,
                end_date=optimization_config.end_date
            )
            
            # Update the current config with the optimized strategy parameters
            CURRENT_CONFIG['strategies'][optimization_config.strategy_type].update(best_params)
            
            # Save the optimization results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = os.path.join("results", "optimization")
            os.makedirs(results_dir, exist_ok=True)
            
            results_file = os.path.join(results_dir, f"optimization_{optimization_config.strategy_type}_{timestamp}.json")
            
            with open(results_file, 'w') as f:
                # Convert all_results to a serializable format
                serializable_results = []
                for result in all_results:
                    serializable_results.append({
                        'params': result['params'],
                        'value': result['value'],
                        'performance': result['performance']
                    })
                
                json.dump({
                    'strategy_type': optimization_config.strategy_type,
                    'metric': optimization_config.metric,
                    'best_params': best_params,
                    'best_performance': best_performance,
                    'all_results': serializable_results
                }, f, indent=4)
            
        except Exception as e:
            print(f"Error in optimization background task: {str(e)}")
    
    # Add the optimization task to background tasks
    background_tasks.add_task(run_optimization)
    
    return {
        "message": "Optimization started in the background",
        "strategy_type": optimization_config.strategy_type,
        "metric": optimization_config.metric
    }

@app.get("/api/compare-strategies")
async def compare_strategies(strategy_types: List[str], start_date: Optional[str] = None, end_date: Optional[str] = None):
    global PROCESSED_DATA, BACKTESTER
    
    if PROCESSED_DATA is None:
        return JSONResponse(
            status_code=400,
            content={"message": "No processed data available. Please upload and process data first."}
        )
    
    try:
        # Create strategies
        strategies = []
        for strategy_type in strategy_types:
            # Get parameters from current config
            params = CURRENT_CONFIG['strategies'].get(strategy_type, {})
            strategy = create_strategy(strategy_type, **params)
            strategies.append(strategy)
        
        # Create a backtester
        BACKTESTER = Backtester(
            data=PROCESSED_DATA,
            initial_capital=CURRENT_CONFIG['backtest']['initial_capital'],
            commission=CURRENT_CONFIG['backtest']['commission']
        )
        
        # Run the backtests
        results = BACKTESTER.compare_strategies(
            strategies=strategies,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get the equity curve plot
        equity_curve_image = BACKTESTER.plot_equity_curves()
        
        # Get the drawdown plot
        drawdown_image = BACKTESTER.plot_drawdowns()
        
        return {
            "message": "Strategy comparison completed successfully",
            "results": results,
            "equity_curve": equity_curve_image,
            "drawdown_curve": drawdown_image
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error comparing strategies: {str(e)}"}
        )

@app.post("/api/save-config")
async def save_config_endpoint(config_data: Dict[str, Any]):
    global CURRENT_CONFIG
    
    try:
        # Update the current config
        CURRENT_CONFIG.update(config_data)
        
        # Save the config
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_dir = os.path.join("results", "configs")
        os.makedirs(config_dir, exist_ok=True)
        
        config_file = os.path.join(config_dir, f"config_{timestamp}.json")
        
        with open(config_file, 'w') as f:
            json.dump(CURRENT_CONFIG, f, indent=4)
        
        return {
            "message": "Configuration saved successfully",
            "config_file": config_file
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error saving configuration: {str(e)}"}
        )

@app.get("/api/load-config/{config_file}")
async def load_config_endpoint(config_file: str):
    global CURRENT_CONFIG
    
    try:
        # Load the config
        config_path = os.path.join("results", "configs", config_file)
        
        with open(config_path, 'r') as f:
            loaded_config = json.load(f)
        
        # Update the current config
        CURRENT_CONFIG.update(loaded_config)
        
        return {
            "message": "Configuration loaded successfully",
            "config": CURRENT_CONFIG
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error loading configuration: {str(e)}"}
        )

@app.get("/api/export-results/{format}")
async def export_results(format: str):
    global BACKTESTER
    
    if BACKTESTER is None or not BACKTESTER.results:
        return JSONResponse(
            status_code=400,
            content={"message": "No backtest results available. Please run a backtest first."}
        )
    
    try:
        # Create the results directory if it doesn't exist
        results_dir = os.path.join("results", "exports")
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == 'json':
            # Export as JSON
            output_file = os.path.join(results_dir, f"backtest_results_{timestamp}.json")
            BACKTESTER.save_results(output_file)
            
            return FileResponse(
                path=output_file,
                filename=f"backtest_results_{timestamp}.json",
                media_type="application/json"
            )
        elif format.lower() == 'csv':
            # Export as CSV
            output_file = os.path.join(results_dir, f"backtest_results_{timestamp}.csv")
            
            # Combine all backtest results into a single DataFrame
            all_results = pd.DataFrame()
            
            for strategy_name, result in BACKTESTER.results.items():
                # Get the backtest results
                backtest_df = result['backtest_results'].copy()
                
                # Add strategy name column
                backtest_df['strategy'] = strategy_name
                
                # Append to all results
                all_results = pd.concat([all_results, backtest_df])
            
            # Save to CSV
            all_results.to_csv(output_file, index=False)
            
            return FileResponse(
                path=output_file,
                filename=f"backtest_results_{timestamp}.csv",
                media_type="text/csv"
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"message": f"Unsupported export format: {format}"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error exporting results: {str(e)}"}
        )

@app.get("/api/current-config")
async def get_current_config():
    global CURRENT_CONFIG
    
    return CURRENT_CONFIG

# Run the app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 