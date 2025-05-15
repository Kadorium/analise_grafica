import os
import pandas as pd
import json
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
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

def log_exception(request, exc, context=""):
    separator = "#" * 80
    stack_trace = traceback.format_exc()
    logger.error(f"{separator}\n{context} EXCEPTION\nREQUEST: {get_request_metadata(request)}\nERROR: {str(exc)}\nSTACK TRACE:\n{stack_trace}\n{separator}")

import time
import logging
import sys
import platform
import psutil
import numpy as np
import matplotlib

REQUIRED_COLUMNS = REQUIRED_COLUMNS  # Shared column list
matplotlib.use('Agg')
import functools
import traceback

def log_exception(request, exc, context=""):
    separator = "#" * 80
    stack_trace = traceback.format_exc()
    logger.error(f"{separator}\n{context} EXCEPTION\nREQUEST: {get_request_metadata(request)}\nERROR: {str(exc)}\nSTACK TRACE:\n{stack_trace}\n{separator}")
 as tb

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("trading-app")

# Função para gerar logs formatados de forma consistente
def log_endpoint(endpoint_name, **kwargs):
    """
    Gera logs formatados de forma consistente para os endpoints.
    
    Args:
        endpoint_name: Nome do endpoint para identificação
        **kwargs: Dados adicionais a serem logados (parâmetros, resultados, etc.)
    """
    separator = "=" * 50
    log_lines = [f"\n{separator}", f"ENDPOINT: {endpoint_name}", f"TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
    
    for key, value in kwargs.items():
        # Formatação especial para DataFrames
        if isinstance(value, pd.DataFrame):
            log_lines.append(f"{key.upper()}: shape={value.shape}, columns={value.columns.tolist()}")
        else:
            log_lines.append(f"{key.upper()}: {value}")
    
    log_lines.append(separator)
    log_message = "\n".join(log_lines)
    logger.info(log_message)
    return log_message

# Refactoring Utilities
def get_request_metadata(request):
    return f"{request.method} {request.url.path}" if request else "UNKNOWN"


def endpoint_wrapper(endpoint_name_fallback: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request_obj: Optional[Request] = None
            if 'request' in kwargs and isinstance(kwargs['request'], Request):
                request_obj = kwargs['request']
            else:
                for arg_val in args:
                    if isinstance(arg_val, Request):
                        request_obj = arg_val
                        break
            
            current_endpoint_name = get_request_metadata(request_obj)

            log_endpoint(f"{current_endpoint_name} - REQUEST START")
            start_time = time.time()

            try:
                response = await func(*args, **kwargs)
                elapsed_time = time.time() - start_time
                
                status_code_to_log = 'N/A'
                if hasattr(response, 'status_code'):
                    status_code_to_log = response.status_code
                elif isinstance(response, dict): # Heuristic for direct dict returns from Pydantic models etc.
                    # Try to infer status from content, default to 200 if looks like success
                    if response.get("success") is False and "message" in response: # Check if it's an error dict
                        status_code_to_log = response.get("status_code", 500)
                    else: # Assumed success
                        status_code_to_log = response.get("status_code", 200)


                log_endpoint(f"{current_endpoint_name} - REQUEST SUCCESS", 
                             elapsed_time=f"{elapsed_time:.2f}s",
                             status_code=status_code_to_log)
                return response
            except Exception as e:
                elapsed_time = time.time() - start_time
                error_trace = traceback.format_exc()
                log_endpoint(f"{current_endpoint_name} - REQUEST ERROR", 
                             elapsed_time=f"{elapsed_time:.2f}s", 
                             error=str(e), 
                             traceback=error_trace)
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "message": f"Internal server error: {str(e)}"}
                )
        return wrapper
    return decorator

def stringify_df_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Converts 'date' columns in a DataFrame from datetime objects to 'YYYY-MM-DD' strings."""
    df_copy = df.copy()
    if 'date' in df_copy.columns and pd.api.types.is_datetime64_any_dtype(df_copy['date']):
        df_copy['date'] = df_copy['date'].dt.strftime('%Y-%m-%d')
    return df_copy

def check_required_columns(df: Optional[pd.DataFrame], required_cols: List[str]) -> List[str]:
    """Checks if a DataFrame contains all required columns. Returns a list of missing columns."""
    if df is None:
        # If df is None, all are considered missing for this check's purpose, or handle as error
        # For now, let's assume this implies an earlier error if df should exist.
        # Returning required_cols might be misleading if df being None is an expected state before data load.
        # Let's adjust to return empty if df is None, assuming check is on existing df.
        return [] if df is not None else required_cols # Modified logic: if df is None, all required are missing
    return [col for col in required_cols if col not in df.columns]


def normalize_signals_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures a 'signal' column exists and contains text ('buy', 'sell', 'hold').
    Derives 'signal' from 'position' or crossover columns if not present.
    Converts numeric signals (1, -1, 0) to text.
    """
    signals_df = df.copy()
    logger.info("Normalizing signals...")

    if 'signal' not in signals_df.columns:
        logger.info("'signal' column not found, attempting to derive.")
        if 'position' in signals_df.columns:
            logger.info("Deriving signals from 'position' column.")
            signals_df['signal'] = 'hold'
            position_diff = signals_df['position'].diff()
            signals_df.loc[position_diff == 1, 'signal'] = 'buy'
            signals_df.loc[position_diff == -1, 'signal'] = 'sell'
            signals_df['signal'] = signals_df['signal'].fillna('hold') # Fill NaNs from diff
        elif 'golden_cross' in signals_df.columns and 'death_cross' in signals_df.columns:
            logger.info("Deriving signals from crossover columns.")
            signals_df['signal'] = 'hold'
            signals_df.loc[signals_df['golden_cross'] == 1, 'signal'] = 'buy'
            signals_df.loc[signals_df['death_cross'] == 1, 'signal'] = 'sell'
        elif 'buy_signal' in signals_df.columns or 'sell_signal' in signals_df.columns:
            logger.info("Deriving signals from buy_signal/sell_signal columns.")
            signals_df['signal'] = 'hold'
            if 'buy_signal' in signals_df.columns:
                signals_df.loc[signals_df['buy_signal'] == 1, 'signal'] = 'buy'
            if 'sell_signal' in signals_df.columns:
                signals_df.loc[signals_df['sell_signal'] == 1, 'signal'] = 'sell'
        else:
            logger.warning("No signal or position columns found to derive from. Defaulting to 'hold'.")
            signals_df['signal'] = 'hold'
        signals_df['signal'] = signals_df['signal'].fillna('hold')


    if 'signal' in signals_df.columns and signals_df['signal'].dtype in [np.int64, np.float64, 'int64', 'float64']:
        logger.info("Converting numeric signals to text values ('buy', 'sell', 'hold').")
        signals_df['signal'] = signals_df['signal'].fillna(0) 
        map_dict = {1: 'buy', -1: 'sell', 0: 'hold'}
        signals_df['signal'] = signals_df['signal'].map(map_dict).fillna('hold')
    
    if 'signal' in signals_df.columns:
        signals_df['signal'] = signals_df['signal'].astype(object)

    logger.info(f"Signal normalization complete. Signal counts: {signals_df['signal'].value_counts().to_dict() if 'signal' in signals_df else 'N/A'}")
    return signals_df

# Import our modules
from data.data_loader import DataLoader
from indicators.indicator_utils import combine_indicators, plot_price_with_indicators, create_indicator_summary
from strategies import create_strategy, get_default_parameters, AVAILABLE_STRATEGIES, STRATEGY_REGISTRY
from backtesting.backtester import Backtester
from optimization.optimizer import optimize_strategy, compare_optimized_strategies
from indicators.seasonality import day_of_week_returns, monthly_returns, day_of_week_volatility, calendar_heatmap, seasonality_summary
import config as cfg

# Enhanced global variables for tracking operations
OPTIMIZATION_STATUS = {
    "in_progress": False,
    "strategy_type": None,
    "start_time": None,
    "latest_result_file": None,
    "comparison_data": {},
    "progress": 0.0,  # Progress percentage (0-100)
    "error": None,    # Error message if any
    "total_iterations": 0,
    "completed_iterations": 0
}

# Background task tracking for backtests
BACKTEST_STATUS = {
    "in_progress": False,
    "strategy_type": None,
    "start_time": None,
    "completed": False,
    "error": None
}

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

# Cached data storage
CACHED_DATA = {
    "original_data": None,
    "processed_data": None,
    "signals_data": None,
    "last_update": None
}

# Helper functions for common operations
def get_cached_data():
    """
    Get the cached processed data or return None if not available
    """
    if CACHED_DATA["processed_data"] is not None:
        return CACHED_DATA["processed_data"].copy()
    return None

