// frontend/js/utils/api.js

// API endpoint definitions
export const API_BASE_URL = '';
export const API_ENDPOINTS = {
    UPLOAD: '/api/upload',
    PROCESS_DATA: '/api/process-data',
    ADD_INDICATORS: '/api/add-indicators',
    PLOT_INDICATORS: '/api/plot-indicators',
    AVAILABLE_STRATEGIES: '/api/available-strategies',
    STRATEGY_PARAMETERS: '/api/strategy-parameters',
    RUN_BACKTEST: '/api/run-backtest',
    OPTIMIZE_STRATEGY: '/api/optimize-strategy',
    OPTIMIZATION_STATUS: '/api/optimization-status',
    OPTIMIZATION_RESULTS: '/api/optimization-results',
    COMPARE_STRATEGIES: '/api/compare-strategies',
    SAVE_CONFIG: '/api/save-config',
    LOAD_CONFIG: '/api/load-config',
    EXPORT_RESULTS: '/api/export-results',
    CURRENT_CONFIG: '/api/current-config',
    ARRANGE_DATA: '/api/arrange-data',
    DATA_STATUS: '/api/data-status',
    SEASONALITY_DAY_OF_WEEK: '/api/seasonality/day-of-week',
    SEASONALITY_MONTHLY: '/api/seasonality/monthly',
    SEASONALITY_VOLATILITY: '/api/seasonality/volatility',
    SEASONALITY_HEATMAP: '/api/seasonality/heatmap',
    SEASONALITY_SUMMARY: '/api/seasonality/summary'
};

// Generic fetch wrapper with error handling
export async function fetchApi(endpoint, options = {}) {
    try {
        console.log(`API call to ${endpoint}`, options);
        const response = await fetch(endpoint, options);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `Error: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API error (${endpoint}):`, error);
        throw error;
    }
}

// Specific API call functions
export async function uploadData(formData) {
    // Log what's being uploaded for debugging
    if (formData.has('file')) {
        const fileEntry = formData.get('file');
        if (fileEntry instanceof File) {
            console.log('Uploading file:', fileEntry.name, 'Size:', fileEntry.size);
        } else {
            console.log('Uploading with empty file field - server will use default file');
        }
    }
    
    try {
        console.log('Calling upload endpoint');
        const response = await fetch(API_ENDPOINTS.UPLOAD, {
            method: 'POST',
            body: formData
        });
        
        // Check for HTTP error response
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({
                message: `HTTP error: ${response.status} ${response.statusText}`
            }));
            throw new Error(errorData.message || `Error ${response.status}: ${response.statusText}`);
        }
        
        // Try to parse the response as JSON
        const data = await response.json().catch(err => {
            console.error('Failed to parse JSON response:', err);
            throw new Error('Invalid response format from server');
        });
        
        console.log('Upload response:', data);
        return {
            success: true,
            ...data
        };
    } catch (error) {
        console.error('Error uploading data:', error);
        // Return a standardized error response
        return {
            success: false,
            message: error.message || 'Error uploading data'
        };
    }
}

export async function processData() {
    try {
        console.log('Calling process-data endpoint');
        const response = await fetch(API_ENDPOINTS.PROCESS_DATA, {
            method: 'POST'
        });
        
        // Check for HTTP error response
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({
                message: `HTTP error: ${response.status} ${response.statusText}`
            }));
            throw new Error(errorData.message || `Error ${response.status}: ${response.statusText}`);
        }
        
        // Try to parse the response as JSON
        const data = await response.json().catch(err => {
            console.error('Failed to parse JSON response:', err);
            throw new Error('Invalid response format from server');
        });
        
        console.log('Process data response:', data);
        return {
            success: true,
            ...data
        };
    } catch (error) {
        console.error('Error processing data:', error);
        // Return a standardized error response
        return {
            success: false,
            message: error.message || 'Error processing data'
        };
    }
}

export async function fetchDataStatus() {
    return fetchApi(API_ENDPOINTS.DATA_STATUS);
}

export async function addIndicators(indicatorConfig) {
    return fetchApi(API_ENDPOINTS.ADD_INDICATORS, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(indicatorConfig)
    });
}

export async function plotIndicators(plotConfig) {
    return fetchApi(API_ENDPOINTS.PLOT_INDICATORS, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(plotConfig)
    });
}

export async function fetchAvailableStrategies() {
    return fetchApi(API_ENDPOINTS.AVAILABLE_STRATEGIES);
}

export async function fetchStrategyParameters(strategyType) {
    return fetchApi(`${API_ENDPOINTS.STRATEGY_PARAMETERS}/${strategyType}`);
}

export async function runBacktest(requestData) {
    // Transform request data into the expected format
    const formattedData = {
        strategy_config: {
            strategy_type: requestData.strategy || '',
            parameters: requestData.parameters || {}
        },
        backtest_config: {
            initial_capital: requestData.initial_capital || 10000.0,
            commission: requestData.commission || 0.001,
            start_date: requestData.start_date || null,
            end_date: requestData.end_date || null
        }
    };
    
    console.log('Formatted backtest request:', formattedData);
    
    return fetchApi(API_ENDPOINTS.RUN_BACKTEST, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formattedData)
    });
}

export async function optimizeStrategy(requestData) {
    return fetchApi(API_ENDPOINTS.OPTIMIZE_STRATEGY, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
    });
}

export async function checkOptimizationStatus() {
    return fetchApi(API_ENDPOINTS.OPTIMIZATION_STATUS);
}

export async function fetchOptimizationResults(strategyType) {
    return fetchApi(`${API_ENDPOINTS.OPTIMIZATION_RESULTS}/${strategyType}`);
}

export async function compareStrategies(requestData) {
    return fetchApi(API_ENDPOINTS.COMPARE_STRATEGIES, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
    });
}

export async function saveConfig(configData) {
    return fetchApi(API_ENDPOINTS.SAVE_CONFIG, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configData)
    });
}

export async function fetchCurrentConfig() {
    return fetchApi(API_ENDPOINTS.CURRENT_CONFIG);
}

export async function arrangeData(arrangeConfig) {
    return fetchApi(API_ENDPOINTS.ARRANGE_DATA, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(arrangeConfig)
    });
}

export async function runSeasonalityAnalysis(params) {
    // Handle the case where we're passed a full params object or just a string analysis type
    const analysisType = typeof params === 'string' ? params : params.pattern_type;
    
    if (!analysisType || typeof analysisType !== 'string') {
        console.error('Invalid analysisType in runSeasonalityAnalysis:', params);
        throw new Error('Invalid analysis type. Expected a string like "day_of_week", "monthly", etc.');
    }
    
    const endpoint = API_ENDPOINTS[`SEASONALITY_${analysisType.toUpperCase().replace('-', '_')}`];
    
    if (!endpoint) {
        console.error(`No endpoint found for analysis type: ${analysisType}`);
        throw new Error(`Unsupported seasonality analysis type: ${analysisType}`);
    }
    
    return fetchApi(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: params && typeof params === 'object' ? JSON.stringify(params) : null
    });
}

// Function to fetch results history
export async function fetchResultsHistory() {
    return fetchApi(`${API_ENDPOINTS.EXPORT_RESULTS}/history`, {
        method: 'GET'
    });
}
