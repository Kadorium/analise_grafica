import os
from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse, FileResponse
import logging
from datetime import datetime
import traceback
from typing import Dict, Any

from optimization.models import OptimizationConfig
from optimization.status import get_optimization_status, set_optimization_status, log_optimization_request
from optimization.file_manager import ensure_optimization_directory, load_optimization_results, get_latest_optimization_file
from optimization.task import run_optimization_task
from optimization.visualization import get_optimization_chart_path

logger = logging.getLogger(__name__)

# Create a router for optimization endpoints
router = APIRouter(
    prefix="/api",
    tags=["optimization"],
)

@router.post("/optimize-strategy")
async def optimize_strategy_endpoint(optimization_config: OptimizationConfig, background_tasks: BackgroundTasks, request: Request, processed_data=None, current_config=None):
    """
    API endpoint to start a strategy optimization
    
    Args:
        optimization_config (OptimizationConfig): The optimization configuration
        background_tasks (BackgroundTasks): FastAPI background tasks
        request (Request): FastAPI request object
        processed_data (pd.DataFrame, optional): The processed data
        current_config (dict, optional): The current application configuration
        
    Returns:
        JSONResponse: Response with optimization status
    """
    # Log the incoming optimization request (initial log, can be brief)
    # The comprehensive log will be written at the end of the task.
    # log_optimization_request(optimization_config.dict()) # This can be removed if we only want one comprehensive log at the end.
    logger.info(f"[ENDPOINT] Received optimization config: {optimization_config.dict()}")

    if processed_data is None:
        # Log this specific failure scenario if desired
        # log_optimization_request(optimization_config.dict(), error="No processed data.") 
        return JSONResponse(status_code=400, content={"success": False, "message": "No processed data."})
    
    # Store the initial API request for comprehensive logging at the end of the task
    initial_api_request_details = optimization_config.dict()

    # Update optimization status
    set_optimization_status({
        "in_progress": True,
        "strategy_type": optimization_config.strategy_type,
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "latest_result_file": None,
        "current_optimization_api_request": initial_api_request_details # Store for later logging
    })

    # Add the optimization task to background tasks
    background_tasks.add_task(
        run_optimization_task,
        data=processed_data,
        optimization_config=optimization_config.dict(),
        current_config=current_config
    )
    
    # Return a response that matches what the frontend expects
    return JSONResponse(content={
        "success": True,
        "message": f"Optimization for {optimization_config.strategy_type} is running in the background.",
        "job_id": optimization_config.strategy_type,  # Use strategy_type as a job_id for tracking
        "status": "in_progress"
    })

@router.get("/optimization-status")
async def get_optimization_status_endpoint():
    """
    API endpoint to get the current optimization status
    
    Returns:
        dict: The current optimization status
    """
    status = get_optimization_status()
    # Adapt the response format to match what the frontend expects
    return {
        "in_progress": status.get("in_progress", False),
        "status": "in_progress" if status.get("in_progress", False) else "completed",
        "strategy_type": status.get("strategy_type"),
        "start_time": status.get("start_time"),
        "progress": 0.5 if status.get("in_progress", False) else 1.0  # Provide a progress value
    }

@router.get("/optimization-results/{strategy_type}")
async def get_optimization_results_endpoint(strategy_type: str, request: Request):
    """
    API endpoint to get optimization results for a strategy
    
    Args:
        strategy_type (str): The strategy type
        request (Request): FastAPI request object
        
    Returns:
        JSONResponse: Response with optimization results
    """
    try:
        optimization_status = get_optimization_status()
        
        # If optimization is in progress, return status
        if optimization_status["in_progress"] and optimization_status["strategy_type"] == strategy_type:
            return {"status": "in_progress", "message": f"Optimization for {strategy_type} is still in progress"}

        # Load the results
        results = load_optimization_results(strategy_type)
        
        if results:
            # Log the size of chart_html (if it exists) to help with debugging
            if 'chart_html' in results:
                logger.info(f"chart_html size: {len(results['chart_html']) if results['chart_html'] else 0} characters")
            
            # Log the size of indicators_chart_html (if it exists)
            if 'indicators_chart_html' in results:
                logger.info(f"indicators_chart_html size: {len(results['indicators_chart_html']) if results['indicators_chart_html'] else 0} characters")
            
            # Return results as JSON
            return {"status": "success", "results": results}
        else:
            return {"status": "not_found", "message": f"No optimization results found for {strategy_type}"}
    except Exception as e:
        logger.error(f"Error getting optimization results: {str(e)}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

def _sanitize_json_values(obj):
    """
    Recursively sanitize all values in a dictionary to ensure JSON compatibility.
    """
    import math
    import numpy as np
    
    if isinstance(obj, dict):
        return {k: _sanitize_json_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_json_values(v) for v in obj]
    elif isinstance(obj, (float, np.float32, np.float64)):
        if math.isnan(float(obj)):
            return 0
        elif math.isinf(float(obj)):
            if float(obj) > 0:
                return 1.0e+308
            else:
                return -1.0e+308
        else:
            return float(obj)
    elif isinstance(obj, (int, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return _sanitize_json_values(obj.tolist())
    else:
        return obj

@router.get("/check-optimization-directory")
async def check_optimization_directory_endpoint():
    """
    API endpoint to check if the optimization directory exists and is writable
    
    Returns:
        dict: Status of the optimization directory
    """
    success, message, directory = ensure_optimization_directory()
    return {
        "success": success,
        "message": message,
        "directory": directory
    }

@router.get("/optimization-chart/{strategy_type}/{timestamp}")
async def get_optimization_chart_endpoint(strategy_type: str, timestamp: str):
    """
    API endpoint to serve an optimization chart image
    
    Args:
        strategy_type (str): The strategy type
        timestamp (str): The chart timestamp
        
    Returns:
        FileResponse: The chart image
    """
    chart_path = get_optimization_chart_path(strategy_type, timestamp)
    
    if os.path.exists(chart_path):
        logger.info(f"Serving backup chart: {chart_path}")
        return FileResponse(chart_path, media_type="image/png")
    else:
        logger.warning(f"Backup chart not found: {chart_path}")
        return JSONResponse(
            status_code=404,
            content={"message": "Backup chart not found"}
        ) 