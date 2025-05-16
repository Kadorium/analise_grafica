// frontend/js/modules/strategySelector.js

// Import dependencies
import { fetchAvailableStrategies, fetchStrategyParameters } from '../utils/api.js';
import { showError, showLoading, showGlobalLoader, hideGlobalLoader } from '../utils/ui.js';
import { formatParamName } from '../utils/formatters.js';
import { appState } from '../utils/state.js';
import { getStrategyConfig, getStrategyDescription, getStrategyDefaultParams } from '../utils/strategies-config.js';

// DOM references - these might be null if script loads before DOM for these elements is parsed
const strategyTypeSelect = document.getElementById('strategy-type');
const strategyParametersContainer = document.getElementById('strategy-parameters'); // Note: HTML was changed to strategy-parameters-form
const backtestStrategySelect = document.getElementById('backtest-strategy');
const optimizationStrategySelect = document.getElementById('optimization-strategy');
const strategyDescriptionContainer = document.getElementById('strategy-description');
const updateStrategyBtn = document.getElementById('update-strategy-btn');

// Make loadStrategyParameters available globally for use in other modules
window.loadStrategyParameters = loadStrategyParameters;

// Build strategy selection dropdowns
export async function buildStrategySelections() {
    const currentStrategySelect = document.getElementById('strategy-select');
    
    // More detailed logging for debugging
    if (currentStrategySelect) {
        console.log('[Debug] buildStrategySelections: Found strategy-select element. OuterHTML:', currentStrategySelect.outerHTML);
    } else {
        console.error('[Debug] buildStrategySelections: strategy-select element NOT FOUND by getElementById.');
    }

    try {
        // Show loading state
        // Adding a more robust check before attempting to use innerHTML
        if (currentStrategySelect && typeof currentStrategySelect.innerHTML !== 'undefined') {
            console.log('[Debug] buildStrategySelections: strategy-select is valid, calling showLoading.');
            showLoading(currentStrategySelect);
        } else {
            console.error('[Debug] buildStrategySelections: strategy-select element is null or not a valid element for showLoading. Value:', currentStrategySelect);
            // Fallback: maybe clear the select if it exists but is weird, or do nothing.
            if (currentStrategySelect) { // if it exists but !currentStrategySelect.innerHTML (unlikely for select)
                 currentStrategySelect.innerHTML = '<option>Error or invalid state</option>';
            }
        }
        
        const response = await fetchAvailableStrategies();
        
        if (!response.strategies || !response.strategies.length) {
            throw new Error('No strategies available');
        }
        
        const strategies = response.strategies;
        
        // Store available strategies in app state
        appState.availableStrategies = strategies;
        
        // Function to populate a select element with strategies
        const populateSelect = (selectElement) => {
            if (!selectElement) {
                 console.warn('[Debug] populateSelect: called with null selectElement');
                 return;
            }
            console.log('[Debug] populateSelect: Populating:', selectElement.id);
            
            // Clear existing options
            selectElement.innerHTML = '';
            
            // Add each strategy as an option
            strategies.forEach(strategy => {
                const option = document.createElement('option');
                option.value = strategy.id || strategy.type || strategy;
                option.textContent = strategy.name || formatParamName(strategy);
                selectElement.appendChild(option);
            });
            
            // Trigger change event to load parameters for the first strategy
            if (selectElement.options.length > 0) {
                selectElement.value = strategies[0].id || strategies[0].type || strategies[0];
                selectElement.dispatchEvent(new Event('change'));
            }
        };
        
        // Populate all strategy selects
        populateSelect(currentStrategySelect); 
        populateSelect(document.getElementById('backtest-strategy')); 
        populateSelect(document.getElementById('optimization-strategy')); 
        populateSelect(document.getElementById('strategy-type')); 

        // ALSO POPULATE COMPARISON CHECKBOXES
        populateStrategyComparisonCheckboxes(strategies); // New function call
        
        // Set default selected strategy in app state
        if (strategies.length > 0) {
            appState.setSelectedStrategy(strategies[0].id || strategies[0].type || strategies[0]);
        }
        
        return strategies;
    } catch (error) {
        showError(error.message || 'Error loading strategies');
        console.error('Error building strategy selections:', error);
        // If currentStrategySelect was found and showLoading was called, ensure it's cleared on error.
        if (currentStrategySelect) {
            currentStrategySelect.innerHTML = '<option value="">Error loading</option>';
        }
        return [];
    }
}

