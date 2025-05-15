# Optimization Module

The Optimization module provides functionality for optimizing trading strategy parameters to achieve better performance metrics. This module has been designed to modularize the optimization functionality previously contained in the main app.py file.

## Module Structure

The optimization module is structured into the following components:

- **models.py**: Contains Pydantic models for data validation and serialization
- **status.py**: Handles optimization status tracking and logging
- **metrics.py**: Implements advanced performance metrics calculations
- **visualization.py**: Generates optimization comparison charts and visualizations
- **file_manager.py**: Manages optimization results file operations
- **task.py**: Contains the main optimization background task
- **routes.py**: Defines FastAPI endpoints for the optimization functionality
- **optimizer.py**: Core optimization algorithms (grid search, etc.)
- **__init__.py**: Exposes key functions and components from the module

## Key Features

- **Grid Search Optimization**: Find optimal strategy parameters
- **Background Processing**: Run optimizations asynchronously
- **Status Tracking**: Monitor optimization progress
- **Result Comparison**: Compare default vs. optimized strategies
- **Visualization**: Generate comparison charts
- **Performance Metrics**: Calculate comprehensive trading metrics
- **File Management**: Organize and store optimization results

## API Endpoints

The module provides the following API endpoints:

- **POST /api/optimize-strategy**: Start a strategy optimization
- **GET /api/optimization-status**: Get the current optimization status
- **GET /api/optimization-results/{strategy_type}**: Get results for a specific strategy
- **GET /api/check-optimization-directory**: Check if the optimization directory exists
- **GET /api/optimization-chart/{strategy_type}/{timestamp}**: Get an optimization chart image

## How to Use

### Start an Optimization

```python
from optimization import OptimizationConfig, run_optimization_task

# Create optimization configuration
optimization_config = OptimizationConfig(
    strategy_type="sma_crossover",
    param_ranges={
        "short_window": [5, 10, 15, 20],
        "long_window": [50, 100, 150, 200]
    },
    metric="sharpe_ratio",
    start_date="2020-01-01",
    end_date="2021-01-01"
)

# Run the optimization task
result = run_optimization_task(
    data=processed_data,
    optimization_config=optimization_config.dict(),
    current_config=app_config
)
```

### Check Optimization Status

```python
from optimization.status import get_optimization_status

# Get current status
status = get_optimization_status()
print(f"In progress: {status['in_progress']}")
print(f"Strategy type: {status['strategy_type']}")
```

### Retrieve Optimization Results

```python
from optimization.file_manager import load_optimization_results

# Load the latest optimization results for a strategy
results, timestamp, error = load_optimization_results("sma_crossover")
if error:
    print(f"Error: {error}")
else:
    print(f"Optimization results from {timestamp}")
    print(f"Default performance: {results['default_performance']}")
    print(f"Optimized performance: {results['optimized_performance']}")
```

## Integration with Main Application

There are two recommended ways to integrate this module with the main application:

### Method 1: Using the Router (Simpler, but may have issues with accessing global state)

```python
# In app.py
from optimization import optimization_router

# Add the optimization router to the FastAPI app
app.include_router(optimization_router)
```

### Method 2: Forwarding Endpoints (Recommended for accessing global variables)

If you encounter a "No processed data" error when using Method 1, this is because the router endpoints don't have access to the global `PROCESSED_DATA` variable. Instead, use this approach:

```python
# In app.py

# Do NOT include the router directly
# app.include_router(optimization_router)  # <-- Comment out or remove

# Instead, create wrapper endpoints that forward to the modularized versions
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

# Add similar wrappers for the other endpoints
@app.get("/api/optimization-status")
@endpoint_wrapper("GET /api/optimization-status")
async def optimization_status_endpoint():
    from optimization.routes import get_optimization_status_endpoint
    return await get_optimization_status_endpoint()

# And so on for other endpoints...
```

## Common Issues and Solutions

### 1. "No processed data" Error

**Problem**: When running an optimization, you get a 400 Bad Request error with the message "No processed data".

**Solution**: 
1. Check that you've successfully loaded and processed data before attempting optimization
2. Use Method 2 for integration (see above) to ensure the endpoint has access to the global PROCESSED_DATA variable
3. Verify that the data is properly stored in the PROCESSED_DATA variable by checking other endpoints that use this data

### 2. Optimization Directory Not Found

**Problem**: Errors related to missing optimization directory or files.

**Solution**:
1. Run the `/api/check-optimization-directory` endpoint to verify the directory status
2. Ensure the application has write permissions to the results/optimization directory
3. Check the logs for any specific error messages related to file operations

## File Storage

Optimization results are stored in the `results/optimization/` directory. The following files are created:

- **optimization_{strategy_type}_{timestamp}.json**: Optimization results
- **chart_backup_{strategy_type}_{timestamp}.png**: Backup chart image

## Error Handling and Logging

The module includes comprehensive error handling and logging:

- All optimization requests are logged to `optimization_requests.log`
- Runtime errors are captured and reported
- Status updates are maintained throughout the optimization process 