// frontend/js/modules/strategySelector.js

// Import dependencies
import { fetchAvailableStrategies, fetchStrategyParameters } from '../utils/api.js';
import { showError, showLoading } from '../utils/ui.js';
import { formatParamName } from '../utils/formatters.js';
import { appState } from '../utils/state.js';

// DOM references
const strategySelect = document.getElementById('strategy-select');
const strategyParametersContainer = document.getElementById('strategy-parameters');
const backtestStrategySelect = document.getElementById('backtest-strategy');
const optimizationStrategySelect = document.getElementById('optimization-strategy');

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
        
        // Function to populate a select element with strategies
        const populateSelect = (select) => {
            if (!select) return;
            
            // Clear existing options
            select.innerHTML = '';
            
            // Add each strategy as an option
            strategies.forEach(strategy => {
                const option = document.createElement('option');
                option.value = strategy.id || strategy;
                option.textContent = strategy.name || formatParamName(strategy);
                select.appendChild(option);
            });
            
            // Trigger change event to load parameters for the first strategy
            if (select.options.length > 0) {
                select.value = strategies[0].id || strategies[0];
                select.dispatchEvent(new Event('change'));
            }
        };
        
        // Populate all strategy selects
        populateSelect(strategySelect);
        populateSelect(backtestStrategySelect);
        populateSelect(optimizationStrategySelect);
        
        // Set default selected strategy in app state
        if (strategies.length > 0) {
            appState.setSelectedStrategy(strategies[0].id || strategies[0]);
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
    const strategy = strategyType || (strategySelect ? strategySelect.value : appState.selectedStrategy);
    
    if (!strategy) {
        console.error('No strategy selected');
        return null;
    }
    
    try {
        // Show loading state
        if (strategyParametersContainer) {
            showLoading(strategyParametersContainer);
        }
        
        // Fetch strategy parameters
        const response = await fetchStrategyParameters(strategy);
        
        if (!response.parameters) {
            throw new Error('No parameters available for this strategy');
        }
        
        // Update the UI with parameters
        updateStrategyParameters(response.parameters);
        
        return response.parameters;
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

// Update the strategy parameters UI
export function updateStrategyParameters(parameters) {
    if (!strategyParametersContainer) return;
    
    // Clear existing parameters
    strategyParametersContainer.innerHTML = '';
    
    if (!parameters || Object.keys(parameters).length === 0) {
        strategyParametersContainer.innerHTML = '<div class="alert alert-info">No parameters available for this strategy</div>';
        return;
    }
    
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
}

// Initialize strategy selector
export function initializeStrategySelector() {
    // Build strategy dropdowns
    buildStrategySelections();
    
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
            // Only update app state, don't load parameters (handled by the backtest module)
            appState.setSelectedStrategy(this.value);
        });
    }
    
    if (optimizationStrategySelect) {
        optimizationStrategySelect.addEventListener('change', function() {
            // Only update app state, don't load parameters (handled by the optimization module)
            appState.setSelectedStrategy(this.value);
        });
    }
}
