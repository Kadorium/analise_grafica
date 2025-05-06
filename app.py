import os
import pandas as pd
import json
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import io
import base64
from datetime import datetime
import traceback

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

# Add global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = str(exc)
    stack_trace = traceback.format_exc()
    print(f"Global exception: {error_detail}\n{stack_trace}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": f"Internal server error: {error_detail}"},
    )

# Add validation exception handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"success": False, "message": f"Validation error: {str(exc)}"},
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
        
        # Save the file temporarily to use with our enhanced DataLoader
        temp_file_path = os.path.join('data', 'temp_upload.csv')
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        
        with open(temp_file_path, 'wb') as f:
            f.write(contents)
        
        # Use our enhanced DataLoader instead of basic pd.read_csv
        data_loader = DataLoader(temp_file_path)
        UPLOADED_DATA = data_loader.load_csv()
        
        # Drop any unwanted unnamed columns that are empty
        for col in UPLOADED_DATA.columns:
            if 'unnamed' in col.lower() and UPLOADED_DATA[col].isna().all():
                UPLOADED_DATA = UPLOADED_DATA.drop(columns=[col])
        
        # Return information about the data - use smaller sample to avoid JSON serialization issues
        sample_data = UPLOADED_DATA.head(5).copy()
        
        # Convert date column to string if it's datetime to ensure JSON serialization
        if 'date' in sample_data.columns and pd.api.types.is_datetime64_any_dtype(sample_data['date']):
            sample_data['date'] = sample_data['date'].dt.strftime('%Y-%m-%d')
        
        return {
            "message": "File uploaded successfully",
            "data_shape": UPLOADED_DATA.shape,
            "data_sample": sample_data.to_dict('records'),
            "columns": list(UPLOADED_DATA.columns)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error processing file: {str(e)}"}
        )

