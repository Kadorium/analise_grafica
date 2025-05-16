// frontend/js/modules/strategySelector.js

// Import dependencies
import { fetchAvailableStrategies, fetchStrategyParameters, runBacktest as runBacktestApi } from '../utils/api.js';
import { showError, showLoading, showSuccessMessage, showGlobalLoader, hideGlobalLoader } from '../utils/ui.js';
import { formatParamName, formatDate, formatNumber } from '../utils/formatters.js';
import { appState } from '../utils/state.js';
import { getStrategyConfig, getStrategyDescription, getStrategyDefaultParams } from '../utils/strategies-config.js';

// DOM references
const strategySelect = document.getElementById('strategy-select');
const strategyTypeSelect = document.getElementById('strategy-type');
const strategyParametersContainer = document.getElementById('strategy-parameters');
const optimizationStrategySelect = document.getElementById('optimization-strategy');
const strategyDescriptionContainer = document.getElementById('strategy-description');
const updateStrategyBtn = document.getElementById('update-strategy-btn');
const backtestForm = document.getElementById('backtest-form');
const runBacktestBtn = document.getElementById('run-backtest-btn');
const initialCapitalInput = document.getElementById('initial-capital');
const commissionInput = document.getElementById('commission');
const backtestStartDateInput = document.getElementById('backtest-start-date');
const backtestEndDateInput = document.getElementById('backtest-end-date');

// Make loadStrategyParameters available globally for use in other modules
window.loadStrategyParameters = loadStrategyParameters;

// Build strategy selection dropdowns
export async function buildStrategySelections() {
    try {
        // Show loading state
        if (strategySelect) {
            showLoading(strategySelect.parentElement);
        }
        
        // Fetch available strategies
        const response = await fetchAvailableStrategies();
        
        if (!response.strategies || !response.strategies.length) {
            throw new Error('No strategies available');
        }
        
        const strategies = response.strategies;
        
        // Store available strategies in app state
        appState.availableStrategies = strategies;
        
        // Function to populate a select element with strategies
        const populateSelect = (select) => {
            if (!select) return;
            
            // Clear existing options
            select.innerHTML = '';
            
            // Add each strategy as an option
            strategies.forEach(strategy => {
                const option = document.createElement('option');
                option.value = strategy.id || strategy.type || strategy;
                option.textContent = strategy.name || formatParamName(strategy);
                select.appendChild(option);
            });
            
            // Trigger change event to load parameters for the first strategy
            if (select.options.length > 0) {
                select.value = strategies[0].id || strategies[0].type || strategies[0];
                select.dispatchEvent(new Event('change'));
            }
        };
        
        // Populate all strategy selects
        populateSelect(strategySelect);
        populateSelect(optimizationStrategySelect);
        populateSelect(strategyTypeSelect);
        
        // Set default selected strategy in app state
        if (strategies.length > 0) {
            appState.setSelectedStrategy(strategies[0].id || strategies[0].type || strategies[0]);
        }
        
        return strategies;
    } catch (error) {
        showError(error.message || 'Error loading strategies');
        console.error('Error building strategy selections:', error);
        return [];
    }
}

// Load strategy parameters for a specific strategy
export async function loadStrategyParameters(strategyType = null) {
    // Use the provided strategyType or get it from the strategy select
    const strategy = strategyType || (strategyTypeSelect ? strategyTypeSelect.value : (strategySelect ? strategySelect.value : appState.selectedStrategy));
    
    if (!strategy) {
        console.error('No strategy selected');
        return null;
    }
    
    try {
        // Show loading state
        if (strategyParametersContainer) {
            showLoading(strategyParametersContainer);
        }
        
        console.log('Loading parameters for strategy:', strategy);
        
        // Get parameters either from the config or API
        let parameters;
        const strategyConfig = getStrategyConfig(strategy);
        
        if (strategyConfig) {
            // Use the predefined parameters from our configuration
            parameters = getStrategyDefaultParams(strategy);
            console.log('Using predefined parameters for', strategy, parameters);
        } else {
            // Fetch parameters from API (legacy approach)
            const response = await fetchStrategyParameters(strategy);
            
            // Extract parameters from response
            if (response.parameters) {
                parameters = response.parameters;
            } else if (response.data && response.data.parameters) {
                parameters = response.data.parameters;
            } else {
                // For direct parameters object
                parameters = response;
            }
        }
        
        // Check if we have parameters
        if (!parameters || Object.keys(parameters).length === 0) {
            throw new Error('No parameters available for this strategy');
        }
        
        console.log('Strategy parameters loaded:', parameters);
        
        // Update strategy description if container exists
        if (strategyDescriptionContainer) {
            updateStrategyDescription(strategy);
        }
        
        // Save parameters to app state
        appState.setStrategyParameters(parameters);
        
        // Update the UI with parameters
        updateStrategyParameters(parameters, strategy);
        
        return parameters;
    } catch (error) {
        showError(error.message || `Error loading parameters for ${strategy}`);
        console.error('Error loading strategy parameters:', error);
        
        // Clear parameters container
        if (strategyParametersContainer) {
            strategyParametersContainer.innerHTML = '<div class="alert alert-danger">Error loading parameters</div>';
        }
        
        return null;
    }
}

