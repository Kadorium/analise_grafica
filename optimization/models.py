from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class OptimizationConfig(BaseModel):
    """Configuration for strategy optimization"""
    strategy_type: str
    param_ranges: Dict[str, List[Any]]
    metric: str = "sharpe_ratio"
    start_date: Optional[str] = None
    end_date: Optional[str] = None 