@app.post("/api/arrange-data")
async def arrange_data(file: UploadFile = File(...)):
    """
    Endpoint to arrange data files (CSV, XLS, XLSX) into a standardized format.
    """
    global PROCESSED_DATA, UPLOADED_DATA
    
    try:
        # Save the uploaded file temporarily
        temp_input_path = os.path.join('data', 'temp_' + file.filename)
        os.makedirs(os.path.dirname(temp_input_path), exist_ok=True)
        
        with open(temp_input_path, 'wb') as f:
            contents = await file.read()
            f.write(contents)
        
        # Import the data arranger module
        from data.data_arranger_script import arrange_data_file
        
        # Create a clean copy with original filename for processing
        clean_input_path = os.path.join('data', file.filename)
        if os.path.exists(clean_input_path):
            # Add timestamp to avoid overwriting existing files
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_base, file_ext = os.path.splitext(file.filename)
            clean_input_path = os.path.join('data', f"{file_base}_{timestamp}{file_ext}")
        
        # Copy the temp file to the clean path
        os.replace(temp_input_path, clean_input_path)
        
        # Arrange the data using original filename
        output_file = arrange_data_file(clean_input_path)
        
        # Clean up the temp file and original file
        if os.path.exists(clean_input_path):
            os.remove(clean_input_path)
        
        # Try to load the arranged data for preview
        data_loader = DataLoader(output_file)
        arranged_data = data_loader.load_csv()
        
        # Set the processed data so it's available for other endpoints
        UPLOADED_DATA = arranged_data.copy()
        PROCESSED_DATA = arranged_data.copy()
        
        # Prepare sample data for JSON serialization
        sample_data = arranged_data.head(5).copy()
        if 'date' in sample_data.columns and pd.api.types.is_datetime64_any_dtype(sample_data['date']):
            sample_data['date'] = sample_data['date'].dt.strftime('%Y-%m-%d')
        
        # Include date range info like in process-data endpoint
        date_range = {
            "start": PROCESSED_DATA['date'].min() if not pd.isna(PROCESSED_DATA['date'].min()) else "N/A",
            "end": PROCESSED_DATA['date'].max() if not pd.isna(PROCESSED_DATA['date'].max()) else "N/A"
        }
        
        if pd.api.types.is_datetime64_any_dtype(PROCESSED_DATA['date']):
            date_range["start"] = date_range["start"].strftime('%Y-%m-%d') if not pd.isna(date_range["start"]) else "N/A"
            date_range["end"] = date_range["end"].strftime('%Y-%m-%d') if not pd.isna(date_range["end"]) else "N/A"
        
        return {
            "message": f"Data arranged successfully and saved to {output_file}",
            "output_file": output_file,
            "data_shape": arranged_data.shape,
            "data_sample": sample_data.to_dict('records'),
            "columns": list(arranged_data.columns),
            "date_range": date_range
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"message": f"Error arranging data: {str(e)}"}
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
        # Create a DataLoader instance and set the data
        data_loader = DataLoader()
        data_loader.data = UPLOADED_DATA.copy()
        
        # Clean the data with our enhanced robust method
        cleaned_data = data_loader.clean_data()
        
        # Handle empty dataset after cleaning
        if len(cleaned_data) == 0:
            # Try European date format specifically for DD/MM/YY
            print("Attempting recovery with European date format...")
            data_copy = UPLOADED_DATA.copy()
            
            # Custom function to parse dates in European format
            def parse_date(date_str):
                if not isinstance(date_str, str):
                    return None
                    
                date_str = date_str.strip()
                
                # Try European formats first
                formats = ['%d/%m/%y', '%d/%m/%Y']
                
                for fmt in formats:
                    try:
                        return pd.to_datetime(date_str, format=fmt)
                    except:
                        continue
                        
                # If European formats fail, try other common formats
                formats = ['%m/%d/%y', '%m/%d/%Y', '%Y-%m-%d']
                for fmt in formats:
                    try:
                        return pd.to_datetime(date_str, format=fmt)
                    except:
                        continue
                
                # Last resort: let pandas try to figure it out
                try:
                    return pd.to_datetime(date_str, errors='coerce')
                except:
                    return None
            
            # Apply date parser
            data_copy['date'] = data_copy['date'].apply(parse_date)
            
            # Convert numeric columns with European decimal format (comma instead of dot)
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in data_copy.columns:
                    if data_copy[col].dtype == object:
                        data_copy[col] = data_copy[col].astype(str).str.replace(',', '.')
                    data_copy[col] = pd.to_numeric(data_copy[col], errors='coerce')
            
            # Drop rows with missing values
            data_copy = data_copy.dropna(subset=['date', 'open', 'high', 'low', 'close', 'volume'])
            
            # Use the manually fixed data if we have rows
            if len(data_copy) > 0:
                cleaned_data = data_copy
                print(f"Recovery successful! Recovered {len(cleaned_data)} rows of data.")
            else:
                return JSONResponse(
                    status_code=400,
                    content={"message": "Could not process data. All rows were invalid after cleaning."}
                )
        
        # Store the processed data
        PROCESSED_DATA = cleaned_data
        
        # For return, format the dates as strings to ensure JSON serialization
        sample_data = PROCESSED_DATA.head().copy()
        if 'date' in sample_data.columns and pd.api.types.is_datetime64_any_dtype(sample_data['date']):
            sample_data['date'] = sample_data['date'].dt.strftime('%Y-%m-%d')
        
        # Return a summary of the processed data
        return {
            "message": "Data processed successfully",
            "data_shape": PROCESSED_DATA.shape,
            "date_range": {
                "start": PROCESSED_DATA['date'].min().strftime('%Y-%m-%d') if not pd.isna(PROCESSED_DATA['date'].min()) else "N/A",
                "end": PROCESSED_DATA['date'].max().strftime('%Y-%m-%d') if not pd.isna(PROCESSED_DATA['date'].max()) else "N/A"
            },
            "data_sample": sample_data.to_dict('records')
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
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
            content={"success": False, "message": "No processed data available. Please upload and process data first."}
        )
    
    try:
        # Convert the indicator config to dict
        indicators_dict = indicator_config.dict(exclude_none=True)
        
        print(f"Adding indicators with config: {indicators_dict}")
        
        # Check that required columns exist
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in PROCESSED_DATA.columns]
        if missing_columns:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": f"Missing required columns in data: {', '.join(missing_columns)}"}
            )
            
        # Make a copy to avoid modifying the original data
        data_for_indicators = PROCESSED_DATA.copy()
        
        # Add indicators
        data_with_indicators = combine_indicators(data_for_indicators, indicators_dict)
        
        # Update the processed data
        PROCESSED_DATA = data_with_indicators
        
        # Get the list of all indicator columns
        indicator_columns = [col for col in PROCESSED_DATA.columns 
                           if col not in ['date', 'open', 'high', 'low', 'close', 'volume']]
        
        # Create a short summary
        summary = ""
        if indicator_columns:
            try:
                # Create a summary of the indicators
                indicator_summary = create_indicator_summary(PROCESSED_DATA, last_n_periods=1)
                summary = f"<div class='alert alert-info'><strong>Indicators added:</strong> {', '.join(indicator_columns)}</div>"
            except Exception as e:
                print(f"Error creating indicator summary: {str(e)}")
                summary = f"<div class='alert alert-warning'><strong>Indicators added</strong> but could not create summary: {str(e)}</div>"
        
        return {
            "success": True,
            "message": "Indicators added successfully",
            "indicator_summary": summary,
            "available_indicators": indicator_columns
        }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error adding indicators: {str(e)}\n{error_trace}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error adding indicators: {str(e)}"}
        )

