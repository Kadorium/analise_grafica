import { compareStrategies, generateMetricsTableHtml, generateParametersTableHtml, generateTradesTableHtml } from '../utils/comparisonService.js';
import { appState } from '../utils/state.js';
import { showError, showSuccessMessage } from '../utils/ui.js';
import { getStrategyConfig } from '../utils/strategies-config.js';

// DOM references to comparison elements
let compareResultsDisplay;
let strategyTabs;
let metricsContainer;
let parametersContainer;
let tradesContainer;
let chartContainer;
let optionsContainer;
let runFullComparisonBtn;

// Track the comparison results
let currentComparisonResults = null;

/**
 * Initialize the strategy comparison module
 */
export function initializeStrategyComparison() {
    console.log('Initializing Strategy Comparison Module');

    // Get DOM references
    compareResultsDisplay = document.getElementById('comparison-results-display');
    
    if (!compareResultsDisplay) {
        console.error('Strategy comparison container not found');
        return;
    }

    // Listen for the run full comparison button
    setupEventListeners();
}

/**
 * Set up event listeners for comparison UI
 */
function setupEventListeners() {
    // Delegate event listener for the "Run Full Comparison" button
    document.addEventListener('click', event => {
        if (event.target && event.target.id === 'run-full-comparison-btn') {
            runFullComparison();
        }
    });
}

/**
 * Run a full comparison based on the strategy-compare-item elements in the DOM
 */
async function runFullComparison() {
    try {
        // Get all strategy items
        const strategyItems = document.querySelectorAll('.strategy-compare-item');
        if (strategyItems.length === 0) {
            showError('No strategies selected for comparison');
            return;
        }

        // Check if optimization is requested
        const shouldOptimize = document.getElementById('optimize-comparison-checkbox')?.checked || false;
        console.log(`[Strategy Comparison] Running comparison with optimization: ${shouldOptimize}`);

        // Collect strategy configurations
        const strategyConfigs = [];
        
        strategyItems.forEach(item => {
            const strategyId = item.dataset.strategyId;
            const parameters = {};
            
            // Collect parameters from form elements
            item.querySelectorAll('input, select').forEach(inputEl => {
                if (inputEl.name) {
                    // Convert parameter value based on type
                    if (inputEl.type === 'number' || inputEl.dataset.paramType === 'number') {
                        parameters[inputEl.name] = parseFloat(inputEl.value);
                    } else if (inputEl.type === 'checkbox') {
                        parameters[inputEl.name] = inputEl.checked;
                    } else {
                        parameters[inputEl.name] = inputEl.value;
                    }
                }
            });
            
            // Get parameter ranges for optimization if needed
            const paramRanges = getParameterRangesForStrategy(strategyId);
            
            strategyConfigs.push({
                strategy_id: strategyId,
                parameters: parameters,
                param_ranges: paramRanges
            });
        });
        
        console.log(`[Strategy Comparison] Running comparison with ${strategyConfigs.length} strategies:`);
        strategyConfigs.forEach(config => {
            console.log(`- ${config.strategy_id}: ${JSON.stringify(config.parameters)}`);
            if (config.param_ranges) {
                console.log(`  With ${Object.keys(config.param_ranges).length} parameter ranges for optimization`);
            }
        });
        
        // Get backtest configuration
        const backtestConfig = {
            initial_capital: parseFloat(document.getElementById('initial-capital')?.value || 10000),
            commission: parseFloat(document.getElementById('commission')?.value || 0.001)
        };
        
        console.log(`[Strategy Comparison] Backtest config: ${JSON.stringify(backtestConfig)}`);
        
        // Run the comparison
        const results = await compareStrategies(
            strategyConfigs, 
            backtestConfig,
            shouldOptimize,
            'sharpe_ratio' // Default optimization metric
        );
        
        if (results && results.success) {
            console.log(`[Strategy Comparison] Comparison completed successfully`);
            if (results.optimization) {
                console.log(`[Strategy Comparison] Optimization was performed for metric: ${results.optimization.metric}`);
            }
            
            currentComparisonResults = results;
            displayComparisonResults(results);
        }
    } catch (error) {
        console.error('Error running comparison:', error);
        showError('Failed to run comparison: ' + error.message);
    }
}