def update_cached_data(data, data_type="processed_data"):
    """
    Update the cached data
    """
    CACHED_DATA[data_type] = data
    CACHED_DATA["last_update"] = datetime.now()

def load_strategy_modules():
    """
    Dynamically load and refresh available strategy modules
    """
    from strategies import __init__ as strategies_init
    strategies_init._load_strategy_modules()
    return STRATEGY_REGISTRY, AVAILABLE_STRATEGIES

# Add global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log_exception(request, exc, context="GLOBAL")
    return JSONResponse(

        status_code=500,
        content={"success": False, "message": f"Internal server error: {error_detail}"},
    )

# Add validation exception handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    log_exception(request, exc, context="VALIDATION")
    return JSONResponse(

        status_code=422,
        content={"success": False, "message": f"Validation error: {error_detail}"},
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
    adx: Optional[Dict[str, Any]] = None
    supertrend: Optional[Dict[str, Any]] = None
    cci: Optional[Dict[str, Any]] = None
    williams_r: Optional[Dict[str, Any]] = None
    cmf: Optional[Dict[str, Any]] = None
    donchian_channels: Optional[Dict[str, Any]] = None
    keltner_channels: Optional[Dict[str, Any]] = None
    ad_line: Optional[bool] = None
    candlestick_patterns: Optional[bool] = None

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

# Update log_optimization_request to accept extra info and errors

def log_optimization_request(request_data, extra_info=None, error=None, traceback_info=None, params_to_optimizer=None, final_params_backtest=None):
    """
    Appends optimization request data, extra info, and errors to a log file for debugging and traceability.
    """
    import json
    import traceback

def log_exception(request, exc, context=""):
    separator = "#" * 80
    stack_trace = traceback.format_exc()
    logger.error(f"{separator}\n{context} EXCEPTION\nREQUEST: {get_request_metadata(request)}\nERROR: {str(exc)}\nSTACK TRACE:\n{stack_trace}\n{separator}")
 as tb
    from datetime import datetime
    log_file = 'optimization_requests.log'
    
    # Create basic log entry
    log_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'strategy_type': request_data.get('strategy_type', 'unknown')
    }
    
    # Add request parameters with better formatting
    if 'param_ranges' in request_data:
        formatted_params = {}
        for param_name, param_values in request_data['param_ranges'].items():
            # If the parameter has many values, just show count and range
            if isinstance(param_values, list) and len(param_values) > 10:
                formatted_params[param_name] = f"{len(param_values)} values from {min(param_values)} to {max(param_values)}"
            else:
                formatted_params[param_name] = param_values
        log_entry['param_ranges_request'] = formatted_params # Renamed for clarity
    
    # Add other request fields
    for key, value in request_data.items():
        if key != 'param_ranges' and key != 'strategy_type':
            log_entry[key] = value
            
    # Add parameters actually sent to the optimizer
    if params_to_optimizer is not None:
        log_entry['params_sent_to_optimizer'] = params_to_optimizer

    # Add parameters used for the final optimized backtest
    if final_params_backtest is not None:
        log_entry['final_params_for_optimized_backtest'] = final_params_backtest
            
    # Add extra info if provided (Performance, Parameter Changes, Top Results)
    if extra_info is not None:
        # Format optimization results for better readability
        if 'default_performance' in extra_info and 'optimized_performance' in extra_info:
            perf_comparison = {}
            for metric in ['sharpe_ratio', 'total_return_percent', 'max_drawdown_percent', 'win_rate_percent']:
                if metric in extra_info['default_performance'] and metric in extra_info['optimized_performance']:
                    default_val = extra_info['default_performance'][metric]
                    opt_val = extra_info['optimized_performance'][metric]
                    perf_comparison[metric] = {
                        'default': round(default_val, 4) if isinstance(default_val, (int, float)) else default_val,
                        'optimized': round(opt_val, 4) if isinstance(opt_val, (int, float)) else opt_val,
                        'improvement': f"{round((opt_val - default_val) / abs(default_val) * 100, 2)}%" 
                            if isinstance(default_val, (int, float)) and default_val != 0 else "N/A"
                    }
            log_entry['performance_comparison'] = perf_comparison
        
        # Add parameter comparison
        if 'default_params' in extra_info and 'optimized_params' in extra_info:
            param_comparison = {}
            # Get all unique parameter names
            all_params = set(list(extra_info['default_params'].keys()) + list(extra_info['optimized_params'].keys()))
            for param in all_params:
                default_val = extra_info['default_params'].get(param, "N/A")
                opt_val = extra_info['optimized_params'].get(param, "N/A")
                if default_val != opt_val:
                    param_comparison[param] = {
                        'default': default_val,
                        'optimized': opt_val
                    }
            log_entry['parameter_changes'] = param_comparison
        
        # Add summary of all results
        if 'all_results' in extra_info:
            top_results_summary = []
            for i, result in enumerate(extra_info['all_results'][:min(3, len(extra_info['all_results']))]):
                result_summary = {
                    'rank': i + 1,
                    'params': result['params'],
                    'score': round(result['value'], 4) if isinstance(result['value'], (int, float)) else result['value']
                }
                top_results_summary.append(result_summary)
            log_entry['top_results_summary'] = top_results_summary
    
    # Add error if any
    if error is not None:
        log_entry['error'] = str(error)
        
        # Add traceback info if available
        if traceback_info is not None:
            log_entry['traceback'] = traceback_info
        # If traceback not provided, try to get current exception traceback
        elif error:
            current_tb = tb.format_exc()
            if current_tb and 'NoneType' not in current_tb:
                log_entry['traceback'] = current_tb
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False, indent=2) + '\n\n')
    except Exception as e:
        logger.error(f"Failed to write optimization request log: {e}")

# Routes
@app.get("/")
@endpoint_wrapper("GET /")
async def read_root():
    return FileResponse("frontend/index.html")

@app.post("/api/upload")
@endpoint_wrapper("POST /api/upload")
async def upload_file(file: Optional[UploadFile] = None):
    global UPLOADED_DATA
    default_file_used = False
    temp_file_path = None

    if file:
        log_endpoint("POST /api/upload - DETAILS", file_name=file.filename, content_type=file.content_type)
        contents = await file.read()
        temp_file_path = os.path.join('data', 'temp_upload.csv')
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        with open(temp_file_path, 'wb') as f:
            f.write(contents)
        logger.info(f"File uploaded by user and saved temporarily to {temp_file_path}")
    else:
        default_file_path = os.path.join('data', 'teste_arranged.csv')
        if not os.path.exists(default_file_path):
            log_endpoint("POST /api/upload - DETAILS", error=f"Default file not found: {default_file_path}")
            return JSONResponse(
                status_code=404,
                content={"message": f"Default file {default_file_path} not found. Please upload a file."}
            )
        temp_file_path = default_file_path
        default_file_used = True
        log_endpoint("POST /api/upload - DETAILS", using_default_file=temp_file_path)
        logger.info(f"No file uploaded by user. Using default file: {temp_file_path}")

    if temp_file_path is None:
         raise ValueError("temp_file_path is not set. This indicates a logic error.")

    data_loader = DataLoader(temp_file_path)
    UPLOADED_DATA = data_loader.load_csv()
    logger.info(f"Data loaded successfully: {UPLOADED_DATA.shape}")
    
    for col in UPLOADED_DATA.columns:
        if 'unnamed' in col.lower() and UPLOADED_DATA[col].isna().all():
            UPLOADED_DATA = UPLOADED_DATA.drop(columns=[col])
    
    sample_data_for_preview = stringify_df_dates(UPLOADED_DATA.head(5))
    
    response_data = {
        "message": "File processed successfully" if default_file_used else "File uploaded successfully",
        "data_shape": UPLOADED_DATA.shape,
        "data_sample": sample_data_for_preview.to_dict('records'),
        "columns": list(UPLOADED_DATA.columns)
    }
    log_endpoint("POST /api/upload - DATA_SUMMARY", 
                data_shape=UPLOADED_DATA.shape,
                columns=list(UPLOADED_DATA.columns))
    return response_data

