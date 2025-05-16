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
        
        console.log('Running comparison with strategies:', strategyConfigs);
        
        // Get backtest configuration
        const backtestConfig = {
            initial_capital: parseFloat(document.getElementById('initial-capital')?.value || 10000),
            commission: parseFloat(document.getElementById('commission')?.value || 0.001)
        };
        
        // Check if optimization is requested
        const shouldOptimize = document.getElementById('optimize-comparison-checkbox')?.checked || false;
        
        // Run the comparison
        const results = await compareStrategies(
            strategyConfigs, 
            backtestConfig,
            shouldOptimize,
            'sharpe_ratio' // Default optimization metric
        );
        
        if (results && results.success) {
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
        parametersContainer.innerHTML = generateParametersTableHtml(results.parameters);
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
        optimizationAlert.innerHTML = `
            <i class="bi bi-info-circle"></i> 
            Parameters were optimized for ${results.optimization.metric}.
        `;
        
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
    if (!shouldOptimize) return null;
    
    // Get strategy configuration
    const strategyConfig = getStrategyConfig(strategyId);
    if (!strategyConfig || !strategyConfig.params) return null;
    
    // Create parameter ranges
    const paramRanges = {};
    
    strategyConfig.params.forEach(param => {
        // Only add ranges for numeric parameters
        if (param.type === 'number' && param.min !== undefined && param.max !== undefined) {
            // Create a range with 5 steps between min and max
            const step = (param.max - param.min) / 4;
            const range = [];
            
            for (let i = 0; i <= 4; i++) {
                range.push(param.min + step * i);
            }
            
            paramRanges[param.id] = range;
        }
    });
    
    return Object.keys(paramRanges).length > 0 ? paramRanges : null;
} 