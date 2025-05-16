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
        tradesCount: results.trades ? results.trades.length : 0
    });
    
    // Create containers if they don't exist
    if (!backtestResultsContainer.querySelector('#backtest-summary')) {
        console.log('Creating summary container inside results container');
        const summaryDiv = document.createElement('div');
        summaryDiv.id = 'backtest-summary';
        summaryDiv.className = 'mt-4';
        backtestResultsContainer.appendChild(summaryDiv);
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
                <h5>Price with Trade Signals</h5>
                <canvas id="price-signals-chart"></canvas>
            </div>
            <div class="chart-container" style="position: relative; height:400px; width:100%;">
                <h5>Indicator Action Signals</h5>
                <canvas id="indicator-signals-chart"></canvas>
            </div>
        `;
        setTimeout(() => {
            const chartsData = results.charts_data;
            // 1. Equity Curve Chart
            const equityCurve = chartsData.equity_curve;
            const equityCtx = document.getElementById('equity-curve-chart');
            if (equityCtx) {
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
            // 2. Price with Trade Signals Chart
            const priceSignals = chartsData.price_signals;
            const priceCtx = document.getElementById('price-signals-chart');
            if (priceCtx) {
                // Prepare buy/sell/exit markers
                const buyPoints = priceSignals.buy_signals.map(i => ({ x: i, y: priceSignals.close[i], r: 7 }));
                const sellPoints = priceSignals.sell_signals.map(i => ({ x: i, y: priceSignals.close[i], r: 7 }));
                const exitPoints = priceSignals.exit_signals.map(i => ({ x: i, y: priceSignals.close[i], r: 6 }));
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
            // 3. Indicator Action Signals Chart
            const indicatorCtx = document.getElementById('indicator-signals-chart');
            if (indicatorCtx) {
                // Plot all available indicators (up to 3 for clarity)
                const indicatorKeys = Object.keys(chartsData.indicators);
                const indicatorDatasets = indicatorKeys.slice(0, 3).map((key, idx) => ({
                    label: key,
                    data: chartsData.indicators[key],
                    borderColor: ['rgb(75, 192, 192)', 'rgb(192, 75, 75)', 'rgb(192, 75, 192)'][idx % 3],
                    backgroundColor: 'transparent',
                    tension: 0.1,
                    yAxisID: idx === 2 ? 'y1' : 'y',
                    pointRadius: 0,
                    borderDash: idx === 2 ? [5, 5] : []
                }));
                new Chart(indicatorCtx, {
                    type: 'line',
                    data: {
                        labels: priceSignals.dates,
                        datasets: indicatorDatasets
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: { mode: 'index', intersect: false },
                        scales: {
                            x: {
                                ticks: {
                                    maxTicksLimit: 12,
                                    callback: function(value) { return priceSignals.dates[value]; }
                                }
                            },
                            y: {
                                type: 'linear',
                                display: true,
                                position: 'left',
                                title: { display: true, text: 'Value' }
                            },
                            y1: {
                                type: 'linear',
                                display: indicatorDatasets.length > 2,
                                position: 'right',
                                min: 0,
                                max: 100,
                                title: { display: true, text: indicatorDatasets.length > 2 ? indicatorKeys[2] : '' },
                                grid: { drawOnChartArea: false }
                            }
                        }
                    }
                });
            }
            console.log('All charts created successfully');
        }, 500);
    } else {
        console.warn('No charts data found or charts container missing');
        if (updatedChartsContainer) {
            updatedChartsContainer.innerHTML = '<div class="alert alert-warning">No chart data available for this backtest.</div>';
        }
    }
    
    // Display trades table if available
    if (results.trades && results.trades.length > 0) {
        console.log('Displaying trades table');
        displayTrades(results.trades, backtestResultsContainer);
    }
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
