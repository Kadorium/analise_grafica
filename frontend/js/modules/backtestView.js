// frontend/js/modules/backtestView.js

// Import dependencies
import { runBacktest as runBacktestApi } from '../utils/api.js';
import { showError, showLoading, showSuccessMessage, showGlobalLoader, hideGlobalLoader } from '../utils/ui.js';
import { formatDate, formatNumber } from '../utils/formatters.js';
import { appState } from '../utils/state.js';

// DOM references
const uploadForm = document.getElementById('upload-form');
const csvFileInput = document.getElementById('csv-file');
const uploadProcessBtn = document.getElementById('upload-process-btn');
const dataInfo = document.getElementById('data-info');
const dataPreview = document.getElementById('data-preview');
const arrangeBtn = document.getElementById('arrange-btn');
const backtestForm = document.getElementById('backtest-form');
// Dynamically query these containers to ensure they are found
const getBacktestResultsContainer = () => document.getElementById('backtest-results');
const getBacktestSummaryContainer = () => document.getElementById('backtest-summary');
const getBacktestDebugContainer = () => document.getElementById('backtest-debug');
const getBacktestChartsContainer = () => document.getElementById('backtest-charts');

// Debug backtest results (display raw data for troubleshooting)
export function debugBacktestResults(results) {
    const backtestDebugContainer = getBacktestDebugContainer();
    if (!backtestDebugContainer) {
        console.error('Debug container not found');
        return;
    }
    
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
    backtestDebugContainer.style.display = 'block';
    console.log('Debug data displayed in container');
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
        
        // Ensure backtest configuration parameters are included
        if (!requestParams.initial_capital) {
            const capitalInput = document.getElementById('initial-capital');
            if (capitalInput) {
                requestParams.initial_capital = parseFloat(capitalInput.value) || 100.0;
            }
        }
        
        if (!requestParams.commission) {
            const commissionInput = document.getElementById('commission');
            if (commissionInput) {
                requestParams.commission = parseFloat(commissionInput.value) || 0.001;
            }
        }
        
        // Add date range if provided
        if (!requestParams.start_date) {
            const startDateInput = document.getElementById('backtest-start-date');
            if (startDateInput && startDateInput.value) {
                requestParams.start_date = startDateInput.value;
            }
        }
        
        if (!requestParams.end_date) {
            const endDateInput = document.getElementById('backtest-end-date');
            if (endDateInput && endDateInput.value) {
                requestParams.end_date = endDateInput.value;
            }
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
    // Add explicit debug logging for seasonality parameters
    console.log('🔍 SEASONALITY DEBUG 🔍');
    console.log('Checking for seasonality parameters in results:');
    console.log('- actual_parameters exists:', !!results.actual_parameters);
    console.log('- optimization_summary exists:', !!results.optimization_summary);
    if (results.actual_parameters) {
        console.log('- actual_parameters keys:', Object.keys(results.actual_parameters));
        console.log('- actual_parameters content:', results.actual_parameters);
    }
    if (results.optimization_summary) {
        console.log('- optimization_summary content:', results.optimization_summary);
    }
    
    const backtestResultsContainer = getBacktestResultsContainer();
    const backtestSummaryContainer = getBacktestSummaryContainer();
    const backtestChartsContainer = getBacktestChartsContainer();

    // Log container existence status
    console.log('Container status:', {
        resultsContainer: backtestResultsContainer ? 'Found' : 'Not found',
        summaryContainer: backtestSummaryContainer ? 'Found' : 'Not found',
        chartsContainer: backtestChartsContainer ? 'Found' : 'Not found'
    });

    if (!backtestResultsContainer || !results) {
        console.error('Backtest results container not found or no results data:', { container: !!backtestResultsContainer, results: !!results });
        return;
    }
    
    // Log the entire results object as JSON for debugging
    console.log('Raw backtest results JSON:', JSON.stringify(results, null, 2));
    
    console.log('Displaying backtest results:', results);
    console.log('Results structure:', {
        hasMetrics: !!results.metrics,
        metricsKeys: results.metrics ? Object.keys(results.metrics) : [],
        hasCharts: !!results.charts,
        chartsLength: results.charts ? results.charts.length : 0,
        hasTrades: !!results.trades,
        tradesCount: results.trades ? results.trades.length : 0,
        hasActualParameters: !!results.actual_parameters,
        hasOptimizationSummary: !!results.optimization_summary
    });
    
    // Create containers if they don't exist
    if (!backtestResultsContainer.querySelector('#backtest-summary')) {
        console.log('Creating summary container inside results container');
        const summaryDiv = document.createElement('div');
        summaryDiv.id = 'backtest-summary';
        summaryDiv.className = 'mt-4';
        backtestResultsContainer.appendChild(summaryDiv);
    }
    
    // Check if this is a seasonality strategy by looking for specific parameters
    const isSeasonalityStrategy = results.actual_parameters && 
        (results.actual_parameters.positive_days !== undefined || 
         results.actual_parameters.positive_months !== undefined ||
         results.actual_parameters.day_of_week_filter !== undefined ||
         results.actual_parameters.month_of_year_filter !== undefined);
    
    // Get the strategy type from the results data - check multiple possible locations
    let strategyType = '';
    
    // Try to find the strategy type from various possible locations in the results
    if (results.metrics && results.metrics.strategy_type) {
        strategyType = results.metrics.strategy_type;
    } else if (results.actual_parameters && results.actual_parameters.strategy_type) {
        strategyType = results.actual_parameters.strategy_type;
    } else if (isSeasonalityStrategy) {
        strategyType = 'seasonality';
    } else if (results.strategy_type) {
        strategyType = results.strategy_type;
    }
    
    // Check if we can deduce the strategy type from parameters
    if (!strategyType && results.actual_parameters) {
        if (results.actual_parameters.short_period && results.actual_parameters.long_period) {
            if (results.actual_parameters.fast_ma_type === 'ema' || results.actual_parameters.slow_ma_type === 'ema') {
                strategyType = 'ema_crossover';
            } else {
                strategyType = 'sma_crossover';
            }
        } else if (results.actual_parameters.rsi_period) {
            strategyType = 'rsi';
        } else if (results.actual_parameters.period && results.actual_parameters.multiplier && results.actual_parameters.multiplier > 0) {
            strategyType = 'supertrend';
        }
    }
    
    console.log('Strategy type detected:', strategyType || 'unknown');
    
    // Handle strategy explanation container
    let strategyExplanationContainer = backtestResultsContainer.querySelector('#strategy-explanation');
    
    // Remove existing strategy explanation container if it exists
    if (strategyExplanationContainer) {
        strategyExplanationContainer.remove();
        strategyExplanationContainer = null;
    }
    
    // Create a new strategy explanation container
    strategyExplanationContainer = document.createElement('div');
    strategyExplanationContainer.id = 'strategy-explanation';
    strategyExplanationContainer.className = 'mt-4';
    
    // Insert at the beginning of the results container
    if (backtestResultsContainer.firstChild) {
        backtestResultsContainer.insertBefore(strategyExplanationContainer, backtestResultsContainer.firstChild);
    } else {
        backtestResultsContainer.appendChild(strategyExplanationContainer);
    }
    
    // Only create seasonality optimization container if it's a seasonality strategy
    let optimizationContainer = backtestResultsContainer.querySelector('#seasonality-optimization');
    
    // If it's not a seasonality strategy but the container exists from a previous run, remove it
    if (!isSeasonalityStrategy && optimizationContainer) {
        console.log('Removing seasonality optimization container for non-seasonality strategy');
        optimizationContainer.remove();
        optimizationContainer = null;
    }
    
    // If it's a seasonality strategy and the container doesn't exist, create it
    if (isSeasonalityStrategy && !optimizationContainer && (results.actual_parameters || results.optimization_summary)) {
        console.log('Creating seasonality optimization container');
        optimizationContainer = document.createElement('div');
        optimizationContainer.id = 'seasonality-optimization';
        optimizationContainer.className = 'mt-4';
        // Insert after the strategy explanation
        backtestResultsContainer.insertBefore(optimizationContainer, strategyExplanationContainer.nextSibling);
    }
    
    if (!backtestResultsContainer.querySelector('#backtest-charts')) {
        console.log('Creating charts container inside results container');
        const chartsDiv = document.createElement('div');
        chartsDiv.id = 'backtest-charts';
        chartsDiv.className = 'mt-4';
        backtestResultsContainer.appendChild(chartsDiv);
    }
    
    // Show results container
    backtestResultsContainer.style.display = 'block';
    console.log('Results container display set to block', backtestResultsContainer.id);

    // Display strategy explanation for all strategies
    if (strategyExplanationContainer) {
        // For seasonality strategy, display a title only (details will be in the optimization section)
        if (isSeasonalityStrategy) {
            strategyExplanationContainer.innerHTML = `
                <div class="card mb-4">
                    <div class="card-header bg-primary text-white">
                        <h4 class="mb-0">Seasonality Strategy</h4>
                    </div>
                </div>
            `;
            strategyExplanationContainer.style.display = 'block';
        } else {
            // For non-seasonality strategies, display detailed explanation
            displayStrategyExplanation(strategyType, strategyExplanationContainer);
        }
    }

    // Display seasonality optimization results if it's a seasonality strategy
    if (isSeasonalityStrategy) {
        // Note: We're re-querying for the container because it may have been created above
        optimizationContainer = backtestResultsContainer.querySelector('#seasonality-optimization');
        if (optimizationContainer && (results.actual_parameters || results.optimization_summary)) {
            console.log('Displaying seasonality auto-optimization results');
            displaySeasonalityOptimization(results, optimizationContainer);
        } else {
            console.log('No optimization container found or no seasonality data available', {
                containerExists: !!optimizationContainer,
                hasActualParameters: !!results.actual_parameters,
                hasOptimizationSummary: !!results.optimization_summary
            });
        }
    } else {
        console.log('Not a seasonality strategy, skipping optimization results display');
    }

    // Display metrics
    const updatedSummaryContainer = backtestResultsContainer.querySelector('#backtest-summary');
    if (updatedSummaryContainer && results.metrics) {
        console.log('Displaying metrics in summary container');
        displayBacktestSummary(results.metrics, updatedSummaryContainer);
    }
    
    // Display charts
    const updatedChartsContainer = backtestResultsContainer.querySelector('#backtest-charts');
    if (updatedChartsContainer && results.metrics && results.charts_data) {
        console.log('Creating charts from charts_data');
        updatedChartsContainer.innerHTML = `
            <h4>Backtest Charts</h4>
            <div class="chart-container mb-4" style="position: relative; height:400px; width:100%;">
                <h5>Equity Curve</h5>
                <canvas id="equity-curve-chart"></canvas>
            </div>
            <div class="chart-container mb-4" style="position: relative; height:400px; width:100%;">
                <h5>Price Chart with Signals</h5>
                <canvas id="price-chart"></canvas>
            </div>
        `;
        
        // Create the equity curve chart
        createEquityCurveChart(results.charts_data);
        
        // Create the price chart with signals
        createPriceChart(results.charts_data);
    }
    
    // Display trades
    if (results.trades && results.trades.length > 0) {
        // Create trades container if it doesn't exist
        if (!backtestResultsContainer.querySelector('#backtest-trades')) {
            console.log('Creating trades container inside results container');
            const tradesDiv = document.createElement('div');
            tradesDiv.id = 'backtest-trades';
            tradesDiv.className = 'mt-4';
            backtestResultsContainer.appendChild(tradesDiv);
        }
        
        const tradesContainer = backtestResultsContainer.querySelector('#backtest-trades');
        displayTrades(results.trades, tradesContainer);
    }
}

// Display seasonality auto-optimization results
function displaySeasonalityOptimization(results, container) {
    if (!container) {
        console.error('No container provided to displaySeasonalityOptimization');
        return;
    }
    
    console.log('Starting to display seasonality optimization with data:', {
        hasActualParameters: !!results.actual_parameters,
        actualParametersKeys: results.actual_parameters ? Object.keys(results.actual_parameters) : [],
        hasOptimizationSummary: !!results.optimization_summary,
        optimizationSummaryLength: results.optimization_summary ? results.optimization_summary.length : 0
    });
    
    // Start with a simple message if no data is available
    if (!results.actual_parameters && (!results.optimization_summary || results.optimization_summary.length === 0)) {
        container.innerHTML = `
            <div class="alert alert-warning">
                <h4>Seasonality Optimization Results Not Available</h4>
                <p>The seasonality strategy ran, but didn't return any optimization results. 
                This might happen if no significant seasonal patterns were found in your data.</p>
            </div>
        `;
        container.style.display = 'block';
        console.log('No seasonality optimization data available');
        return;
    }
    
    let html = `
        <div class="card mb-4" style="border: 2px solid #17a2b8; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
            <div class="card-header bg-info text-white">
                <h4 class="mb-0">Seasonality Strategy Auto-Optimization Results</h4>
            </div>
            <div class="card-body">
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i> The seasonality strategy automatically analyzes your historical data to identify statistically significant seasonal patterns.
                </div>
    `;
    
    // Display optimization summary if available (user-friendly summary)
    if (results.optimization_summary && results.optimization_summary.length > 0) {
        html += `
            <div class="mb-3">
                <h5>Detected Trading Patterns:</h5>
                <ul class="list-group">
        `;
        
        results.optimization_summary.forEach(item => {
            html += `<li class="list-group-item">${item}</li>`;
        });
        
        html += `
                </ul>
            </div>
        `;
    }
    
    // If we have detailed parameters, show them in a collapsible section
    if (results.actual_parameters) {
        const params = results.actual_parameters;
        
        // Show strategy statistics
        if (params.total_signals || params.buy_signals || params.sell_signals) {
            html += `
                <div class="mb-3">
                    <h5>Signal Statistics:</h5>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="card bg-light">
                                <div class="card-body text-center">
                                    <h2 class="text-primary">${params.total_signals || 0}</h2>
                                    <p class="mb-0">Total Signals</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card bg-light">
                                <div class="card-body text-center">
                                    <h2 class="text-success">${params.buy_signals || 0}</h2>
                                    <p class="mb-0">Buy Signals</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card bg-light">
                                <div class="card-body text-center">
                                    <h2 class="text-danger">${params.sell_signals || 0}</h2>
                                    <p class="mb-0">Sell Signals</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Add a collapsible section for detailed parameters
        html += `
            <div class="mb-3">
                <button class="btn btn-outline-primary w-100" type="button" data-bs-toggle="collapse" data-bs-target="#detailedParams">
                    Show Detailed Parameters
                </button>
                <div class="collapse mt-3" id="detailedParams">
                    <div class="card card-body">
                        <h5>Auto-Optimization Parameters:</h5>
                        <ul class="list-group">
        `;
        
        // Add threshold parameters
        html += `
            <li class="list-group-item">Return Threshold: ${params.return_threshold || 'N/A'}</li>
            <li class="list-group-item">Significance Threshold: ${params.significance_threshold || 'N/A'}</li>
            <li class="list-group-item">Exit After Days: ${params.exit_after_days || 'N/A'}</li>
            <li class="list-group-item">Combined Seasonality: ${params.combined_seasonality ? 'Yes' : 'No'}</li>
        `;
        
        // Add days of week filter
        if (params.day_of_week_filter && params.day_of_week_filter.length > 0) {
            const dayNames = {
                0: 'Monday', 1: 'Tuesday', 2: 'Wednesday',
                3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'
            };
            const daysList = params.day_of_week_filter.map(day => dayNames[day] || day).join(', ');
            html += `<li class="list-group-item">Buy Days: ${daysList}</li>`;
        }
        
        // Add negative days of week
        if (params.negative_day_of_week && params.negative_day_of_week.length > 0) {
            const dayNames = {
                0: 'Monday', 1: 'Tuesday', 2: 'Wednesday',
                3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'
            };
            const daysList = params.negative_day_of_week.map(day => dayNames[day] || day).join(', ');
            html += `<li class="list-group-item">Sell Days: ${daysList}</li>`;
        }
        
        // Add months of year filter
        if (params.month_of_year_filter && params.month_of_year_filter.length > 0) {
            const monthNames = {
                1: 'January', 2: 'February', 3: 'March', 4: 'April',
                5: 'May', 6: 'June', 7: 'July', 8: 'August',
                9: 'September', 10: 'October', 11: 'November', 12: 'December'
            };
            const monthsList = params.month_of_year_filter.map(month => monthNames[month] || month).join(', ');
            html += `<li class="list-group-item">Buy Months: ${monthsList}</li>`;
        }
        
        // Add negative months of year 
        if (params.negative_month_of_year && params.negative_month_of_year.length > 0) {
            const monthNames = {
                1: 'January', 2: 'February', 3: 'March', 4: 'April',
                5: 'May', 6: 'June', 7: 'July', 8: 'August',
                9: 'September', 10: 'October', 11: 'November', 12: 'December'
            };
            const monthsList = params.negative_month_of_year.map(month => monthNames[month] || month).join(', ');
            html += `<li class="list-group-item">Sell Months: ${monthsList}</li>`;
        }
        
        html += `
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }
    
    html += `
            </div>
        </div>
    `;
    
    // Set the container HTML and make it visible with animation
    container.innerHTML = html;
    container.style.display = 'block';
    container.style.opacity = 0;
    
    // Simple fade-in animation
    setTimeout(() => {
        container.style.transition = 'opacity 0.5s ease-in';
        container.style.opacity = 1;
    }, 100);
    
    console.log('Seasonality optimization display complete');
}

// Display trades table
function displayTrades(trades, container) {
    if (!trades || !container) return;
    
    // Create or get trades container
    let tradesContainer = container.querySelector('#backtest-trades');
    if (!tradesContainer) {
        tradesContainer = document.createElement('div');
        tradesContainer.id = 'backtest-trades';
        tradesContainer.className = 'mt-4';
        container.appendChild(tradesContainer);
    }
    
    // Create trades table
    let tableHtml = `
        <h4>Trade Summary</h4>
        <div class="table-responsive">
            <table class="table table-bordered table-striped table-sm">
                <thead>
                    <tr>
                        <th>Entry Date</th>
                        <th>Exit Date</th>
                        <th>Entry Price</th>
                        <th>Exit Price</th>
                        <th>Profit ($)</th>
                        <th>Profit (%)</th>
                        <th>Result</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Add each trade as a row
    for (const trade of trades) {
        const profitClass = trade.profit > 0 ? 'text-success' : 'text-danger';
        tableHtml += `
            <tr>
                <td>${trade.entry_date}</td>
                <td>${trade.exit_date}</td>
                <td>${formatNumber(trade.entry_price)}</td>
                <td>${formatNumber(trade.exit_price)}</td>
                <td class="${profitClass}">${formatNumber(trade.profit)}</td>
                <td class="${profitClass}">${formatNumber(trade.profit_pct)}%</td>
                <td class="${profitClass}">${trade.result.toUpperCase()}</td>
            </tr>
        `;
    }
    
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    tradesContainer.innerHTML = tableHtml;
}

// Helper function to create metrics HTML directly
function createMetricsHtml(metrics) {
    if (!metrics) return '';
    
    let tableHtml = `
        <div id="backtest-summary-manual" class="mt-4">
            <h4>Backtest Performance Metrics</h4>
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
    
    return tableHtml;
}

// Display backtest summary metrics
function displayBacktestSummary(metrics, container) {
    if (!container || !metrics) {
        console.error('Summary container not found or no metrics data:', { container: !!container, metrics: !!metrics });
        return;
    }
    
    console.log('Displaying summary metrics:', metrics);
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
    
    container.innerHTML = tableHtml;
    container.style.display = 'block';
    console.log('Summary metrics updated in container', container.id);
}

// Create equity curve chart
function createEquityCurveChart(chartsData) {
    if (!chartsData || !chartsData.equity_curve) {
        console.warn('No equity curve data available');
        return;
    }
    
    const equityCurve = chartsData.equity_curve;
    const equityCtx = document.getElementById('equity-curve-chart');
    
    if (!equityCtx) {
        console.warn('Equity curve chart canvas element not found');
        return;
    }
    
    new Chart(equityCtx, {
        type: 'line',
        data: {
            labels: equityCurve.dates,
            datasets: [
                {
                    label: 'Strategy',
                    data: equityCurve.equity,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.1,
                    fill: true
                },
                {
                    label: 'Buy & Hold',
                    data: equityCurve.buy_and_hold,
                    borderColor: 'rgb(192, 75, 75)',
                    backgroundColor: 'rgba(192, 75, 75, 0.1)',
                    borderDash: [5, 5],
                    tension: 0.1,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: false },
                tooltip: { mode: 'index', intersect: false }
            },
            scales: {
                x: { display: true, title: { display: true, text: 'Date' }, ticks: { maxTicksLimit: 12 } },
                y: { display: true, title: { display: true, text: 'Equity ($)' } }
            }
        }
    });
}

// Create price chart with signals
function createPriceChart(chartsData) {
    if (!chartsData || !chartsData.price_signals) {
        console.warn('No price signals data available');
        return;
    }
    
    const priceSignals = chartsData.price_signals;
    const priceCtx = document.getElementById('price-chart');
    
    if (!priceCtx) {
        console.warn('Price chart canvas element not found');
        return;
    }
    
    // Prepare buy/sell/exit markers
    const buyPoints = priceSignals.buy_signals.map(i => ({ x: i, y: priceSignals.close[i], r: 7 }));
    const sellPoints = priceSignals.sell_signals.map(i => ({ x: i, y: priceSignals.close[i], r: 7 }));
    const exitPoints = priceSignals.exit_signals ? priceSignals.exit_signals.map(i => ({ x: i, y: priceSignals.close[i], r: 6 })) : [];
    
    new Chart(priceCtx, {
        type: 'line',
        data: {
            labels: priceSignals.dates,
            datasets: [
                {
                    label: 'Price',
                    data: priceSignals.close,
                    borderColor: 'rgb(100, 100, 100)',
                    backgroundColor: 'rgba(100, 100, 100, 0.1)',
                    tension: 0.1,
                    fill: false,
                    pointRadius: 0
                },
                {
                    label: 'Buy',
                    data: buyPoints,
                    backgroundColor: 'rgba(75, 192, 75, 0.8)',
                    borderColor: 'rgba(75, 192, 75, 1)',
                    type: 'bubble',
                    pointStyle: 'triangle',
                    pointRadius: 8,
                    pointHoverRadius: 10
                },
                {
                    label: 'Sell',
                    data: sellPoints,
                    backgroundColor: 'rgba(192, 75, 75, 0.8)',
                    borderColor: 'rgba(192, 75, 75, 1)',
                    type: 'bubble',
                    pointStyle: 'triangle',
                    pointRadius: 8,
                    pointRotation: 180,
                    pointHoverRadius: 10
                },
                {
                    label: 'Exit',
                    data: exitPoints,
                    backgroundColor: 'rgba(75, 75, 192, 0.8)',
                    borderColor: 'rgba(75, 75, 192, 1)',
                    type: 'bubble',
                    pointStyle: 'circle',
                    pointRadius: 7,
                    pointHoverRadius: 9
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.dataset.label === 'Buy') {
                                return 'BUY @ ' + context.parsed.y;
                            } else if (context.dataset.label === 'Sell') {
                                return 'SELL @ ' + context.parsed.y;
                            } else if (context.dataset.label === 'Exit') {
                                return 'EXIT @ ' + context.parsed.y;
                            }
                            return context.dataset.label + ': ' + context.parsed.y;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxTicksLimit: 12,
                        callback: function(value) { return priceSignals.dates[value]; }
                    }
                },
                y: { title: { display: true, text: 'Price' } }
            }
        }
    });
}

