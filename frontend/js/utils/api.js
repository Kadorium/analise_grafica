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
    RECENT_COMPARISONS: '/api/recent-comparisons',
    CHECK_OPTIMIZATION_DIR: '/api/check-optimization-directory',
    SAVE_CONFIG: '/api/save-config',
    LOAD_CONFIG: '/api/load-config',
    EXPORT_RESULTS: '/api/export-results',
    CURRENT_CONFIG: '/api/current-config',
    ARRANGE_DATA: '/api/arrange-data',
    DATA_STATUS: '/api/data-status',
    SEASONALITY_DOW: '/api/seasonality/day-of-week',
    SEASONALITY_MONTHLY: '/api/seasonality/monthly',
    SEASONALITY_VOLATILITY: '/api/seasonality/volatility',
    SEASONALITY_HEATMAP: '/api/seasonality/heatmap',
    SEASONALITY_SUMMARY: '/api/seasonality/summary',
    DEBUG_INFO: '/api/debug-info',
    MULTI_ASSET_UPLOAD: '/api/upload-multi-asset',
    GENERATE_SIGNALS: '/api/generate-signals',
    FETCH_SIGNALS: '/api/fetch-signals',
    UPDATE_WEIGHTS: '/api/update-weights',
    FETCH_WEIGHTS: '/api/fetch-weights'
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
            body: formData,
            // Important: Don't set Content-Type header for multipart/form-data
            // Let the browser set it with the correct boundary
            headers: {
                // Explicitly set to null to prevent default being added
                'Content-Type': null
            }
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