// Update the strategy description based on the strategy type
function updateStrategyDescription(strategyType) {
    if (!strategyDescriptionContainer) return;
    
    // Try to get the description from our configuration first
    const description = getStrategyDescription(strategyType);
    
    if (description) {
        strategyDescriptionContainer.innerHTML = `<p>${description}</p>`;
        return;
    }
    
    // Fallback to hardcoded descriptions for legacy strategies
    let legacyDescription = '';
    
    switch(strategyType) {
        case 'trend_following':
            legacyDescription = 'Buys when fast MA crosses above slow MA (golden cross) and sells when fast MA crosses below slow MA (death cross).';
            break;
        case 'mean_reversion':
            legacyDescription = 'Buys when RSI is below oversold level and sells when RSI is above overbought level. Also exits positions when RSI crosses the middle level.';
            break;
        case 'breakout':
            legacyDescription = 'Buys when price breaks out above recent highs with increased volume. Uses volatility-based exit strategies.';
            break;
        default:
            legacyDescription = 'Select a strategy type to see its description.';
    }
    
    strategyDescriptionContainer.innerHTML = `<p>${legacyDescription}</p>`;
}

// Update the strategy parameters UI
export function updateStrategyParameters(parameters, strategyType) {
    if (!strategyParametersContainer) return;
    
    // Clear existing parameters
    strategyParametersContainer.innerHTML = '';
    
    if (!parameters || Object.keys(parameters).length === 0) {
        strategyParametersContainer.innerHTML = '<div class="alert alert-info">No parameters available for this strategy</div>';
        return;
    }
    
    // Ensure parameters are stored in app state
    appState.strategyParameters = parameters;
    
    // Create a nested form for parameters
    const form = document.createElement('div');
    form.className = 'nested-form';
    
    // For each parameter, create an input field
    Object.entries(parameters).forEach(([param, value]) => {
        // Format the parameter name for display
        const displayName = formatParamName(param);
        
        // Create a form group
        const formGroup = document.createElement('div');
        formGroup.className = 'mb-3';
        
        // Add a label
        const label = document.createElement('label');
        label.className = 'form-label';
        label.htmlFor = `param-${param}`;
        label.textContent = displayName;
        formGroup.appendChild(label);
        
        // Determine the type of parameter
        const paramType = typeof value;
        
        // Create the input based on parameter type
        let input;
        
        if (paramType === 'boolean') {
            // For boolean values, create a checkbox
            input = document.createElement('input');
            input.type = 'checkbox';
            input.className = 'form-check-input ms-2';
            input.id = `param-${param}`;
            input.checked = value;
            input.dataset.paramName = param;
            
            // Replace the default form-group with a form-check
            formGroup.className = 'form-check mb-3';
            label.className = 'form-check-label';
            label.htmlFor = `param-${param}`;
            
            // Rearrange to put checkbox first
            formGroup.innerHTML = '';
            formGroup.appendChild(input);
            formGroup.appendChild(label);
        } else if (Array.isArray(value) || paramType === 'object') {
            // For arrays or objects, create a textarea
            input = document.createElement('textarea');
            input.className = 'form-control';
            input.id = `param-${param}`;
            input.value = JSON.stringify(value, null, 2);
            input.rows = 3;
            input.dataset.paramName = param;
            input.dataset.paramType = 'json';
        } else if (paramType === 'number') {
            // For numeric values, create a number input
            input = document.createElement('input');
            input.type = 'number';
            input.className = 'form-control';
            input.id = `param-${param}`;
            input.value = value;
            input.step = Number.isInteger(value) ? '1' : '0.01';
            input.dataset.paramName = param;
        } else {
            // For everything else, create a text input
            input = document.createElement('input');
            input.type = 'text';
            input.className = 'form-control';
            input.id = `param-${param}`;
            input.value = value;
            input.dataset.paramName = param;
        }
        
        // Only append input if it wasn't already appended (e.g., for checkboxes)
        if (input.parentNode !== formGroup) {
            formGroup.appendChild(input);
        }
        
        // Add the form group to the form
        form.appendChild(formGroup);
    });
    
    // Add the form to the parameters container
    strategyParametersContainer.appendChild(form);
}