/**
 * Display comparison results in the UI
 * @param {Object} results - Comparison results from the API
 */
function displayComparisonResults(results) {
    if (!compareResultsDisplay) {
        console.error('Comparison results display container not found');
        return;
    }
    
    // Create containers for the results if they don't exist
    compareResultsDisplay.innerHTML = `
        <h5 class="mt-3">Comparison Results</h5>
        
        <ul class="nav nav-tabs mb-3" id="comparison-tabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="metrics-tab" data-bs-toggle="tab" 
                    data-bs-target="#metrics-content" type="button" role="tab" 
                    aria-controls="metrics-content" aria-selected="true">Performance Metrics</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="params-tab" data-bs-toggle="tab" 
                    data-bs-target="#params-content" type="button" role="tab" 
                    aria-controls="params-content" aria-selected="false">Parameters</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="trades-tab" data-bs-toggle="tab" 
                    data-bs-target="#trades-content" type="button" role="tab" 
                    aria-controls="trades-content" aria-selected="false">Trades</button>
            </li>
        </ul>
        
        <div class="tab-content">
            <div class="tab-pane fade show active" id="metrics-content" role="tabpanel" aria-labelledby="metrics-tab">
                <div id="comparison-metrics-container"></div>
            </div>
            <div class="tab-pane fade" id="params-content" role="tabpanel" aria-labelledby="params-tab">
                <div id="comparison-parameters-container"></div>
            </div>
            <div class="tab-pane fade" id="trades-content" role="tabpanel" aria-labelledby="trades-tab">
                <div class="mb-3">
                    <label for="trades-strategy-select" class="form-label">Select Strategy:</label>
                    <select id="trades-strategy-select" class="form-select"></select>
                </div>
                <div id="comparison-trades-container"></div>
            </div>
        </div>
        
        <div class="mt-4" id="comparison-chart-container">
            <h6>Equity Curves Comparison</h6>
            <img src="data:image/png;base64,${results.chart_image}" class="img-fluid" alt="Equity Curves Comparison">
        </div>
    `;
    
    // Get references to the containers
    metricsContainer = document.getElementById('comparison-metrics-container');
    parametersContainer = document.getElementById('comparison-parameters-container');
    tradesContainer = document.getElementById('comparison-trades-container');
    strategyTabs = document.getElementById('comparison-tabs');
    
    // Populate metrics table
    if (metricsContainer && results.comparison_metrics) {
        metricsContainer.innerHTML = generateMetricsTableHtml(results.comparison_metrics);
    }
    
    // Populate parameters table
    if (parametersContainer && results.parameters) {
        // Check if we have optimization data with parameter changes
        if (results.optimization && results.optimization.parameter_changes) {
            // Generate a more detailed parameters table showing original vs. optimized
            parametersContainer.innerHTML = generateParametersComparisonHtml(
                results.parameters, 
                results.optimization.original_parameters,
                results.optimization.parameter_changes
            );
        } else {
            // Use the standard parameters table
            parametersContainer.innerHTML = generateParametersTableHtml(results.parameters);
        }
    }
    
    // Set up trades selector
    const tradesSelect = document.getElementById('trades-strategy-select');
    if (tradesSelect && results.trades) {
        // Clear and populate the strategy select
        tradesSelect.innerHTML = '';
        
        Object.keys(results.trades).forEach(strategyId => {
            const option = document.createElement('option');
            option.value = strategyId;
            option.textContent = strategyId;
            tradesSelect.appendChild(option);
        });
        
        // Display trades for first strategy
        if (tradesSelect.options.length > 0) {
            const firstStrategy = tradesSelect.options[0].value;
            showTradesForStrategy(firstStrategy, results.trades);
            
            // Set up change listener
            tradesSelect.addEventListener('change', () => {
                showTradesForStrategy(tradesSelect.value, results.trades);
            });
        }
    }
    
    // Add an alert if optimization was performed
    if (results.optimization) {
        const optimizationAlert = document.createElement('div');
        optimizationAlert.className = 'alert alert-info mt-3';
        
        let alertContent = `<i class="bi bi-info-circle"></i> Parameters were optimized for ${results.optimization.metric}.`;
        
        // Add information about changed parameters if available
        if (results.optimization.parameter_changes) {
            const changedStrategies = Object.entries(results.optimization.parameter_changes)
                .filter(([_, changes]) => Object.keys(changes).length > 0)
                .map(([strategyId, _]) => strategyId);
                
            if (changedStrategies.length > 0) {
                alertContent += ` Improvements found for: ${changedStrategies.join(', ')}.`;
                alertContent += ' <strong>Check the Parameters tab for details.</strong>';
            } else {
                alertContent += ' No parameter improvements were found (optimal parameters already selected).';
            }
        }
        
        optimizationAlert.innerHTML = alertContent;
        compareResultsDisplay.insertBefore(optimizationAlert, compareResultsDisplay.firstChild);
    }
    
    // Show the best strategy for each metric
    if (results.best_strategies) {
        const bestStrategyContainer = document.createElement('div');
        bestStrategyContainer.className = 'best-strategies-container mt-3 mb-3';
        bestStrategyContainer.innerHTML = `
            <h6>Best Strategies:</h6>
            <ul>
                ${Object.entries(results.best_strategies).map(([metric, strategyId]) => `
                    <li><strong>${formatMetricName(metric)}:</strong> ${strategyId}</li>
                `).join('')}
            </ul>
        `;
        
        // Add before the tabs
        const tabsElement = document.getElementById('comparison-tabs');
        if (tabsElement) {
            compareResultsDisplay.insertBefore(bestStrategyContainer, tabsElement);
        }
    }
}