// Function to upload and process multi-asset data
export async function uploadMultiAssetData(formData) {
    // Log what's being uploaded for debugging
    if (formData.has('file')) {
        const fileEntry = formData.get('file');
        if (fileEntry instanceof File) {
            console.log('Uploading multi-asset file:', fileEntry.name, 'Size:', fileEntry.size);
        } else {
            console.log('Uploading with empty file field - server will use default multi-asset file');
        }
    }
    
    try {
        console.log('Calling multi-asset upload endpoint');
        const response = await fetch(API_ENDPOINTS.MULTI_ASSET_UPLOAD, {
            method: 'POST',
            body: formData,
            // Important: Don't set Content-Type header for multipart/form-data
            // Let the browser set it with the correct boundary
            headers: {
                // Explicitly set to null to prevent default being added
                'Content-Type': null
            }
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
        
        console.log('Multi-asset upload response:', data);
        return {
            success: true,
            ...data
        };
    } catch (error) {
        console.error('Error uploading multi-asset data:', error);
        // Return a standardized error response
        return {
            success: false,
            message: error.message || 'Error uploading multi-asset data'
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

/**
 * Generate trading signals for multiple assets using specified strategies.
 * 
 * @param {Object} options - Signal generation options
 * @param {Array} options.strategies - Array of [strategy_type, param_type] pairs
 * @param {number} [options.max_workers] - Maximum number of worker processes
 * @param {boolean} [options.refresh_cache] - Whether to refresh cached results
 * @param {string} [options.weights_file] - Path to weights file
 * @param {boolean} [options.include_ml] - Whether to include ML signals
 * @returns {Promise<Object>} Promise resolving to the signal generation result
 */
export async function generateSignals(options) {
    try {
        const response = await fetch(API_ENDPOINTS.GENERATE_SIGNALS, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                strategies: options.strategies,
                max_workers: options.max_workers || null,
                refresh_cache: options.refresh_cache || false,
                weights_file: options.weights_file || null,
                include_ml: options.include_ml || false
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to generate signals');
        }

        return await response.json();
    } catch (error) {
        console.error('Error generating signals:', error);
        throw error;
    }
}

/**
 * Fetch signals from a cached file.
 * 
 * @param {string} cacheFile - The cached file name or path
 * @returns {Promise<Object>} - Promise resolving to the signals data
 */
export async function fetchCachedSignals(cacheFile) {
    try {
        // Extract the filename from the cache file path if it includes directories
        const filename = cacheFile.split('/').pop().split('\\').pop();
        console.log('Fetching cached signals from:', filename);
        
        const response = await fetch(`${API_ENDPOINTS.FETCH_SIGNALS}/${filename}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({
                message: `HTTP error: ${response.status} ${response.statusText}`
            }));
            throw new Error(errorData.message || `Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`Fetched ${data.count || 0} signals from cache`);
        
        if (data.success && data.signals) {
            // Get the latest weights file to merge with signals
            try {
                const latestWeightsResponse = await fetch(`${API_ENDPOINTS.FETCH_WEIGHTS}/latest`, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json'
                    }
                });
                
                if (latestWeightsResponse.ok) {
                    const weightsData = await latestWeightsResponse.json();
                    
                    if (weightsData.success && weightsData.weights) {
                        // Merge weights and metrics with signals
                        data.signals.forEach(signal => {
                            const asset = signal.asset;
                            const strategyKey = `${signal.strategy}_${signal.parameters}`;
                            
                            // Add weight if available
                            if (weightsData.weights[asset] && weightsData.weights[asset][strategyKey] !== undefined) {
                                signal.weight = weightsData.weights[asset][strategyKey];
                            }
                            
                            // Add metrics if available
                            if (weightsData.metrics && 
                                weightsData.metrics[asset] && 
                                weightsData.metrics[asset][strategyKey]) {
                                
                                const metrics = weightsData.metrics[asset][strategyKey];
                                signal.total_return = metrics.total_return;
                                signal.sharpe_ratio = metrics.sharpe_ratio;
                                signal.max_drawdown = metrics.max_drawdown;
                                signal.win_rate = metrics.win_rate;
                                signal.num_trades = metrics.num_trades;
                            }
                        });
                        
                        console.log('Merged weights and metrics with signals');
                    }
                }
            } catch (weightsError) {
                console.warn('Could not fetch weights to merge with signals:', weightsError);
                // Continue with signals only
            }
            
            return {
                success: true,
                signals: data.signals
            };
        } else {
            throw new Error(data.message || 'No signals returned from cache');
        }
    } catch (error) {
        console.error('Error fetching cached signals:', error);
        throw error;
    }
}

/**
 * Calculate performance-based weights for asset-strategy pairs.
 * 
 * @param {Object} requestData - Weight calculation configuration
 * @param {Array} requestData.strategies - Array of [strategy_type, param_type] pairs
 * @param {string} requestData.goal_seek_metric - Metric to use for weighting
 * @param {Object} [requestData.custom_weights] - Custom weight factors
 * @param {string} requestData.lookback_period - Period to look back for backtesting
 * @param {number} [requestData.max_workers] - Maximum number of worker processes
 * @param {boolean} [requestData.refresh_cache] - Whether to refresh cached results
 * @returns {Promise<Object>} Promise resolving to the weight calculation result
 */
export async function updateWeights(requestData) {
    try {
        console.log('Calling update-weights endpoint:', requestData);
        
        const response = await fetch(API_ENDPOINTS.UPDATE_WEIGHTS, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({
                message: `HTTP error: ${response.status} ${response.statusText}`
            }));
            throw new Error(errorData.message || `Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Update weights response:', data);
        
        return {
            success: true,
            ...data
        };
    } catch (error) {
        console.error('Error updating weights:', error);
        return {
            success: false,
            message: error.message || 'Error updating weights'
        };
    }
}

/**
 * Fetch weights from a cached file.
 * 
 * @param {string} cacheFile - The cached file name or path
 * @returns {Promise<Object>} - Promise resolving to the weights data
 */
export async function fetchWeights(cacheFile) {
    try {
        // Extract the filename from the cache file path if it includes directories
        const filename = cacheFile.split('/').pop().split('\\').pop();
        console.log('Fetching cached weights from:', filename);
        
        const response = await fetch(`${API_ENDPOINTS.FETCH_WEIGHTS}/${filename}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({
                message: `HTTP error: ${response.status} ${response.statusText}`
            }));
            throw new Error(errorData.message || `Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`Fetched weights from cache`);
        
        if (data.success && data.weights) {
            return data;
        } else {
            throw new Error(data.message || 'No weights returned from cache');
        }
    } catch (error) {
        console.error('Error fetching weights:', error);
        throw error;
    }
}

// Add alias exports at the end of the file
export const getStrategies = fetchAvailableStrategies;
export const getStrategyParameters = fetchStrategyParameters;
export const getAnalysis = runSeasonalityAnalysis;
export const loadConfig = fetchCurrentConfig;
export const fetchSignals = fetchCachedSignals;
export const calculateWeights = updateWeights;
