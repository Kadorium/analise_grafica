// frontend/js/modules/optimizationPanel.js

// Import dependencies
import { optimizeStrategy as runOptimizationApi, checkOptimizationStatus as checkOptimizationStatusApi, fetchOptimizationResults } from '../utils/api.js';
import { showError, showLoading, showSuccessMessage, showGlobalLoader, hideGlobalLoader } from '../utils/ui.js';
import { formatNumber, formatParamName } from '../utils/formatters.js';
import { appState } from '../utils/state.js';

// DOM references
const optimizationForm = document.getElementById('optimization-form');
const optimizationParamsContainer = document.getElementById('optimization-params');
const optimizationResultsContainer = document.getElementById('optimization-results');
const optimizationStatusContainer = document.getElementById('optimization-status');
const optimizationProgressBar = document.getElementById('optimization-progress');
const useOptimizedParamsBtn = document.getElementById('use-optimized-params');

// Status check interval
let statusCheckInterval = null;

// Setup optimization parameters based on strategy
export function setupOptimizationParameters(strategyParams) {
    if (!optimizationParamsContainer || !strategyParams) return;
    
    // Clear existing params
    optimizationParamsContainer.innerHTML = '';
    
    // Create optimization fields for each parameter
    Object.entries(strategyParams).forEach(([paramName, paramConfig]) => {
        // Skip parameters that shouldn't be optimized
        if (paramConfig.optimize === false) return;
        
        // Get default value and range
        let defaultValue, minValue, maxValue, stepValue;
        
        if (typeof paramConfig === 'object') {
            defaultValue = paramConfig.default !== undefined ? paramConfig.default : '';
            minValue = paramConfig.min !== undefined ? paramConfig.min : '';
            maxValue = paramConfig.max !== undefined ? paramConfig.max : '';
            stepValue = paramConfig.step !== undefined ? paramConfig.step : 'any';
        } else {
            defaultValue = paramConfig;
            minValue = '';
            maxValue = '';
            stepValue = 'any';
        }
        
        // Create form group
        const formGroup = document.createElement('div');
        formGroup.className = 'card mb-3';
        
        // Create card header
        const cardHeader = document.createElement('div');
        cardHeader.className = 'card-header bg-light';
        cardHeader.innerHTML = `
            <div class="form-check">
                <input class="form-check-input param-optimize-check" type="checkbox" id="optimize-${paramName}" name="optimize_params" value="${paramName}">
                <label class="form-check-label" for="optimize-${paramName}">
                    <strong>${formatParamName(paramName)}</strong>
                </label>
            </div>
        `;
        
        // Create card body
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        cardBody.innerHTML = `
            <div class="row">
                <div class="col-md-4">
                    <label class="form-label">Min</label>
                    <input type="number" class="form-control param-min" name="min_${paramName}" value="${minValue}" step="${stepValue}">
                </div>
                <div class="col-md-4">
                    <label class="form-label">Max</label>
                    <input type="number" class="form-control param-max" name="max_${paramName}" value="${maxValue}" step="${stepValue}">
                </div>
                <div class="col-md-4">
                    <label class="form-label">Step</label>
                    <input type="number" class="form-control param-step" name="step_${paramName}" value="${stepValue}" step="any">
                </div>
            </div>
        `;
        
        // Assemble the form group
        formGroup.appendChild(cardHeader);
        formGroup.appendChild(cardBody);
        optimizationParamsContainer.appendChild(formGroup);
    });
}

// Run optimization with provided parameters
export async function runOptimization(params = {}) {
    if (!appState.dataProcessed) {
        showError('Please upload and process data first');
        return false;
    }
    
    try {
        showGlobalLoader('Submitting optimization job...');
        
        // Run optimization
        const response = await runOptimizationApi(params);
        
        if (response.success && response.job_id) {
            showSuccessMessage('Optimization job started. Tracking progress...');
            
            // Store job ID in state
            appState.setOptimizationJobId(response.job_id);
            
            // Start checking status
            startStatusCheck(response.job_id);
            
            return true;
        } else {
            throw new Error(response.error || 'Error starting optimization job');
        }
    } catch (error) {
        showError(error.message || 'Failed to start optimization');
        return false;
    } finally {
        hideGlobalLoader();
    }
}

// Start checking optimization status
function startStatusCheck(jobId) {
    // Clear any existing interval
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    // Show status container
    if (optimizationStatusContainer) {
        optimizationStatusContainer.style.display = 'block';
    }
    
    // Set initial progress
    if (optimizationProgressBar) {
        optimizationProgressBar.style.width = '0%';
        optimizationProgressBar.setAttribute('aria-valuenow', '0');
        optimizationProgressBar.textContent = '0%';
    }
    
    // Check status immediately
    checkOptimizationStatusLocal(jobId);
    
    // Set interval to check every 5 seconds
    statusCheckInterval = setInterval(() => {
        checkOptimizationStatusLocal(jobId);
    }, 5000);
}

