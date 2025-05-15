import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def ensure_optimization_directory():
    """
    Ensures that the optimization results directory exists and is writable.
    
    Returns:
        tuple: (success, message, directory)
            success (bool): Whether the directory is ready for use
            message (str): Status message
            directory (str): Path to the optimization directory
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
        
        return True, "Optimization directory exists and is writable", results_dir
    except Exception as e:
        logger.error(f"Error checking optimization directory: {str(e)}")
        return False, f"Error with optimization directory: {str(e)}", results_dir

def save_optimization_results(strategy_type, results_data):
    """
    Save optimization results to a JSON file
    
    Args:
        strategy_type (str): The strategy type
        results_data (dict): The optimization results data
        
    Returns:
        str: The path to the saved file or None if there was an error
    """
    success, _, results_dir = ensure_optimization_directory()
    if not success:
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"optimization_{strategy_type}_{timestamp}.json"
    file_path = os.path.join(results_dir, file_name)
    
    try:
        with open(file_path, 'w') as f:
            json.dump(results_data, f, indent=4)
        logger.info(f"Saved optimization results to: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving optimization results: {str(e)}")
        return None

def get_latest_optimization_file(strategy_type):
    """
    Get the latest optimization results file for a strategy
    
    Args:
        strategy_type (str): The strategy type
        
    Returns:
        tuple: (file_path, error_message)
            file_path (str): Path to the latest file or None if not found
            error_message (str): Error message or None if successful
    """
    results_dir = os.path.join("results", "optimization")
    if not os.path.exists(results_dir):
        return None, "No optimization results directory found"
    
    try:
        files = [f for f in os.listdir(results_dir) 
                if f.startswith(f"optimization_{strategy_type}_") and f.endswith(".json")]
    except FileNotFoundError:
        return None, "Optimization results directory disappeared"
    
    if not files:
        return None, f"No optimization results found for strategy type '{strategy_type}'"
    
    latest_file = max(files, key=lambda f_name: os.path.getmtime(os.path.join(results_dir, f_name)))
    file_path = os.path.join(results_dir, latest_file)
    
    return file_path, None

def load_optimization_results(strategy_type):
    """
    Load the latest optimization results for a strategy
    
    Args:
        strategy_type (str): The strategy type
        
    Returns:
        tuple: (results, timestamp, error_message)
            results (dict): The optimization results or None if not found
            timestamp (str): Timestamp of the file or None if not found
            error_message (str): Error message or None if successful
    """
    file_path, error_message = get_latest_optimization_file(strategy_type)
    if error_message:
        return None, None, error_message
    
    try:
        with open(file_path, 'r') as f:
            results = json.load(f)
        
        # If the file doesn't have top_results, transform it to match the expected format
        if 'top_results' not in results:
            if 'all_results' in results:
                # Take the top 10 results (or fewer if less available)
                top_results = []
                for i, result in enumerate(results.get('all_results', [])[:10]):
                    top_results.append({
                        "params": result.get('params', {}),
                        "score": result.get('value', 0),
                        "metrics": result.get('performance', {})
                    })
                results['top_results'] = top_results
            else:
                # Create empty top_results if all_results is missing
                results['top_results'] = []
                
        timestamp = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
        return results, timestamp, None
    except Exception as e:
        logger.error(f"Error reading optimization results file: {str(e)}")
        return None, None, f"Error reading optimization results: {str(e)}" 