// New function to populate strategy comparison checkboxes
function populateStrategyComparisonCheckboxes(strategies) {
    const checkboxesContainer = document.getElementById('strategy-comparison-checkboxes');
    if (!checkboxesContainer) {
        console.error('Strategy comparison checkboxes container not found.');
        return;
    }
    checkboxesContainer.innerHTML = ''; // Clear existing

    if (!strategies || strategies.length === 0) {
        checkboxesContainer.innerHTML = '<p class="text-muted">No strategies available for comparison.</p>';
        return;
    }

    strategies.forEach(strategy => {
        const strategyId = strategy.id || strategy.type || strategy;
        const strategyName = strategy.name || formatParamName(strategy);

        const div = document.createElement('div');
        div.classList.add('form-check');

        const input = document.createElement('input');
        input.classList.add('form-check-input', 'strategy-compare-checkbox');
        input.type = 'checkbox';
        input.value = strategyId;
        input.id = `compare-checkbox-${strategyId.replace(/[^a-zA-Z0-9]/g, '-')}`;

        const label = document.createElement('label');
        label.classList.add('form-check-label');
        label.htmlFor = input.id;
        label.textContent = strategyName;

        div.appendChild(input);
        div.appendChild(label);
        checkboxesContainer.appendChild(div);
    });
}