@app.post("/api/plot-indicators")
async def plot_indicators(plot_config: PlotConfig):
    global PROCESSED_DATA
    
    if PROCESSED_DATA is None:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "No processed data available. Please upload and process data first."}
        )
    
    try:
        # Convert the plot config to dict
        plot_dict = plot_config.dict(exclude_none=True)
        
        # Create the plot
        image_base64 = plot_price_with_indicators(PROCESSED_DATA, plot_dict)
        
        return {
            "success": True,
            "message": "Plot created successfully",
            "chart_image": image_base64
        }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error creating plot: {str(e)}\n{error_trace}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error creating plot: {str(e)}"}
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
            content={"success": False, "message": "No processed data available. Please upload and process data first."}
        )
    
    try:
        print(f"Running backtest with strategy: {strategy_config.strategy_type}, params: {strategy_config.parameters}")
        print(f"Backtest config: {backtest_config}")
        
        # Check that required columns exist
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in PROCESSED_DATA.columns]
        if missing_columns:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": f"Missing required columns in data: {', '.join(missing_columns)}"}
            )
            
        # Make a copy of the data for backtesting
        backtest_data = PROCESSED_DATA.copy()
        
        # Create the strategy
        try:
            strategy = create_strategy(strategy_config.strategy_type, **strategy_config.parameters)
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": f"Error creating strategy: {str(e)}"}
            )
        
        # Create a backtester
        try:
            BACKTESTER = Backtester(
                data=backtest_data,
                initial_capital=backtest_config.initial_capital,
                commission=backtest_config.commission
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Error initializing backtester: {str(e)}"}
            )
        
        # Run the backtest
        try:
            backtest_result = BACKTESTER.run_backtest(
                strategy=strategy,
                start_date=backtest_config.start_date,
                end_date=backtest_config.end_date
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Error during backtest execution: {str(e)}"}
            )
        
        # Generate plots and statistics (with proper error handling)
        try:
            # Get the equity curve plot
            equity_curve_image = BACKTESTER.plot_equity_curves([strategy.name])
            
            # Get the drawdown plot
            drawdown_image = BACKTESTER.plot_drawdowns([strategy.name])
            
            # Get trade statistics
            trade_stats = BACKTESTER.get_trade_statistics(strategy.name)
        except Exception as e:
            # If plotting fails, we can still return the backtest result
            print(f"Error generating plots: {str(e)}")
            equity_curve_image = None
            drawdown_image = None
            trade_stats = {}
        
        return {
            "success": True,
            "message": "Backtest completed successfully",
            "strategy_name": backtest_result["strategy_name"],
            "performance_metrics": backtest_result["performance_metrics"],
            "trade_statistics": trade_stats,
            "equity_curve": equity_curve_image,
            "drawdown_curve": drawdown_image
        }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error running backtest: {str(e)}\n{error_trace}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error running backtest: {str(e)}"}
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

@app.post("/api/compare-strategies")
async def compare_strategies(request: Request):
    global PROCESSED_DATA, BACKTESTER
    
    if PROCESSED_DATA is None:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "No processed data available. Please upload and process data first."}
        )
    
    try:
        # Parse the request body
        body = await request.json()
        strategy_types = body.get("strategy_types", [])
        start_date = body.get("start_date")
        end_date = body.get("end_date")
        
        print(f"Comparing strategies: {strategy_types} from {start_date} to {end_date}")
        
        # Validate input
        if not strategy_types or len(strategy_types) == 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "At least one strategy type must be provided"}
            )
            
        # Check all strategy types are valid
        valid_strategy_types = [s['type'] for s in AVAILABLE_STRATEGIES]
        invalid_strategies = [s for s in strategy_types if s not in valid_strategy_types]
        if invalid_strategies:
            return JSONResponse(
                status_code=422,
                content={"success": False, "message": f"Invalid strategy types: {', '.join(invalid_strategies)}. Valid types are: {', '.join(valid_strategy_types)}"}
            )
        
        # Create strategies with error handling
        strategies = []
        for strategy_type in strategy_types:
            try:
                params = CURRENT_CONFIG['strategies'].get(strategy_type, {})
                strategy = create_strategy(strategy_type, **params)
                strategies.append(strategy)
            except Exception as e:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": f"Error creating strategy '{strategy_type}': {str(e)}"}
                )
        
        # Create a backtester
        BACKTESTER = Backtester(
            data=PROCESSED_DATA.copy(),
            initial_capital=CURRENT_CONFIG['backtest']['initial_capital'],
            commission=CURRENT_CONFIG['backtest']['commission']
        )
        
        # Run the backtests
        results = BACKTESTER.compare_strategies(
            strategies=strategies,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get equity curve image
        try:
            equity_curve_image = BACKTESTER.plot_equity_curves()
        except Exception as e:
            print(f"Error generating equity curve: {str(e)}")
            equity_curve_image = None
            
        # Find best strategy
        best_strategy_name = "Unknown"
        if results:
            try:
                best_strategy_name = max(results.items(), key=lambda x: x[1].get('sharpe_ratio', -float('inf')))[0]
            except Exception as e:
                print(f"Error finding best strategy: {str(e)}")
        
        return {
            "success": True,
            "message": "Strategy comparison completed successfully",
            "best_strategy": best_strategy_name,
            "results": results,
            "chart_image": equity_curve_image
        }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error comparing strategies: {str(e)}\n{error_trace}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error comparing strategies: {str(e)}"}
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

@app.get("/api/data-status")
async def data_status():
    global UPLOADED_DATA, PROCESSED_DATA
    return {
        "uploaded": UPLOADED_DATA is not None,
        "processed": PROCESSED_DATA is not None,
        "shape": PROCESSED_DATA.shape if PROCESSED_DATA is not None else None
    }

# Run the app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 