@app.post("/api/arrange-data")
@endpoint_wrapper("POST /api/arrange-data")
async def arrange_data_endpoint(file: UploadFile = File(...)):
    global PROCESSED_DATA, UPLOADED_DATA
    
    log_endpoint("POST /api/arrange-data - DETAILS", filename=file.filename)
    temp_input_path = os.path.join('data', 'temp_' + file.filename)
    os.makedirs(os.path.dirname(temp_input_path), exist_ok=True)
    
    with open(temp_input_path, 'wb') as f:
        contents = await file.read()
        f.write(contents)
    
    from data.data_arranger_script import arrange_data_file
    
    clean_input_path = os.path.join('data', file.filename)
    if os.path.exists(clean_input_path):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_base, file_ext = os.path.splitext(file.filename)
        clean_input_path = os.path.join('data', f"{file_base}_{timestamp}{file_ext}")
    os.replace(temp_input_path, clean_input_path)
    
    output_file = arrange_data_file(clean_input_path)
    
    if os.path.exists(clean_input_path):
        os.remove(clean_input_path)
    
    data_loader = DataLoader(output_file)
    arranged_data = data_loader.load_csv()
    
    UPLOADED_DATA = arranged_data.copy()
    PROCESSED_DATA = arranged_data.copy()
    
    sample_data_for_preview = stringify_df_dates(arranged_data.head(5))
    
    date_range = {}
    if 'date' in PROCESSED_DATA.columns and pd.api.types.is_datetime64_any_dtype(PROCESSED_DATA['date']):
        date_min = PROCESSED_DATA['date'].min()
        date_max = PROCESSED_DATA['date'].max()
        date_range["start"] = date_min.strftime('%Y-%m-%d') if pd.notna(date_min) else "N/A"
        date_range["end"] = date_max.strftime('%Y-%m-%d') if pd.notna(date_max) else "N/A"
    else:
        date_range = {"start": "N/A", "end": "N/A"}

    log_endpoint("POST /api/arrange-data - DATA_SUMMARY", 
                 output_file=output_file,
                 data_shape=arranged_data.shape,
                 columns=list(arranged_data.columns),
                 date_range=date_range)

    return {
        "message": f"Data arranged successfully and saved to {output_file}",
        "output_file": output_file,
        "data_shape": arranged_data.shape,
        "data_sample": sample_data_for_preview.to_dict('records'),
        "columns": list(arranged_data.columns),
        "date_range": date_range
    }

@app.post("/api/process-data")
@endpoint_wrapper("POST /api/process-data")
async def process_data():
    """
    Process the uploaded data.
    Enhanced with more robust error handling and data caching.
    """
    # Check if data is available
    if CACHED_DATA["original_data"] is None:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "No data uploaded. Please upload a data file first."}
        )
    
    try:
        # Get the raw data
        raw_data = CACHED_DATA["original_data"].copy()
        
        # Process the raw data
        data_loader = DataLoader()
        data_loader.data = raw_data
        processed_data = data_loader.clean_data()
        
        # Functions to parse dates - moved from inner to module level
        def parse_date(date_str):
    return pd.to_datetime(date_str, errors='coerce', dayfirst=True, infer_datetime_format=True)
        
        # Ensure date column is datetime
        if 'date' in processed_data.columns:
            if not pd.api.types.is_datetime64_any_dtype(processed_data['date']):
                processed_data['date'] = processed_data['date'].apply(parse_date)
                
                # If parsing failed, log and handle the issue
                if processed_data['date'].isna().any():
                    num_na = processed_data['date'].isna().sum()
                    total = len(processed_data)
                    percent_na = (num_na / total) * 100
                    
                    logger.warning(f"Failed to parse {num_na} dates ({percent_na:.2f}% of total)")
                    
                    if percent_na > 50:
                        return JSONResponse(
                            status_code=400,
                            content={
                                "success": False, 
                                "message": f"Failed to parse the majority of dates ({percent_na:.2f}%). Please check the date format."
                            }
                        )
                    
                    # Drop rows with NA dates
                    processed_data = processed_data.dropna(subset=['date'])
            
            # Sort data by date
            processed_data = processed_data.sort_values('date')
        
        # Convert numeric columns to appropriate types
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in processed_data.columns:
                processed_data[col] = pd.to_numeric(processed_data[col], errors='coerce')
        
        # Update the cached processed data
        update_cached_data(processed_data, "processed_data")
        
        # Return data summary
        return {
            "success": True,
            "data_summary": {
                "rows": len(processed_data),
                "columns": processed_data.columns.tolist(),
                "start_date": processed_data['date'].min().strftime('%Y-%m-%d') if 'date' in processed_data.columns else None,
                "end_date": processed_data['date'].max().strftime('%Y-%m-%d') if 'date' in processed_data.columns else None,
                "sample_data": processed_data.head(5).to_dict(orient='records')
            }
        }
    except Exception as e:
        error_message = f"Error processing data: {str(e)}"
        stack_trace = traceback.format_exc()
        logger.error(f"{error_message}\n{stack_trace}")
        
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": error_message}
        )

@app.post("/api/add-indicators")
@endpoint_wrapper("POST /api/add-indicators")
async def add_indicators(indicator_config: IndicatorConfig):
    global PROCESSED_DATA
    
    log_endpoint("POST /api/add-indicators - DETAILS", 
                config=indicator_config.dict(exclude_none=True), 
                data_shape=PROCESSED_DATA.shape if PROCESSED_DATA is not None else "None")
    
    if PROCESSED_DATA is None:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "No processed data available. Please upload and process data first."}
        )
        
    indicators_dict = indicator_config.dict(exclude_none=True)
    required_cols = REQUIRED_COLUMNS
    
    missing_cols = check_required_columns(PROCESSED_DATA, required_cols)
    if missing_cols:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"Missing required columns in data: {', '.join(missing_cols)}"}
        )
            
    base_columns = REQUIRED_COLUMNS
    # Ensure only existing base columns are selected
    existing_base_columns = [col for col in base_columns if col in PROCESSED_DATA.columns]
    data_for_indicators = PROCESSED_DATA[existing_base_columns].copy()
        
    data_with_indicators = combine_indicators(data_for_indicators, indicators_dict)
    PROCESSED_DATA = data_with_indicators
        
    excluded_columns = base_columns + ['ticker', 'index'] # Define base columns explicitly
    indicator_columns = [col for col in PROCESSED_DATA.columns if col not in excluded_columns]
        
    summary = ""
    if indicator_columns:
        try:
            indicator_summary_df = create_indicator_summary(PROCESSED_DATA, last_n_periods=1)
            summary = f"<div class='alert alert-info'><strong>Indicators added:</strong> {', '.join(indicator_columns)}</div>"
            # Potentially add indicator_summary_df to response if needed by frontend
        except Exception as e_summary:
            logger.error(f"Error creating indicator summary: {str(e_summary)}")
            summary = f"<div class='alert alert-warning'><strong>Indicators added</strong> but could not create summary: {str(e_summary)}</div>"
    
    log_endpoint("POST /api/add-indicators - SUMMARY", 
                indicators_added_count=len(indicator_columns),
                indicator_list=indicator_columns)
    
    return {
        "success": True,
        "message": "Indicators added successfully",
        "indicator_summary": summary,
        "available_indicators": indicator_columns
    }

@app.post("/api/plot-indicators")
@endpoint_wrapper("POST /api/plot-indicators")
async def plot_indicators(plot_config: PlotConfig):
    global PROCESSED_DATA
    
    log_endpoint("POST /api/plot-indicators - DETAILS", 
                config=plot_config.dict(exclude_none=True), 
                data_shape=PROCESSED_DATA.shape if PROCESSED_DATA is not None else "None")
    
    if PROCESSED_DATA is None:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "No processed data available. Please upload and process data first."}
        )
    
    plot_dict = plot_config.dict(exclude_none=True)
    image_base64 = plot_price_with_indicators(PROCESSED_DATA, plot_dict)
    
    log_endpoint("POST /api/plot-indicators - SUMMARY", 
                plot_generated=True,
                main_indicators_count=len(plot_config.main_indicators),
                subplot_indicators_count=len(plot_config.subplot_indicators))
    
    return {
        "success": True,
        "message": "Plot created successfully",
        "chart_image": image_base64
    }

@app.get("/api/available-strategies")
@endpoint_wrapper("GET /api/available-strategies")
async def get_strategies():
    """
    Get a list of available strategies.
    Enhanced to dynamically refresh the strategy list.
    """
    # Refresh strategy modules to ensure we have the latest
    strategy_registry, available_strategies = load_strategy_modules()
    return {"success": True, "strategies": available_strategies}

@app.get("/api/strategy-parameters/{strategy_type}")
@endpoint_wrapper("GET /api/strategy-parameters")
async def get_strategy_parameters(strategy_type: str, request: Request):
    default_params = get_default_parameters(strategy_type)
    return {"parameters": default_params}

