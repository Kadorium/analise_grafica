// frontend/js/modules/strategySelector.js

// Import dependencies
import { fetchAvailableStrategies, fetchStrategyParameters } from '../utils/api.js';
import { showError, showLoading, showGlobalLoader, hideGlobalLoader } from '../utils/ui.js';
import { formatParamName } from '../utils/formatters.js';
import { appState } from '../utils/state.js';

// DOM references
const strategySelect = document.getElementById('strategy-select');
const strategyTypeSelect = document.getElementById('strategy-type');
const strategyParametersContainer = document.getElementById('strategy-parameters');
const backtestStrategySelect = document.getElementById('backtest-strategy');
const optimizationStrategySelect = document.getElementById('optimization-strategy');
const strategyDescriptionContainer = document.getElementById('strategy-description');
const updateStrategyBtn = document.getElementById('update-strategy-btn');

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
        populateSelect(backtestStrategySelect);
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
        
        // Fetch strategy parameters
        const response = await fetchStrategyParameters(strategy);
        
        // Update strategy description if container exists
        if (strategyDescriptionContainer) {
            updateStrategyDescription(strategy);
        }
        
        // Extract parameters from response
        let parameters;
        if (response.parameters) {
            parameters = response.parameters;
        } else if (response.data && response.data.parameters) {
            parameters = response.data.parameters;
        } else {
            // For direct parameters object
            parameters = response;
        }
        
        // Check if we have parameters
        if (!parameters || Object.keys(parameters).length === 0) {
            throw new Error('No parameters available for this strategy');
        }
        
        console.log('Strategy parameters loaded:', parameters);
        
        // Save parameters to app state
        appState.setStrategyParameters(parameters);
        
        // Update the UI with parameters
        updateStrategyParameters(parameters);
        
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
    
    let description = '';
    
    switch(strategyType) {
        case 'trend_following':
            description = '<p>Buys when fast MA crosses above slow MA (golden cross) and sells when fast MA crosses below slow MA (death cross).</p>';
            break;
        case 'mean_reversion':
            description = '<p>Buys when RSI is below oversold level and sells when RSI is above overbought level. Also exits positions when RSI crosses the middle level.</p>';
            break;
        case 'breakout':
            description = '<p>Buys when price breaks out above recent highs with increased volume. Uses volatility-based exit strategies.</p>';
            break;
        default:
            description = '<p>Select a strategy type to see its description.</p>';
    }
    
    strategyDescriptionContainer.innerHTML = description;
}

// Update the strategy parameters UI
export function updateStrategyParameters(parameters) {
    if (!strategyParametersContainer) return;
    
    // Clear existing parameters
    strategyParametersContainer.innerHTML = '';
    
    if (!parameters || Object.keys(parameters).length === 0) {
        strategyParametersContainer.innerHTML = '<div class="alert alert-info">No parameters available for this strategy</div>';
        return;
    }
    
    // Ensure parameters are stored in app state
    appState.setStrategyParameters(parameters);
    
    // Create form elements for each parameter
    Object.entries(parameters).forEach(([paramName, paramConfig]) => {
        const formGroup = document.createElement('div');
        formGroup.className = 'mb-3';
        
        // Create label
        const label = document.createElement('label');
        label.className = 'form-label';
        label.textContent = formatParamName(paramName);
        
        if (typeof paramConfig === 'object' && paramConfig.description) {
            label.title = paramConfig.description;
            label.classList.add('text-info');
        }
        
        // Determine default value and input type
        let defaultValue, min, max, step;
        let inputType = 'number';
        
        if (typeof paramConfig === 'object') {
            defaultValue = paramConfig.default !== undefined ? paramConfig.default : '';
            min = paramConfig.min !== undefined ? paramConfig.min : '';
            max = paramConfig.max !== undefined ? paramConfig.max : '';
            step = paramConfig.step !== undefined ? paramConfig.step : 'any';
            
            if (paramConfig.type === 'boolean') {
                inputType = 'checkbox';
            } else if (paramConfig.type === 'select' && paramConfig.options) {
                inputType = 'select';
            }
        } else {
            defaultValue = paramConfig;
        }
        
        // Create input element
        let input;
        
        if (inputType === 'select') {
            input = document.createElement('select');
            input.className = 'form-select';
            
            // Add options
            if (paramConfig.options) {
                paramConfig.options.forEach(option => {
                    const optionEl = document.createElement('option');
                    optionEl.value = option.value || option;
                    optionEl.textContent = option.label || option;
                    
                    if (option.value === defaultValue || option === defaultValue) {
                        optionEl.selected = true;
                    }
                    
                    input.appendChild(optionEl);
                });
            }
        } else if (inputType === 'checkbox') {
            input = document.createElement('input');
            input.type = 'checkbox';
            input.className = 'form-check-input';
            input.checked = defaultValue === true;
            
            // Use form-check div for checkbox
            formGroup.className = 'form-check mb-3';
            label.className = 'form-check-label';
            label.style.marginLeft = '10px';
        } else {
            input = document.createElement('input');
            input.type = inputType;
            input.className = 'form-control';
            input.value = defaultValue;
            
            if (inputType === 'number') {
                if (min !== '') input.min = min;
                if (max !== '') input.max = max;
                if (step !== '') input.step = step;
            }
        }
        
        input.id = `param-${paramName}`;
        input.name = paramName;
        
        // Add data attribute to store parameter metadata
        input.dataset.paramType = typeof defaultValue;
        
        // Add elements to form group
        if (inputType === 'checkbox') {
            formGroup.appendChild(input);
            formGroup.appendChild(label);
        } else {
            formGroup.appendChild(label);
            formGroup.appendChild(input);
        }
        
        // Add form group to container
        strategyParametersContainer.appendChild(formGroup);
    });
    
    // Add run backtest button if it doesn't exist
    if (!document.getElementById('run-backtest-btn')) {
        const runBacktestBtn = document.createElement('button');
        runBacktestBtn.type = 'button';
        runBacktestBtn.className = 'btn btn-primary';
        runBacktestBtn.id = 'run-backtest-btn';
        runBacktestBtn.textContent = 'Run Backtest';
        
        strategyParametersContainer.appendChild(runBacktestBtn);
        
        // Add event listener for the run backtest button
        runBacktestBtn.addEventListener('click', function() {
            // Get strategy parameters
            const parameters = getStrategyParameters();
            
            // Store parameters in app state for use in backtest
            appState.strategyParameters = parameters;
            try {
                sessionStorage.setItem('strategyParameters', JSON.stringify(parameters));
            } catch (e) {
                console.error('Error saving strategy parameters:', e);
            }
            
            // Get the active tab
            const backtestTab = document.getElementById('backtest-tab');
            if (backtestTab) {
                // Click the backtest tab to navigate to it
                backtestTab.click();
                
                // Update the backtest strategy select to match the current strategy
                const backtestStrategySelect = document.getElementById('backtest-strategy');
                if (backtestStrategySelect && strategyTypeSelect) {
                    backtestStrategySelect.value = strategyTypeSelect.value;
                    backtestStrategySelect.dispatchEvent(new Event('change'));
                }
                
                // Optionally, click the run backtest button in the backtest tab
                setTimeout(() => {
                    const runBacktestBtnInTab = document.getElementById('run-backtest-form-btn');
                    if (runBacktestBtnInTab) {
                        runBacktestBtnInTab.click();
                    }
                }, 300);
            }
        });
    }
}

