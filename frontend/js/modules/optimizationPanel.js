// frontend/js/modules/optimizationPanel.js

// Import dependencies
import { optimizeStrategy as runOptimizationApi, checkOptimizationStatus as checkOptimizationStatusApi, fetchOptimizationResults } from '../utils/api.js';
import { showError, showLoading, showSuccessMessage, showGlobalLoader, hideGlobalLoader } from '../utils/ui.js';
import { formatNumber, formatParamName } from '../utils/formatters.js';
import { appState } from '../utils/state.js';
import { getStrategyDefaultParams, getStrategyConfig } from '../utils/strategies-config.js';
import { OptimizationParamTable } from './optimizationParamTable.js';
import { Parameter } from '../utils/parameterModel.js';
import { strategies } from '../utils/strategies-config.js';

// DOM references
const optimizationForm = document.getElementById('optimization-form');
const optimizationParamsContainer = document.getElementById('optimization-parameters');
const optimizationResultsContainer = document.getElementById('optimization-results');
const optimizationStatusContainer = document.getElementById('optimization-status');
const optimizationProgressBar = document.getElementById('optimization-progress');
const useOptimizedParamsBtn = document.getElementById('use-optimized-params');

// Status check interval
let statusCheckInterval = null;
let paramTable = null;
let pollingInterval = null;

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
            stepValue = paramConfig.step !== undefined ? paramConfig.step : '';
        } else {
            defaultValue = paramConfig;
            minValue = '';
            maxValue = '';
            stepValue = '';
        }
        // Only set value attribute if not empty
        const minValueAttr = minValue !== '' ? `value="${minValue}"` : '';
        const maxValueAttr = maxValue !== '' ? `value="${maxValue}"` : '';
        const stepValueAttr = stepValue !== '' ? `step=\"${stepValue}\"` : 'step="any"';
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
                    <input type="number" class="form-control param-min" name="min_${paramName}" ${minValueAttr} ${stepValueAttr}>
                </div>
                <div class="col-md-4">
                    <label class="form-label">Max</label>
                    <input type="number" class="form-control param-max" name="max_${paramName}" ${maxValueAttr} ${stepValueAttr}>
                </div>
                <div class="col-md-4">
                    <label class="form-label">Step</label>
                    <input type="number" class="form-control param-step" name="step_${paramName}" ${stepValueAttr}>
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
        
        // Log the params object just before the API call
        console.log('[DEBUG] Params object right before runOptimizationApi:', JSON.stringify(params));

        // Run optimization
        const response = await runOptimizationApi(params);
        
        // Accept backend response with just a message as success
        if ((response.job_id) || (response.message && response.message.toLowerCase().includes('optimization started'))) {
            showSuccessMessage(response.message || 'Optimization job started. Tracking progress...');
            
            // Store strategy type in state
            appState.setCurrentOptimizationStrategy(params.strategy_type);
            
            // Store job ID in state if present
            if (response.job_id) {
                appState.setOptimizationJobId(response.job_id);
            }
            
            // Start polling for results
            if (params.strategy_type) {
                pollOptimizationResults(params.strategy_type);
            }
            return true;
        } else {
            throw new Error(response.error || response.message || 'Error starting optimization job');
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
    console.log("Received optimization results:", results);
    const container = document.getElementById('optimization-results');
    if (!container) {
        console.error("Optimization results container not found");
        return;
    }
    
    // Clear previous content
    container.innerHTML = '';
    
    // Handle the case where results is an array
    let resultsData = results;
    if (Array.isArray(results)) {
        // Extract the actual results object from the array
        resultsData = results[0];
        console.log("Extracted results data from array:", resultsData);
    }
    
    // Check if we have results to display
    if (!resultsData || !resultsData.top_results || resultsData.top_results.length === 0) {
        container.innerHTML = '<div class="alert alert-warning">No optimization results found.</div>';
        return;
    }

    // Show only the best result (first in top_results array)
    const best = resultsData.top_results[0];
    let bestParamsHtml = '';
    if (best && best.params) {
        bestParamsHtml = Object.entries(best.params)
            .map(([key, value]) => `<tr><td>${formatParamName(key)}</td><td><strong>${value}</strong></td></tr>`)
            .join('');
    }

    // Check if we have comparison data
    const hasComparison = resultsData.default_params && resultsData.optimized_params && 
                         resultsData.default_performance && resultsData.optimized_performance;
                         
    // --- DEBUG LOGGING: Output the actual values used for the table ---
    if (hasComparison) {
        console.log("[DEBUG] Default Performance:", resultsData.default_performance);
        console.log("[DEBUG] Optimized Performance:", resultsData.optimized_performance);
        console.log("[DEBUG] Default Params:", resultsData.default_params);
        console.log("[DEBUG] Optimized Params:", resultsData.optimized_params);
    }

    // Create the comparison section if it exists
    let comparisonHtml = '';
    if (hasComparison) {
        const defaultParams = resultsData.default_params;
        const optimizedParams = resultsData.optimized_params;
        
        // Create parameter comparison table
        let paramComparisonRows = '';
        const allParamKeys = [...new Set([...Object.keys(defaultParams), ...Object.keys(optimizedParams)])];
        
        for (const key of allParamKeys) {
            const defaultValue = defaultParams[key] !== undefined ? defaultParams[key] : 'N/A';
            const optimizedValue = optimizedParams[key] !== undefined ? optimizedParams[key] : 'N/A';
            const isChanged = defaultValue !== optimizedValue;
            
            paramComparisonRows += `
                <tr ${isChanged ? 'class="table-success"' : ''}>
                    <td>${formatParamName(key)}</td>
                    <td>${defaultValue}</td>
                    <td>${optimizedValue}</td>
                </tr>
            `;
        }
        
        // Create performance metric comparison table
        let metricComparisonRows = '';
        const metricsToCompare = [
            {key: 'sharpe_ratio', label: 'Sharpe Ratio', higherBetter: true},
            {key: 'sortino_ratio', label: 'Sortino Ratio', higherBetter: true},
            {key: 'calmar_ratio', label: 'Calmar Ratio', higherBetter: true},
            {key: 'total_return', label: 'Total Return (%)', higherBetter: true, isPercent: true},
            {key: 'annual_return', label: 'Annual Return (%)', higherBetter: true, isPercent: true},
            {key: 'max_drawdown', label: 'Max Drawdown (%)', higherBetter: false, isPercent: true},
            {key: 'win_rate', label: 'Win Rate (%)', higherBetter: true, isPercent: true},
            {key: 'profit_factor', label: 'Profit Factor', higherBetter: true},
            {key: 'percent_profitable_days', label: 'Profitable Days (%)', higherBetter: true, isPercent: true},
            {key: 'max_consecutive_wins', label: 'Max Consecutive Wins', higherBetter: true},
            {key: 'max_consecutive_losses', label: 'Max Consecutive Losses', higherBetter: false}
        ];
        
        for (const metric of metricsToCompare) {
            if (!resultsData.default_performance || !resultsData.optimized_performance) {
                console.error("Missing performance data:", { 
                    default: resultsData.default_performance, 
                    optimized: resultsData.optimized_performance
                });
                continue;
            }
            let defaultValue = resultsData.default_performance[metric.key];
            let optimizedValue = resultsData.optimized_performance[metric.key];
            if (metric.isPercent) {
                defaultValue = defaultValue !== undefined ? formatNumber(defaultValue * 100, 2) + '%' : 'N/A';
                optimizedValue = optimizedValue !== undefined ? formatNumber(optimizedValue * 100, 2) + '%' : 'N/A';
            } else {
                defaultValue = defaultValue !== undefined ? formatNumber(defaultValue) : 'N/A';
                optimizedValue = optimizedValue !== undefined ? formatNumber(optimizedValue) : 'N/A';
            }
            let isImproved = false;
            let improvementPercent = '';
            if (resultsData.default_performance[metric.key] !== undefined && 
                resultsData.optimized_performance[metric.key] !== undefined &&
                resultsData.default_performance[metric.key] !== 0) {
                const defaultVal = resultsData.default_performance[metric.key];
                const optimizedVal = resultsData.optimized_performance[metric.key];
                if (metric.higherBetter) {
                    isImproved = optimizedVal > defaultVal;
                    if (defaultVal !== 0) {
                        improvementPercent = ((optimizedVal - defaultVal) / Math.abs(defaultVal) * 100).toFixed(2) + '%';
                    }
                } else {
                    isImproved = optimizedVal < defaultVal;
                    if (defaultVal !== 0) {
                        improvementPercent = ((defaultVal - optimizedVal) / Math.abs(defaultVal) * 100).toFixed(2) + '%';
                    }
                }
            }
            metricComparisonRows += `
                <tr ${isImproved ? 'class="table-success"' : ''}>
                    <td>${metric.label}</td>
                    <td>${defaultValue}</td>
                    <td>${optimizedValue}</td>
                    <td>${improvementPercent || '-'}</td>
                </tr>
            `;
        }
        
        // Check if we have a chart
        let chartSectionHtml = '';
        if (resultsData.chart_html) {
            console.log("[OPTIMIZATION_PANEL] chart_html received from backend. Length:", resultsData.chart_html.length);
            chartSectionHtml = resultsData.chart_html; // Store the HTML string
        } else {
            console.warn("[OPTIMIZATION_PANEL] No chart_html found in results object. results.chart_html was:", resultsData.chart_html, "Full results object:", resultsData);
            chartSectionHtml = '<div class="alert alert-warning mt-4">No comparison chart available for display.</div>';
        }
        
        // Get the indicators chart if available
        let indicatorsChartHtml = '';
        if (resultsData.indicators_chart_html) {
            console.log("[OPTIMIZATION_PANEL] indicators_chart_html received from backend. Length:", resultsData.indicators_chart_html.length);
            indicatorsChartHtml = resultsData.indicators_chart_html;
        }
        
        // Build the complete comparison HTML
        comparisonHtml = `
            <div class="card mb-4">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">Default vs. Optimized Comparison</h5>
                </div>
                <div class="card-body">
                    <h6>Parameter Comparison</h6>
                    <table class="table table-bordered table-striped">
                        <thead>
                            <tr>
                                <th>Parameter</th>
                                <th>Default Value</th>
                                <th>Optimized Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${paramComparisonRows}
                        </tbody>
                    </table>
                    
                    <h6 class="mt-4">Performance Comparison</h6>
                    <table class="table table-bordered table-striped">
                        <thead>
                            <tr>
                                <th>Metric</th>
                                <th>Default</th>
                                <th>Optimized</th>
                                <th>Improvement</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${metricComparisonRows}
                        </tbody>
                    </table>
                    
                    <div class="row mt-4">
                        <div class="col-12">
                            <ul class="nav nav-tabs" id="comparison-charts-tabs" role="tablist">
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link active" id="equity-chart-tab" data-bs-toggle="tab" 
                                        data-bs-target="#equity-chart-content" type="button" role="tab" 
                                        aria-controls="equity-chart-content" aria-selected="true">
                                        Equity Comparison
                                    </button>
                                </li>
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link" id="indicators-chart-tab" data-bs-toggle="tab" 
                                        data-bs-target="#indicators-chart-content" type="button" role="tab" 
                                        aria-controls="indicators-chart-content" aria-selected="false">
                                        Indicators Comparison
                                    </button>
                                </li>
                            </ul>
                            <div class="tab-content mt-3" id="comparison-charts-content">
                                <div class="tab-pane fade show active" id="equity-chart-content" role="tabpanel" 
                                    aria-labelledby="equity-chart-tab">
                                    ${chartSectionHtml}
                                </div>
                                <div class="tab-pane fade" id="indicators-chart-content" role="tabpanel" 
                                    aria-labelledby="indicators-chart-tab">
                                    ${indicatorsChartHtml || '<div class="alert alert-warning">No indicators comparison chart available.</div>'}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;
    }

    // Create a clean and simple display of the best parameters and comparison
    let summaryHtml = `
        <div class="card mb-4">
            <div class="card-header bg-success text-white">
                <h5 class="mb-0">Best Optimization Result</h5>
            </div>
            <div class="card-body">
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${bestParamsHtml}
                    </tbody>
                </table>
                ${best.score ? `<p class="mt-3 mb-0"><strong>Score:</strong> ${formatNumber(best.score)}</p>` : ''}
            </div>
        </div>
        ${comparisonHtml}
    `;
    
    // Add the summary to the container
    container.innerHTML = summaryHtml;
    
    // After setting innerHTML, find and execute scripts from chartSectionHtml if it was populated
    if (resultsData.chart_html || resultsData.indicators_chart_html) {
        // Function to extract and execute scripts from HTML
        const executeScriptsFromHtml = (html) => {
            if (!html) return;
            
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            const scripts = tempDiv.querySelectorAll('script');
            
            scripts.forEach(scriptTag => {
                if (scriptTag.textContent) {
                    try {
                        console.log("[OPTIMIZATION_PANEL] Attempting to execute script content:", scriptTag.textContent.substring(0, 50) + "...");
                        new Function(scriptTag.textContent)();
                        console.log("[OPTIMIZATION_PANEL] Successfully executed script content.");
                    } catch (e) {
                        console.error("[OPTIMIZATION_PANEL] Error executing script content:", e);
                    }
                }
            });
        };
        
        // Execute scripts from both chart types
        executeScriptsFromHtml(resultsData.chart_html);
        executeScriptsFromHtml(resultsData.indicators_chart_html);
    }
    
    // Add download and use parameter buttons
    const currentStrategy = document.getElementById('optimization-strategy') ? 
        document.getElementById('optimization-strategy').value : 
        appState.currentOptimizationStrategy;
        
    addDownloadButton(resultsData, currentStrategy);
    
    // Add buttons container if not present
    let buttonContainer = document.querySelector('#optimization-results .param-buttons-container');
    if (!buttonContainer) {
        buttonContainer = document.createElement('div');
        buttonContainer.className = 'param-buttons-container d-flex mt-3 gap-2';
        document.getElementById('optimization-results').appendChild(buttonContainer);
    } else {
        buttonContainer.innerHTML = ''; // Clear existing buttons
    }
    
    // Add "Use Default Parameters" button
    if (resultsData.default_params) {
        const useDefaultBtn = document.createElement('button');
        useDefaultBtn.id = 'use-default-params';
        useDefaultBtn.className = 'btn btn-outline-primary';
        useDefaultBtn.innerHTML = '<i class="bi bi-arrow-counterclockwise"></i> Use Default Parameters';
        useDefaultBtn.onclick = () => {
            useOptimizedParameters(resultsData.default_params);
        };
        buttonContainer.appendChild(useDefaultBtn);
    }
    
    // Add "Use Optimized Parameters" button
    const useOptimizedBtn = document.createElement('button');
    useOptimizedBtn.id = 'use-optimized-params';
    useOptimizedBtn.className = 'btn btn-success';
    useOptimizedBtn.innerHTML = '<i class="bi bi-check-circle"></i> Use Optimized Parameters';
    useOptimizedBtn.onclick = () => {
        if (resultsData.optimized_params) {
            useOptimizedParameters(resultsData.optimized_params);
        } else if (resultsData.best_params) {
            useOptimizedParameters(resultsData.best_params);
        } else if (resultsData.top_results && resultsData.top_results.length > 0 && resultsData.top_results[0].params) {
            useOptimizedParameters(resultsData.top_results[0].params);
        } else {
            showError('No optimized parameters available to use');
        }
    };
    buttonContainer.appendChild(useOptimizedBtn);
}

// Check if Chart.js is loaded and retry if needed
function ensureChartJsLoaded(callback, maxRetries = 5, retryDelay = 300, currentRetry = 0) {
    if (window.Chart) {
        // Chart.js is loaded, call the callback
        callback();
        return;
    }
    
    if (currentRetry >= maxRetries) {
        console.error(`Chart.js not loaded after ${maxRetries} retries`);
        // Display error in any chart containers
        document.querySelectorAll('.comparison-chart-container').forEach(container => {
            container.innerHTML = '<div class="alert alert-danger">Chart.js library not loaded. Please reload the page.</div>';
        });
        return;
    }
    
    console.warn(`Chart.js not loaded, retrying (${currentRetry + 1}/${maxRetries})...`);
    setTimeout(() => {
        ensureChartJsLoaded(callback, maxRetries, retryDelay, currentRetry + 1);
    }, retryDelay);
}

// Helper function to initialize chart toggle handlers
function initChartToggleHandlers() {
    console.log("Initializing chart toggle handlers...");
    try {
        // First find all chart containers
        const chartContainers = document.querySelectorAll('.comparison-chart-container');
        if (chartContainers.length === 0) {
            console.error('No chart containers found in the DOM');
            return;
        }
        
        console.log(`Found ${chartContainers.length} chart container(s)`);
        
        // Process each container
        chartContainers.forEach((container, index) => {
            const canvasElement = container.querySelector('canvas');
            if (!canvasElement) {
                console.error(`No canvas element found in chart container #${index+1}`);
                return;
            }
            
            const chartId = canvasElement.id;
            if (!chartId) {
                console.error('Canvas element has no ID attribute');
                return;
            }
            
            console.log(`Setting up handlers for chart #${index+1} with ID: ${chartId}`);
            
            // Set up the chart type toggle buttons
            const toggleButtons = document.querySelectorAll('.chart-type-toggle button');
            if (toggleButtons.length === 0) {
                console.warn('No chart type toggle buttons found');
            } else {
                console.log(`Found ${toggleButtons.length} toggle buttons`);
                
                toggleButtons.forEach(btn => {
                    btn.addEventListener('click', function() {
                        console.log(`Chart type button clicked: ${this.getAttribute('data-chart-type')}`);
                        
                        // Remove active class from all buttons
                        toggleButtons.forEach(b => b.classList.remove('active'));
                        
                        // Add active class to clicked button
                        this.classList.add('active');
                        
                        // Get chart instance
                        let chartInstance;
                        try {
                            chartInstance = Chart.getChart(chartId);
                            if (!chartInstance) {
                                throw new Error(`No chart instance found for ID: ${chartId}`);
                            }
                        } catch (e) {
                            console.error('Error getting chart instance:', e);
                            alert('Error updating chart: Chart instance not found. Try refreshing the page.');
                            return;
                        }
                        
                        // Update chart type
                        const chartType = this.getAttribute('data-chart-type');
                        console.log(`Changing chart type to: ${chartType}`);
                        
                        try {
                            chartInstance.config.type = chartType === 'area' ? 'line' : chartType;
                            
                            // For area charts, set fill to true
                            chartInstance.data.datasets.forEach(dataset => {
                                dataset.fill = chartType === 'area';
                            });
                            
                            // Update the chart
                            chartInstance.update();
                            console.log('Chart updated successfully');
                        } catch (e) {
                            console.error('Error updating chart type:', e);
                            alert('Error updating chart. See console for details.');
                        }
                    });
                });
            }
            
            // Set up the download button
            const downloadBtn = document.querySelector('.download-chart-btn');
            if (!downloadBtn) {
                console.warn('Download chart button not found');
            } else {
                console.log('Setting up download button handler');
                
                downloadBtn.addEventListener('click', function() {
                    console.log('Download chart button clicked');
                    
                    // Get chart instance
                    let chartInstance;
                    try {
                        chartInstance = Chart.getChart(chartId);
                        if (!chartInstance) {
                            throw new Error(`No chart instance found for ID: ${chartId}`);
                        }
                    } catch (e) {
                        console.error('Error getting chart instance for download:', e);
                        alert('Error downloading chart: Chart instance not found. Try refreshing the page.');
                        return;
                    }
                    
                    try {
                        // Create a temporary link element
                        const link = document.createElement('a');
                        link.download = 'strategy_comparison_chart.png';
                        link.href = chartInstance.toBase64Image();
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        console.log('Chart download initiated');
                    } catch (e) {
                        console.error('Error downloading chart:', e);
                        alert('Error downloading chart. See console for details.');
                    }
                });
            }
        });
        
        console.log('Chart handlers initialization complete');
    } catch (e) {
        console.error('Error initializing chart toggle handlers:', e);
        alert('Error initializing chart controls. Try refreshing the page.');
    }
}

