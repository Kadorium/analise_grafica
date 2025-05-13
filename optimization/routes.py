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
    # Log the incoming optimization request
    log_optimization_request(optimization_config.dict())
    logger.info(f"[ENDPOINT] Received optimization config: {optimization_config.dict()}")

    if processed_data is None:
        log_optimization_request(optimization_config.dict(), error="No processed data.")
        return JSONResponse(status_code=400, content={"success": False, "message": "No processed data."})
    
    # Update optimization status
    set_optimization_status({
        "in_progress": True,
        "strategy_type": optimization_config.strategy_type,
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "latest_result_file": None
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
        results, timestamp, error = load_optimization_results(strategy_type)
        if error:
            logger.warning(f"Error loading optimization results: {error}")
            return {"status": "not_found", "message": error}
        
        # Check if comparison data is present in the loaded results
        has_comparison = ('default_params' in results and 
                        'optimized_params' in results and
                        'default_performance' in results and
                        'optimized_performance' in results)
        
        # If no comparison data in the file but we have it in memory, add it to the results
        if not has_comparison and optimization_status.get('comparison_data'):
            logger.info(f"Adding comparison data from memory to results: {strategy_type}")
            results.update(optimization_status.get('comparison_data', {}))
        
        # Ensure key fields expected by the frontend are present
        if 'top_results' not in results:
            results['top_results'] = []
            # If we have optimized_params, add them as the best result
            if 'optimized_params' in results and 'optimized_performance' in results:
                results['top_results'].append({
                    'params': results['optimized_params'],
                    'metrics': results['optimized_performance']
                })
        
        # Rename fields to match frontend expectations if needed
        if 'total_return_percent' in results.get('default_performance', {}) and 'total_return' not in results['default_performance']:
            results['default_performance']['total_return'] = results['default_performance']['total_return_percent'] / 100
        if 'total_return_percent' in results.get('optimized_performance', {}) and 'total_return' not in results['optimized_performance']:
            results['optimized_performance']['total_return'] = results['optimized_performance']['total_return_percent'] / 100
        
        # Sanitize all float values to ensure JSON compatibility
        sanitized_results = _sanitize_json_values(results)
        
        return JSONResponse(content={
            "status": "success",
            "results": sanitized_results,
            "timestamp": timestamp
        })
    except Exception as e:
        logger.error(f"Error processing optimization results: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Internal server error: {str(e)}"}
        )

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