// Display strategy-specific explanation
function displayStrategyExplanation(strategyType, container) {
    if (!container || !strategyType) {
        console.error('Container or strategy type missing for displayStrategyExplanation');
        return;
    }
    
    // Strategy descriptions and explanations
    const strategyInfo = {
        'trend_following': {
            title: 'Trend Following Strategy',
            description: 'This strategy follows market trends by using moving average crossovers. It generates buy signals when a shorter-term moving average crosses above a longer-term moving average (golden cross), and sell signals when the shorter-term MA crosses below the longer-term MA (death cross).',
            howItWorks: 'The strategy assumes that once a trend has been established, it is more likely to continue than to reverse. Moving averages help smooth out price data to identify the direction of the trend.'
        },
        'mean_reversion': {
            title: 'Mean Reversion Strategy',
            description: 'This strategy is based on the concept that prices tend to revert to their average over time. It generates buy signals when prices move significantly below their average (oversold), and sell signals when prices move significantly above their average (overbought).',
            howItWorks: 'The strategy uses indicators like RSI (Relative Strength Index) to identify when a market has moved too far in one direction and is likely to revert back.'
        },
        'breakout': {
            title: 'Breakout Strategy',
            description: 'This strategy identifies when price breaks through significant support or resistance levels. It generates buy signals when price breaks above resistance with increased volume, and sell signals when price breaks below support with increased volume.',
            howItWorks: 'The strategy looks for price movements that exceed previous highs or lows, indicating a potential new trend direction.'
        },
        'sma_crossover': {
            title: 'SMA Crossover Strategy',
            description: 'This strategy uses Simple Moving Average (SMA) crossovers to identify trend changes. It generates buy signals when a shorter-term SMA crosses above a longer-term SMA, and sell signals when the shorter-term SMA crosses below the longer-term SMA.',
            howItWorks: 'SMAs calculate the average price over a specified period, with each data point having equal weight. Crossovers indicate changes in momentum and potential trend reversals.'
        },
        'ema_crossover': {
            title: 'EMA Crossover Strategy',
            description: 'This strategy uses Exponential Moving Average (EMA) crossovers to identify trend changes. It generates buy signals when a shorter-term EMA crosses above a longer-term EMA, and sell signals when the shorter-term EMA crosses below the longer-term EMA.',
            howItWorks: 'EMAs give more weight to recent prices, making them more responsive to new information than SMAs. This makes EMA crossovers potentially faster at identifying trend changes.'
        },
        'macd_crossover': {
            title: 'MACD Crossover Strategy',
            description: 'This strategy uses the Moving Average Convergence Divergence (MACD) indicator to identify momentum changes. It generates buy signals when the MACD line crosses above the signal line, and sell signals when the MACD line crosses below the signal line.',
            howItWorks: 'The MACD is calculated by subtracting the 26-period EMA from the 12-period EMA. The signal line is a 9-period EMA of the MACD line. Crossovers indicate potential trend changes and trading opportunities.'
        },
        'rsi': {
            title: 'RSI Strategy',
            description: 'This strategy uses the Relative Strength Index (RSI) to identify overbought and oversold conditions. It generates buy signals when RSI moves from oversold to normal levels, and sell signals when RSI moves from overbought to normal levels.',
            howItWorks: 'The RSI measures the speed and change of price movements on a scale from 0 to 100. Values below 30 generally indicate oversold conditions, while values above 70 indicate overbought conditions.'
        },
        'bollinger_breakout': {
            title: 'Bollinger Bands Breakout Strategy',
            description: 'This strategy identifies when price breaks out of the Bollinger Bands. It generates buy signals when price crosses above the upper band, and sell signals when price crosses below the lower band.',
            howItWorks: 'Bollinger Bands consist of a middle band (usually a 20-period SMA) and two outer bands that are standard deviations away from the middle band. Breakouts indicate potential trend continuations or reversals.'
        },
        'supertrend': {
            title: 'SuperTrend Strategy',
            description: 'This strategy uses the SuperTrend indicator to identify trend direction and potential reversals. It generates buy signals when price crosses above the SuperTrend line, and sell signals when price crosses below the SuperTrend line.',
            howItWorks: 'The SuperTrend is calculated using Average True Range (ATR) to adjust for market volatility. It plots a single line above or below the price, indicating the current trend direction.'
        },
        'adx': {
            title: 'ADX Strategy',
            description: 'This strategy uses the Average Directional Index (ADX) to identify trend strength. It generates buy signals when ADX rises above a threshold in conjunction with positive directional movement, and sell signals when ADX rises above a threshold with negative directional movement.',
            howItWorks: 'The ADX measures trend strength on a scale from 0 to 100, with values above 25 generally indicating a strong trend. It does not indicate trend direction by itself, so it\'s often used with +DI and -DI indicators.'
        },
        'stochastic': {
            title: 'Stochastic Oscillator Strategy',
            description: 'This strategy uses the Stochastic Oscillator to identify potential turning points in price by measuring the relationship between closing price and the high-low range over a period of time.',
            howItWorks: 'The Stochastic Oscillator consists of two lines: %K and %D (a moving average of %K). Buy signals occur when the lines cross above the oversold level (typically 20), and sell signals occur when they cross below the overbought level (typically 80).'
        },
        'cci': {
            title: 'CCI Strategy',
            description: 'This strategy uses the Commodity Channel Index (CCI) to identify cyclical trends in price movement. It helps identify overbought and oversold levels, as well as potential trend reversals.',
            howItWorks: 'The CCI compares the current price to an average price over a period of time. Readings above +100 may indicate overbought conditions, while readings below -100 may indicate oversold conditions.'
        },
        'williams_r': {
            title: 'Williams %R Strategy',
            description: 'This strategy uses the Williams %R indicator to identify overbought and oversold conditions in the market. It helps identify potential trend reversals by measuring the current closing price in relation to the high and low range over a specific period.',
            howItWorks: 'Williams %R ranges from 0 to -100, with readings between -80 and -100 indicating oversold conditions (potential buy signals), and readings between 0 and -20 indicating overbought conditions (potential sell signals).'
        },
        'cmf': {
            title: 'Chaikin Money Flow Strategy',
            description: 'This strategy uses the Chaikin Money Flow (CMF) indicator to measure the amount of Money Flow Volume over a specific period. It helps identify buying or selling pressure in the market.',
            howItWorks: 'CMF combines price and volume to gauge buying and selling pressure. Positive values indicate accumulation (buying pressure), while negative values indicate distribution (selling pressure).'
        },
        'atr_breakout': {
            title: 'ATR Breakout Strategy',
            description: 'This strategy uses the Average True Range (ATR) to identify significant price movements. It generates buy signals when price moves up by a multiple of the ATR, and sell signals when price moves down by a multiple of the ATR.',
            howItWorks: 'ATR measures market volatility by calculating the average range between high and low prices. By using multiples of ATR, the strategy adapts to changing market conditions and volatility levels.'
        },
        'donchian_breakout': {
            title: 'Donchian Channel Breakout Strategy',
            description: 'This strategy uses Donchian Channels to identify breakouts from recent price ranges. It generates buy signals when price breaks above the upper channel, and sell signals when price breaks below the lower channel.',
            howItWorks: 'Donchian Channels plot the highest high and lowest low over a specified period, creating a price envelope. Breakouts from this range often indicate the start of new trends.'
        },
        'keltner_reversal': {
            title: 'Keltner Channel Reversal Strategy',
            description: 'This strategy uses Keltner Channels to identify potential price reversals. It looks for price to reach the channel boundaries and then reverse direction.',
            howItWorks: 'Keltner Channels use an EMA as the middle line with upper and lower bands at fixed multiples of ATR. The strategy generates buy signals when price touches the lower band and starts to rise, and sell signals when price touches the upper band and starts to fall.'
        },
        'adaptive_trend': {
            title: 'Adaptive Trend Strategy',
            description: 'This advanced strategy dynamically adjusts to market conditions by using multiple indicators and adapting its parameters based on recent price action and volatility.',
            howItWorks: 'The strategy combines trend-following and momentum indicators while adjusting their sensitivity based on market volatility. This adaptive approach helps it perform well in different market environments.'
        },
        'hybrid_momentum_volatility': {
            title: 'Hybrid Momentum/Volatility Strategy',
            description: 'This strategy combines momentum indicators with volatility measures to identify high-probability trading opportunities with controlled risk.',
            howItWorks: 'By using both momentum indicators (like RSI) and volatility indicators (like Bollinger Bands), the strategy aims to enter trades when momentum is favorable and volatility conditions suggest a good risk/reward ratio.'
        },
        'pattern_recognition': {
            title: 'Pattern Recognition Strategy',
            description: 'This strategy identifies common chart patterns that historically indicate potential trend continuations or reversals.',
            howItWorks: 'The strategy analyzes price data to detect recurring patterns like double tops/bottoms, head and shoulders, triangles, and more. When recognized, these patterns can provide trading signals with definable entry and exit points.'
        },
        'seasonality': {
            title: 'Seasonality Strategy',
            description: 'This strategy identifies and trades based on recurring seasonal patterns in price movements. It analyzes historical data to find statistically significant patterns related to specific days of the week, months of the year, or days of the month.',
            howItWorks: 'By analyzing historical returns across different time periods, the strategy identifies when prices tend to consistently rise or fall, and generates trading signals based on these recurring patterns.'
        }
    };
    
    // Default explanation if strategy type not found
    const defaultInfo = {
        title: 'Trading Strategy',
        description: 'This trading strategy analyzes market data to identify potential buying and selling opportunities based on its specific rules and indicators.',
        howItWorks: 'The strategy processes historical price and volume data to generate signals that aim to outperform a simple buy-and-hold approach.'
    };
    
    // Get strategy info or use default
    const info = strategyInfo[strategyType] || defaultInfo;
    
    // Create HTML for strategy explanation
    let html = `
        <div class="card mb-4">
            <div class="card-header bg-primary text-white">
                <h4 class="mb-0">${info.title}</h4>
            </div>
            <div class="card-body">
                <p class="mb-3">${info.description}</p>
                <h5>How It Works</h5>
                <p>${info.howItWorks}</p>
            </div>
        </div>
    `;
    
    // Set container HTML
    container.innerHTML = html;
    container.style.display = 'block';
    
    console.log(`Strategy explanation displayed for ${strategyType}`);
}

