"""
Multi-Asset Signal Screener module for the AI-Powered Trading Analysis System.
"""

import os

# Ensure necessary directories exist
os.makedirs(os.path.join('results', 'signals'), exist_ok=True)
os.makedirs(os.path.join('results', 'logs'), exist_ok=True)

# Export main components
from .signal_generator import (
    generate_signals_for_assets,
    load_cached_signals,
    get_latest_signals_file,
    get_optimized_parameters
)

# Import components after resolving circular dependencies
from .log_utils import setup_file_logger

# Functions to be exposed by the package
__all__ = [
    'generate_signals_for_assets',
    'load_cached_signals',
    'get_latest_signals_file',
    'get_optimized_parameters',
    'setup_file_logger',
] 