// Load strategy parameters for a specific strategy
export async function loadStrategyParameters(strategyType = null) {
    // Re-fetch strategy select element for current value, or use appState
    const currentStrategySelectValue = document.getElementById('strategy-select') ? document.getElementById('strategy-select').value : null;
    const strategy = strategyType || (document.getElementById('strategy-type') ? document.getElementById('strategy-type').value : (currentStrategySelectValue || appState.selectedStrategy));
    
    // Re-fetch parameters container
    const currentStrategyParametersContainer = document.getElementById('strategy-parameters-form'); // Corrected ID
    
    if (!strategy) {
        console.error('No strategy selected');
        return null;
    }
    
    try {
        // Show loading state
        if (currentStrategyParametersContainer) {
            showLoading(currentStrategyParametersContainer);
        } else {
            console.error('strategy-parameters-form element not found in loadStrategyParameters');
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
        const currentStrategyDescriptionContainer = document.getElementById('strategy-description');
        if (currentStrategyDescriptionContainer) {
            updateStrategyDescription(strategy, currentStrategyDescriptionContainer); // Pass container
        }
        
        // Save parameters to app state
        appState.setStrategyParameters(parameters);
        
        // Update the UI with parameters
        if (currentStrategyParametersContainer) { // Check again before using
             updateStrategyParameters(parameters, strategy, currentStrategyParametersContainer); // Pass container
        } else {
            console.error("Cannot update UI, strategy-parameters-form not found.");
        }
        
        return parameters;
    } catch (error) {
        showError(error.message || `Error loading parameters for ${strategy}`);
        console.error('Error loading strategy parameters:', error);
        
        // Clear parameters container
        if (currentStrategyParametersContainer) {
            currentStrategyParametersContainer.innerHTML = '<div class="alert alert-danger">Error loading parameters</div>';
        }
        
        return null;
    }
}

// Update the strategy description based on the strategy type
function updateStrategyDescription(strategyType, container) { // Accept container as argument
    if (!container) return;
    
    // Try to get the description from our configuration first
    const description = getStrategyDescription(strategyType);
    
    if (description) {
        container.innerHTML = `<p>${description}</p>`;
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
    
    container.innerHTML = `<p>${legacyDescription}</p>`;
}

// Update the strategy parameters UI
export function updateStrategyParameters(parameters, strategyType, container) { // Accept container as argument
    if (!container) return;
    
    // Clear existing parameters
    container.innerHTML = '';
    
    if (!parameters || Object.keys(parameters).length === 0) {
        container.innerHTML = '<div class="alert alert-info">No parameters available for this strategy</div>';
        return;
    }
    
    // Ensure parameters are stored in app state
    appState.setStrategyParameters(parameters); // This might be redundant if called from loadStrategyParameters already
    
    // Get strategy configuration if available
    const strategyConfig = getStrategyConfig(strategyType);
    
    if (strategyConfig && strategyConfig.params) {
        // Use the configuration to create the form elements with proper labels, types, etc.
        strategyConfig.params.forEach(paramConfig => {
            const formGroup = document.createElement('div');
            formGroup.className = 'mb-3';
            
            // Create label
            const label = document.createElement('label');
            label.className = 'form-label';
            label.textContent = paramConfig.label;
            
            if (paramConfig.description) {
                label.title = paramConfig.description;
                label.classList.add('text-info');
            }
            
            // Create input element based on type
            let input;
            
            if (paramConfig.type === 'select' && paramConfig.options) {
                input = document.createElement('select');
                input.className = 'form-select';
                
                // Add options
                paramConfig.options.forEach(option => {
                    const optionEl = document.createElement('option');
                    optionEl.value = option.value || option;
                    optionEl.textContent = option.label || option;
                    
                    if (option.value === parameters[paramConfig.id] || option === parameters[paramConfig.id]) {
                        optionEl.selected = true;
                    }
                    
                    input.appendChild(optionEl);
                });
            } else if (paramConfig.type === 'checkbox') {
                input = document.createElement('input');
                input.type = 'checkbox';
                input.className = 'form-check-input';
                input.checked = parameters[paramConfig.id] === true;
                
                // Use form-check div for checkbox
                formGroup.className = 'form-check mb-3';
                label.className = 'form-check-label';
                label.style.marginLeft = '10px';
            } else {
                input = document.createElement('input');
                input.type = paramConfig.type || 'number';
                input.className = 'form-control';
                input.value = parameters[paramConfig.id] !== undefined ? parameters[paramConfig.id] : paramConfig.default;
                
                if (paramConfig.type === 'number') {
                    if (paramConfig.min !== undefined) input.min = paramConfig.min;
                    if (paramConfig.max !== undefined) input.max = paramConfig.max;
                    if (paramConfig.step !== undefined) input.step = paramConfig.step;
                }
            }
            
            input.id = `param-${paramConfig.id}`;
            input.name = paramConfig.id;
            
            // Add data attribute to store parameter metadata
            input.dataset.paramType = typeof paramConfig.default;
            
            // Add elements to form group
            if (paramConfig.type === 'checkbox') {
                formGroup.appendChild(input);
                formGroup.appendChild(label);
            } else {
                formGroup.appendChild(label);
                formGroup.appendChild(input);
            }
            
            // Add form group to container
            container.appendChild(formGroup);
        });
    } else {
        // Fallback to generic parameter rendering for unknown strategies
        Object.entries(parameters).forEach(([paramName, paramValue]) => {
            const formGroup = document.createElement('div');
            formGroup.className = 'mb-3';
            
            // Create label
            const label = document.createElement('label');
            label.className = 'form-label';
            label.textContent = formatParamName(paramName);
            
            // Create input element based on value type
            let input;
            
            if (typeof paramValue === 'boolean') {
                input = document.createElement('input');
                input.type = 'checkbox';
                input.className = 'form-check-input';
                input.checked = paramValue;
                
                // Use form-check div for checkbox
                formGroup.className = 'form-check mb-3';
                label.className = 'form-check-label';
                label.style.marginLeft = '10px';
            } else if (typeof paramValue === 'number') {
                input = document.createElement('input');
                input.type = 'number';
                input.className = 'form-control';
                input.value = paramValue;
                input.step = paramName.includes('period') ? 1 : 0.1;
            } else {
                input = document.createElement('input');
                input.type = 'text';
                input.className = 'form-control';
                input.value = paramValue;
            }
            
            input.id = `param-${paramName}`;
            input.name = paramName;
            
            // Add data attribute to store parameter metadata
            input.dataset.paramType = typeof paramValue;
            
            // Add elements to form group
            if (typeof paramValue === 'boolean') {
                formGroup.appendChild(input);
                formGroup.appendChild(label);
            } else {
                formGroup.appendChild(label);
                formGroup.appendChild(input);
            }
            
            // Add form group to container
            container.appendChild(formGroup);
        });
    }
    
    // Remove run backtest button if it exists from previous renders inside this specific container.
    // The main run backtest button is now static in index.html for the merged tab.
    const existingBtn = container.querySelector('#run-backtest-btn');
    if (existingBtn) {
        existingBtn.remove();
    }
}

// Get strategy parameters from the form
export function getStrategyParameters() {
    const currentStrategyParametersContainer = document.getElementById('strategy-parameters-form'); // Corrected ID
    if (!currentStrategyParametersContainer) {
        return {};
    }
    
    const parameters = {};
    const inputs = currentStrategyParametersContainer.querySelectorAll('input, select');
    
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
    
    buildStrategySelections();
    
    const mainStrategySelect = document.getElementById('strategy-select');
    if (mainStrategySelect) {
        mainStrategySelect.addEventListener('change', function() {
            const selectedStrategy = this.value;
            if (selectedStrategy) {
                appState.setSelectedStrategy(selectedStrategy);
                loadStrategyParameters(selectedStrategy);
            }
        });
    }
    
    // Event listener for the 'Compare Selected Strategies' button
    const compareBtn = document.getElementById('compare-strategies-btn');
    if (compareBtn) {
        compareBtn.addEventListener('click', async () => {
            // Get selected strategies for comparison
            const selectedForComparison = [];
            document.querySelectorAll('.strategy-compare-checkbox:checked').forEach(checkbox => {
                selectedForComparison.push(checkbox.value);
            });

            const resultsContainer = document.getElementById('strategy-comparison-results');
            if (!resultsContainer) {
                console.error('Strategy comparison results container not found.');
                return;
            }
            resultsContainer.innerHTML = ''; // Clear previous results

            if (selectedForComparison.length === 0) {
                resultsContainer.innerHTML = '<p class="text-warning">Please select at least one strategy to compare.</p>';
                return;
            }
            
            // Create a container for the comparison results display
            const compareResultsDisplay = document.getElementById('comparison-results-display');
            if (compareResultsDisplay) {
                compareResultsDisplay.classList.remove('d-none');
            }
            
            // Display strategy parameter forms for each selected strategy
            for (const strategyId of selectedForComparison) {
                const strategyConfig = getStrategyConfig(strategyId);
                const strategyName = strategyConfig ? strategyConfig.name : formatParamName(strategyId);
                let parameters = getStrategyDefaultParams(strategyId); // Fetch default params

                if (!parameters || Object.keys(parameters).length === 0) {
                    // Fallback for strategies not in strategies-config.js (should be rare if config is comprehensive)
                    try {
                        const apiParams = await fetchStrategyParameters(strategyId); // Simplified call
                        if (apiParams && apiParams.parameters) parameters = apiParams.parameters;
                        else if (apiParams && Object.keys(apiParams).length > 0) parameters = apiParams; // Direct object
                        else parameters = {}; // Ensure parameters is an object
                        console.warn(`Fetched parameters from API for ${strategyId} in comparison view as it was not in local config.`);
                    } catch (err) {
                        console.error(`Could not fetch parameters for ${strategyId} for comparison view:`, err);
                        parameters = {}; // Ensure parameters is an object even on error
                    }
                }
                
                const strategyContainer = document.createElement('div');
                strategyContainer.className = 'mb-4 border p-3 rounded strategy-compare-item';
                strategyContainer.dataset.strategyId = strategyId;

                const title = document.createElement('h6');
                title.textContent = strategyName;
                strategyContainer.appendChild(title);

                const paramsForm = document.createElement('div');
                paramsForm.className = 'row gx-2'; // Use gx-2 for small horizontal gutter between columns

                if (parameters && Object.keys(parameters).length > 0) {
                    const paramSource = (strategyConfig && strategyConfig.params) ? strategyConfig.params : null;

                    if (paramSource) { // Use detailed config from strategies-config.js
                        paramSource.forEach(paramCfg => {
                            const paramValue = parameters[paramCfg.id];
                            const paramDiv = document.createElement('div');
                            paramDiv.className = 'col-auto mb-2'; // col-auto makes columns take up only needed space

                            const label = document.createElement('label');
                            label.className = 'form-label form-label-sm';
                            label.textContent = paramCfg.label || formatParamName(paramCfg.id);
                            label.htmlFor = `compare-${strategyId}-param-${paramCfg.id}`;
                            
                            let input;
                            if (paramCfg.type === 'select' && paramCfg.options) {
                                input = document.createElement('select');
                                input.className = 'form-select form-select-sm';
                                paramCfg.options.forEach(opt => {
                                    const optionEl = document.createElement('option');
                                    optionEl.value = opt.value || opt;
                                    optionEl.textContent = opt.label || opt;
                                    if (optionEl.value == paramValue) optionEl.selected = true; // Use == for loose comparison
                                    input.appendChild(optionEl);
                                });
                            } else {
                                input = document.createElement('input');
                                input.type = paramCfg.type || 'number';
                                input.className = 'form-control form-control-sm';
                                input.value = paramValue !== undefined ? paramValue : (paramCfg.default !== undefined ? paramCfg.default : '');
                                if (paramCfg.min !== undefined) input.min = paramCfg.min;
                                if (paramCfg.max !== undefined) input.max = paramCfg.max;
                                if (paramCfg.step !== undefined) input.step = paramCfg.step;
                            }
                            input.id = `compare-${strategyId}-param-${paramCfg.id}`;
                            input.name = paramCfg.id;
                            input.dataset.paramType = paramCfg.type || (typeof paramValue);

                            paramDiv.appendChild(label);
                            paramDiv.appendChild(input);
                            paramsForm.appendChild(paramDiv);
                        });
                    } else { // Generic fallback if strategy is not in strategies-config.js or params structure differs
                        Object.entries(parameters).forEach(([paramId, paramValue]) => {
                            const paramDiv = document.createElement('div');
                            paramDiv.className = 'col-auto mb-2';

                            const label = document.createElement('label');
                            label.className = 'form-label form-label-sm';
                            label.textContent = formatParamName(paramId);
                            label.htmlFor = `compare-${strategyId}-param-${paramId}`;

                            const input = document.createElement('input');
                            input.type = (typeof paramValue === 'number') ? 'number' : 'text';
                            input.className = 'form-control form-control-sm';
                            input.value = paramValue;
                            input.id = `compare-${strategyId}-param-${paramId}`;
                            input.name = paramId;
                            input.dataset.paramType = typeof paramValue;

                            paramDiv.appendChild(label);
                            paramDiv.appendChild(input);
                            paramsForm.appendChild(paramDiv);
                        });
                    }
                } else {
                    paramsForm.innerHTML = '<p class="text-muted col-12"><em>No configurable parameters for this strategy.</em></p>';
                }
                strategyContainer.appendChild(paramsForm);
                resultsContainer.appendChild(strategyContainer);
            }
        });
    }
    
    // Initial load of parameters for the default strategy
    const strategyToLoad = mainStrategySelect ? mainStrategySelect.value : null;
    if (strategyToLoad) {
        loadStrategyParameters(strategyToLoad);
    } else {
        if(appState.availableStrategies && appState.availableStrategies.length > 0) {
            const defaultStrategy = appState.availableStrategies[0].id || appState.availableStrategies[0].type || appState.availableStrategies[0];
            if (defaultStrategy) loadStrategyParameters(defaultStrategy);
        }
    }
}