// Use optimized parameters
export function useOptimizedParameters(params) {
    if (!params) {
        showError('No parameters provided to apply');
        return;
    }
    
    try {
        // Determine if these are default or optimized parameters by checking button id
        const buttonId = document.activeElement ? document.activeElement.id : '';
        const isDefault = buttonId === 'use-default-params' || 
                         (document.activeElement && document.activeElement.closest('#use-default-params'));
        
        // Trigger event to notify other modules
        const event = new CustomEvent('use-optimized-params', { 
            detail: { 
                params,
                isDefault: isDefault
            } 
        });
        document.dispatchEvent(event);
        
        // Show visual feedback
        const message = isDefault ? 
            'Default parameters applied to strategy' : 
            'Optimized parameters applied to strategy';
            
        showSuccessMessage(message);
        
        // Highlight the appropriate button
        document.querySelectorAll('.param-buttons-container button').forEach(btn => {
            btn.classList.remove('pulse-animation');
        });
        
        const buttonSelector = isDefault ? '#use-default-params' : '#use-optimized-params';
        const activeButton = document.querySelector(buttonSelector);
        if (activeButton) {
            activeButton.classList.add('pulse-animation');
            // Remove the animation class after it completes
            setTimeout(() => {
                activeButton.classList.remove('pulse-animation');
            }, 1000);
        }
        
        // Scroll to strategy section if needed
        const strategiesTab = document.getElementById('strategies-tab');
        if (strategiesTab) {
            strategiesTab.click();
        }
    } catch (error) {
        console.error('Error applying parameters:', error);
        showError('Failed to apply parameters. See console for details.');
    }
}

