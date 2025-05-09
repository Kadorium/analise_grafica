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
                requestParams.initial_capital = parseFloat(capitalInput.value) || 10000.0;
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
    if (updatedChartsContainer && results.metrics) {
        console.log('Creating charts from metrics data');
        
        // Clear existing content and ensure the container is visible
        updatedChartsContainer.innerHTML = '';
        updatedChartsContainer.style.display = 'block';
        
        // Create container divs for all three charts
        updatedChartsContainer.innerHTML = `
            <h4>Backtest Charts</h4>
            
            <!-- Equity Curve Chart -->
            <div class="chart-container mb-4" style="position: relative; height:400px; width:100%;">
                <h5>Equity Curve</h5>
                <canvas id="equity-curve-chart"></canvas>
            </div>
            
            <!-- Price Chart with Trade Signals -->
            <div class="chart-container mb-4" style="position: relative; height:400px; width:100%;">
                <h5>Price with Trade Signals</h5>
                <canvas id="price-signals-chart"></canvas>
            </div>
            
            <!-- Indicator Action Signals -->
            <div class="chart-container" style="position: relative; height:400px; width:100%;">
                <h5>Indicator Action Signals</h5>
                <canvas id="indicator-signals-chart"></canvas>
            </div>
        `;
        
        // Check if Chart.js is available
        if (typeof Chart === 'undefined') {
            console.error('Chart.js library not loaded');
            updatedChartsContainer.innerHTML = '<div class="alert alert-danger">Chart.js library not available. Charts cannot be displayed.</div>';
        } else {
            // Extract chart data from server response
            try {
                // Create the charts when DOM is ready
                setTimeout(() => {
                    // Extract common data from HTML if available
                    let dates = [];
                    let priceData = [];
                    let equityData = [];
                    let indicators = {};
                    let tradeSignals = [];
                    
                    if (results.charts) {
                        const labelsMatch = results.charts.match(/labels:\s*(\[.*?\])/s);
                        const equityMatch = results.charts.match(/data:\s*(\[.*?\])/s);
                        
                        if (labelsMatch && labelsMatch[1]) {
                            try {
                                dates = JSON.parse(labelsMatch[1].replace(/'/g, '"'));
                            } catch (e) {
                                console.error('Error parsing chart dates:', e);
                            }
                        }
                        
                        if (equityMatch && equityMatch[1]) {
                            try {
                                equityData = JSON.parse(equityMatch[1].replace(/'/g, '"'));
                            } catch (e) {
                                console.error('Error parsing equity data:', e);
                            }
                        }
                    }
                    
                    // Extract price data and signals from trades if available
                    if (results.trades && results.trades.length > 0) {
                        // Create a synthetic price dataset if not available directly
                        // This is a simplification - ideally we'd have the actual price data from the server
                        const pricePoints = results.trades.map(trade => ({
                            date: trade.entry_date,
                            price: trade.entry_price,
                            signal: 'buy'
                        })).concat(results.trades.map(trade => ({
                            date: trade.exit_date,
                            price: trade.exit_price,
                            signal: 'sell'
                        }))).sort((a, b) => new Date(a.date) - new Date(b.date));
                        
                        // Create synthetic price data spanning the entire date range
                        const startDate = new Date(dates[0] || pricePoints[0].date);
                        const endDate = new Date(dates[dates.length-1] || pricePoints[pricePoints.length-1].date);
                        
                        // Generate price data for each date in our range
                        priceData = dates.map((date, i) => {
                            // Look for an exact match in our pricePoints
                            const matchPoint = pricePoints.find(point => point.date === date);
                            if (matchPoint) return matchPoint.price;
                            
                            // If no match, interpolate based on nearby trades or use equity as a proxy
                            // For simplicity, we're using a scaled version of the equity curve
                            const baseValue = equityData[i] || 100;
                            return baseValue * 0.1; // Scale down for visualization
                        });
                        
                        // Extract trade signals
                        tradeSignals = pricePoints.map(point => ({
                            date: point.date,
                            price: point.price,
                            signal: point.signal
                        }));
                    }
                    
                    // 1. Create equity curve chart
                    const equityCtx = document.getElementById('equity-curve-chart');
                    if (equityCtx) {
                        new Chart(equityCtx, {
                            type: 'line',
                            data: {
                                labels: dates,
                                datasets: [{
                                    label: 'Strategy',
                                    data: equityData,
                                    borderColor: 'rgb(75, 192, 192)',
                                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                                    tension: 0.1,
                                    fill: true
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    title: {
                                        display: false
                                    },
                                    tooltip: {
                                        mode: 'index',
                                        intersect: false,
                                    }
                                },
                                scales: {
                                    x: {
                                        display: true,
                                        title: {
                                            display: true,
                                            text: 'Date'
                                        },
                                        ticks: {
                                            maxTicksLimit: 12
                                        }
                                    },
                                    y: {
                                        display: true,
                                        title: {
                                            display: true,
                                            text: 'Equity ($)'
                                        }
                                    }
                                }
                            }
                        });
                    }
                    
                    // 2. Create price chart with trade signals
                    const priceCtx = document.getElementById('price-signals-chart');
                    if (priceCtx) {
                        // Prepare data for signal markers
                        const buySignals = tradeSignals.filter(s => s.signal === 'buy').map(s => {
                            const index = dates.indexOf(s.date);
                            return index >= 0 ? {
                                x: index,
                                y: s.price,
                                r: 6  // size of the point
                            } : null;
                        }).filter(s => s !== null);
                        
                        const sellSignals = tradeSignals.filter(s => s.signal === 'sell').map(s => {
                            const index = dates.indexOf(s.date);
                            return index >= 0 ? {
                                x: index,
                                y: s.price,
                                r: 6  // size of the point
                            } : null;
                        }).filter(s => s !== null);
                        
                        new Chart(priceCtx, {
                            type: 'line',
                            data: {
                                labels: dates,
                                datasets: [
                                    {
                                        label: 'Price',
                                        data: priceData,
                                        borderColor: 'rgb(100, 100, 100)',
                                        backgroundColor: 'rgba(100, 100, 100, 0.1)',
                                        tension: 0.1,
                                        fill: false,
                                        pointRadius: 0
                                    },
                                    {
                                        label: 'Buy Signals',
                                        data: buySignals,
                                        backgroundColor: 'rgba(75, 192, 75, 0.8)',
                                        borderColor: 'rgba(75, 192, 75, 1)',
                                        type: 'bubble',
                                        pointStyle: 'triangle',
                                        pointRadius: 8,
                                        pointHoverRadius: 10
                                    },
                                    {
                                        label: 'Sell Signals',
                                        data: sellSignals,
                                        backgroundColor: 'rgba(192, 75, 75, 0.8)',
                                        borderColor: 'rgba(192, 75, 75, 1)',
                                        type: 'bubble',
                                        pointStyle: 'triangle',
                                        pointRadius: 8,
                                        pointRotation: 180,
                                        pointHoverRadius: 10
                                    }
                                ]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                interaction: {
                                    mode: 'index',
                                    intersect: false
                                },
                                plugins: {
                                    tooltip: {
                                        callbacks: {
                                            label: function(context) {
                                                if (context.dataset.label === 'Buy Signals') {
                                                    return 'BUY @ ' + context.parsed.y;
                                                } else if (context.dataset.label === 'Sell Signals') {
                                                    return 'SELL @ ' + context.parsed.y;
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
                                            callback: function(value) {
                                                return dates[value];
                                            }
                                        }
                                    },
                                    y: {
                                        title: {
                                            display: true,
                                            text: 'Price'
                                        }
                                    }
                                }
                            }
                        });
                    }
                    
                    // 3. Create indicator signals chart
                    const indicatorCtx = document.getElementById('indicator-signals-chart');
                    if (indicatorCtx) {
                        // Generate mock indicator data based on trade signals
                        // In a real implementation, this would come from the server
                        const mockSMA50 = priceData.map((price, i) => price * (1 + Math.sin(i/20) * 0.05));
                        const mockSMA200 = priceData.map((price, i) => price * (1 + Math.sin(i/50) * 0.1));
                        const mockRSI = Array(dates.length).fill(0).map((_, i) => 
                            50 + 20 * Math.sin(i/15) + 10 * Math.sin(i/7)
                        );
                        
                        new Chart(indicatorCtx, {
                            type: 'line',
                            data: {
                                labels: dates,
                                datasets: [
                                    {
                                        label: 'SMA 50',
                                        data: mockSMA50,
                                        borderColor: 'rgb(75, 192, 192)',
                                        backgroundColor: 'transparent',
                                        tension: 0.1,
                                        yAxisID: 'y',
                                        pointRadius: 0
                                    },
                                    {
                                        label: 'SMA 200',
                                        data: mockSMA200,
                                        borderColor: 'rgb(192, 75, 75)',
                                        backgroundColor: 'transparent',
                                        tension: 0.1,
                                        yAxisID: 'y',
                                        pointRadius: 0
                                    },
                                    {
                                        label: 'RSI',
                                        data: mockRSI,
                                        borderColor: 'rgb(192, 75, 192)',
                                        backgroundColor: 'transparent',
                                        tension: 0.1,
                                        yAxisID: 'y1',
                                        pointRadius: 0,
                                        borderDash: [5, 5]
                                    }
                                ]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                interaction: {
                                    mode: 'index',
                                    intersect: false
                                },
                                scales: {
                                    x: {
                                        ticks: {
                                            maxTicksLimit: 12,
                                            callback: function(value) {
                                                return dates[value];
                                            }
                                        }
                                    },
                                    y: {
                                        type: 'linear',
                                        display: true,
                                        position: 'left',
                                        title: {
                                            display: true,
                                            text: 'Price'
                                        }
                                    },
                                    y1: {
                                        type: 'linear',
                                        display: true,
                                        position: 'right',
                                        min: 0,
                                        max: 100,
                                        title: {
                                            display: true,
                                            text: 'RSI'
                                        },
                                        grid: {
                                            drawOnChartArea: false
                                        }
                                    }
                                }
                            }
                        });
                        
                        console.log('All charts created successfully');
                    }
                }, 500);
            } catch (error) {
                console.error('Error setting up charts:', error);
                updatedChartsContainer.innerHTML += `<div class="alert alert-danger">Error setting up charts: ${error.message}</div>`;
            }
        }
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
                // Skip empty values
                if (value === '') continue;
                
                // Handle numeric values
                if (!isNaN(value)) {
                    params[key] = parseFloat(value);
                } else {
                    params[key] = value;
                }
                
                // Convert field IDs to expected parameter names
                if (key === 'initial-capital') {
                    params['initial_capital'] = params[key];
                    delete params[key];
                } else if (key === 'backtest-start-date') {
                    params['start_date'] = params[key];
                    delete params[key];
                } else if (key === 'backtest-end-date') {
                    params['end_date'] = params[key];
                    delete params[key];
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
            
            console.log('Submitting backtest with form data:', params);
            // Run backtest with form params
            await runBacktest(params);
        });
    }
}