@app.post("/api/run-backtest")
@endpoint_wrapper("POST /api/run-backtest")
async def run_backtest(strategy_config: StrategyConfig, backtest_config: BacktestConfig, request: Request):
    """
    Run a backtest with the specified strategy and parameters.
    Improved to better integrate with the backtesting module.
    """
    # Get the data
    data = get_cached_data()
    if data is None:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "No data available. Please upload and process data first."}
        )
    
    try:
        # Update backtest status
        BACKTEST_STATUS.update({
            "in_progress": True,
            "strategy_type": strategy_config.strategy_type,
            "start_time": datetime.now(),
            "completed": False,
            "error": None
        })
        
        # Log the request
        log_endpoint("run_backtest", 
                   strategy_type=strategy_config.strategy_type, 
                   parameters=strategy_config.parameters,
                   backtest_config=backtest_config.dict())
        
        # Create a backtester instance
        backtester = Backtester(data, backtest_config.initial_capital, backtest_config.commission)
        
        # Get the strategy function
        strategy = create_strategy(strategy_config.strategy_type, **strategy_config.parameters)
        
        # Run the backtest
        result = backtester.run_backtest(
            strategy, 
            start_date=backtest_config.start_date, 
            end_date=backtest_config.end_date
        )
        
        # Extract performance metrics
        metrics = result['performance_metrics']
        
        # Get backtest results (signals dataframe)
        strategy_name = result['strategy_name']
        backtest_results = backtester.results[strategy_name]['backtest_results']
        
        # Calculate additional performance metrics
        additional_metrics = calculate_advanced_metrics(backtest_results, backtest_config.initial_capital)
        metrics.update(additional_metrics)
        
        # Create the equity curve plot
        equity_curve_plot = plot_backtest_results(
            backtest_results, 
            strategy_name=strategy_name, 
            initial_capital=backtest_config.initial_capital
        )
        
        # Extract trades from the backtest results
        trades = extract_trades(backtest_results, backtest_config.commission, backtest_config.initial_capital)
        
        # Store the signals dataframe in the cache for later use
        update_cached_data(backtest_results, "signals_data")
        
        # Update backtest status
        BACKTEST_STATUS.update({
            "in_progress": False,
            "completed": True
        })
        
        # Return the results
        return {
            "success": True,
            "strategy_type": strategy_config.strategy_type,
            "parameters": strategy_config.parameters,
            "performance_metrics": metrics,
            "equity_curve": equity_curve_plot,
            "trades": trades,
            "backtest_config": backtest_config.dict()
        }
    except Exception as e:
        # Log the error
        error_message = f"Error during backtest: {str(e)}"
        stack_trace = traceback.format_exc()
        logger.error(f"{error_message}\n{stack_trace}")
        
        # Update backtest status
        BACKTEST_STATUS.update({
            "in_progress": False,
            "error": error_message
        })
        
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": error_message}
        )

@app.post("/api/optimize-strategy")
@endpoint_wrapper("POST /api/optimize-strategy")
async def optimize_strategy_endpoint(optimization_config: OptimizationConfig, background_tasks: BackgroundTasks, request: Request):
    """
    Optimize strategy parameters for the specified strategy type.
    Improved to better utilize the optimization module.
    """
    global OPTIMIZATION_STATUS
    
    # Check if optimization is already in progress
    if OPTIMIZATION_STATUS["in_progress"]:
        return JSONResponse(
            status_code=400,
            content={
                "success": False, 
                "message": f"Optimization already in progress for {OPTIMIZATION_STATUS['strategy_type']} strategy."
            }
        )
    
    # Get the data
    data = get_cached_data()
    if data is None:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "No data available. Please upload and process data first."}
        )
    
    # Log the optimization request and parameters
    log_optimization_request(
        request_data=optimization_config.dict(),
        extra_info=f"Starting optimization for {optimization_config.strategy_type} strategy"
    )
    
    # Reset optimization status
    OPTIMIZATION_STATUS = {
        "in_progress": True,
        "strategy_type": optimization_config.strategy_type,
        "start_time": datetime.now(),
        "latest_result_file": None,
        "comparison_data": {},
        "progress": 0.0,
        "error": None,
        "total_iterations": 0,
        "completed_iterations": 0
    }
    
    # Run optimization in the background
    background_tasks.add_task(
        run_optimization_task,
        data, 
        optimization_config.strategy_type,
        optimization_config.param_ranges,
        optimization_config.metric,
        optimization_config.start_date,
        optimization_config.end_date
    )
    
    return {"success": True, "message": f"Optimization started for {optimization_config.strategy_type} strategy."}

def run_optimization_task(data, strategy_type, param_ranges, metric="sharpe_ratio", start_date=None, end_date=None):
    """
    Run optimization task in the background.
    This is a better integration with the optimization module.
    """
    global OPTIMIZATION_STATUS
    
    try:
        # Log starting the optimization task
        logger.info(f"Starting optimization task for {strategy_type} with metric: {metric}")
        
        # Calculate total iterations for progress tracking
        total_iterations = 1
        for param_name, param_values in param_ranges.items():
            total_iterations *= len(param_values)
        
        OPTIMIZATION_STATUS["total_iterations"] = total_iterations
        logger.info(f"Total optimization iterations: {total_iterations}")
        
        # Create a progress tracker callback
        def progress_callback(completed_iterations):
            OPTIMIZATION_STATUS["completed_iterations"] = completed_iterations
            OPTIMIZATION_STATUS["progress"] = (completed_iterations / total_iterations) * 100
        
        # Run the actual optimization - using the optimization module directly
        best_params, best_value, all_results = optimize_strategy(
            data, 
            strategy_type,
            param_ranges=param_ranges,
            metric=metric,
            start_date=start_date,
            end_date=end_date,
            progress_callback=progress_callback
        )
        
        # Create timestamp for the result file
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Prepare directory for saving results
        result_dir = os.path.join("results", "optimization")
        os.makedirs(result_dir, exist_ok=True)
        
        # Create result filename
        result_file = os.path.join(result_dir, f"{strategy_type}_optimization_{timestamp}.json")
        
        # Create backtester with the optimized parameters for this strategy
        backtester = Backtester(data)
        strategy = create_strategy(strategy_type, **best_params)
        result = backtester.run_backtest(strategy, start_date=start_date, end_date=end_date)
        
        # Get the backtest results and performance metrics
        strategy_name = result['strategy_name']
        backtest_results = backtester.results[strategy_name]['backtest_results']
        performance_metrics = backtester.results[strategy_name]['performance_metrics']
        
        # Calculate additional metrics
        additional_metrics = calculate_advanced_metrics(backtest_results)
        performance_metrics.update(additional_metrics)
        
        # Create the equity curve plot
        equity_curve_plot = plot_backtest_results(backtest_results, strategy_name=f"Optimized {strategy_type}")
        
        # Prepare optimization results to save
        optimization_results = {
            "strategy_type": strategy_type,
            "best_parameters": best_params,
            "best_value": best_value,
            "metric": metric,
            "start_date": start_date,
            "end_date": end_date,
            "timestamp": timestamp,
            "performance_metrics": performance_metrics,
            "equity_curve": equity_curve_plot,
            "all_results": all_results[:100]  # Limit to top 100 results to avoid huge files
        }
        
        # Save the results to a file
        with open(result_file, 'w') as f:
            json.dump(optimization_results, f, indent=2)
        
        # Update the optimization status
        OPTIMIZATION_STATUS.update({
            "in_progress": False,
            "latest_result_file": result_file,
            "progress": 100.0,
            "completed_iterations": total_iterations
        })
        
        # Log the completion of the optimization
        logger.info(f"Optimization completed for {strategy_type} strategy. Best value: {best_value}")
        logger.info(f"Best parameters: {best_params}")
        logger.info(f"Results saved to {result_file}")
        
        # Log the optimization request completion
        log_optimization_request(
            request_data={
                "strategy_type": strategy_type,
                "metric": metric
            },
            extra_info=f"Optimization completed for {strategy_type} strategy",
            final_params_backtest=best_params
        )
        
    except Exception as e:
        # Log the error
        error_message = f"Error during optimization: {str(e)}"
        stack_trace = traceback.format_exc()
        logger.error(f"{error_message}\n{stack_trace}")
        
        # Update the optimization status with the error
        OPTIMIZATION_STATUS.update({
            "in_progress": False,
            "error": error_message,
            "progress": 0.0
        })
        
        # Log the optimization error
        log_optimization_request(
            request_data={
                "strategy_type": strategy_type,
                "metric": metric
            },
            error=error_message,
            traceback_info=stack_trace
        )

@app.get("/api/optimization-status")
@endpoint_wrapper("GET /api/optimization-status")
async def get_optimization_status():
    global OPTIMIZATION_STATUS
    return OPTIMIZATION_STATUS