function createParameterObjects(paramConfigs) {
    return paramConfigs.map(cfg => new Parameter({
        id: cfg.id,
        label: cfg.label,
        type: cfg.type === 'checkbox' ? 'bool' : (cfg.type || 'number'),
        defaultValue: cfg.default,
        min: cfg.min,
        max: cfg.max,
        step: cfg.step,
        options: cfg.options
    }));
}

// Initialize optimization panel
export function initializeOptimizationPanel() {
    const optimizationStrategySelect = document.getElementById('optimization-strategy');
    const paramTableContainer = document.getElementById('optimization-parameters');
    
    // Check if the optimization directory exists and is writable
    fetch('/api/check-optimization-directory')
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error("Optimization directory issue:", data.message);
                showError(`Warning: ${data.message} - Optimization results may not be saved.`);
            } else {
                console.log("Optimization directory check successful:", data.message);
            }
        })
        .catch(err => {
            console.error("Failed to check optimization directory:", err);
        });
    
    if (optimizationStrategySelect) {
        optimizationStrategySelect.addEventListener('change', function() {
            const selectedStrategy = this.value;
            if (selectedStrategy) {
                const strategyConfig = getStrategyConfig(selectedStrategy);
                if (strategyConfig && strategyConfig.params) {
                    const parameterObjs = createParameterObjects(strategyConfig.params);
                    paramTable = new OptimizationParamTable(paramTableContainer, parameterObjs);
                }
            }
        });
        // On initial load, render parameters for the default strategy
        if (optimizationStrategySelect.value) {
            const strategyConfig = getStrategyConfig(optimizationStrategySelect.value);
            if (strategyConfig && strategyConfig.params) {
                const parameterObjs = createParameterObjects(strategyConfig.params);
                paramTable = new OptimizationParamTable(paramTableContainer, parameterObjs);
            }
        }
    }
    // Initialize form submission
    if (optimizationForm) {
        optimizationForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!paramTable) {
                showError('No parameter table available');
                return;
            }
            const paramRanges = paramTable.getParamRanges();
            if (!paramRanges || Object.keys(paramRanges).length === 0) {
                showError('Please select at least one parameter to optimize');
                return;
            }
            const params = {
                strategy_type: document.getElementById('optimization-strategy').value,
                param_ranges: paramRanges,
                optimization_metric: document.getElementById('optimization-metric').value,
                start_date: document.getElementById('optimization-start-date').value || null,
                end_date: document.getElementById('optimization-end-date').value || null
            };
            // Log the params object right before runOptimization, including new dates
            console.log('[DEBUG] Params object right before runOptimization, from optimizationPanel.js event listener:', JSON.stringify(params));
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