/**
 * Display trades for a specific strategy
 * @param {String} strategyId - The strategy ID
 * @param {Object} tradesData - Trades data from comparison results
 */
function showTradesForStrategy(strategyId, tradesData) {
    if (!tradesContainer) return;
    
    tradesContainer.innerHTML = generateTradesTableHtml(tradesData, strategyId);
}

/**
 * Format a metric name for display
 * @param {String} metricName - The metric name (e.g., 'sharpe_ratio')
 * @returns {String} Formatted metric name (e.g., 'Sharpe Ratio')
 */
function formatMetricName(metricName) {
    const metricNames = {
        'total_return': 'Total Return',
        'annual_return': 'Annual Return',
        'sharpe_ratio': 'Sharpe Ratio',
        'max_drawdown': 'Max Drawdown',
        'win_rate': 'Win Rate'
    };
    
    return metricNames[metricName] || metricName
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

/**
 * Get parameter ranges for a strategy to be used in optimization
 * @param {String} strategyId - The strategy ID
 * @returns {Object|null} Parameter ranges or null if not available
 */
function getParameterRangesForStrategy(strategyId) {
    // Check if optimization is enabled
    const shouldOptimize = document.getElementById('optimize-comparison-checkbox')?.checked || false;
    if (!shouldOptimize) {
        console.log(`[Strategy Comparison] Optimization disabled for ${strategyId}`);
        return null;
    }
    
    console.log(`[Strategy Comparison] Generating parameter ranges for ${strategyId}`);
    
    // Predefined sensible parameter ranges for common strategies
    const PREDEFINED_RANGES = {
        'trend_following': {
            'fast_ma_type': ['sma', 'ema'],
            'fast_ma_period': [5, 10, 15, 20, 25],
            'slow_ma_type': ['sma', 'ema'],
            'slow_ma_period': [30, 50, 100, 150, 200]
        },
        'mean_reversion': {
            'rsi_period': [7, 10, 14, 21],
            'oversold': [20, 25, 30, 35],
            'overbought': [65, 70, 75, 80],
            'exit_middle': [45, 50, 55]
        },
        'breakout': {
            'lookback_period': [10, 15, 20, 25, 30],
            'volume_threshold': [1.2, 1.5, 2.0, 2.5],
            'price_threshold': [0.01, 0.02, 0.03, 0.05],
            'atr_multiplier': [1.5, 2.0, 2.5, 3.0]
        },
        'sma_crossover': {
            'short_period': [5, 10, 20, 50],
            'long_period': [50, 100, 150, 200]
        },
        'ema_crossover': {
            'short_period': [5, 8, 12, 20],
            'long_period': [20, 50, 100, 200]
        },
        'macd_crossover': {
            'fast_period': [8, 12, 16],
            'slow_period': [21, 26, 30],
            'signal_period': [5, 9, 13]
        },
        'rsi': {
            'period': [7, 10, 14, 21],
            'buy_level': [20, 25, 30],
            'sell_level': [70, 75, 80]
        },
        'bollinger_breakout': {
            'period': [10, 15, 20, 25],
            'std_dev': [1.5, 2.0, 2.5, 3.0]
        },
        'supertrend': {
            'period': [7, 10, 14, 21],
            'multiplier': [2.0, 2.5, 3.0, 3.5]
        },
        'stochastic': {
            'k_period': [5, 9, 14],
            'd_period': [3, 5, 7, 9]
        },
        'adaptive_trend': {
            'fast_period': [5, 8, 10, 12, 15],
            'slow_period': [20, 25, 30, 35, 40],
            'signal_period': [5, 7, 9, 11, 13]
        },
        'accum_dist': {
            'period': [10, 15, 20, 25, 30]
        }
    };
    
    // Check if we have predefined ranges for this strategy
    if (PREDEFINED_RANGES[strategyId]) {
        console.log(`[Strategy Comparison] Using predefined parameter ranges for ${strategyId}`);
        return PREDEFINED_RANGES[strategyId];
    }
    
    // Get strategy configuration for strategies not in predefined ranges
    const strategyConfig = getStrategyConfig(strategyId);
    if (!strategyConfig || !strategyConfig.params) {
        console.warn(`[Strategy Comparison] No config found for ${strategyId}`);
        return null;
    }
    
    // Create parameter ranges
    const paramRanges = {};
    
    strategyConfig.params.forEach(param => {
        // Only add ranges for numeric parameters with min/max defined
        if (param.type === 'number' && param.min !== undefined && param.max !== undefined) {
            // For large ranges like moving average periods
            if (param.id.includes('period') || param.id.includes('length')) {
                // Common period values that make sense for most indicators
                if (param.max >= 100) {
                    // For longer periods (like slow moving averages)
                    paramRanges[param.id] = [20, 50, 100, 150, 200];
                } else {
                    // For shorter periods (like fast moving averages or RSI)
                    paramRanges[param.id] = [5, 10, 14, 20, 30];
                }
            } else if (param.id.includes('multiplier') || param.id.includes('factor')) {
                // For multipliers and factors (usually between 1-5)
                paramRanges[param.id] = [1.0, 1.5, 2.0, 2.5, 3.0];
            } else if (param.id.includes('threshold')) {
                // For thresholds
                paramRanges[param.id] = [
                    param.min,
                    param.min + (param.max - param.min) * 0.25,
                    param.min + (param.max - param.min) * 0.5,
                    param.min + (param.max - param.min) * 0.75,
                    param.max
                ].map(v => Math.round(v * 100) / 100);
            } else if (param.max - param.min > 10) {
                // For larger ranges, create sensible steps
                const steps = Math.min(5, param.max - param.min);
                const step = (param.max - param.min) / (steps - 1);
                const range = [];
                
                for (let i = 0; i < steps; i++) {
                    const value = Math.round((param.min + step * i) * 100) / 100; // Round to 2 decimal places
                    range.push(value);
                }
                
                paramRanges[param.id] = range;
            } else if (Number.isInteger(param.min) && Number.isInteger(param.max)) {
                // For smaller integer ranges, include reasonable integers
                const range = [];
                // If range is small, use all integers
                if (param.max - param.min <= 10) {
                    for (let i = param.min; i <= param.max; i++) {
                        range.push(i);
                    }
                } else {
                    // Otherwise, distribute evenly
                    const step = Math.max(1, Math.floor((param.max - param.min) / 4));
                    for (let i = param.min; i <= param.max; i += step) {
                        range.push(i);
                    }
                    // Make sure max is included
                    if (range[range.length - 1] !== param.max) {
                        range.push(param.max);
                    }
                }
                paramRanges[param.id] = range;
            } else {
                // For smaller decimal ranges, create a few points
                paramRanges[param.id] = [
                    param.min,
                    param.min + (param.max - param.min) / 3,
                    param.min + 2 * (param.max - param.min) / 3,
                    param.max
                ].map(v => Math.round(v * 100) / 100);
            }
        } else if (param.type === 'boolean' || param.type === 'bool') {
            // For boolean parameters, try both values
            paramRanges[param.id] = [true, false];
        } else if (param.type === 'select' && param.options) {
            // For select parameters, try all options
            paramRanges[param.id] = param.options.map(opt => opt.value || opt);
        }
    });
    
    const hasRanges = Object.keys(paramRanges).length > 0;
    console.log(`[Strategy Comparison] Generated ranges for ${strategyId}:`, hasRanges ? paramRanges : "None");
    
    return hasRanges ? paramRanges : null;
}

/**
 * Generate HTML for parameters comparison table showing original vs. optimized values
 * @param {Object} optimizedParams - The optimized parameters for each strategy
 * @param {Object} originalParams - The original parameters for each strategy
 * @param {Object} paramChanges - Parameter changes for each strategy
 * @returns {String} HTML for parameters comparison table
 */
function generateParametersComparisonHtml(optimizedParams, originalParams, paramChanges) {
    if (!optimizedParams) return '<p>No parameters data available</p>';

    const strategyIds = Object.keys(optimizedParams);
    if (strategyIds.length === 0) return '<p>No strategies to compare</p>';

    // Get all parameter names across all strategies
    const allParamNames = new Set();
    strategyIds.forEach(strategyId => {
        const params = optimizedParams[strategyId] || {};
        Object.keys(params).forEach(paramName => allParamNames.add(paramName));
    });

    const paramNames = Array.from(allParamNames);
    if (paramNames.length === 0) return '<p>No parameters to compare</p>';

    // Start building the table
    let html = `
        <div class="table-responsive">
            <table class="table table-bordered table-hover">
                <thead>
                    <tr>
                        <th>Parameter</th>
                        ${strategyIds.map(id => `<th colspan="2">${id}</th>`).join('')}
                    </tr>
                    <tr>
                        <th></th>
                        ${strategyIds.map(() => `<th>Original</th><th>Optimized</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
    `;

    // Add rows for each parameter
    paramNames.forEach(paramName => {
        // Start the row
        html += `<tr><td>${paramName}</td>`;
        
        // Add cells for each strategy
        strategyIds.forEach(strategyId => {
            const optimizedValue = optimizedParams[strategyId]?.[paramName];
            const originalValue = originalParams[strategyId]?.[paramName];
            
            // Check if this parameter was changed during optimization
            const isChanged = paramChanges[strategyId]?.[paramName] !== undefined;
            const changeClass = isChanged ? 'table-success' : '';
            
            // Format the values
            const formattedOriginal = formatParameterValue(originalValue);
            const formattedOptimized = formatParameterValue(optimizedValue);
            
            html += `<td>${formattedOriginal}</td><td class="${changeClass}">${formattedOptimized}</td>`;
        });
        
        // End the row
        html += '</tr>';
    });

    // Close the table
    html += `
                </tbody>
            </table>
        </div>
        <div class="small text-muted mt-2">
            <span class="badge bg-success">Highlighted</span> parameters were improved through optimization.
        </div>
    `;

    return html;
}

/**
 * Format a parameter value for display
 * @param {any} value - The parameter value
 * @returns {String} Formatted parameter value
 */
function formatParameterValue(value) {
    if (value === undefined || value === null) return '-';
    if (typeof value === 'boolean') return value ? 'true' : 'false';
    if (typeof value === 'number') return value.toLocaleString(undefined, {
        maximumFractionDigits: 4
    });
    return String(value);
} 