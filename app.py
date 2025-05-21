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
import time
import logging
import sys
import platform
import psutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import functools
import traceback as tb

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
            
            current_endpoint_name = endpoint_name_fallback
            if request_obj:
                current_endpoint_name = f"{request_obj.method} {request_obj.url.path}"

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
    Coerces any unexpected values to 'hold'.
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

    # Use the shared normalization utility for signals
    signals_df = normalize_signals_column(signals_df)

    logger.info(f"Signal normalization complete. Signal counts: {signals_df['signal'].value_counts().to_dict() if 'signal' in signals_df else 'N/A'}")
    return signals_df

# Import our modules
from data.data_loader import DataLoader
from indicators.indicator_utils import combine_indicators, plot_price_with_indicators, create_indicator_summary, normalize_signals_column
from strategies import create_strategy, get_default_parameters, AVAILABLE_STRATEGIES, STRATEGY_REGISTRY
from backtesting.backtester import Backtester
from optimization import (
    optimization_router,
    OptimizationConfig,
    calculate_advanced_metrics
)
from optimization.status import (
    get_optimization_status, 
    set_optimization_status, 
    log_optimization_request,
    OPTIMIZATION_STATUS
)
from indicators.seasonality import day_of_week_returns, monthly_returns, day_of_week_volatility, calendar_heatmap, seasonality_summary
import config as cfg

# Import the comparison module
from comparison.routes import compare_strategies_endpoint, get_recent_comparisons_endpoint, ComparisonRequestModel

# Global variables for other modules
UPLOADED_DATA = None
PROCESSED_DATA = None
MULTI_ASSET_DATA = {}  # New global to store multi-asset data
BACKTESTER = None
CURRENT_CONFIG = cfg.get_all_config()

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

# Modified router include with dependencies
# This ensures the optimization endpoints have access to the global PROCESSED_DATA
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

# Include the other optimization endpoints directly
@app.get("/api/optimization-status")
@endpoint_wrapper("GET /api/optimization-status")
async def optimization_status_endpoint():
    """Forward to the modularized endpoint"""
    from optimization.routes import get_optimization_status_endpoint
    return await get_optimization_status_endpoint()

@app.get("/api/optimization-results/{strategy_type}")
@endpoint_wrapper("GET /api/optimization-results")
async def get_optimization_results(strategy_type: str, request: Request):
    """Forward to the modularized endpoint"""
    from optimization.routes import get_optimization_results_endpoint
    return await get_optimization_results_endpoint(strategy_type, request)

@app.get("/api/check-optimization-directory")
@endpoint_wrapper("GET /api/check-optimization-directory")
async def check_optimization_directory():
    """Forward to the modularized endpoint"""
    from optimization.routes import check_optimization_directory_endpoint
    return await check_optimization_directory_endpoint()

@app.get("/api/optimization-chart/{strategy_type}/{timestamp}")
@endpoint_wrapper("GET /api/optimization-chart")
async def get_optimization_chart(strategy_type: str, timestamp: str):
    """Forward to the modularized endpoint"""
    from optimization.routes import get_optimization_chart_endpoint
    return await get_optimization_chart_endpoint(strategy_type, timestamp)

# Add the optimization progress endpoint
@app.get("/api/optimization-progress")
@endpoint_wrapper("GET /api/optimization-progress")
async def get_optimization_progress(request: Request):
    """Get the current progress of optimization tasks"""
    from optimization.routes import get_optimization_progress_endpoint
    return await get_optimization_progress_endpoint()

# Add global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = str(exc)
    stack_trace = traceback.format_exc()
    
    # Log the error with detailed information
    separator = "#" * 80
    error_log = f"""
{separator}
GLOBAL EXCEPTION HANDLER
TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
REQUEST: {request.method} {request.url}
CLIENT: {request.client.host if request.client else 'Unknown'}
ERROR: {error_detail}
STACK TRACE:
{stack_trace}
{separator}
"""
    logger.error(error_log)
    
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": f"Internal server error: {error_detail}"},
    )