// Initialize backtest component
export function initializeBacktestView() {
    console.log('Initializing Backtest View...');
    const runBacktestButton = document.getElementById('run-backtest-btn');

    if (runBacktestButton) {
        console.log('Run Backtest button found, attaching click listener.');
        runBacktestButton.addEventListener('click', async () => {
            console.log('Run Backtest button clicked.');
            // Gather parameters for the backtest manually since there is no form
            const params = {};

            const initialCapitalInput = document.getElementById('initial-capital');
            if (initialCapitalInput) {
                params.initial_capital = parseFloat(initialCapitalInput.value) || 100.0;
            }

            const commissionInput = document.getElementById('commission'); // Matches the ID in index.html
            if (commissionInput) {
                params.commission = parseFloat(commissionInput.value) || 0.001;
            }

            const startDateInput = document.getElementById('backtest-start-date');
            if (startDateInput && startDateInput.value) {
                params.start_date = startDateInput.value;
            }

            const endDateInput = document.getElementById('backtest-end-date');
            if (endDateInput && endDateInput.value) {
                params.end_date = endDateInput.value;
            }

            // Strategy and its parameters will be picked up from appState by the runBacktest function
            // as per its existing logic: appState.selectedStrategy and appState.strategyParameters
            console.log('Manually gathered backtest config params:', params);
            
            // Call the main runBacktest function (which handles API call and result display)
            await runBacktest(params); 
        });
    } else {
        console.error('Run Backtest button (id: run-backtest-btn) not found. Backtest functionality will not be triggered.');
    }
    
    // Any other initializations for backtest view can go here
    // For example, if there are default displays or states to set up for the results area.
    const backtestResultsContainer = document.getElementById('backtest-results');
    if (backtestResultsContainer) {
        // Ensure it is clear or shows a placeholder if no results yet.
        // displayBacktestResults will populate it when results are available.
        // For now, ensure it doesn't show stale data if any.
        // backtestResultsContainer.innerHTML = '<p><em>Run a backtest to see results here.</em></p>';
    }
}
