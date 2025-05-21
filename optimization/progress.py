import threading
import time
from datetime import datetime

# Global progress tracking
OPTIMIZATION_PROGRESS = {
    "in_progress": False,
    "strategy_type": None,
    "start_time": None,
    "current_step": 0,
    "total_steps": 0,
    "current_params": None,
    "best_params": None,
    "best_score": None,
    "completed_evaluations": 0,
    "interim_results": []
}

# Lock for thread-safe updates
progress_lock = threading.Lock()

def get_optimization_progress():
    """
    Get the current optimization progress.
    
    Returns:
        dict: The current optimization progress
    """
    with progress_lock:
        progress_data = OPTIMIZATION_PROGRESS.copy()
        
        # Calculate elapsed time if in progress
        if progress_data["in_progress"] and progress_data["start_time"]:
            elapsed = time.time() - progress_data["start_time"]
            progress_data["elapsed_seconds"] = elapsed
            
            # Calculate estimated time remaining if we have enough data
            if (progress_data["total_steps"] > 0 and 
                progress_data["completed_evaluations"] > 0):
                
                time_per_evaluation = elapsed / progress_data["completed_evaluations"]
                remaining_evaluations = progress_data["total_steps"] - progress_data["completed_evaluations"]
                estimated_remaining = time_per_evaluation * remaining_evaluations
                
                progress_data["estimated_remaining_seconds"] = estimated_remaining
        
        # Calculate percentage
        if progress_data["total_steps"] > 0:
            progress_data["percentage"] = (progress_data["completed_evaluations"] / progress_data["total_steps"]) * 100
        else:
            progress_data["percentage"] = 0
            
        return progress_data

def set_optimization_progress(update):
    """
    Update the optimization progress.
    
    Args:
        update (dict): The progress update to apply
    """
    with progress_lock:
        OPTIMIZATION_PROGRESS.update(update)
        
        # If we're starting a new optimization, reset the interim results
        if "in_progress" in update and update["in_progress"]:
            OPTIMIZATION_PROGRESS["start_time"] = time.time()
            OPTIMIZATION_PROGRESS["completed_evaluations"] = 0
            OPTIMIZATION_PROGRESS["interim_results"] = []
            
def add_interim_result(params, score, metrics):
    """
    Add an interim result from parameter evaluation.
    
    Args:
        params (dict): The parameters that were evaluated
        score (float): The score for the evaluation
        metrics (dict): The performance metrics for this evaluation
    """
    with progress_lock:
        OPTIMIZATION_PROGRESS["completed_evaluations"] += 1
        
        # Keep only the top 5 results in the interim results list
        result = {
            "params": params,
            "score": score,
            "metrics": {k: metrics[k] for k in ["total_return", "sharpe_ratio", "max_drawdown"] 
                        if k in metrics},
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add to interim results and sort by score (descending)
        OPTIMIZATION_PROGRESS["interim_results"].append(result)
        
        # Sort and keep only top 5
        OPTIMIZATION_PROGRESS["interim_results"].sort(key=lambda x: x["score"], reverse=True)
        OPTIMIZATION_PROGRESS["interim_results"] = OPTIMIZATION_PROGRESS["interim_results"][:5]
        
        # Update best params if this is the best score so far
        if (OPTIMIZATION_PROGRESS["best_score"] is None or 
            score > OPTIMIZATION_PROGRESS["best_score"]):
            OPTIMIZATION_PROGRESS["best_params"] = params
            OPTIMIZATION_PROGRESS["best_score"] = score

def reset_optimization_progress():
    """Reset the optimization progress to its default state"""
    with progress_lock:
        OPTIMIZATION_PROGRESS.update({
            "in_progress": False,
            "strategy_type": None,
            "start_time": None,
            "current_step": 0,
            "total_steps": 0,
            "current_params": None,
            "best_params": None,
            "best_score": None,
            "completed_evaluations": 0,
            "interim_results": []
        }) 