# Add validation exception handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_detail = str(exc)
    
    # Log the validation error with detailed information
    separator = "#" * 80
    error_log = f"""
{separator}
VALIDATION EXCEPTION HANDLER
TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
REQUEST: {request.method} {request.url}
CLIENT: {request.client.host if request.client else 'Unknown'}
ERROR: {error_detail}
VALIDATION ERRORS: {exc.errors()}
{separator}
"""
    logger.error(error_log)
    
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
    initial_capital: float = 100.0
    commission: float = 0.001
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class PlotConfig(BaseModel):
    main_indicators: List[str] = []
    subplot_indicators: List[str] = []
    title: str = "Price Chart with Indicators"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

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
    global UPLOADED_DATA, PROCESSED_DATA
    
    log_endpoint("POST /api/process-data - START_DETAILS", 
                uploaded_data_shape=UPLOADED_DATA.shape if UPLOADED_DATA is not None else "None")
    
    if UPLOADED_DATA is None:
        return JSONResponse(
            status_code=400, # Keep specific status codes for client-side logic
            content={"success": False, "message": "No data uploaded. Please upload a CSV file first."}
        )
    
    # This try-except is for the recovery logic, separate from the main endpoint wrapper
    try:
        data_loader = DataLoader()
        data_loader.data = UPLOADED_DATA.copy()
        cleaned_data = data_loader.clean_data()
        
        if len(cleaned_data) == 0:
            logger.warning("Empty dataset after cleaning. Attempting recovery with European date format...")
            data_copy = UPLOADED_DATA.copy()
            def parse_date(date_str): # Inner function for specific parsing
                if not isinstance(date_str, str): return None
                date_str = date_str.strip()
                formats = ['%d/%m/%y', '%d/%m/%Y', '%m/%d/%y', '%m/%d/%Y', '%Y-%m-%d']
                for fmt in formats:
                    try: return pd.to_datetime(date_str, format=fmt)
                    except: continue
                try: return pd.to_datetime(date_str, errors='coerce')
                except: return None
            
            data_copy['date'] = data_copy['date'].apply(parse_date)
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in data_copy.columns:
                    if data_copy[col].dtype == object:
                        data_copy[col] = data_copy[col].astype(str).str.replace(',', '.')
                    data_copy[col] = pd.to_numeric(data_copy[col], errors='coerce')
            data_copy = data_copy.dropna(subset=['date', 'open', 'high', 'low', 'close', 'volume'])
            
            if len(data_copy) > 0:
                cleaned_data = data_copy
                logger.info(f"Recovery successful! Recovered {len(cleaned_data)} rows of data.")
            else:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": "Could not process data. All rows were invalid after cleaning."}
                )
        
        PROCESSED_DATA = cleaned_data
        sample_data_for_preview = stringify_df_dates(PROCESSED_DATA.head())
        
        date_range = {}
        if 'date' in PROCESSED_DATA.columns and pd.api.types.is_datetime64_any_dtype(PROCESSED_DATA['date']):
            date_min = PROCESSED_DATA['date'].min()
            date_max = PROCESSED_DATA['date'].max()
            date_range["start"] = date_min.strftime('%Y-%m-%d') if pd.notna(date_min) else "N/A"
            date_range["end"] = date_max.strftime('%Y-%m-%d') if pd.notna(date_max) else "N/A"
        else: # Ensure date_range is always structured
             date_range = {"start": "N/A", "end": "N/A"}


        log_endpoint("POST /api/process-data - DATA_SUMMARY", 
                    data_shape=PROCESSED_DATA.shape,
                    date_range=date_range)
        
        return {
            "message": "Data processed successfully",
            "data_shape": PROCESSED_DATA.shape,
            "date_range": date_range,
            "data_sample": sample_data_for_preview.to_dict('records')
        }
    except Exception as e_recovery: # Catch specific recovery errors
        logger.error(f"Error during data processing/recovery: {str(e_recovery)}\n{traceback.format_exc()}")
        # This error will be caught by the endpoint_wrapper if re-raised,
        # or return a specific JSONResponse here.
        # For consistency, let the wrapper handle it by re-raising or returning a specific known error.
        # However, if we return a JSONResponse here, the wrapper's error handling won't run.
        # It's better to raise a specific error or let the original exception propagate to the wrapper.
        # For now, let the wrapper catch it.
        raise e_recovery


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
    required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
    
    missing_cols = check_required_columns(PROCESSED_DATA, required_cols)
    if missing_cols:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"Missing required columns in data: {', '.join(missing_cols)}"}
        )
            
    base_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
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
async def plot_indicators(plot_config: PlotConfig, request: Request = None):
    """
    Plot price and selected indicators, returning a base64 image for the frontend. 
    No chart is saved to disk unless debug mode is enabled.
    """
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
    # Only save debug chart if DEBUG_SAVE_CHART env var is set
    debug_save_path = None
    if os.environ.get("DEBUG_SAVE_CHART", "0") == "1":
        debug_save_path = os.path.join(os.getcwd(), "test_chart.png")
    image_base64 = plot_price_with_indicators(PROCESSED_DATA, plot_dict, debug_save_path=debug_save_path)
    
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
    return {"strategies": AVAILABLE_STRATEGIES}