// Get strategy parameters from the UI
export function getStrategyParameters() {
    const parameters = {};
    
    // If we don't have a parameters container, use the ones from state
    if (!strategyParametersContainer) {
        return appState.strategyParameters || {};
    }
    
    // Get all parameter inputs
    const inputs = strategyParametersContainer.querySelectorAll('input, textarea, select');
    
    // Process each input
    inputs.forEach(input => {
        const paramName = input.dataset.paramName;
        if (!paramName) return;
        
        let value;
        
        if (input.type === 'checkbox') {
            value = input.checked;
        } else if (input.dataset.paramType === 'json') {
            try {
                value = JSON.parse(input.value);
            } catch (e) {
                console.error('Error parsing JSON value for', paramName, e);
                value = null;
            }
        } else if (input.type === 'number' || input.dataset.paramType === 'number') {
            value = parseFloat(input.value);
            if (Number.isNaN(value)) value = 0;
        } else {
            value = input.value;
        }
        
        parameters[paramName] = value;
    });
    
    return parameters;
}

// Run backtest with current settings
export async function runBacktest(params = {}) {
    if (!appState.dataProcessed) {
        showError('Please upload and process data first');
        return null;
    }
    
    try {
        showGlobalLoader('Running backtest...');
        
        // Create request parameters
        const requestParams = { ...params };
        
        // Get the strategy type
        const strategyType = strategyTypeSelect ? strategyTypeSelect.value : appState.selectedStrategy;
        requestParams.strategy_type = strategyType;
        
        // Get strategy parameters from UI
        const parameters = getStrategyParameters();
        requestParams.parameters = parameters;
        
        // Create the backtesting configuration
        const backtestConfig = {
            initial_capital: initialCapitalInput ? parseFloat(initialCapitalInput.value) : 10000.0,
            commission: commissionInput ? parseFloat(commissionInput.value) : 0.001
        };
        
        // Add date range if provided
        if (backtestStartDateInput && backtestStartDateInput.value) {
            backtestConfig.start_date = backtestStartDateInput.value;
        }
        
        if (backtestEndDateInput && backtestEndDateInput.value) {
            backtestConfig.end_date = backtestEndDateInput.value;
        }
        
        console.log('Running backtest with parameters:', {
            strategy_config: {
                strategy_type: requestParams.strategy_type,
                parameters: requestParams.parameters
            },
            backtest_config: backtestConfig
        });
        
        // Run backtest
        const response = await runBacktestApi({
            strategy_config: {
                strategy_type: requestParams.strategy_type,
                parameters: requestParams.parameters
            },
            backtest_config: backtestConfig
        });
        
        if (response.success) {
            showSuccessMessage('Backtest completed successfully');
            
            // Display results
            displayBacktestResults(response);
            
            return response;
        } else {
            throw new Error(response.message || 'Error running backtest');
        }
    } catch (error) {
        showError(error.message || 'Failed to run backtest');
        console.error('Backtest error:', error);
        return null;
    } finally {
        hideGlobalLoader();
    }
}