// Get strategy parameters from the form
export function getStrategyParameters() {
    if (!strategyParametersContainer) {
        return {};
    }
    
    const parameters = {};
    const inputs = strategyParametersContainer.querySelectorAll('input, select');
    
    inputs.forEach(input => {
        if (input.id && input.id.startsWith('param-')) {
            const paramName = input.id.replace('param-', '');
            
            if (input.type === 'checkbox') {
                parameters[paramName] = input.checked;
            } else if (input.type === 'number') {
                parameters[paramName] = parseFloat(input.value);
            } else {
                parameters[paramName] = input.value;
            }
        }
    });
    
    // Update app state with the current parameters
    appState.setStrategyParameters(parameters);
    
    return parameters;
}

// Initialize strategy selector
export function initializeStrategySelector() {
    console.log('Initializing strategy selector');
    
    // Build strategy dropdowns
    buildStrategySelections();
    
    // Add event listener to strategy type select
    if (strategyTypeSelect) {
        strategyTypeSelect.addEventListener('change', function() {
            const selectedStrategy = this.value;
            
            if (selectedStrategy) {
                appState.setSelectedStrategy(selectedStrategy);
                loadStrategyParameters(selectedStrategy);
            }
        });
    }
    
    // Add event listener to strategy select
    if (strategySelect) {
        strategySelect.addEventListener('change', function() {
            const selectedStrategy = this.value;
            
            if (selectedStrategy) {
                appState.setSelectedStrategy(selectedStrategy);
                loadStrategyParameters(selectedStrategy);
            }
        });
    }
    
    // Add event listeners to other strategy selects
    if (backtestStrategySelect) {
        backtestStrategySelect.addEventListener('change', function() {
            const selectedStrategy = this.value;
            if (selectedStrategy) {
                appState.setSelectedStrategy(selectedStrategy);
                // Load parameters when backtest strategy changes
                loadStrategyParameters(selectedStrategy);
            }
        });
    }
    
    if (optimizationStrategySelect) {
        optimizationStrategySelect.addEventListener('change', function() {
            // Only update app state, don't load parameters (handled by the optimization module)
            appState.setSelectedStrategy(this.value);
        });
    }
    
    // Add event listener to update strategy button
    if (updateStrategyBtn) {
        updateStrategyBtn.addEventListener('click', function() {
            // Get strategy parameters
            const parameters = getStrategyParameters();
            
            // Update app state with selected strategy and parameters
            if (strategyTypeSelect) {
                appState.setSelectedStrategy(strategyTypeSelect.value);
            }
            
            // Use direct assignment instead of method call
            appState.strategyParameters = parameters;
            try {
                sessionStorage.setItem('strategyParameters', JSON.stringify(parameters));
            } catch (e) {
                console.error('Error saving strategy parameters:', e);
            }
            
            // Navigate to the backtest tab
            const backtestTab = document.getElementById('backtest-tab');
            if (backtestTab) {
                // Click the backtest tab to navigate to it
                backtestTab.click();
                
                // Update the backtest strategy select to match the current strategy
                if (backtestStrategySelect && strategyTypeSelect) {
                    backtestStrategySelect.value = strategyTypeSelect.value;
                    backtestStrategySelect.dispatchEvent(new Event('change'));
                }
                
                // Give UI time to update, then automatically run backtest
                setTimeout(() => {
                    const runBacktestBtn = document.getElementById('run-backtest-form-btn');
                    if (runBacktestBtn) {
                        runBacktestBtn.click();
                    }
                }, 300);
            }
        });
    }
    
    // Initial load of parameters for the default strategy
    if (strategyTypeSelect && strategyTypeSelect.value) {
        loadStrategyParameters(strategyTypeSelect.value);
    } else if (strategySelect && strategySelect.value) {
        loadStrategyParameters(strategySelect.value);
    }
}
