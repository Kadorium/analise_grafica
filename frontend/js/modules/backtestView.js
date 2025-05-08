// frontend/js/modules/backtestView.js

// Import dependencies
import { runBacktest as runBacktestApi } from '../utils/api.js';
import { showError, showLoading, showSuccessMessage, showGlobalLoader, hideGlobalLoader } from '../utils/ui.js';
import { formatDate, formatNumber } from '../utils/formatters.js';
import { appState } from '../utils/state.js';

// DOM references
const backtestForm = document.getElementById('backtest-form');
const backtestResultsContainer = document.getElementById('backtest-results');
const backtestSummaryContainer = document.getElementById('backtest-summary');
const backtestDebugContainer = document.getElementById('backtest-debug');
const backtestChartsContainer = document.getElementById('backtest-charts');

// Debug backtest results (display raw data for troubleshooting)
export function debugBacktestResults(results) {
    if (!backtestDebugContainer) return;
    
    // Format the results as JSON with indentation
    const formattedJson = JSON.stringify(results, null, 2);
    
    // Display the formatted JSON
    backtestDebugContainer.innerHTML = `
        <div class="card">
            <div class="card-header bg-light">
                <h5 class="mb-0">Debug Data</h5>
            </div>
            <div class="card-body">
                <pre class="code-block">${formattedJson}</pre>
            </div>
        </div>
    `;
}

// Run backtest with current settings
export async function runBacktest(params = {}) {
    if (!appState.dataProcessed) {
        showError('Please upload and process data first');
        return null;
    }
    
    try {
        showGlobalLoader('Running backtest...');
        
        // Combine parameters with existing strategy parameters if they exist
        const requestParams = { ...params };
        
        // Make sure we have the strategy from state if not provided
        if (!requestParams.strategy && appState.selectedStrategy) {
            requestParams.strategy = appState.selectedStrategy;
        }
        
        // Add strategy parameters from appState
        if (appState.strategyParameters && Object.keys(appState.strategyParameters).length > 0) {
            // Only use appState parameters if not provided directly
            if (!requestParams.parameters || Object.keys(requestParams.parameters).length === 0) {
                requestParams.parameters = JSON.parse(JSON.stringify(appState.strategyParameters));
            }
            console.log('Using strategy parameters:', requestParams.parameters);
        } else {
            console.warn('No strategy parameters found in appState');
        }
        
        console.log('Running backtest with parameters:', requestParams);
        
        // Run backtest
        const response = await runBacktestApi(requestParams);
        
        if (response.success) {
            showSuccessMessage('Backtest completed successfully');
            
            // Display results
            displayBacktestResults(response.results);
            
            return response.results;
        } else {
            throw new Error(response.error || 'Error running backtest');
        }
    } catch (error) {
        showError(error.message || 'Failed to run backtest');
        return null;
    } finally {
        hideGlobalLoader();
    }
}

// Display backtest results
export function displayBacktestResults(results) {
    if (!backtestResultsContainer || !results) return;
    
    // Show results container
    backtestResultsContainer.style.display = 'block';
    
    // Display summary metrics
    if (backtestSummaryContainer && results.metrics) {
        displayBacktestSummary(results.metrics);
    }
    
    // Display charts
    if (backtestChartsContainer && results.charts) {
        backtestChartsContainer.innerHTML = results.charts;
    }
    
    // Debug data if needed
    if (appState.debugMode && results) {
        debugBacktestResults(results);
    }
}

// Display backtest summary metrics
function displayBacktestSummary(metrics) {
    if (!backtestSummaryContainer || !metrics) return;
    
    // Create a table with metrics
    let tableHtml = `
        <div class="table-responsive">
            <table class="table table-bordered table-striped">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Add each metric as a row
    for (const [key, value] of Object.entries(metrics)) {
        const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        let formattedValue = value;
        
        // Format values based on type
        if (typeof value === 'number') {
            if (key.includes('percent') || key.includes('rate')) {
                formattedValue = formatNumber(value, 2) + '%';
            } else if (key.includes('ratio')) {
                formattedValue = formatNumber(value, 2);
            } else {
                formattedValue = formatNumber(value);
            }
        } else if (key.includes('date')) {
            formattedValue = formatDate(value);
        }
        
        tableHtml += `
            <tr>
                <td>${formattedKey}</td>
                <td>${formattedValue}</td>
            </tr>
        `;
    }
    
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    backtestSummaryContainer.innerHTML = tableHtml;
}

// Initialize backtest component
export function initializeBacktestView() {
    // Initialize backtest form
    if (backtestForm) {
        // Get the run backtest button
        const runBacktestBtn = document.querySelector('#backtest-form button[type="submit"]');
        if (runBacktestBtn) {
            runBacktestBtn.id = 'run-backtest-form-btn';
        }
        
        backtestForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Get form values
            const formData = new FormData(backtestForm);
            const params = {};
            
            // Convert form data to params object
            for (const [key, value] of formData.entries()) {
                // Convert numeric values
                if (!isNaN(value) && value !== '') {
                    params[key] = parseFloat(value);
                } else {
                    params[key] = value;
                }
            }
            
            // Add selected strategy
            if (appState.selectedStrategy) {
                params.strategy = appState.selectedStrategy;
            }
            
            // Add strategy parameters from appState 
            if (appState.strategyParameters && Object.keys(appState.strategyParameters).length > 0) {
                params.parameters = JSON.parse(JSON.stringify(appState.strategyParameters));
                console.log('Using strategy parameters from appState:', params.parameters);
            } else {
                console.warn('No strategy parameters found in appState');
            }
            
            // Run backtest with form params
            await runBacktest(params);
        });
    }
}