function showOptimizationProgress(message = 'Optimization running...') {
    const container = document.getElementById('optimization-results');
    container.innerHTML = `
        <div class="progress my-3">
            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                 role="progressbar" style="width: 100%"> 
                ${message}
            </div>
        </div>
    `;
}

function addDownloadButton(results, strategyType) {
    const container = document.getElementById('optimization-results');
    if (!container) {
        console.error("Optimization results container not found");
        return;
    }
    
    // Check if download button already exists
    if (container.querySelector('.download-results-btn')) {
        return; // Don't add duplicate buttons
    }
    
    const btnContainer = document.createElement('div');
    btnContainer.className = 'd-flex mt-3';
    
    // Add download button
    const btn = document.createElement('button');
    btn.className = 'btn btn-primary download-results-btn';
    btn.innerHTML = '<i class="bi bi-download"></i> Download Results (JSON)';
    btn.onclick = () => {
        try {
            const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `optimization_${strategyType}_${new Date().toISOString().slice(0, 19).replace(/[T:]/g, '-')}.json`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error("Error creating download:", error);
            showError("Could not create download file. See console for details.");
        }
    };
    
    btnContainer.appendChild(btn);
    container.appendChild(btnContainer);
}

function pollOptimizationResults(strategyType) {
    if (pollingInterval) clearInterval(pollingInterval);
    
    // Show progress indicator
    showOptimizationProgress('Optimization running...');
    
    // Check immediately first
    checkOptimizationStatus(strategyType);
    
    // Then set up polling
    pollingInterval = setInterval(async () => {
        await checkOptimizationStatus(strategyType);
    }, 5000);
}