@app.get("/api/strategy-parameters/{strategy_type}")
@endpoint_wrapper("GET /api/strategy-parameters")
async def get_strategy_parameters(strategy_type: str, request: Request):
    default_params = get_default_parameters(strategy_type)
    return {"parameters": default_params}

@app.post("/api/run-backtest")
@endpoint_wrapper("POST /api/run-backtest")
async def run_backtest(strategy_config: StrategyConfig, backtest_config: BacktestConfig, request: Request):
    global PROCESSED_DATA, BACKTESTER
    
    log_endpoint(f"{request.method} {request.url.path} - DETAILS", 
                 strategy_type=strategy_config.strategy_type, 
                 params=strategy_config.parameters,
                 backtest_config_params=backtest_config.dict())
    
    if PROCESSED_DATA is None:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "No processed data available."}
        )
    
    data = PROCESSED_DATA.copy()
    filtered_data = data.copy()
    if backtest_config.start_date:
        filtered_data = filtered_data[filtered_data['date'] >= pd.to_datetime(backtest_config.start_date)]
    if backtest_config.end_date:
        filtered_data = filtered_data[filtered_data['date'] <= pd.to_datetime(backtest_config.end_date)]
    
    strategy = create_strategy(strategy_config.strategy_type, **strategy_config.parameters)
    
    # Support both class-based and function-based (StrategyAdapter) strategies
    if hasattr(strategy, 'generate_signals'):
        signals_df = strategy.generate_signals(filtered_data)
    elif hasattr(strategy, 'backtest'):
        # For function-based strategies, backtest returns the full DataFrame with signals
        signals_df = strategy.backtest(filtered_data, initial_capital=backtest_config.initial_capital, commission=backtest_config.commission)
    elif callable(strategy):
        # Fallback: direct function call (should not be needed with current registry)
        signals_df = strategy(filtered_data, **strategy_config.parameters)
    else:
        raise ValueError(f"Strategy object does not support signal generation or backtesting: {type(strategy)}")
    
    required_cols_signals = ['date', 'close']
    missing_cols = check_required_columns(signals_df, required_cols_signals)
    if missing_cols:
        raise ValueError(f"Missing required columns in signals_df from strategy: {missing_cols}")

    signals_df = normalize_signals_df(signals_df)

    # Generate more test signals if counts are low (this logic is specific)
    if 'signal' in signals_df.columns:
        buy_count = (signals_df['signal'] == 'buy').sum()
        sell_count = (signals_df['signal'] == 'sell').sum()
        if buy_count < 3 or sell_count < 3:
            logger.warning(f"Few signals found (Buy: {buy_count}, Sell: {sell_count}), attempting to add more test signals based on MA crossover.")
            if 'close' in signals_df.columns:
                if 'sma_20' not in signals_df.columns:
                    signals_df['sma_20'] = signals_df['close'].rolling(window=20, min_periods=1).mean()
                if 'sma_50' not in signals_df.columns:
                    signals_df['sma_50'] = signals_df['close'].rolling(window=50, min_periods=1).mean()
                
                # Ensure no NaNs at the start of MAs if window is large
                signals_df.dropna(subset=['sma_20', 'sma_50'], inplace=True)
                if not signals_df.empty : # Check if df is not empty after dropna
                    # Generate crossover signals only where we have data
                    buy_condition = (signals_df['sma_20'] > signals_df['sma_50']) & (signals_df['sma_20'].shift(1) <= signals_df['sma_50'].shift(1))
                    sell_condition = (signals_df['sma_20'] < signals_df['sma_50']) & (signals_df['sma_20'].shift(1) >= signals_df['sma_50'].shift(1))
                    
                    # Apply signals where conditions are met and current signal is 'hold'
                    signals_df.loc[buy_condition & (signals_df['signal'] == 'hold'), 'signal'] = 'buy'
                    signals_df.loc[sell_condition & (signals_df['signal'] == 'hold'), 'signal'] = 'sell'
                    logger.info(f"Added MA crossover test signals. New counts: Buy: {(signals_df['signal'] == 'buy').sum()}, Sell: {(signals_df['signal'] == 'sell').sum()}")

    results_metrics = calculate_performance_metrics(signals_df, 
                                           initial_capital=backtest_config.initial_capital, 
                                           commission=backtest_config.commission)
    
    # Ensure equity is added to signals_df for plotting (calculate_performance_metrics should return it)
    # This part seems redundant if calculate_performance_metrics already adds/returns equity correctly with signals_df
    # For now, assuming calculate_performance_metrics returns a modified signals_df or the equity series directly.
    # Let's assume calculate_performance_metrics returns a tuple (metrics_dict, signals_df_with_equity)
    
    # Rework based on calculate_performance_metrics potentially modifying signals_df or returning it
    # For now, assume metrics is a dict and signals_df might be modified in place or we use the one we have.
    # The original code implicitly assumed calculate_performance_metrics might not add 'equity' to the original signals_df.
    # Let's ensure 'equity' and 'cumulative_market_return' are in signals_df for plot_backtest_results.
    
    if 'equity' not in signals_df.columns and 'final_capital_series' in results_metrics: # Check if metrics returned it
        signals_df['equity'] = results_metrics['final_capital_series'] # Hypothetical key
    elif 'equity' not in signals_df.columns: # Fallback if not in metrics or signals_df
        logger.warning("'equity' column not found in signals_df after performance calculation. Re-calculating for plot.")
        # Simplified equity calculation for plotting if missing
        temp_equity = [backtest_config.initial_capital]
        current_pos = 0
        entry_p = 0
        for i in range(len(signals_df)):
            price = signals_df['close'].iloc[i]
            signal = signals_df['signal'].iloc[i]
            if signal == 'buy' and current_pos == 0:
                current_pos = 1
                entry_p = price
                temp_equity.append(temp_equity[-1]) # No change on buy day itself
            elif signal == 'sell' and current_pos == 1:
                current_pos = 0
                profit = (price - entry_p) # Simplified, no commission for this fallback plot equity
                temp_equity.append(temp_equity[-1] + profit)
            else:
                # If holding, equity changes by price change relative to entry if we had a 'shares' concept
                # For simplicity, if holding, equity stays or follows market if PnL is tracked daily
                temp_equity.append(temp_equity[-1]) # Simplification
        signals_df['equity'] = temp_equity[1:] if len(temp_equity) > len(signals_df) else temp_equity # Align length

    if 'cumulative_market_return' not in signals_df.columns:
        signals_df['market_return_pct'] = signals_df['close'].pct_change().fillna(0)
        signals_df['cumulative_market_return'] = (1 + signals_df['market_return_pct']).cumprod()

    # Ensure BACKTESTER is initialized
    if BACKTESTER is None:
        BACKTESTER = Backtester()
    # Use the new plot_price_with_trade_signals for the first chart
    chart_image_b64 = BACKTESTER.plot_price_with_trade_signals(
        signals_df,
        strategy_name=strategy_config.strategy_type.replace("_", " ").title(),
        initial_capital=backtest_config.initial_capital
    )
    
    def clean_for_json(data_item):
        if isinstance(data_item, dict):
            return {k: clean_for_json(v) for k, v in data_item.items()}
        elif isinstance(data_item, list):
            return [clean_for_json(item) for item in data_item]
        elif isinstance(data_item, float):
            if np.isnan(data_item) or np.isinf(data_item): return None
            return data_item
        elif isinstance(data_item, (np.int64, np.int32, np.int16, np.int8)): return int(data_item)
        elif isinstance(data_item, (np.float64, np.float32)):
            if np.isnan(data_item) or np.isinf(data_item): return None
            return float(data_item)
        elif isinstance(data_item, pd.Timestamp): return data_item.strftime('%Y-%m-%d %H:%M:%S')
        return data_item

    # Prepare chart data for frontend charting
    chart_data = {
        "equity_curve": {
            "dates": signals_df['date'].dt.strftime('%Y-%m-%d').tolist() if pd.api.types.is_datetime64_any_dtype(signals_df['date']) else signals_df['date'].astype(str).tolist(),
            "equity": signals_df['equity'].tolist() if 'equity' in signals_df else [],
            "buy_and_hold": (signals_df['cumulative_market_return'] * backtest_config.initial_capital).tolist() if 'cumulative_market_return' in signals_df else []
        },
        "price_signals": {
            "dates": signals_df['date'].dt.strftime('%Y-%m-%d').tolist() if pd.api.types.is_datetime64_any_dtype(signals_df['date']) else signals_df['date'].astype(str).tolist(),
            "close": signals_df['close'].tolist() if 'close' in signals_df else [],
            "buy_signals": [i for i, s in enumerate(signals_df['signal']) if s == 'buy'],
            "sell_signals": [i for i, s in enumerate(signals_df['signal']) if s == 'sell'],
            "exit_signals": [i for i in range(1, len(signals_df)) if signals_df['position'].iloc[i-1] == 1 and signals_df['position'].iloc[i] == 0]
        },
        "indicators": {}
    }
    # Add available indicators (e.g., rsi, sma_50, ema_20, etc.)
    indicator_cols = [col for col in signals_df.columns if col not in ['date', 'open', 'high', 'low', 'close', 'volume', 'signal', 'position', 'equity', 'cumulative_market_return', 'market_return_pct']]
    for col in indicator_cols:
        chart_data["indicators"][col] = signals_df[col].tolist()

    result_data = clean_for_json({
        "metrics": results_metrics,
        "charts_data": chart_data,
        "trades": extract_trades(signals_df, 
                                commission=backtest_config.commission,
                                initial_capital=backtest_config.initial_capital)
    })
    
    # Save the current config
    CURRENT_CONFIG['strategy'] = {'type': strategy_config.strategy_type, 'parameters': strategy_config.parameters}
    
    # If the strategy is using auto-optimization (like seasonality), get the actual optimized parameters
    if hasattr(strategy, 'get_parameters'):
        # For strategy adapters, we can get the parameters which may have been updated
        # during the auto-optimization process
        print("=================================================================")
        print(f"DEBUG: Strategy {strategy_config.strategy_type} has get_parameters method")
        actual_parameters = strategy.get_parameters()
        print(f"DEBUG: Retrieved parameters: {list(actual_parameters.keys())}")
        
        # Update the result data with the actual parameters used (especially useful for auto-optimizing strategies)
        result_data["actual_parameters"] = clean_for_json(actual_parameters)
        print(f"DEBUG: Added actual_parameters to result_data")
        
        # If the strategy has produced a summary for UI display, include it
        if 'summary' in actual_parameters:
            print(f"DEBUG: Found summary in parameters: {actual_parameters['summary']}")
            result_data["optimization_summary"] = actual_parameters['summary']
            print(f"DEBUG: Added optimization_summary to result_data")
        else:
            print(f"DEBUG: No summary found in parameters")
        
        # Also update the current config to show the actual parameters that were used
        CURRENT_CONFIG['strategy']['actual_parameters'] = actual_parameters
        print("=================================================================")
    else:
        print(f"DEBUG: Strategy {strategy_config.strategy_type} does NOT have get_parameters method")
    
    indicator_columns = [col for col in data.columns if col not in ['date', 'open', 'high', 'low', 'close', 'volume']]
    CURRENT_CONFIG['indicators'] = indicator_columns
    
    log_endpoint(f"{request.method} {request.url.path} - RESULT_SUMMARY", strategy_metrics=results_metrics.get('total_return_percent', 'N/A'))
    return {"success": True, "results": result_data}


