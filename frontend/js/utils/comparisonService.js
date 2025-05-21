import { showGlobalLoader, hideGlobalLoader, showError, showSuccessMessage, updateProgressBar } from './ui.js';
import { fetchApi, API_ENDPOINTS } from './api.js';
import { appState } from './state.js';
import { formatNumber, formatDate } from './formatters.js';

// Variable to store the progress polling interval
let progressIntervalId = null;

/**
 * Run a comparison of multiple trading strategies
 * @param {Array} strategyConfigs - Array of strategy configurations with strategy_id and parameters
 * @param {Object} backtestConfig - Backtest configuration (initial_capital, commission, etc.)
 * @param {Boolean} optimize - Whether to optimize parameters before comparison
 * @param {String} optimizationMetric - Metric to optimize for if optimize=true
 * @returns {Promise<Object>} - Comparison results
 */
export async function compareStrategies(strategyConfigs, backtestConfig = {}, optimize = false, optimizationMetric = 'sharpe_ratio') {
    try {
        if (!appState.dataProcessed) {
            showError('Please upload and process data first');
            return null;
        }

        if (!strategyConfigs || strategyConfigs.length === 0) {
            showError('No strategies selected for comparison');
            return null;
        }

        // Prepare request data
        const requestData = {
            strategy_configs: strategyConfigs,
            backtest_config: backtestConfig,
            optimize: optimize,
            optimization_metric: optimizationMetric
        };

        // Show loader with appropriate message
        const loadingMessage = optimize 
            ? 'Optimizing and comparing strategies...' 
            : 'Comparing strategies...';
        
        showGlobalLoader(loadingMessage);
        
        // If optimizing, start progress tracking
        if (optimize) {
            // Create progress bar
            const loaderContainer = document.querySelector('.global-loader');
            if (loaderContainer) {
                if (!loaderContainer.querySelector('.progress')) {
                    const progressHTML = `
                        <div class="mt-3 mb-2">
                            <div class="progress" style="height: 20px;">
                                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                    role="progressbar" style="width: 0%;" 
                                    aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%</div>
                            </div>
                            <div class="text-center mt-1 small" id="progress-details">
                                Starting optimization...
                            </div>
                            <div class="mt-3" id="interim-results"></div>
                        </div>
                    `;
                    loaderContainer.innerHTML += progressHTML;
                }
            }
            
            // Start progress polling
            startProgressPolling();
        }

        // Make API call
        const response = await fetchApi('/api/compare-strategies', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        // Stop progress polling
        stopProgressPolling();

        // Hide loader
        hideGlobalLoader();

        if (!response.success) {
            throw new Error(response.message || 'Error comparing strategies');
        }

        showSuccessMessage('Strategy comparison completed successfully');
        return response;
    } catch (error) {
        // Stop progress polling if there's an error
        stopProgressPolling();
        
        hideGlobalLoader();
        showError(error.message || 'Failed to compare strategies');
        console.error('Strategy comparison error:', error);
        return null;
    }
}

/**
 * Start polling for optimization progress
 */
function startProgressPolling() {
    // Clear any existing interval
    stopProgressPolling();
    
    // Poll every 500ms
    progressIntervalId = setInterval(async () => {
        try {
            const response = await fetchApi('/api/optimization-progress', {
                method: 'GET'
            });
            
            if (response.success && response.progress) {
                updateOptimizationProgress(response.progress);
            }
        } catch (error) {
            console.warn('Error polling for progress:', error);
        }
    }, 500);
}

/**
 * Stop polling for optimization progress
 */
function stopProgressPolling() {
    if (progressIntervalId !== null) {
        clearInterval(progressIntervalId);
        progressIntervalId = null;
    }
}

/**
 * Update the optimization progress display
 * @param {Object} progress - Progress data from the API
 */
function updateOptimizationProgress(progress) {
    // Only update if the operation is in progress
    if (!progress.in_progress) {
        stopProgressPolling();
        return;
    }
    
    // Update progress bar
    const percentage = progress.percentage || 0;
    updateProgressBar(Math.round(percentage));
    
    // Update progress details
    const detailsElement = document.getElementById('progress-details');
    if (detailsElement) {
        // Create status text
        let statusText = `Processing ${progress.completed_evaluations || 0} of ${progress.total_steps || 0} combinations`;
        
        // Add time information if available
        if (progress.elapsed_formatted) {
            statusText += ` (Elapsed: ${progress.elapsed_formatted}`;
            
            if (progress.estimated_remaining_formatted) {
                statusText += `, Remaining: ${progress.estimated_remaining_formatted}`;
            }
            
            statusText += ')';
        }
        
        detailsElement.textContent = statusText;
    }
    
    // Update interim results if available
    const interimContainer = document.getElementById('interim-results');
    if (interimContainer && progress.interim_results && progress.interim_results.length > 0) {
        let resultsHTML = '<div class="card"><div class="card-header">Top Results So Far</div><div class="card-body p-2">';
        resultsHTML += '<table class="table table-sm table-striped mb-0"><thead><tr>';
        resultsHTML += '<th>Score</th><th>Return</th><th>Sharpe</th><th>Params</th></tr></thead><tbody>';
        
        progress.interim_results.forEach(result => {
            resultsHTML += '<tr>';
            resultsHTML += `<td>${formatNumber(result.score, 2)}</td>`;
            
            // Format metrics
            const totalReturn = result.metrics.total_return ? 
                (formatNumber(result.metrics.total_return * 100, 2) + '%') : 'N/A';
            const sharpeRatio = result.metrics.sharpe_ratio ? 
                formatNumber(result.metrics.sharpe_ratio, 2) : 'N/A';
                
            resultsHTML += `<td>${totalReturn}</td>`;
            resultsHTML += `<td>${sharpeRatio}</td>`;
            
            // Format parameters (shortened version)
            const paramValues = Object.entries(result.params)
                .map(([key, value]) => `${key.substring(0, 3)}:${value}`)
                .join(', ');
            
            resultsHTML += `<td title="${JSON.stringify(result.params).replace(/"/g, "'")}">${paramValues}</td>`;
            resultsHTML += '</tr>';
        });
        
        resultsHTML += '</tbody></table></div></div>';
        interimContainer.innerHTML = resultsHTML;
    }
}

/**
 * Get recent strategy comparisons
 * @returns {Promise<Object>} - Recent comparison results
 */
export async function getRecentComparisons() {
    try {
        const response = await fetchApi('/api/recent-comparisons', {
            method: 'GET'
        });

        if (!response.success) {
            throw new Error(response.message || 'Error retrieving recent comparisons');
        }

        return response.comparisons;
    } catch (error) {
        console.error('Error retrieving recent comparisons:', error);
        return [];
    }
}

/**
 * Generate HTML for a comparison metrics table
 * @param {Object} metricsData - Metrics data from comparison results
 * @returns {String} - HTML for metrics table
 */
export function generateMetricsTableHtml(metricsData) {
    if (!metricsData) return '<p>No metrics data available</p>';

    const metricNames = {
        'total_return': 'Total Return',
        'annual_return': 'Annual Return',
        'sharpe_ratio': 'Sharpe Ratio',
        'max_drawdown': 'Max Drawdown',
        'win_rate': 'Win Rate'
    };

    // Get strategy IDs
    const strategyIds = Object.keys(metricsData.total_return || {});
    if (strategyIds.length === 0) return '<p>No strategies to compare</p>';

    // Start building the table
    let tableHtml = `
        <div class="table-responsive">
            <table class="table table-bordered table-hover">
                <thead>
                    <tr>
                        <th>Metric</th>
                        ${strategyIds.map(id => `<th>${id}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
    `;

    // Add rows for each metric
    Object.entries(metricNames).forEach(([metricKey, metricLabel]) => {
        const metricData = metricsData[metricKey] || {};
        
        // Start the row
        tableHtml += `<tr><td>${metricLabel}</td>`;
        
        // Add cells for each strategy
        strategyIds.forEach(strategyId => {
            const value = metricData[strategyId];
            let formattedValue = '';
            let colorClass = '';
            
            // Format the value based on the metric type
            if (metricKey === 'total_return' || metricKey === 'annual_return') {
                formattedValue = formatNumber(value * 100, 2) + '%';
                colorClass = value > 0 ? 'text-success' : value < 0 ? 'text-danger' : '';
            } else if (metricKey === 'max_drawdown') {
                formattedValue = formatNumber(value * 100, 2) + '%';
                colorClass = 'text-danger';
            } else if (metricKey === 'win_rate') {
                formattedValue = formatNumber(value * 100, 2) + '%';
            } else {
                formattedValue = formatNumber(value, 2);
            }
            
            tableHtml += `<td class="${colorClass}">${formattedValue}</td>`;
        });
        
        // End the row
        tableHtml += '</tr>';
    });

    // Close the table
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;

    return tableHtml;
}

/**
 * Generate HTML for a parameters comparison table
 * @param {Object} parametersData - Parameters data from comparison results
 * @returns {String} - HTML for parameters table
 */
export function generateParametersTableHtml(parametersData) {
    if (!parametersData) return '<p>No parameters data available</p>';

    const strategyIds = Object.keys(parametersData);
    if (strategyIds.length === 0) return '<p>No strategies to compare</p>';

    // Get all parameter names across all strategies
    const allParamNames = new Set();
    strategyIds.forEach(strategyId => {
        const params = parametersData[strategyId] || {};
        Object.keys(params).forEach(paramName => allParamNames.add(paramName));
    });

    const paramNames = Array.from(allParamNames);
    if (paramNames.length === 0) return '<p>No parameters to compare</p>';

    // Start building the table
    let tableHtml = `
        <div class="table-responsive">
            <table class="table table-bordered table-hover">
                <thead>
                    <tr>
                        <th>Parameter</th>
                        ${strategyIds.map(id => `<th>${id}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
    `;

    // Add rows for each parameter
    paramNames.forEach(paramName => {
        // Start the row
        tableHtml += `<tr><td>${paramName}</td>`;
        
        // Add cells for each strategy
        strategyIds.forEach(strategyId => {
            const params = parametersData[strategyId] || {};
            const value = params[paramName];
            
            // Format the value based on its type
            let formattedValue = '';
            if (value === undefined) {
                formattedValue = '-';
            } else if (typeof value === 'number') {
                formattedValue = formatNumber(value);
            } else if (typeof value === 'boolean') {
                formattedValue = value ? 'True' : 'False';
            } else {
                formattedValue = value.toString();
            }
            
            tableHtml += `<td>${formattedValue}</td>`;
        });
        
        // End the row
        tableHtml += '</tr>';
    });

    // Close the table
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;

    return tableHtml;
}

/**
 * Generate HTML for a trades comparison
 * @param {Object} tradesData - Trades data from comparison results
 * @returns {String} - HTML for trades display
 */
export function generateTradesTableHtml(tradesData, strategyId) {
    if (!tradesData || !strategyId || !tradesData[strategyId]) {
        return '<p>No trades data available</p>';
    }

    const trades = tradesData[strategyId];
    if (trades.length === 0) {
        return '<p>No trades for this strategy</p>';
    }

    // Start building the table
    let tableHtml = `
        <div class="table-responsive">
            <table class="table table-bordered table-hover table-sm">
                <thead>
                    <tr>
                        <th>Entry Date</th>
                        <th>Exit Date</th>
                        <th>Entry Price</th>
                        <th>Exit Price</th>
                        <th>Profit</th>
                        <th>Result</th>
                    </tr>
                </thead>
                <tbody>
    `;

    // Add rows for each trade
    trades.forEach(trade => {
        const profitClass = trade.profit_pct >= 0 ? 'text-success' : 'text-danger';
        
        tableHtml += `
            <tr>
                <td>${trade.entry_date}</td>
                <td>${trade.exit_date}</td>
                <td>${formatNumber(trade.entry_price)}</td>
                <td>${formatNumber(trade.exit_price)}</td>
                <td class="${profitClass}">${formatNumber(trade.profit_pct)}%</td>
                <td class="${profitClass}">${trade.result.toUpperCase()}</td>
            </tr>
        `;
    });

    // Close the table
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;

    return tableHtml;
} 