async function checkOptimizationStatus(strategyType) {
    try {
        // Get current status
        const statusResponse = await fetch('/api/optimization-status');
        const statusData = await statusResponse.json();
        
        if (!statusData) {
            console.error('No status data received');
            return;
        }
        
        // Check if optimization is still in progress
        if (statusData.in_progress) {
            // Still running, show progress
            showOptimizationProgress('Optimization in progress...');
            return;
        }
        
        // Optimization is complete, try to get results
        clearInterval(pollingInterval);
        
        try {
            const response = await fetch(`/api/optimization-results/${strategyType}`);
            const data = await response.json();
            
            if (data && data.status === 'success' && data.results) {
                // We have results, display them
                displayOptimizationResults(data.results);
                
                // Check if results have a download button, if not add one
                const downloadBtns = document.querySelectorAll('#optimization-results button.btn-primary');
                if (downloadBtns.length === 0) {
                    addDownloadButton(data.results, strategyType);
                }
            } else if (data && data.status === 'not_found') {
                // No results found
                const container = document.getElementById('optimization-results');
                container.innerHTML = `<div class="alert alert-warning">${data.message || 'No optimization results found.'}</div>`;
            } else {
                // Unknown status
                console.warn('Unknown status from optimization results API:', data);
                showOptimizationProgress('Waiting for results to be processed...');
                
                // Try again in a few seconds
                setTimeout(() => {
                    checkOptimizationStatus(strategyType);
                }, 5000);
            }
        } catch (err) {
            console.error('Error fetching optimization results:', err);
            showOptimizationProgress('Error fetching results. Retrying...');
            
            // Try again in a few seconds
            setTimeout(() => {
                checkOptimizationStatus(strategyType);
            }, 5000);
        }
    } catch (err) {
        console.error('Error checking optimization status:', err);
    }
}