# calculate_performance_metrics and other helpers are assumed to be mostly unchanged for now,
# unless their error handling or logging was duplicative.
# The main change is that the top-level try-except in endpoints is removed.

# ... (calculate_performance_metrics, plot_backtest_results, extract_trades remain largely as is, ensure they don't have conflicting try-excepts for general errors)

@app.post("/api/compare-strategies")
@endpoint_wrapper("POST /api/compare-strategies")
async def compare_strategies(request_model: ComparisonRequestModel, request: Request):
    """
    Enhanced endpoint for comparing multiple trading strategies.
    Supports strategy parameter optimization.
    """
    global PROCESSED_DATA, CURRENT_CONFIG
    
    # Call the modularized endpoint with the necessary dependencies
    return await compare_strategies_endpoint(
        request_model=request_model,
        request=request,
        processed_data=PROCESSED_DATA,
        current_config=CURRENT_CONFIG
    )

@app.get("/api/recent-comparisons")
@endpoint_wrapper("GET /api/recent-comparisons")
async def recent_comparisons(request: Request):
    """
    Retrieve recent strategy comparison results.
    """
    return await get_recent_comparisons_endpoint(request)

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
                           if col not in ['date', 'open', 'high', 'low', 'close', 'volume']]
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
            "has_indicators": len([c for c in PROCESSED_DATA.columns if c not in ['date', 'open', 'high', 'low', 'close', 'volume']]) > 0
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
def calculate_performance_metrics(signals_df, initial_capital=100.0, commission=0.001):
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
    buy_signals_indices = []
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
                logger.info(f"[BACKTEST] BUY at {current_date} price: {entry_price:.2f} (raw: {current_price:.2f}) equity: {equity:.2f}")
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
                logger.info(f"[BACKTEST] SELL at {current_date} price: {exit_price:.2f} (raw: {current_price:.2f}) profit: {trade_profit:.2f} equity: {equity:.2f}")
            entry_price = 0.0
            entry_date_val = None
        df.at[df.index[i], 'equity'] = equity
    df['market_return'] = df['close'].pct_change().fillna(0)
    df['cumulative_market_return'] = (1 + df['market_return']).cumprod()
    start_date = df['date'].min()
    end_date = df['date'].max()
    days = (end_date - start_date).days
    years = max(days / 365.25, 0.01)
    final_equity = df['equity'].iloc[-1] if not df['equity'].empty else initial_capital
    total_return_calc = (final_equity / initial_capital) - 1
    annual_return_calc = ((1 + total_return_calc) ** (1 / years)) - 1 if years > 0 else 0
    df['drawdown'] = (df['equity'].cummax() - df['equity']) / df['equity'].cummax().replace(0, np.nan)
    max_drawdown_calc = df['drawdown'].max() if not df['drawdown'].empty else 0
    max_drawdown_calc = max_drawdown_calc if pd.notna(max_drawdown_calc) else 0
    win_rate_calc = winning_trades / total_trades if total_trades > 0 else 0
    avg_win_calc = total_profit / winning_trades if winning_trades > 0 else 0
    avg_loss_calc = abs(total_loss / losing_trades) if losing_trades > 0 else 0
    profit_factor_calc = abs(total_profit / total_loss) if total_loss != 0 else float('inf')
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
    }
    signals_df['equity'] = df['equity']
    signals_df['cumulative_market_return'] = df['cumulative_market_return']
    return metrics

