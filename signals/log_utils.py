import os
import logging

def setup_file_logger(log_file_path: str) -> logging.Logger:
    """
    Set up a dedicated file logger for signal generation and weight calculation.
    
    Args:
        log_file_path: Path to the log file
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    
    # Configure file handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Create logger
    file_logger = logging.getLogger("signal_screening")
    file_logger.setLevel(logging.INFO)
    
    # Remove existing handlers if any
    if file_logger.handlers:
        file_logger.handlers.clear()
    
    file_logger.addHandler(file_handler)
    file_logger.propagate = False  # Don't propagate to root logger
    
    return file_logger 