// Check optimization status
export async function checkOptimizationStatusLocal(jobId = null) {
    // Use provided job ID or get from state
    const optimizationJobId = jobId || appState.optimizationJobId;
    
    if (!optimizationJobId) {
        console.error('No optimization job ID available');
        return;
    }
    
    try {
        // Check status
        const response = await checkOptimizationStatusApi();
        
        if (response.status) {
            // Update progress bar
            if (optimizationProgressBar && response.progress !== undefined) {
                const progressPercent = Math.round(response.progress * 100);
                optimizationProgressBar.style.width = `${progressPercent}%`;
                optimizationProgressBar.setAttribute('aria-valuenow', progressPercent);
                optimizationProgressBar.textContent = `${progressPercent}%`;
            }
            
            // Check if completed
            if (response.status === 'completed') {
                showSuccessMessage('Optimization completed successfully');
                
                // Stop checking
                if (statusCheckInterval) {
                    clearInterval(statusCheckInterval);
                    statusCheckInterval = null;
                }
                
                // Fetch results
                fetchAndDisplayOptimizationResults(optimizationJobId);
            } else if (response.status === 'failed') {
                showError('Optimization failed: ' + (response.error || 'Unknown error'));
                
                // Stop checking
                if (statusCheckInterval) {
                    clearInterval(statusCheckInterval);
                    statusCheckInterval = null;
                }
            }
        }
    } catch (error) {
        console.error('Error checking optimization status:', error);
    }
}

// Fetch and display optimization results
export async function fetchAndDisplayOptimizationResults(jobId = null) {
    // Use provided job ID or get from state
    const optimizationJobId = jobId || appState.optimizationJobId;
    
    if (!optimizationJobId) {
        console.error('No optimization job ID available');
        return;
    }
    
    try {
        showLoading(optimizationResultsContainer);
        
        // Fetch results
        const response = await fetchOptimizationResults(optimizationJobId);
        
        if (response.results) {
            // Store results in state
            appState.setOptimizationResults(response.results);
            
            // Display results
            displayOptimizationResults(response.results);
        } else {
            throw new Error('No results available');
        }
    } catch (error) {
        showError(error.message || 'Failed to fetch optimization results');
        optimizationResultsContainer.innerHTML = '';
    }
}

// Display optimization results
function displayOptimizationResults(results) {
    if (!optimizationResultsContainer || !results) return;
    
    // Create table for results
    let tableHtml = `
        <div class="table-responsive">
            <table class="table table-bordered table-striped">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Score</th>
                        ${Object.keys(results.best_params || {}).map(param => 
                            `<th>${formatParamName(param)}</th>`
                        ).join('')}
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Add each result as a row
    let rank = 1;
    for (const result of results.top_results || []) {
        tableHtml += `
            <tr>
                <td>${rank}</td>
                <td>${formatNumber(result.score, 4)}</td>
                ${Object.entries(result.params || {}).map(([param, value]) => 
                    `<td>${formatNumber(value)}</td>`
                ).join('')}
                <td>
                    <button class="btn btn-sm btn-primary use-params-btn" data-rank="${rank - 1}">
                        Use
                    </button>
                </td>
            </tr>
        `;
        rank++;
    }
    
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    // Add charts if available
    if (results.charts) {
        tableHtml += `
            <div class="optimization-charts mt-4">
                ${results.charts}
            </div>
        `;
    }
    
    optimizationResultsContainer.innerHTML = tableHtml;
    
    // Add event listeners to "Use" buttons
    const useButtons = optimizationResultsContainer.querySelectorAll('.use-params-btn');
    useButtons.forEach(button => {
        button.addEventListener('click', () => {
            const rank = parseInt(button.dataset.rank);
            if (!isNaN(rank) && results.top_results && results.top_results[rank]) {
                useOptimizedParameters(results.top_results[rank].params);
            }
        });
    });
}

// Use optimized parameters
export function useOptimizedParameters(params) {
    if (!params) return;
    
    // Trigger event to notify other modules
    const event = new CustomEvent('use-optimized-params', { detail: { params } });
    document.dispatchEvent(event);
    
    showSuccessMessage('Optimized parameters applied');
}

// Initialize optimization panel
export function initializeOptimizationPanel() {
    // Initialize form submission
    if (optimizationForm) {
        optimizationForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Get selected parameters to optimize
            const checkboxes = optimizationForm.querySelectorAll('input[name="optimize_params"]:checked');
            if (!checkboxes.length) {
                showError('Please select at least one parameter to optimize');
                return;
            }
            
            // Build params object
            const params = {
                strategy: document.getElementById('optimization-strategy').value,
                params_to_optimize: {},
                optimization_metric: document.getElementById('optimization-metric').value
            };
            
            // Add each parameter range
            checkboxes.forEach(checkbox => {
                const paramName = checkbox.value;
                const paramGroup = checkbox.closest('.card');
                
                const minInput = paramGroup.querySelector(`.param-min[name="min_${paramName}"]`);
                const maxInput = paramGroup.querySelector(`.param-max[name="max_${paramName}"]`);
                const stepInput = paramGroup.querySelector(`.param-step[name="step_${paramName}"]`);
                
                params.params_to_optimize[paramName] = {
                    min: parseFloat(minInput.value),
                    max: parseFloat(maxInput.value),
                    step: parseFloat(stepInput.value)
                };
            });
            
            // Run optimization
            await runOptimization(params);
        });
    }
    
    // Initialize use optimized params button
    if (useOptimizedParamsBtn) {
        useOptimizedParamsBtn.addEventListener('click', () => {
            // Use best params from current results
            if (appState.optimizationResults && appState.optimizationResults.best_params) {
                useOptimizedParameters(appState.optimizationResults.best_params);
            } else {
                showError('No optimization results available');
            }
        });
    }
}