def plot_backtest_results(signals_df, strategy_name='Strategy', initial_capital=100.0):
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

def extract_trades(signals_df, commission=0.001, initial_capital=100.0):
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
        current_date = df.iloc[i]['date']
        if current_signal == 'buy' and position == 0:
            position = 1
            entry_price = current_price * (1 + commission)
            entry_date_val = current_date
            logger.info(f"[TRADES] Entry: {entry_date_val} at {entry_price:.2f} (raw: {current_price:.2f})")
        elif current_signal == 'sell' and position == 1:
            position = 0
            exit_price = current_price * (1 - commission)
            exit_date_val = current_date
            if entry_price != 0:
                profit_val = exit_price - entry_price
                profit_pct_val = (profit_val / entry_price) * 100
                logger.info(f"[TRADES] Exit: {exit_date_val} at {exit_price:.2f} (raw: {current_price:.2f}) | Profit: {profit_val:.2f} | Profit %: {profit_pct_val:.2f}")
                trades.append({
                    'entry_date': entry_date_val.strftime('%Y-%m-%d') if hasattr(entry_date_val, 'strftime') else str(entry_date_val),
                    'exit_date': exit_date_val.strftime('%Y-%m-%d') if hasattr(exit_date_val, 'strftime') else str(exit_date_val),
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'profit': profit_val,
                    'profit_pct': profit_pct_val,
                    'result': 'win' if profit_val > 0 else 'loss'
                })
            entry_price = 0.0
            entry_date_val = None
    return trades