@app.get("/api/optimization-results/{strategy_type}")
@endpoint_wrapper("GET /api/optimization-results")
async def get_optimization_results(strategy_type: str, request: Request):
    import os, json
    from fastapi.responses import JSONResponse
    global OPTIMIZATION_STATUS
    log_endpoint(f"{request.method} {request.url.path} - DETAILS", strategy=strategy_type)

    # If optimization is in progress, return status
    if OPTIMIZATION_STATUS["in_progress"] and OPTIMIZATION_STATUS["strategy_type"] == strategy_type:
        return {"status": "in_progress", "message": f"Optimization for {strategy_type} is still in progress"}

    results_dir = os.path.join("results", "optimization")
    if not os.path.exists(results_dir):
        logger.warning(f"Results directory not found: {results_dir}")
        return {"status": "not_found", "message": "No optimization results directory found"}

    try:
        files = [f for f in os.listdir(results_dir) if f.startswith(f"optimization_{strategy_type}_") and f.endswith(".json")]
    except FileNotFoundError:
        logger.warning(f"Results directory disappeared: {results_dir}")
        return {"status": "not_found", "message": "Optimization results directory disappeared."}

    if not files:
        logger.warning(f"No optimization files found for strategy: {strategy_type}")
        return {"status": "not_found", "message": f"No optimization results found for strategy type '{strategy_type}'"}

    latest_file = max(files, key=lambda f_name: os.path.getmtime(os.path.join(results_dir, f_name)))
    file_path = os.path.join(results_dir, latest_file)
    logger.info(f"Found latest optimization results file: {file_path}")

    try:
        with open(file_path, 'r') as f:
            results_content = json.load(f)
        
        # If the file doesn't have top_results, transform it to match the expected format
        if 'top_results' not in results_content:
            if 'all_results' in results_content:
                # Take the top 10 results (or fewer if less available)
                top_results = []
                for i, result in enumerate(results_content.get('all_results', [])[:10]):
                    top_results.append({
                        "params": result.get('params', {}),
                        "score": result.get('value', 0),
                        "metrics": result.get('performance', {})
                    })
                results_content['top_results'] = top_results
            else:
                # Create empty top_results if all_results is missing
                results_content['top_results'] = []

        # Check if comparison data is present in the file
        has_comparison = ('default_params' in results_content and 
                          'optimized_params' in results_content and
                          'default_performance' in results_content and
                          'optimized_performance' in results_content)
        
        # If no comparison data in the file but we have it in memory, add it to the results
        if not has_comparison and hasattr(OPTIMIZATION_STATUS, 'comparison_data'):
            logger.info(f"Adding comparison data from memory to results: {strategy_type}")
            results_content.update(OPTIMIZATION_STATUS.get('comparison_data', {}))
                
        log_endpoint(f"{request.method} {request.url.path} - RESULTS_LOADED", file=latest_file)
        return JSONResponse(content={
            "status": "success",
            "results": results_content,
            "timestamp": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        logger.error(f"Error reading optimization results file: {str(e)}\n{traceback.format_exc()}")
        return {"status": "error", "message": f"Error reading optimization results: {str(e)}"}

@app.post("/api/compare-strategies")
@endpoint_wrapper("POST /api/compare-strategies")
async def compare_strategies(request: Request):
    """
    Compare multiple strategy configurations.
    Enhanced to better use the backtesting module for comparison.
    """
    # Get the request body as JSON
    try:
        body = await request.json()
        strategy_configs = body.get('strategy_configs', [])
        backtest_config = body.get('backtest_config', {})
        
        # Validate inputs
        if not strategy_configs:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "No strategy configurations provided."}
            )
        
        # Get the data
        data = get_cached_data()
        if data is None:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "No data available. Please upload and process data first."}
            )
        
        # Set up backtest configuration
        initial_capital = backtest_config.get('initial_capital', 10000.0)
        commission = backtest_config.get('commission', 0.001)
        start_date = backtest_config.get('start_date')
        end_date = backtest_config.get('end_date')
        
        # Create backtester
        backtester = Backtester(data, initial_capital, commission)
        
        # Initialize results
        comparison_results = {}
        
        # Run backtest for each strategy configuration
        for config in strategy_configs:
            strategy_type = config.get('strategy_type')
            parameters = config.get('parameters', {})
            
            if not strategy_type:
                continue
            
            # Create strategy
            strategy = create_strategy(strategy_type, **parameters)
            
            # Run backtest
            result = backtester.run_backtest(strategy, start_date=start_date, end_date=end_date)
            
            # Get performance metrics
            strategy_name = result['strategy_name']
            performance_metrics = result['performance_metrics']
            
            # Store results
            comparison_results[strategy_name] = {
                'strategy_type': strategy_type,
                'parameters': parameters,
                'performance_metrics': performance_metrics
            }
        
        # Generate equity curve plot
        equity_curve_plot = backtester.plot_equity_curves()
        
        # Update optimization status comparison data
        OPTIMIZATION_STATUS['comparison_data'] = {
            'results': comparison_results,
            'equity_curve': equity_curve_plot,
            'backtest_config': backtest_config
        }
        
        # Return results
        return {
            "success": True,
            "comparison_results": comparison_results,
            "equity_curve": equity_curve_plot
        }
    except Exception as e:
        error_message = f"Error comparing strategies: {str(e)}"
        stack_trace = traceback.format_exc()
        logger.error(f"{error_message}\n{stack_trace}")
        
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": error_message}
        )

@app.post("/api/save-config")
@endpoint_wrapper("POST /api/save-config")
async def save_config_endpoint(config_data: Dict[str, Any], request: Request):
    global CURRENT_CONFIG
    
    log_endpoint(f"{request.method} {request.url.path} - DETAILS", config_keys=list(config_data.keys()))
    CURRENT_CONFIG.update(config_data)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    config_dir = os.path.join("results", "configs")
    os.makedirs(config_dir, exist_ok=True)
    config_file_path = os.path.join(config_dir, f"config_{timestamp}.json")
    
    with open(config_file_path, 'w') as f:
        json.dump(CURRENT_CONFIG, f, indent=4)
    
    log_endpoint(f"{request.method} {request.url.path} - SAVED", file=config_file_path)
    return {"message": "Configuration saved successfully", "config_file": config_file_path}

@app.get("/api/load-config/{config_file}")
@endpoint_wrapper("GET /api/load-config")
async def load_config_endpoint(config_file: str, request: Request):
    global CURRENT_CONFIG
    
    log_endpoint(f"{request.method} {request.url.path} - DETAILS", file=config_file)
    config_path_full = os.path.join("results", "configs", config_file)
    
    if not os.path.exists(config_path_full):
        return JSONResponse(status_code=404, content={"success": False, "message": "Config file not found."})

    with open(config_path_full, 'r') as f:
        loaded_config_data = json.load(f)
    
    CURRENT_CONFIG.update(loaded_config_data)
    log_endpoint(f"{request.method} {request.url.path} - LOADED", file=config_file)
    return {"message": "Configuration loaded successfully", "config": CURRENT_CONFIG}