// Display backtest results
export function displayBacktestResults(results) {
    const backtestResultsContainer = document.getElementById('backtest-results');
    const equityCurveContainer = document.getElementById('equity-curve-container');

    if (!backtestResultsContainer || !results) {
        console.error('Backtest results container not found or no results data');
        return;
    }
    
    console.log('Displaying backtest results:', results);
    
    // Extract performance metrics
    const metrics = results.performance_metrics || {};
    
    // Create a formatted metrics summary
    let metricsHtml = '<div class="row">';
    
    // Format key metrics for display
    const keyMetrics = [
        { name: 'Total Return', value: metrics.total_return, format: 'percent' },
        { name: 'Annual Return', value: metrics.annual_return, format: 'percent' },
        { name: 'Sharpe Ratio', value: metrics.sharpe_ratio, format: 'decimal' },
        { name: 'Max Drawdown', value: metrics.max_drawdown, format: 'percent' },
        { name: 'Win Rate', value: metrics.win_rate, format: 'percent' },
        { name: 'Profit Factor', value: metrics.profit_factor, format: 'decimal' }
    ];
    
    // Create a card for each key metric
    keyMetrics.forEach(metric => {
        if (metric.value !== undefined) {
            let formattedValue;
            
            if (metric.format === 'percent') {
                formattedValue = (metric.value * 100).toFixed(2) + '%';
            } else if (metric.format === 'decimal') {
                formattedValue = parseFloat(metric.value).toFixed(2);
            } else {
                formattedValue = metric.value.toString();
            }
            
            metricsHtml += `
                <div class="col-md-4 mb-3">
                    <div class="card h-100">
                        <div class="card-body text-center">
                            <h5 class="card-title">${metric.name}</h5>
                            <p class="card-text display-6 ${metric.value < 0 ? 'text-danger' : 'text-success'}">
                                ${formattedValue}
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }
    });
    
    metricsHtml += '</div>';
    
    // Add trades table if available
    if (results.signals && results.signals.length) {
        metricsHtml += `
            <div class="mt-4">
                <h4>Trade History</h4>
                <div class="table-responsive">
                    <table class="table table-striped table-sm">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Action</th>
                                <th>Price</th>
                                <th>Return</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        // Add up to 10 most recent trades for display
        const tradesToShow = results.signals.slice(-10);
        
        tradesToShow.forEach(trade => {
            const actionClass = trade.signal === 'buy' ? 'text-success' : (trade.signal === 'sell' ? 'text-danger' : '');
            
            metricsHtml += `
                <tr>
                    <td>${trade.date}</td>
                    <td class="${actionClass}">${trade.signal.toUpperCase()}</td>
                    <td>${trade.close ? trade.close.toFixed(2) : 'N/A'}</td>
                    <td>${trade.return ? (trade.return * 100).toFixed(2) + '%' : 'N/A'}</td>
                </tr>
            `;
        });
        
        metricsHtml += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    // Display results
    backtestResultsContainer.innerHTML = metricsHtml;
    
    // Display equity curve if available
    if (results.chart && equityCurveContainer) {
        equityCurveContainer.innerHTML = `<img src="data:image/png;base64,${results.chart}" class="img-fluid" alt="Equity Curve">`;
        equityCurveContainer.style.display = 'block';
    }
}

// Initialize the strategy selector and backtest form
export function initializeStrategySelector() {
    // Build the strategy selections
    buildStrategySelections().then(() => {
        console.log('Strategy selections built successfully');
    });
    
    // Event listeners
    if (strategyTypeSelect) {
        strategyTypeSelect.addEventListener('change', async () => {
            const selectedStrategy = strategyTypeSelect.value;
            console.log('Strategy changed to:', selectedStrategy);
            
            // Update app state
            appState.setSelectedStrategy(selectedStrategy);
            
            // Load parameters for the selected strategy
            await loadStrategyParameters(selectedStrategy);
        });
    }
    
    if (updateStrategyBtn) {
        updateStrategyBtn.addEventListener('click', () => {
            // Get parameters from UI
            const parameters = getStrategyParameters();
            
            // Update app state
            appState.setStrategyParameters(parameters);
            
            // Show confirmation
            showSuccessMessage('Strategy parameters updated');
        });
    }
    
    if (backtestForm) {
        backtestForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Run backtest
            await runBacktest();
        });
    }
    
    // Set default date range for backtest
    if (backtestStartDateInput && backtestEndDateInput && appState.dateRange) {
        backtestStartDateInput.value = appState.dateRange.startDate || '';
        backtestEndDateInput.value = appState.dateRange.endDate || '';
    }
}

// Clean up function to remove any event listeners
export function cleanup() {
    if (strategyTypeSelect) {
        strategyTypeSelect.removeEventListener('change', () => {});
    }
    
    if (updateStrategyBtn) {
        updateStrategyBtn.removeEventListener('click', () => {});
    }
    
    if (backtestForm) {
        backtestForm.removeEventListener('submit', () => {});
    }
}