@app.post("/api/upload-multi-asset")
@endpoint_wrapper("POST /api/upload-multi-asset")
async def upload_multi_asset(file: Optional[UploadFile] = None):
    global MULTI_ASSET_DATA
    default_file_used = False
    temp_file_path = None

    try:
        if file:
            log_endpoint("POST /api/upload-multi-asset - DETAILS", file_name=file.filename, content_type=file.content_type)
            contents = await file.read()
            temp_file_path = os.path.join('data', 'temp_multi_upload.xlsx')
            os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
            with open(temp_file_path, 'wb') as f:
                f.write(contents)
            logger.info(f"Multi-asset file uploaded by user and saved temporarily to {temp_file_path}")
        else:
            default_file_path = os.path.join('data', 'test multidata.xlsx')
            if not os.path.exists(default_file_path):
                log_endpoint("POST /api/upload-multi-asset - DETAILS", error=f"Default multi-asset file not found: {default_file_path}")
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "message": f"Default multi-asset file {default_file_path} not found. Please upload a file."}
                )
            temp_file_path = default_file_path
            default_file_used = True
            log_endpoint("POST /api/upload-multi-asset - DETAILS", using_default_file=temp_file_path)
            logger.info(f"No file uploaded by user. Using default multi-asset file: {temp_file_path}")

        # Load and process the multi-sheet Excel file
        data_loader = DataLoader(temp_file_path)
        MULTI_ASSET_DATA = data_loader.load_multi_asset_excel()
        
        # Get assets list and create a preview for each
        assets = list(MULTI_ASSET_DATA.keys())
        previews = {}
        
        for asset, df in MULTI_ASSET_DATA.items():
            # Prepare sample for preview (first 5 rows)
            sample_df = df.head(5)
            if 'date' in sample_df.columns and pd.api.types.is_datetime64_any_dtype(sample_df['date']):
                sample_df = sample_df.copy()
                sample_df['date'] = sample_df['date'].dt.strftime('%Y-%m-%d')
            previews[asset] = sample_df.to_dict('records')
        
        # Get overall date range from loader
        date_range = getattr(data_loader, 'multi_asset_date_range', {
            'start': 'N/A',
            'end': 'N/A'
        })
        
        response_data = {
            "success": True,
            "message": "Multi-asset file processed successfully" if default_file_used else "Multi-asset file uploaded and processed successfully",
            "assets": assets,
            "date_range": date_range,
            "previews": previews,
            "asset_count": len(assets)
        }
        
        log_endpoint("POST /api/upload-multi-asset - DATA_SUMMARY", 
                    assets=assets,
                    asset_count=len(assets),
                    date_range=date_range)
                    
        return response_data
        
    except Exception as e:
        error_trace = traceback.format_exc()
        log_endpoint("POST /api/upload-multi-asset - ERROR", 
                     error=str(e),
                     traceback=error_trace)
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False, 
                "message": f"Error processing multi-asset file: {str(e)}"
            }
        )

# Run the app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)