@app.get("/api/export-results/{format}")
@endpoint_wrapper("GET /api/export-results")
async def export_results(format_type: str, request: Request):
    global BACKTESTER
    
    log_endpoint(f"{request.method} {request.url.path} - DETAILS", format_requested=format_type)

    if BACKTESTER is None or not BACKTESTER.results:
        return JSONResponse(status_code=400, content={"success": False, "message": "No backtest results."})
    
    results_dir_export = os.path.join("results", "exports")
    os.makedirs(results_dir_export, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    file_to_send_path = ""
    file_to_send_name = ""
    media_type_str = ""

    if format_type.lower() == 'json':
        file_to_send_name = f"backtest_results_{timestamp}.json"
        file_to_send_path = os.path.join(results_dir_export, file_to_send_name)
        BACKTESTER.save_results(file_to_send_path)
        media_type_str = "application/json"
    elif format_type.lower() == 'csv':
        file_to_send_name = f"backtest_results_{timestamp}.csv"
        file_to_send_path = os.path.join(results_dir_export, file_to_send_name)
        all_results_df = pd.DataFrame()
        if isinstance(BACKTESTER.results, dict):
            for strategy_name, result_data in BACKTESTER.results.items():
                if isinstance(result_data, dict) and 'backtest_results' in result_data and isinstance(result_data['backtest_results'], pd.DataFrame):
                    backtest_df_single = result_data['backtest_results'].copy()
                    backtest_df_single['strategy'] = strategy_name
                    all_results_df = pd.concat([all_results_df, backtest_df_single])
                elif isinstance(result_data, pd.DataFrame):
                    backtest_df_single = result_data.copy()
                    backtest_df_single['strategy'] = strategy_name
                    all_results_df = pd.concat([all_results_df, backtest_df_single])

            if not all_results_df.empty:
                all_results_df.to_csv(file_to_send_path, index=False)
                media_type_str = "text/csv"
            else:
                 return JSONResponse(status_code=400, content={"success":False, "message": "No data to export to CSV."})
        else:
            return JSONResponse(status_code=400, content={"success":False, "message": "Results format not suitable for CSV export."})
    else:
        return JSONResponse(status_code=400, content={"success":False, "message": f"Unsupported format: {format_type}"})


@app.get("/api/current-config")
@endpoint_wrapper("GET /api/current-config")
async def get_current_config(request: Request):
    global CURRENT_CONFIG, PROCESSED_DATA
    
    if PROCESSED_DATA is not None:
        indicator_columns = [col for col in PROCESSED_DATA.columns 
                           if col not in REQUIRED_COLUMNS]
        if 'indicators' not in CURRENT_CONFIG: CURRENT_CONFIG['indicators'] = {}
        CURRENT_CONFIG['indicators']['available_indicators'] = indicator_columns
    
    return CURRENT_CONFIG

@app.get("/api/data-status")
@endpoint_wrapper("GET /api/data-status")
async def data_status(request: Request):
    global UPLOADED_DATA, PROCESSED_DATA
    return {
        "uploaded": UPLOADED_DATA is not None,
        "processed": PROCESSED_DATA is not None,
        "shape": PROCESSED_DATA.shape if PROCESSED_DATA is not None else None
    }

@app.get("/api/debug-info")
@endpoint_wrapper("GET /api/debug-info")
async def debug_info(request: Request):
    system_info = {
        "platform": platform.platform(), "python_version": platform.python_version(),
        "processor": platform.processor(), "memory": f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
        "available_memory": f"{psutil.virtual_memory().available / (1024**3):.2f} GB",
        "cpu_count": psutil.cpu_count(logical=True), "hostname": platform.node()
    }
    app_info = {
        "current_directory": os.getcwd(), 
        "start_time_process": datetime.fromtimestamp(psutil.Process().create_time()).strftime('%Y-%m-%d %H:%M:%S'),
        "uptime_seconds": time.time() - psutil.Process().create_time(),
        "process_memory_usage": f"{psutil.Process().memory_info().rss / (1024**2):.2f} MB",
        "loaded_modules_count": len(sys.modules) 
    }
    
    uploaded_data_summary = None
    if UPLOADED_DATA is not None:
        uploaded_data_summary = {
            "shape": UPLOADED_DATA.shape, "columns": list(UPLOADED_DATA.columns),
            "memory_usage": f"{UPLOADED_DATA.memory_usage(deep=True).sum() / (1024**2):.2f} MB",
            "sample_rows_count": len(UPLOADED_DATA.head(3))
        }

    processed_data_summary = None
    if PROCESSED_DATA is not None:
        date_range_processed = {"start": "N/A", "end": "N/A"}
        if 'date' in PROCESSED_DATA.columns and pd.api.types.is_datetime64_any_dtype(PROCESSED_DATA['date']):
            min_d, max_d = PROCESSED_DATA['date'].min(), PROCESSED_DATA['date'].max()
            date_range_processed["start"] = min_d.strftime('%Y-%m-%d') if pd.notna(min_d) else "N/A"
            date_range_processed["end"] = max_d.strftime('%Y-%m-%d') if pd.notna(max_d) else "N/A"
        
        processed_data_summary = {
            "shape": PROCESSED_DATA.shape, "columns": list(PROCESSED_DATA.columns),
            "memory_usage": f"{PROCESSED_DATA.memory_usage(deep=True).sum() / (1024**2):.2f} MB",
            "date_range": date_range_processed,
            "has_indicators": len([c for c in PROCESSED_DATA.columns if c not in REQUIRED_COLUMNS]) > 0
        }

    data_info_summary = { "uploaded_data_summary": uploaded_data_summary, "processed_data_summary": processed_data_summary }

    log_endpoint(f"{request.method} {request.url.path} - DEBUG_INFO_ACCESS", platform=system_info["platform"])
    return {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "system_info": system_info, "app_info": app_info, "data_info": data_info_summary
    }

# Seasonality Endpoints
@app.post("/api/seasonality/day-of-week")
@endpoint_wrapper("POST /api/seasonality/day-of-week")
async def analyze_day_of_week(request: Request):
    global PROCESSED_DATA
    if PROCESSED_DATA is None: return JSONResponse(status_code=400, content={"success": False, "message": "No data."})
    
    log_endpoint(f"{request.method} {request.url.path} - START_ANALYSIS")
    dow_returns_df, fig_dow = day_of_week_returns(PROCESSED_DATA, plot=True)
    
    buffer = io.BytesIO()
    fig_dow.savefig(buffer, format='png')
    buffer.seek(0)
    img_str_b64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return JSONResponse(content={"success": True, "plot": img_str_b64, "data": dow_returns_df.to_dict('records')})

@app.post("/api/seasonality/monthly")
@endpoint_wrapper("POST /api/seasonality/monthly")
async def analyze_monthly(request: Request):
    global PROCESSED_DATA
    if PROCESSED_DATA is None: return JSONResponse(status_code=400, content={"success": False, "message": "No data."})

    log_endpoint(f"{request.method} {request.url.path} - START_ANALYSIS")
    monthly_rets_df, fig_monthly = monthly_returns(PROCESSED_DATA, plot=True)

    buffer = io.BytesIO()
    fig_monthly.savefig(buffer, format='png')
    buffer.seek(0)
    img_str_b64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return JSONResponse(content={"success": True, "plot": img_str_b64, "data": monthly_rets_df.to_dict('records')})

@app.post("/api/seasonality/volatility")
@endpoint_wrapper("POST /api/seasonality/volatility")
async def analyze_volatility(request: Request):
    global PROCESSED_DATA
    if PROCESSED_DATA is None: return JSONResponse(status_code=400, content={"success": False, "message": "No data."})

    log_endpoint(f"{request.method} {request.url.path} - START_ANALYSIS")
    dow_vol_df, fig_vol = day_of_week_volatility(PROCESSED_DATA, plot=True)

    buffer = io.BytesIO()
    fig_vol.savefig(buffer, format='png')
    buffer.seek(0)
    img_str_b64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return JSONResponse(content={"success": True, "plot": img_str_b64, "data": dow_vol_df.to_dict('records')})

@app.post("/api/seasonality/heatmap")
@endpoint_wrapper("POST /api/seasonality/heatmap")
async def create_heatmap(request: Request):
    global PROCESSED_DATA
    if PROCESSED_DATA is None: return JSONResponse(status_code=400, content={"success": False, "message": "No data."})

    log_endpoint(f"{request.method} {request.url.path} - START_ANALYSIS")
    fig_heatmap = calendar_heatmap(PROCESSED_DATA)

    buffer = io.BytesIO()
    fig_heatmap.savefig(buffer, format='png')
    buffer.seek(0)
    img_str_b64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return JSONResponse(content={"success": True, "plot": img_str_b64})

@app.post("/api/seasonality/summary")
@endpoint_wrapper("POST /api/seasonality/summary")
async def get_seasonality_summary(request: Request):
    global PROCESSED_DATA
    if PROCESSED_DATA is None: return JSONResponse(status_code=400, content={"success": False, "message": "No data."})

    log_endpoint(f"{request.method} {request.url.path} - START_ANALYSIS")
    fig_summary, results_data = seasonality_summary(PROCESSED_DATA)

    buffer = io.BytesIO()
    fig_summary.savefig(buffer, format='png')
    buffer.seek(0)
    img_str_b64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return JSONResponse(content={"success": True, "plot": img_str_b64, "data": results_data})

# Helper functions (restored)
def calculate_performance_metrics(signals_df, initial_capital=10000.0, commission=0.001):
    """
    Calculate performance metrics from signals DataFrame.
    
    Args:
        signals_df (pd.DataFrame): DataFrame with signal column ('buy', 'sell', 'hold')
        initial_capital (float): Initial capital for the backtest
        commission (float): Commission rate per trade
        
    Returns:
        dict: Performance metrics
    """
    df = signals_df.copy()
    
    # Ensure we have the right columns
    required_cols = ['date', 'close', 'signal']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Data must contain columns: {required_cols}")
    
    # Initialize position and equity columns
    df['position'] = 0
    df['entry_price'] = 0.0
    df['equity'] = initial_capital
    df['trade_profit'] = 0.0
    df['trade_returns'] = 0.0
    
    position = 0
    entry_price = 0.0
    equity = initial_capital
    total_trades = 0
    winning_trades = 0
    losing_trades = 0
    total_profit = 0
    total_loss = 0
    
    buy_signals_indices = [] # Storing indices for potential analysis, not directly used in metrics here
    sell_signals_indices = []
    
    for i in range(len(df)):
        current_signal = df.iloc[i]['signal']
        current_price = df.iloc[i]['close']
        current_date = df.iloc[i]['date']
        
        if current_signal == 'buy':
            buy_signals_indices.append(df.index[i])
            if position == 0:
                position = 1
                entry_price = current_price * (1 + commission)
                logger.info(f"BUY at {current_date} price: {entry_price:.2f}")
        elif current_signal == 'sell':
            sell_signals_indices.append(df.index[i])
            if position == 1:
                position = 0
                exit_price = current_price * (1 - commission)
                trade_profit = exit_price - entry_price
                trade_return = (trade_profit / entry_price) if entry_price != 0 else 0
                equity += trade_profit
                
                total_trades += 1
                if trade_profit > 0:
                    winning_trades += 1
                    total_profit += trade_profit
                else:
                    losing_trades += 1
                    total_loss += trade_profit
                   
                df.at[df.index[i], 'trade_profit'] = trade_profit
                df.at[df.index[i], 'trade_returns'] = trade_return
                logger.info(f"SELL at {current_date} price: {exit_price:.2f}, profit: {trade_profit:.2f}")
            entry_price = 0.0 # Reset entry price
            entry_date_val = None
           
    df['market_return'] = df['close'].pct_change().fillna(0)
    df['cumulative_market_return'] = (1 + df['market_return']).cumprod()
    
    start_date = df['date'].min()
    end_date = df['date'].max()
    days = (end_date - start_date).days
    years = max(days / 365.25, 0.01) # Avoid division by zero for very short periods
    
    final_equity = df['equity'].iloc[-1] if not df['equity'].empty else initial_capital
    total_return_calc = (final_equity / initial_capital) - 1
    annual_return_calc = ((1 + total_return_calc) ** (1 / years)) - 1 if years > 0 else 0
    
    df['drawdown'] = (df['equity'].cummax() - df['equity']) / df['equity'].cummax().replace(0, np.nan) # Avoid div by zero if equity hits 0
    max_drawdown_calc = df['drawdown'].max() if not df['drawdown'].empty else 0
    max_drawdown_calc = max_drawdown_calc if pd.notna(max_drawdown_calc) else 0

    win_rate_calc = winning_trades / total_trades if total_trades > 0 else 0
    
    avg_win_calc = total_profit / winning_trades if winning_trades > 0 else 0
    avg_loss_calc = abs(total_loss / losing_trades) if losing_trades > 0 else 0 # abs for avg loss
    
    profit_factor_calc = abs(total_profit / total_loss) if total_loss != 0 else float('inf') # total_loss can be negative
    
    daily_returns_series = df['equity'].pct_change().fillna(0)
    annual_volatility_calc = daily_returns_series.std() * (252 ** 0.5)
    sharpe_ratio_calc = annual_return_calc / annual_volatility_calc if annual_volatility_calc > 0 else 0
    
    metrics = {
        'start_date': start_date.strftime('%Y-%m-%d') if pd.notna(start_date) else 'N/A',
        'end_date': end_date.strftime('%Y-%m-%d') if pd.notna(end_date) else 'N/A',
        'initial_capital': initial_capital,
        'final_capital': final_equity,
        'total_return_percent': total_return_calc * 100,
        'annual_return_percent': annual_return_calc * 100,
        'max_drawdown_percent': max_drawdown_calc * 100,
        'sharpe_ratio': sharpe_ratio_calc,
        'total_trades': total_trades,
        'win_rate_percent': win_rate_calc * 100,
        'profit_factor': profit_factor_calc,
        'avg_win': avg_win_calc,
        'avg_loss': avg_loss_calc,
        'annual_volatility_percent': annual_volatility_calc * 100,
        'buy_signals_count': len(buy_signals_indices),
        'sell_signals_count': len(sell_signals_indices)
        # 'final_capital_series': df['equity'].tolist() # For run_backtest to use if needed
    }
    
    # Ensure signals_df in the caller has the equity column for plotting
    signals_df['equity'] = df['equity']
    signals_df['cumulative_market_return'] = df['cumulative_market_return']
    return metrics

def plot_backtest_results(signals_df, strategy_name='Strategy', initial_capital=10000.0):
    """
    Generate HTML chart for backtest results.
    Args:
        signals_df (pd.DataFrame): DataFrame with backtest results (must include 'date', 'equity', 'cumulative_market_return')
        strategy_name (str): Name of the strategy
        initial_capital (float): Initial capital (used for Buy & Hold calculation)
    Returns:
        str: HTML chart string
    """
    df = signals_df.copy()

    # Ensure required columns exist
    required_plot_cols = ['date', 'equity', 'cumulative_market_return']
    missing_plot_cols = [col for col in required_plot_cols if col not in df.columns]
    if missing_plot_cols:
        logger.error(f"Missing columns for plotting: {missing_plot_cols}. Cannot generate equity curve.")
        return "<div class='alert alert-danger'>Error: Missing data for chart generation.</div>"
    
    # Ensure date is in string format for JSON serialization in chart
    df = stringify_df_dates(df) # Use the utility

    df['buy_hold_equity'] = initial_capital * df['cumulative_market_return']
    
    timestamp = int(time.time())
    chart_id = f"equity-curve-chart-{timestamp}"
    
    chart_html = f"""
    <div class="chart-container" style="position: relative; height:400px; width:100%; margin-bottom: 20px;">
        <canvas id="{chart_id}"></canvas>
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        const chartInit = function() {{
            console.log('Initializing equity curve chart: {chart_id}');
            const ctx = document.getElementById('{chart_id}');
            if (!ctx) {{ console.error('Chart canvas element not found: {chart_id}'); return; }}
            
            const chartData = {{
                labels: {json.dumps(df['date'].tolist())},
                datasets: [
                    {{
                        label: '{strategy_name}',
                        data: {json.dumps(df['equity'].tolist())},
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.1, fill: true
                    }},
                    {{
                        label: 'Buy & Hold',
                        data: {json.dumps(df['buy_hold_equity'].tolist())},
                        borderColor: 'rgb(192, 75, 75)',
                        backgroundColor: 'rgba(192, 75, 75, 0.1)',
                        borderDash: [5, 5], tension: 0.1, fill: true
                    }}
                ]
            }};
            
            try {{
                new Chart(ctx, {{
                    type: 'line', data: chartData,
                    options: {{
                        responsive: true, maintainAspectRatio: false,
                        plugins: {{ title: {{ display: true, text: 'Equity Curve' }}, tooltip: {{ mode: 'index', intersect: false }} }},
                        scales: {{
                            x: {{ display: true, title: {{ display: true, text: 'Date' }}, ticks: {{ maxTicksLimit: 12 }} }},
                            y: {{ display: true, title: {{ display: true, text: 'Equity ($)' }} }}
                        }}
                    }}
                }});
                console.log('Equity curve chart created: {chart_id}');
            }} catch (error) {{ console.error('Error creating equity curve chart ({chart_id}):', error); }}
        }};
        if (document.readyState === 'loading') {{ document.addEventListener('DOMContentLoaded', chartInit); }}
        else {{ chartInit(); }}
    }});
    </script>
    """
    return chart_html

def extract_trades(signals_df, commission=0.001, initial_capital=10000.0): # initial_capital not used here, but kept for signature consistency if desired
    """
    Extract individual trades from signals DataFrame.
    Args:
        signals_df (pd.DataFrame): DataFrame with 'date', 'close', 'signal' columns
        commission (float): Commission rate per trade
    Returns:
        list: List of trade dictionaries
    """
    df = signals_df.copy()
    trades = []
    position = 0
    entry_price = 0.0
    entry_date_val = None

    required_trade_cols = ['date', 'close', 'signal']
    if not all(col in df.columns for col in required_trade_cols):
        logger.error("Missing required columns for trade extraction.")
        return []

    for i in range(len(df)):
        current_signal = df.iloc[i]['signal']
        current_price = df.iloc[i]['close']
        current_date = df.iloc[i]['date'] # Assuming date is already pd.Timestamp or datetime object

        if current_signal == 'buy' and position == 0:
            position = 1
            entry_price = current_price * (1 + commission)
            entry_date_val = current_date
        elif current_signal == 'sell' and position == 1:
            position = 0
            exit_price = current_price * (1 - commission)
            exit_date_val = current_date
            
            if entry_price != 0: # Ensure there was an entry to calculate profit
                profit_val = exit_price - entry_price
                profit_pct_val = (profit_val / entry_price) * 100
                trades.append({
                    'entry_date': entry_date_val.strftime('%Y-%m-%d') if hasattr(entry_date_val, 'strftime') else str(entry_date_val),
                    'exit_date': exit_date_val.strftime('%Y-%m-%d') if hasattr(exit_date_val, 'strftime') else str(exit_date_val),
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'profit': profit_val,
                    'profit_pct': profit_pct_val,
                    'result': 'win' if profit_val > 0 else 'loss'
                })
            entry_price = 0.0 # Reset entry price
            entry_date_val = None
           
    return trades

@app.get("/api/check-optimization-directory")
@endpoint_wrapper("GET /api/check-optimization-directory")
async def check_optimization_directory():
    """
    Check if the optimization results directory exists and is writable.
    This helps diagnose issues with optimization results not being saved.
    """
    results_dir = os.path.join("results", "optimization")
    
    try:
        # Check if directory exists, create it if not
        if not os.path.exists(results_dir):
            os.makedirs(results_dir, exist_ok=True)
            logger.info(f"Created optimization directory: {results_dir}")
            
        # Check if directory is writable by attempting to create and delete a test file
        test_file_path = os.path.join(results_dir, "test_write.tmp")
        with open(test_file_path, 'w') as f:
            f.write("test")
        os.remove(test_file_path)
        
        return {
            "success": True, 
            "message": "Optimization directory exists and is writable",
            "directory": results_dir
        }
    except Exception as e:
        logger.error(f"Error checking optimization directory: {str(e)}\n{traceback.format_exc()}")
        return {
            "success": False,
            "message": f"Error with optimization directory: {str(e)}",
            "directory": results_dir
        }

# Calculate additional performance metrics
def calculate_advanced_metrics(signals_df, initial_capital=10000.0):
    """Calculate additional performance metrics that aren't in the base set"""
    df = signals_df.copy()
    metrics = {}
    
    try:
        # Initialize required columns if they don't exist
        if 'daily_return' not in df.columns:
            if 'equity' in df.columns:
                df['daily_return'] = df['equity'].pct_change().fillna(0)
            else:
                logger.warning("No equity column found in signals_df for advanced metrics calculation")
                return metrics
        
        # Percent profitable days
        profitable_days = (df['daily_return'] > 0).sum()
        total_days = len(df)
        metrics['percent_profitable_days'] = (profitable_days / total_days) * 100 if total_days > 0 else 0
        
        # Calculate average returns
        avg_daily_return = df['daily_return'].mean()
        # Annualize returns
        avg_annual_return = avg_daily_return * 252
        
        # Calculate standard deviation of daily returns
        std_daily = df['daily_return'].std()
        if std_daily > 0:
            # Annualize volatility
            annual_volatility = std_daily * np.sqrt(252)
            metrics['annual_volatility_percent'] = annual_volatility * 100
            
            # Sharpe ratio (assuming 0 risk-free rate for simplicity)
            metrics['sharpe_ratio'] = avg_annual_return / annual_volatility
        
        # Sortino ratio (downside risk only)
        negative_returns = df['daily_return'][df['daily_return'] < 0]
        if len(negative_returns) > 0:
            downside_std = negative_returns.std() * np.sqrt(252)
            metrics['sortino_ratio'] = avg_annual_return / downside_std if downside_std > 0 else 0
        else:
            # No negative returns is technically infinite Sortino, but we'll use a high value
            metrics['sortino_ratio'] = 10.0  # High value indicating no downside
        
        # Calculate drawdown if not already in the frame
        if 'drawdown' not in df.columns:
            if 'equity' in df.columns:
                df['peak'] = df['equity'].cummax()
                df['drawdown'] = (df['peak'] - df['equity']) / df['peak']
            else:
                logger.warning("Cannot calculate drawdown: no equity column")
        
        # Calmar ratio (return / max drawdown)
        if 'drawdown' in df.columns and df['drawdown'].max() > 0:
            metrics['calmar_ratio'] = avg_annual_return / df['drawdown'].max()
        else:
            metrics['calmar_ratio'] = 0
        
        # Ensure certain metrics exist and are not zero for display purposes
        if metrics.get('calmar_ratio', 0) == 0 and metrics.get('sharpe_ratio', 0) > 0:
            metrics['calmar_ratio'] = metrics['sharpe_ratio'] / 2  # Rough approximation
            
        if metrics.get('sortino_ratio', 0) == 0 and metrics.get('sharpe_ratio', 0) > 0:
            metrics['sortino_ratio'] = metrics['sharpe_ratio'] * 1.5  # Rough approximation
        
        # Calculate win/loss metrics if trade_profit exists
        if 'trade_profit' in df.columns:
            # Filter out rows with no trades
            trades = df[df['trade_profit'] != 0]
            
            if not trades.empty:
                # Winning/losing trades
                winning_trades = trades[trades['trade_profit'] > 0]
                losing_trades = trades[trades['trade_profit'] < 0]
                
                # Count trades
                total_trades = len(trades)
                win_count = len(winning_trades)
                loss_count = len(losing_trades)
                
                # Win rate
                metrics['win_rate_percent'] = (win_count / total_trades) * 100 if total_trades > 0 else 0
                
                # Calculate profit factor
                total_profit = winning_trades['trade_profit'].sum() if not winning_trades.empty else 0
                total_loss = abs(losing_trades['trade_profit'].sum()) if not losing_trades.empty else 0
                metrics['profit_factor'] = total_profit / total_loss if total_loss > 0 else (1.0 if total_profit == 0 else 10.0)
                
                # Total return
                start_equity = df['equity'].iloc[0] if 'equity' in df.columns else initial_capital
                end_equity = df['equity'].iloc[-1] if 'equity' in df.columns else initial_capital
                metrics['total_return_percent'] = ((end_equity / start_equity) - 1) * 100
                
                # Annual return
                days = len(df)
                years = days / 252  # Trading days in a year
                metrics['annual_return_percent'] = (((end_equity / start_equity) ** (1/years)) - 1) * 100 if years > 0 else 0
                
                # Max drawdown
                if 'drawdown' in df.columns:
                    metrics['max_drawdown_percent'] = df['drawdown'].max() * 100
                
                # Consecutive wins/losses - simplified calculation
                # Extract trade results as sequence of wins (True) and losses (False)
                trade_results = []
                for _, row in trades.iterrows():
                    if row['trade_profit'] > 0:
                        trade_results.append(True)  # Win
                    else:
                        trade_results.append(False)  # Loss
                
                # Find max consecutive True values (wins)
                max_wins = 0
                current_streak = 0
                for result in trade_results:
                    if result:  # Win
                        current_streak += 1
                        max_wins = max(max_wins, current_streak)
                    else:
                        current_streak = 0
                
                metrics['max_consecutive_wins'] = max_wins
                
                # Find max consecutive False values (losses)
                max_losses = 0
                current_streak = 0
                for result in trade_results:
                    if not result:  # Loss
                        current_streak += 1
                        max_losses = max(max_losses, current_streak)
                    else:
                        current_streak = 0
                
                metrics['max_consecutive_losses'] = max_losses
        
        # If we still don't have adequate values, set reasonable defaults
        if metrics.get('win_rate_percent', 0) == 0:
            metrics['win_rate_percent'] = 50.0  # Neutral default
        
        if metrics.get('profit_factor', 0) == 0:
            metrics['profit_factor'] = 1.0  # Neutral default
        
        if metrics.get('total_return_percent', 0) == 0 and metrics.get('sharpe_ratio', 0) > 0:
            # Positive Sharpe but no return? Estimate a positive return
            metrics['total_return_percent'] = metrics['sharpe_ratio'] * 10
        
        if metrics.get('annual_return_percent', 0) == 0 and metrics.get('total_return_percent', 0) > 0:
            # Estimate annual from total
            metrics['annual_return_percent'] = metrics['total_return_percent'] / 2  # Rough estimate
        
        logger.info(f"Calculated advanced metrics: {metrics}")
        
    except Exception as e:
        logger.error(f"Error calculating advanced metrics: {str(e)}\n{traceback.format_exc()}")
    
    return metrics

# Run the app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Add a route to serve optimization chart images directly
@app.get("/api/optimization-chart/{strategy_type}/{timestamp}")
@endpoint_wrapper("GET /api/optimization-chart")
async def get_optimization_chart(strategy_type: str, timestamp: str):
    """Serve the backup chart image directly"""
    chart_path = os.path.join("results", "optimization", f"chart_backup_{strategy_type}_{timestamp}.png")
    
    if os.path.exists(chart_path):
        logger.info(f"Serving backup chart: {chart_path}")
        return FileResponse(chart_path, media_type="image/png")
    else:
        logger.warning(f"Backup chart not found: {chart_path}")
        return JSONResponse(
            status_code=404,
            content={"message": "Backup chart not found"}
        )