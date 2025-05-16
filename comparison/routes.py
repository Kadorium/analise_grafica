from fastapi import Request, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from .controller import run_comparison_controller, load_recent_comparisons

logger = logging.getLogger("trading-app.comparison.routes")

class StrategyConfigModel(BaseModel):
    strategy_id: str
    parameters: Dict[str, Any]
    param_ranges: Optional[Dict[str, List[Any]]] = None
    
class ComparisonRequestModel(BaseModel):
    strategy_configs: List[StrategyConfigModel]
    backtest_config: Optional[Dict[str, Any]] = None
    optimize: bool = False
    optimization_metric: str = 'sharpe_ratio'

async def compare_strategies_endpoint(
    request_model: ComparisonRequestModel, 
    request: Request,
    processed_data=None,
    current_config=None
):
    """
    FastAPI endpoint for comparing multiple trading strategies.
    
    Args:
        request_model (ComparisonRequestModel): The request model containing strategy configurations
        request (Request): The FastAPI request object
        processed_data: The processed price data (injected by app.py)
        current_config: The current application configuration (injected by app.py)
        
    Returns:
        dict: Comparison results
    """
    logger.info(f"Strategy comparison request received with {len(request_model.strategy_configs)} strategies.")
    logger.info(f"Optimization requested: {request_model.optimize}")
    
    # Convert strategy configs from Pydantic models to dictionaries
    strategy_configs = [config.dict() for config in request_model.strategy_configs]
    
    # Run the comparison
    result = await run_comparison_controller(
        processed_data=processed_data,
        strategy_configs=strategy_configs,
        backtest_config=request_model.backtest_config,
        optimize=request_model.optimize,
        optimization_metric=request_model.optimization_metric
    )
    
    if not result.get('success', False):
        return JSONResponse(
            status_code=500,
            content=result
        )
    
    return result

async def get_recent_comparisons_endpoint(request: Request):
    """
    FastAPI endpoint for retrieving recent comparison results.
    
    Args:
        request (Request): The FastAPI request object
        
    Returns:
        dict: Recent comparison results
    """
    logger.info("Request for recent comparison results received.")
    
    recent_comparisons = load_recent_comparisons()
    
    return {
        "success": True,
        "message": f"Retrieved {len(recent_comparisons)} recent comparisons.",
        "comparisons": recent_comparisons
    } 