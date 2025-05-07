// App.js - Main JavaScript file for the Trading Analysis System

// DOM Element References
const dataTab = document.getElementById('data-tab');
const indicatorsTab = document.getElementById('indicators-tab');
const strategiesTab = document.getElementById('strategies-tab');
const backtestTab = document.getElementById('backtest-tab');
const optimizationTab = document.getElementById('optimization-tab');
const seasonalityTab = document.getElementById('seasonality-tab');
const resultsTab = document.getElementById('results-tab');

const pageTitle = document.getElementById('page-title');

const dataSection = document.getElementById('data-section');
const indicatorsSection = document.getElementById('indicators-section');
const strategiesSection = document.getElementById('strategies-section');
const backtestSection = document.getElementById('backtest-section');
const optimizationSection = document.getElementById('optimization-section');
const seasonalitySection = document.getElementById('seasonality-section');
const resultsSection = document.getElementById('results-section');

const uploadForm = document.getElementById('upload-form');
const csvFileInput = document.getElementById('csv-file');
const uploadProcessBtn = document.getElementById('upload-process-btn');

const dataInfo = document.getElementById('data-info');
const dataPreview = document.getElementById('data-preview');

const saveConfigBtn = document.getElementById('save-config-btn');
const exportJsonBtn = document.getElementById('export-json-btn');
const exportCsvBtn = document.getElementById('export-csv-btn');

const errorModal = new bootstrap.Modal(document.getElementById('error-modal'));
const errorMessage = document.getElementById('error-message');

const saveConfigModal = new bootstrap.Modal(document.getElementById('save-config-modal'));
const saveConfigConfirmBtn = document.getElementById('save-config-confirm');

// Global state
let dataUploaded = false;
let dataProcessed = false;
let availableIndicators = [];
let selectedStrategy = 'trend_following';
let currentConfig = {};

// Global variables for optimization
let optimizationStatusInterval = null;
let currentOptimizationStrategy = null;

// API endpoints
const API_BASE_URL = '';
const API_ENDPOINTS = {
    UPLOAD: '/api/upload',
    PROCESS_DATA: '/api/process-data',
    ADD_INDICATORS: '/api/add-indicators',
    PLOT_INDICATORS: '/api/plot-indicators',
    AVAILABLE_STRATEGIES: '/api/available-strategies',
    STRATEGY_PARAMETERS: '/api/strategy-parameters',
    RUN_BACKTEST: '/api/run-backtest',
    OPTIMIZE_STRATEGY: '/api/optimize-strategy',
    OPTIMIZATION_STATUS: '/api/optimization-status',
    OPTIMIZATION_RESULTS: '/api/optimization-results',
    COMPARE_STRATEGIES: '/api/compare-strategies',
    SAVE_CONFIG: '/api/save-config',
    LOAD_CONFIG: '/api/load-config',
    EXPORT_RESULTS: '/api/export-results',
    CURRENT_CONFIG: '/api/current-config',
    ARRANGE_DATA: '/api/arrange-data',
    DATA_STATUS: '/api/data-status',
    SEASONALITY_DAY_OF_WEEK: '/api/seasonality/day-of-week',
    SEASONALITY_MONTHLY: '/api/seasonality/monthly',
    SEASONALITY_VOLATILITY: '/api/seasonality/volatility',
    SEASONALITY_HEATMAP: '/api/seasonality/heatmap',
    SEASONALITY_SUMMARY: '/api/seasonality/summary'
};

// Utility functions
function showError(message) {
    errorMessage.textContent = message;
    errorModal.show();
}

function showLoading(element) {
    const spinnerHtml = `
        <div class="spinner-container">
            <div class="spinner-border text-primary spinner" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    element.innerHTML = spinnerHtml;
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toISOString().split('T')[0];
}

function formatNumber(num, decimals = 2) {
    return Number(num).toFixed(decimals);
}

// Tab navigation
function activateTab(tab, section, title) {
    // Deactivate all tabs and hide all sections
    [dataTab, indicatorsTab, strategiesTab, backtestTab, optimizationTab, seasonalityTab, resultsTab].forEach(t => {
        t.classList.remove('active');
    });
    
    [dataSection, indicatorsSection, strategiesSection, backtestSection, optimizationSection, seasonalitySection, resultsSection].forEach(s => {
        s.classList.remove('active');
    });
    
    // Activate the selected tab and show the corresponding section
    tab.classList.add('active');
    section.classList.add('active');
    pageTitle.textContent = title;
    
    // Save the active tab to session storage to persist across page reloads
    sessionStorage.setItem('activeTab', tab.id);
}

// Initialize tab navigation
dataTab.addEventListener('click', (e) => {
    e.preventDefault();
    activateTab(dataTab, dataSection, 'Data Upload');
});

indicatorsTab.addEventListener('click', (e) => {
    e.preventDefault();
    if (!dataProcessed) {
        showError('Please upload and process data first.');
        activateTab(dataTab, dataSection, 'Data Upload');
        return;
    }
    activateTab(indicatorsTab, indicatorsSection, 'Technical Indicators');
});

strategiesTab.addEventListener('click', (e) => {
    e.preventDefault();
    if (!dataProcessed) {
        showError('Please upload and process data first.');
        activateTab(dataTab, dataSection, 'Data Upload');
        return;
    }
    activateTab(strategiesTab, strategiesSection, 'Trading Strategies');
    loadStrategyParameters();
});

backtestTab.addEventListener('click', (e) => {
    e.preventDefault();
    if (!dataProcessed) {
        showError('Please upload and process data first.');
        activateTab(dataTab, dataSection, 'Data Upload');
        return;
    }
    activateTab(backtestTab, backtestSection, 'Backtest');
});

optimizationTab.addEventListener('click', (e) => {
    e.preventDefault();
    if (!dataProcessed) {
        showError('Please upload and process data first.');
        activateTab(dataTab, dataSection, 'Data Upload');
        return;
    }
    activateTab(optimizationTab, optimizationSection, 'Strategy Optimization');
    setupOptimizationParameters();
    
    // Check if there are any previous optimization results for the currently selected strategy
    const strategyType = document.getElementById('optimization-strategy').value;
    if (strategyType) {
        // Check for existing results
        fetchAndDisplayOptimizationResults(strategyType);
    }
});

seasonalityTab.addEventListener('click', (e) => {
    e.preventDefault();
    if (!dataProcessed) {
        showError('Please upload and process data first.');
        activateTab(dataTab, dataSection, 'Data Upload');
        return;
    }
    activateTab(seasonalityTab, seasonalitySection, 'Seasonality Analysis');
});

resultsTab.addEventListener('click', (e) => {
    e.preventDefault();
    const backtestResults = document.getElementById('backtest-results');
    if (backtestResults.innerHTML === '' && !dataProcessed) {
        showError('Please run a backtest first to see results.');
        return;
    }
    activateTab(resultsTab, resultsSection, 'Analysis Results');
});

// Data Upload and Processing
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('csv-file');
    const formData = new FormData(); // Create FormData object here
    let fileNameForLog = "default_teste_arranged.csv"; // For logging purposes

    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        formData.append('file', file);
        fileNameForLog = file.name;
    } else {
        // No file selected by user, backend will use default.
        // Append an empty string for the 'file' part to ensure multipart structure.
        formData.append('file', ''); 
        AppLogger.info('No file selected by user, attempting to use default file on backend.');
    }
    
    try {
        // --- UPLOAD PHASE ---
        uploadProcessBtn.disabled = true;
        uploadProcessBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Uploading...';
        AppLogger.info('Initiating upload/process', { file: fileNameForLog });
        
        const uploadResponse = await fetch(API_ENDPOINTS.UPLOAD, {
            method: 'POST',
            body: formData // FormData will be empty if no file selected, backend handles this
        });
        
        const uploadData = await uploadResponse.json();
        
        if (!uploadResponse.ok) {
            throw new Error(uploadData.message || 'Error uploading file');
        }
        
        // Update UI with data preview from upload
        updateDataPreview(uploadData);
        
        // --- PROCESS PHASE (only if upload was successful) ---
        uploadProcessBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
        
        const processResponse = await fetch(API_ENDPOINTS.PROCESS_DATA, {
            method: 'POST'
        });
        
        const processData = await processResponse.json();
        
        if (!processResponse.ok) {
            // If processing fails, dataUploaded should reflect the state from the upload step
            dataUploaded = true; // Upload was successful
            sessionStorage.setItem('dataUploaded', 'true');
            dataProcessed = false; // Processing failed
            sessionStorage.setItem('dataProcessed', 'false');
            throw new Error(processData.message || 'Error processing data');
        }
        
        // Update UI with processed data preview
        updateDataPreview(processData);
        
        dataUploaded = true;
        dataProcessed = true;
        sessionStorage.setItem('dataUploaded', 'true');
        sessionStorage.setItem('dataProcessed', 'true');
        
        dataInfo.innerHTML += `<div class="alert alert-success mt-2">Data uploaded and processed successfully!</div>`;
        fetchCurrentConfig();
        
    } catch (error) {
        showError(error.message);
        // dataUploaded and dataProcessed will be false or set according to failure point
        // Button is re-enabled in finally
    } finally {
        uploadProcessBtn.disabled = false;
        uploadProcessBtn.textContent = 'Upload and Process';
    }
});

// Add handler for Arrange Data button
const arrangeBtn = document.getElementById('arrange-btn');
arrangeBtn.addEventListener('click', async () => {
    const fileInput = document.getElementById('csv-file');
    if (!fileInput.files.length) {
        showError('Please select a file to arrange.');
        return;
    }
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        arrangeBtn.disabled = true;
        arrangeBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Arranging...';
        
        const response = await fetch(API_ENDPOINTS.ARRANGE_DATA, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error arranging data');
        }
        
        // Update UI with arranged data preview
        updateDataPreview(data);
        
        // Make an additional call to process-data to ensure backend state is consistent
        try {
            const processResponse = await fetch(API_ENDPOINTS.PROCESS_DATA, { method: 'POST' });
            const processData = await processResponse.json();
            if (processResponse.ok) {
                console.log('Data auto-processed after arrangement:', processData);
            }
        } catch (processError) {
            console.warn('Auto-processing after arrangement failed:', processError);
        }
        
        // Set global state flags
        dataUploaded = true;
        dataProcessed = true;
        
        // Store flags in sessionStorage
        sessionStorage.setItem('dataUploaded', 'true');
        sessionStorage.setItem('dataProcessed', 'true');
        
        // Show success message
        dataInfo.innerHTML += `<div class="alert alert-success mt-2">Data arranged successfully! Saved to ${data.output_file}</div>`;
        
        // Fetch current config to update UI date ranges
        fetchCurrentConfig();
        
    } catch (error) {
        showError(error.message);
    } finally {
        arrangeBtn.disabled = false;
        arrangeBtn.textContent = 'Arrange Data';
    }
});

// Load current configuration
async function fetchCurrentConfig() {
    try {
        const response = await fetch(API_ENDPOINTS.CURRENT_CONFIG);
        currentConfig = await response.json();
        
        // Set dates in the UI based on the data range
        if (currentConfig.data && currentConfig.data.start_date && currentConfig.data.end_date) {
            const startDateInputs = document.querySelectorAll('#chart-start-date, #backtest-start-date, #optimization-start-date, #compare-start-date');
            const endDateInputs = document.querySelectorAll('#chart-end-date, #backtest-end-date, #optimization-end-date, #compare-end-date');
            
            startDateInputs.forEach(input => {
                input.value = currentConfig.data.start_date;
            });
            
            endDateInputs.forEach(input => {
                input.value = currentConfig.data.end_date;
            });
        }
        
        // Check for available indicators
        if (currentConfig.indicators && currentConfig.indicators.available_indicators) {
            availableIndicators = currentConfig.indicators.available_indicators;
            console.log("Available indicators from config:", availableIndicators);
            updateIndicatorDropdowns();
        }
    } catch (error) {
        console.error('Error fetching current config:', error);
    }
}

function updateDataPreview(data) {
    dataInfo.innerHTML = `
        <p><strong>Rows:</strong> ${data.data_shape[0]} | <strong>Columns:</strong> ${data.data_shape[1]}</p>
        ${data.date_range ? `<p><strong>Date Range:</strong> ${data.date_range.start} to ${data.date_range.end}</p>` : ''}
    `;
    
    // Clear previous table data
    const thead = dataPreview.querySelector('thead tr');
    const tbody = dataPreview.querySelector('tbody');
    thead.innerHTML = '';
    tbody.innerHTML = '';
    
    if (data.data_sample && data.data_sample.length > 0) {
        // Add table headers
        Object.keys(data.data_sample[0]).forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            thead.appendChild(th);
        });
        
        // Add table rows
        data.data_sample.forEach(row => {
            const tr = document.createElement('tr');
            
            Object.values(row).forEach(value => {
                const td = document.createElement('td');
                td.textContent = value;
                tr.appendChild(td);
            });
            
            tbody.appendChild(tr);
        });
    }
}

// Save Config and Export buttons
saveConfigBtn.addEventListener('click', () => {
    if (!dataProcessed) {
        showError('Please upload and process data first.');
        return;
    }
    
    saveConfigModal.show();
});

saveConfigConfirmBtn.addEventListener('click', async () => {
    const configName = document.getElementById('config-name').value;
    
    if (!configName) {
        showError('Please enter a name for your configuration.');
        return;
    }
    
    try {
        saveConfigConfirmBtn.disabled = true;
        saveConfigConfirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
        
        // Add name to the current config
        const configToSave = { ...currentConfig, name: configName };
        
        const response = await fetch(API_ENDPOINTS.SAVE_CONFIG, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(configToSave)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error saving configuration');
        }
        
        saveConfigModal.hide();
        
        // Show success message
        alert('Configuration saved successfully!');
        
    } catch (error) {
        showError(error.message);
    } finally {
        saveConfigConfirmBtn.disabled = false;
        saveConfigConfirmBtn.textContent = 'Save';
    }
});

exportJsonBtn.addEventListener('click', () => {
    window.location.href = API_ENDPOINTS.EXPORT_RESULTS + '/json';
});

exportCsvBtn.addEventListener('click', () => {
    window.location.href = API_ENDPOINTS.EXPORT_RESULTS + '/csv';
});

// Function to load strategy parameters
async function loadStrategyParameters() {
    try {
        const strategyType = document.getElementById('strategy-type').value;
        const strategyParametersDiv = document.getElementById('strategy-parameters');
        
        // Show loading spinner
        showLoading(strategyParametersDiv);
        
        // Get strategy parameters from API
        const response = await fetch(`${API_ENDPOINTS.STRATEGY_PARAMETERS}/${strategyType}`);
        const data = await response.json();
        
        // Update UI with parameter inputs
        let html = '';
        
        if (strategyType === 'trend_following') {
            html = `
                <div class="mb-3">
                    <label for="fast-ma-type" class="form-label">Fast MA Type</label>
                    <select class="form-select" id="fast-ma-type">
                        <option value="sma" ${data.parameters.fast_ma_type === 'sma' ? 'selected' : ''}>Simple Moving Average</option>
                        <option value="ema" ${data.parameters.fast_ma_type === 'ema' ? 'selected' : ''}>Exponential Moving Average</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label for="fast-ma-period" class="form-label">Fast MA Period</label>
                    <input type="number" class="form-control" id="fast-ma-period" value="${data.parameters.fast_ma_period}" min="1" max="100">
                </div>
                <div class="mb-3">
                    <label for="slow-ma-type" class="form-label">Slow MA Type</label>
                    <select class="form-select" id="slow-ma-type">
                        <option value="sma" ${data.parameters.slow_ma_type === 'sma' ? 'selected' : ''}>Simple Moving Average</option>
                        <option value="ema" ${data.parameters.slow_ma_type === 'ema' ? 'selected' : ''}>Exponential Moving Average</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label for="slow-ma-period" class="form-label">Slow MA Period</label>
                    <input type="number" class="form-control" id="slow-ma-period" value="${data.parameters.slow_ma_period}" min="1" max="500">
                </div>
            `;
            
            // Update strategy description
            document.getElementById('strategy-description').innerHTML = `
                <p>Buys when fast MA crosses above slow MA (golden cross) and sells when fast MA crosses below slow MA (death cross).</p>
            `;
        } else if (strategyType === 'mean_reversion') {
            html = `
                <div class="mb-3">
                    <label for="rsi-period" class="form-label">RSI Period</label>
                    <input type="number" class="form-control" id="rsi-period" value="${data.parameters.rsi_period}" min="1" max="100">
                </div>
                <div class="mb-3">
                    <label for="oversold" class="form-label">Oversold Level</label>
                    <input type="number" class="form-control" id="oversold" value="${data.parameters.oversold}" min="0" max="100">
                </div>
                <div class="mb-3">
                    <label for="overbought" class="form-label">Overbought Level</label>
                    <input type="number" class="form-control" id="overbought" value="${data.parameters.overbought}" min="0" max="100">
                </div>
                <div class="mb-3">
                    <label for="exit-middle" class="form-label">Exit Middle Level</label>
                    <input type="number" class="form-control" id="exit-middle" value="${data.parameters.exit_middle}" min="0" max="100">
                </div>
            `;
            
            // Update strategy description
            document.getElementById('strategy-description').innerHTML = `
                <p>Buys when RSI is below oversold level and sells when RSI is above overbought level. Also exits positions when RSI crosses the middle level.</p>
            `;
        } else if (strategyType === 'breakout') {
            html = `
                <div class="mb-3">
                    <label for="lookback-period" class="form-label">Lookback Period</label>
                    <input type="number" class="form-control" id="lookback-period" value="${data.parameters.lookback_period}" min="1" max="100">
                </div>
                <div class="mb-3">
                    <label for="volume-threshold" class="form-label">Volume Threshold</label>
                    <input type="number" class="form-control" id="volume-threshold" value="${data.parameters.volume_threshold}" min="1" max="5" step="0.1">
                </div>
                <div class="mb-3">
                    <label for="price-threshold" class="form-label">Price Threshold (%)</label>
                    <input type="number" class="form-control" id="price-threshold" value="${data.parameters.price_threshold * 100}" min="0.1" max="10" step="0.1">
                </div>
                <div class="mb-3 form-check">
                    <input type="checkbox" class="form-check-input" id="volatility-exit" ${data.parameters.volatility_exit ? 'checked' : ''}>
                    <label class="form-check-label" for="volatility-exit">Use Volatility-Based Exit</label>
                </div>
                <div class="mb-3">
                    <label for="atr-multiplier" class="form-label">ATR Multiplier</label>
                    <input type="number" class="form-control" id="atr-multiplier" value="${data.parameters.atr_multiplier}" min="0.5" max="5" step="0.1">
                </div>
                <div class="mb-3 form-check">
                    <input type="checkbox" class="form-check-input" id="use-bbands" ${data.parameters.use_bbands ? 'checked' : ''}>
                    <label class="form-check-label" for="use-bbands">Use Bollinger Bands</label>
                </div>
            `;
            
            // Update strategy description
            document.getElementById('strategy-description').innerHTML = `
                <p>Buys when price breaks out above recent highs with increased volume. Uses volatility-based exit strategies.</p>
            `;
        }
        
        // Add run backtest button
        html += `
            <button type="button" class="btn btn-primary" id="run-backtest-btn">Run Backtest</button>
        `;
        
        strategyParametersDiv.innerHTML = html;
        
        // Add event listener for run backtest button
        document.getElementById('run-backtest-btn').addEventListener('click', runBacktest);
        
    } catch (error) {
        console.error('Error loading strategy parameters:', error);
        showError('Error loading strategy parameters: ' + error.message);
    }
}

// Function to set up optimization parameters
function setupOptimizationParameters() {
    try {
        const strategyType = document.getElementById('optimization-strategy').value || 'trend_following';
        const optimizationParametersDiv = document.getElementById('optimization-parameters');
        
        // Clear previous parameters
        optimizationParametersDiv.innerHTML = '';
        
        let html = '';
        
        if (strategyType === 'trend_following') {
            html = `
                <h6 class="mt-4">Parameter Ranges</h6>
                <div class="mb-3">
                    <label class="form-label">Fast MA Type</label>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" value="sma" id="fast-ma-type-sma" checked>
                        <label class="form-check-label" for="fast-ma-type-sma">SMA</label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" value="ema" id="fast-ma-type-ema" checked>
                        <label class="form-check-label" for="fast-ma-type-ema">EMA</label>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">Fast MA Period</label>
                    <div class="row">
                        <div class="col">
                            <input type="number" class="form-control" id="fast-ma-period-min" placeholder="Min" value="5">
                        </div>
                        <div class="col">
                            <input type="number" class="form-control" id="fast-ma-period-max" placeholder="Max" value="25">
                        </div>
                        <div class="col">
                            <input type="number" class="form-control" id="fast-ma-period-step" placeholder="Step" value="5">
                        </div>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">Slow MA Type</label>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" value="sma" id="slow-ma-type-sma" checked>
                        <label class="form-check-label" for="slow-ma-type-sma">SMA</label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" value="ema" id="slow-ma-type-ema" checked>
                        <label class="form-check-label" for="slow-ma-type-ema">EMA</label>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">Slow MA Period</label>
                    <div class="row">
                        <div class="col">
                            <input type="number" class="form-control" id="slow-ma-period-min" placeholder="Min" value="30">
                        </div>
                        <div class="col">
                            <input type="number" class="form-control" id="slow-ma-period-max" placeholder="Max" value="200">
                        </div>
                        <div class="col">
                            <input type="number" class="form-control" id="slow-ma-period-step" placeholder="Step" value="30">
                        </div>
                    </div>
                </div>
            `;
        } else if (strategyType === 'mean_reversion') {
            html = `
                <h6 class="mt-4">Parameter Ranges</h6>
                <div class="mb-3">
                    <label class="form-label">RSI Period</label>
                    <div class="row">
                        <div class="col">
                            <input type="number" class="form-control" id="rsi-period-min" placeholder="Min" value="7">
                        </div>
                        <div class="col">
                            <input type="number" class="form-control" id="rsi-period-max" placeholder="Max" value="21">
                        </div>
                        <div class="col">
                            <input type="number" class="form-control" id="rsi-period-step" placeholder="Step" value="7">
                        </div>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">Oversold Level</label>
                    <div class="row">
                        <div class="col">
                            <input type="number" class="form-control" id="oversold-min" placeholder="Min" value="20">
                        </div>
                        <div class="col">
                            <input type="number" class="form-control" id="oversold-max" placeholder="Max" value="35">
                        </div>
                        <div class="col">
                            <input type="number" class="form-control" id="oversold-step" placeholder="Step" value="5">
                        </div>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">Overbought Level</label>
                    <div class="row">
                        <div class="col">
                            <input type="number" class="form-control" id="overbought-min" placeholder="Min" value="65">
                        </div>
                        <div class="col">
                            <input type="number" class="form-control" id="overbought-max" placeholder="Max" value="80">
                        </div>
                        <div class="col">
                            <input type="number" class="form-control" id="overbought-step" placeholder="Step" value="5">
                        </div>
                    </div>
                </div>
            `;
        } else if (strategyType === 'breakout') {
            html = `
                <h6 class="mt-4">Parameter Ranges</h6>
                <div class="mb-3">
                    <label class="form-label">Lookback Period</label>
                    <div class="row">
                        <div class="col">
                            <input type="number" class="form-control" id="lookback-period-min" placeholder="Min" value="10">
                        </div>
                        <div class="col">
                            <input type="number" class="form-control" id="lookback-period-max" placeholder="Max" value="30">
                        </div>
                        <div class="col">
                            <input type="number" class="form-control" id="lookback-period-step" placeholder="Step" value="10">
                        </div>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">Volume Threshold</label>
                    <div class="row">
                        <div class="col">
                            <input type="number" class="form-control" id="volume-threshold-min" placeholder="Min" value="1.2">
                        </div>
                        <div class="col">
                            <input type="number" class="form-control" id="volume-threshold-max" placeholder="Max" value="2.0">
                        </div>
                        <div class="col">
                            <input type="number" class="form-control" id="volume-threshold-step" placeholder="Step" value="0.4">
                        </div>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">Price Threshold (%)</label>
                    <div class="row">
                        <div class="col">
                            <input type="number" class="form-control" id="price-threshold-min" placeholder="Min" value="1">
                        </div>
                        <div class="col">
                            <input type="number" class="form-control" id="price-threshold-max" placeholder="Max" value="3">
                        </div>
                        <div class="col">
                            <input type="number" class="form-control" id="price-threshold-step" placeholder="Step" value="1">
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Remove the "Add the run optimization button" code
        // Previously had:
        // html += `
        //    <button type="button" class="btn btn-primary" id="run-optimization-btn">Run Optimization</button>
        // `;
        
        optimizationParametersDiv.innerHTML = html;
        
        // Add event listener for the form's submit button that already exists in HTML
        const optimizationForm = document.getElementById('optimization-form');
        if (optimizationForm) {
            optimizationForm.addEventListener('submit', (e) => {
                e.preventDefault();
                runOptimization();
            });
        }
        
    } catch (error) {
        console.error('Error setting up optimization parameters:', error);
        showError('Error setting up optimization parameters: ' + error.message);
    }
}

// Add event listener for strategy type change
document.getElementById('strategy-type').addEventListener('change', loadStrategyParameters);

// Add event listener for optimization strategy type change
document.getElementById('optimization-strategy').addEventListener('change', setupOptimizationParameters);

// Debugging function to log backtest results
function debugBacktestResults(results) {
    console.log('------- BACKTEST RESULTS DEBUG -------');
    console.log('Full results object:', results);
    
    // Check for equity_curve and drawdown_curve data
    if (results.equity_curve) {
        console.log('Equity curve data is present, length:', results.equity_curve.length);
    } else {
        console.log('WARNING: No equity_curve data found in results');
    }
    
    if (results.drawdown_curve) {
        console.log('Drawdown curve data is present, length:', results.drawdown_curve.length);
    } else {
        console.log('WARNING: No drawdown_curve data found in results');
    }
    
    if (results.performance_metrics) {
        console.log('Performance metrics:', results.performance_metrics);
    } else {
        console.log('WARNING: No performance_metrics found in results');
    }
    
    console.log('------- END DEBUG -------');
}

// Function to run a backtest
async function runBacktest() {
    try {
        const strategyType = document.getElementById('strategy-type').value;
        const backTestBtn = document.getElementById('run-backtest-btn');
        
        // Get strategy parameters
        let parameters = {};
        
        if (strategyType === 'trend_following') {
            parameters = {
                fast_ma_type: document.getElementById('fast-ma-type').value,
                fast_ma_period: parseInt(document.getElementById('fast-ma-period').value),
                slow_ma_type: document.getElementById('slow-ma-type').value,
                slow_ma_period: parseInt(document.getElementById('slow-ma-period').value)
            };
        } else if (strategyType === 'mean_reversion') {
            parameters = {
                rsi_period: parseInt(document.getElementById('rsi-period').value),
                oversold: parseInt(document.getElementById('oversold').value),
                overbought: parseInt(document.getElementById('overbought').value),
                exit_middle: parseInt(document.getElementById('exit-middle').value)
            };
        } else if (strategyType === 'breakout') {
            parameters = {
                lookback_period: parseInt(document.getElementById('lookback-period').value),
                volume_threshold: parseFloat(document.getElementById('volume-threshold').value),
                price_threshold: parseFloat(document.getElementById('price-threshold').value) / 100, // Convert from % to decimal
                volatility_exit: document.getElementById('volatility-exit').checked,
                atr_multiplier: parseFloat(document.getElementById('atr-multiplier').value),
                use_bbands: document.getElementById('use-bbands').checked
            };
        }
        
        // Get backtest parameters
        const initialCapital = parseFloat(document.getElementById('initial-capital').value || 10000);
        const commission = parseFloat(document.getElementById('commission').value || 0.001);
        const startDate = document.getElementById('backtest-start-date').value;
        const endDate = document.getElementById('backtest-end-date').value;
        
        // Prepare request data - separate strategy_config and backtest_config as expected by the API
        const requestData = {
            strategy_config: {
                strategy_type: strategyType,
                parameters: parameters
            },
            backtest_config: {
                initial_capital: initialCapital,
                commission: commission,
                start_date: startDate,
                end_date: endDate
            }
        };
        
        // Disable the button
        backTestBtn.disabled = true;
        backTestBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Running...';
        
        // Call the API
        const response = await fetch(API_ENDPOINTS.RUN_BACKTEST, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        let data;
        if (!response.ok) {
            data = await response.json();
            throw new Error(data.message || `Error running backtest (${response.status})`);
        }
        
        data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || 'Error running backtest');
        }
        
        // Debug backtest results
        debugBacktestResults(data);
        
        // Update backtest results
        displayBacktestResults(data);
        
        // Switch to backtest tab
        activateTab(backtestTab, backtestSection, 'Backtest');
        
    } catch (error) {
        console.error('Error running backtest:', error);
        showError('Error running backtest: ' + error.message);
    } finally {
        const backTestBtn = document.getElementById('run-backtest-btn');
        if (backTestBtn) {
            backTestBtn.disabled = false;
            backTestBtn.textContent = 'Run Backtest';
        }
    }
}

function displayBacktestResults(results) {
    console.log('Displaying backtest results:', results);
    
    const resultsContainer = document.getElementById('backtest-results');
    if (!resultsContainer) {
        console.error('Backtest results container not found');
        return;
    }
    
    resultsContainer.innerHTML = ''; // Clear previous results
    
    // Add strategy name
    const strategyName = document.createElement('h3');
    strategyName.textContent = `Strategy: ${results.strategy_name}`;
    resultsContainer.appendChild(strategyName);
    
    // Add performance metrics table
    const metricsTable = document.createElement('table');
    metricsTable.className = 'table table-sm';
    
    const metricsHeader = document.createElement('thead');
    metricsHeader.innerHTML = '<tr><th>Metric</th><th>Value</th></tr>';
    metricsTable.appendChild(metricsHeader);
    
    const metricsBody = document.createElement('tbody');
    for (const [metric, value] of Object.entries(results.performance_metrics)) {
        const row = document.createElement('tr');
        
        const metricCell = document.createElement('td');
        metricCell.textContent = formatMetricName(metric);
        row.appendChild(metricCell);
        
        const valueCell = document.createElement('td');
        valueCell.textContent = formatMetricValue(metric, value);
        row.appendChild(valueCell);
        
        metricsBody.appendChild(row);
    }
    
    metricsTable.appendChild(metricsBody);
    resultsContainer.appendChild(metricsTable);
    
    // Display equity curve chart if available
    if (results.equity_curve) {
        const chartContainer = document.getElementById('equity-curve-container');
        if (chartContainer) {
            chartContainer.innerHTML = '';
            
            const chartImg = document.createElement('img');
            chartImg.src = `data:image/png;base64,${results.equity_curve}`;
            chartImg.alt = 'Equity Curve';
            chartImg.className = 'img-fluid';
            chartContainer.appendChild(chartImg);
            
            // Make sure the chart container is visible
            chartContainer.style.display = 'block';
        }
    }

    // Also handle drawdown curve if available
    if (results.drawdown_curve) {
        // Create or find a container for the drawdown curve
        let drawdownContainer = document.getElementById('drawdown-curve-container');
        if (!drawdownContainer) {
            drawdownContainer = document.createElement('div');
            drawdownContainer.id = 'drawdown-curve-container';
            drawdownContainer.style.marginTop = '20px';
            drawdownContainer.innerHTML = '<h5>Drawdown</h5>';
            
            // Insert after equity curve container
            const equityCurveContainer = document.getElementById('equity-curve-container');
            if (equityCurveContainer && equityCurveContainer.parentNode) {
                equityCurveContainer.parentNode.insertBefore(drawdownContainer, equityCurveContainer.nextSibling);
            } else {
                resultsContainer.appendChild(drawdownContainer);
            }
        } else {
            drawdownContainer.innerHTML = '<h5>Drawdown</h5>';
        }
        
        const drawdownImg = document.createElement('img');
        drawdownImg.src = `data:image/png;base64,${results.drawdown_curve}`;
        drawdownImg.alt = 'Drawdown Curve';
        drawdownImg.className = 'img-fluid';
        drawdownContainer.appendChild(drawdownImg);
        drawdownContainer.style.display = 'block';
    }
}

// Function to run optimization
async function runOptimization() {
    try {
        const strategyType = document.getElementById('optimization-strategy').value;
        // Reference the form submit button instead of the dynamically created one
        const optimizationBtn = document.querySelector('#optimization-form button[type="submit"]');
        
        // Get optimization parameters
        const metric = document.getElementById('optimization-metric').value;
        const startDate = document.getElementById('optimization-start-date').value;
        const endDate = document.getElementById('optimization-end-date').value;
        
        // Build parameter ranges
        let paramRanges = {};
        
        if (strategyType === 'trend_following') {
            // Fast MA type
            const fastMaTypes = [];
            const fastMaTypeSma = document.getElementById('fast-ma-type-sma').checked;
            const fastMaTypeEma = document.getElementById('fast-ma-type-ema').checked;
            
            if (fastMaTypeSma) fastMaTypes.push('sma');
            if (fastMaTypeEma) fastMaTypes.push('ema');
            
            // Fast MA period
            const fastMaPeriodMin = parseInt(document.getElementById('fast-ma-period-min').value);
            const fastMaPeriodMax = parseInt(document.getElementById('fast-ma-period-max').value);
            const fastMaPeriodStep = parseInt(document.getElementById('fast-ma-period-step').value);
            const fastMaPeriods = [];
            
            for (let i = fastMaPeriodMin; i <= fastMaPeriodMax; i += fastMaPeriodStep) {
                fastMaPeriods.push(i);
            }
            
            // Slow MA type
            const slowMaTypes = [];
            const slowMaTypeSma = document.getElementById('slow-ma-type-sma').checked;
            const slowMaTypeEma = document.getElementById('slow-ma-type-ema').checked;
            
            if (slowMaTypeSma) slowMaTypes.push('sma');
            if (slowMaTypeEma) slowMaTypes.push('ema');
            
            // Slow MA period
            const slowMaPeriodMin = parseInt(document.getElementById('slow-ma-period-min').value);
            const slowMaPeriodMax = parseInt(document.getElementById('slow-ma-period-max').value);
            const slowMaPeriodStep = parseInt(document.getElementById('slow-ma-period-step').value);
            const slowMaPeriods = [];
            
            for (let i = slowMaPeriodMin; i <= slowMaPeriodMax; i += slowMaPeriodStep) {
                slowMaPeriods.push(i);
            }
            
            // Build parameter ranges
            paramRanges = {
                fast_ma_type: fastMaTypes,
                fast_ma_period: fastMaPeriods,
                slow_ma_type: slowMaTypes,
                slow_ma_period: slowMaPeriods
            };
        } else if (strategyType === 'mean_reversion') {
            // RSI period
            const rsiPeriodMin = parseInt(document.getElementById('rsi-period-min').value);
            const rsiPeriodMax = parseInt(document.getElementById('rsi-period-max').value);
            const rsiPeriodStep = parseInt(document.getElementById('rsi-period-step').value);
            const rsiPeriods = [];
            
            for (let i = rsiPeriodMin; i <= rsiPeriodMax; i += rsiPeriodStep) {
                rsiPeriods.push(i);
            }
            
            // Oversold level
            const oversoldMin = parseInt(document.getElementById('oversold-min').value);
            const oversoldMax = parseInt(document.getElementById('oversold-max').value);
            const oversoldStep = parseInt(document.getElementById('oversold-step').value);
            const oversoldLevels = [];
            
            for (let i = oversoldMin; i <= oversoldMax; i += oversoldStep) {
                oversoldLevels.push(i);
            }
            
            // Overbought level
            const overboughtMin = parseInt(document.getElementById('overbought-min').value);
            const overboughtMax = parseInt(document.getElementById('overbought-max').value);
            const overboughtStep = parseInt(document.getElementById('overbought-step').value);
            const overboughtLevels = [];
            
            for (let i = overboughtMin; i <= overboughtMax; i += overboughtStep) {
                overboughtLevels.push(i);
            }
            
            // Build parameter ranges
            paramRanges = {
                rsi_period: rsiPeriods,
                oversold: oversoldLevels,
                overbought: overboughtLevels
            };
        } else if (strategyType === 'breakout') {
            // Lookback period
            const lookbackPeriodMin = parseInt(document.getElementById('lookback-period-min').value);
            const lookbackPeriodMax = parseInt(document.getElementById('lookback-period-max').value);
            const lookbackPeriodStep = parseInt(document.getElementById('lookback-period-step').value);
            const lookbackPeriods = [];
            
            for (let i = lookbackPeriodMin; i <= lookbackPeriodMax; i += lookbackPeriodStep) {
                lookbackPeriods.push(i);
            }
            
            // Volume threshold
            const volumeThresholdMin = parseFloat(document.getElementById('volume-threshold-min').value);
            const volumeThresholdMax = parseFloat(document.getElementById('volume-threshold-max').value);
            const volumeThresholdStep = parseFloat(document.getElementById('volume-threshold-step').value);
            const volumeThresholds = [];
            
            for (let i = volumeThresholdMin; i <= volumeThresholdMax; i += volumeThresholdStep) {
                volumeThresholds.push(parseFloat(i.toFixed(2)));
            }
            
            // Price threshold
            const priceThresholdMin = parseFloat(document.getElementById('price-threshold-min').value);
            const priceThresholdMax = parseFloat(document.getElementById('price-threshold-max').value);
            const priceThresholdStep = parseFloat(document.getElementById('price-threshold-step').value);
            const priceThresholds = [];
            
            for (let i = priceThresholdMin; i <= priceThresholdMax; i += priceThresholdStep) {
                priceThresholds.push(parseFloat((i / 100).toFixed(4))); // Convert from % to decimal
            }
            
            // Build parameter ranges
            paramRanges = {
                lookback_period: lookbackPeriods,
                volume_threshold: volumeThresholds,
                price_threshold: priceThresholds
            };
        }
        
        // Prepare request data
        const requestData = {
            strategy_type: strategyType,
            param_ranges: paramRanges,
            metric: metric,
            start_date: startDate,
            end_date: endDate
        };
        
        // Disable the button
        if (optimizationBtn) {
            optimizationBtn.disabled = true;
            optimizationBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Running...';
        }
        
        // Clear previous optimization status check interval
        if (optimizationStatusInterval) {
            clearInterval(optimizationStatusInterval);
            optimizationStatusInterval = null;
        }
        
        // Call the API
        const response = await fetch(API_ENDPOINTS.OPTIMIZE_STRATEGY, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error running optimization');
        }
        
        // Show message that optimization is running in the background
        const optimizationResults = document.getElementById('optimization-results');
        optimizationResults.innerHTML = `
            <div class="alert alert-info mt-3">
                <h5>Optimization Running</h5>
                <p>The optimization is running in the background. This may take several minutes depending on the number of parameter combinations.</p>
                <p>The results will appear here when complete.</p>
                <div class="progress mt-3">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 100%"></div>
                </div>
            </div>
        `;
        
        // Store the current optimization strategy
        currentOptimizationStrategy = strategyType;
        
        // Set up periodic check for optimization status
        optimizationStatusInterval = setInterval(checkOptimizationStatus, 5000); // Check every 5 seconds
        
    } catch (error) {
        console.error('Error running optimization:', error);
        showError('Error running optimization: ' + error.message);
    } finally {
        // Use the form submit button for re-enabling
        const optimizationBtn = document.querySelector('#optimization-form button[type="submit"]');
        if (optimizationBtn) {
            optimizationBtn.disabled = false;
            optimizationBtn.textContent = 'Run Optimization';
        }
    }
}

// Function to check optimization status
async function checkOptimizationStatus() {
    try {
        const response = await fetch(API_ENDPOINTS.OPTIMIZATION_STATUS);
        const statusData = await response.json();
        
        // If optimization is no longer in progress, fetch and display results
        if (!statusData.in_progress && statusData.strategy_type === currentOptimizationStrategy) {
            // Clear the interval
            clearInterval(optimizationStatusInterval);
            optimizationStatusInterval = null;
            
            // Fetch the results
            await fetchAndDisplayOptimizationResults(currentOptimizationStrategy);
        }
    } catch (error) {
        console.error('Error checking optimization status:', error);
    }
}

// Function to fetch and display optimization results
async function fetchAndDisplayOptimizationResults(strategyType) {
    try {
        const response = await fetch(`${API_ENDPOINTS.OPTIMIZATION_RESULTS}/${strategyType}`);
        const data = await response.json();
        
        const optimizationResults = document.getElementById('optimization-results');
        
        if (data.status === 'success') {
            const results = data.results;
            
            // Format best parameters
            let bestParamsHtml = '';
            for (const [param, value] of Object.entries(results.best_params)) {
                bestParamsHtml += `<tr>
                    <td>${formatMetricName(param)}</td>
                    <td>${value}</td>
                </tr>`;
            }
            
            // Format performance metrics
            let performanceHtml = '';
            for (const [metric, value] of Object.entries(results.best_performance)) {
                performanceHtml += `<tr>
                    <td>${formatMetricName(metric)}</td>
                    <td>${formatMetricValue(metric, value)}</td>
                </tr>`;
            }
            
            // Display results
            optimizationResults.innerHTML = `
                <div class="alert alert-success mt-3">
                    <h5>Optimization Complete</h5>
                    <p>Optimization for ${formatMetricName(results.strategy_type)} strategy completed on ${data.timestamp}</p>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Best Parameters</h5>
                            </div>
                            <div class="card-body">
                                <table class="table table-sm table-striped">
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
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Performance Metrics</h5>
                            </div>
                            <div class="card-body">
                                <table class="table table-sm table-striped">
                                    <thead>
                                        <tr>
                                            <th>Metric</th>
                                            <th>Value</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${performanceHtml}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <button type="button" class="btn btn-primary" onclick="useOptimizedParameters('${results.strategy_type}')">
                        Use These Parameters
                    </button>
                </div>
            `;
        } else if (data.status === 'in_progress') {
            // Still running - leave the progress indicator in place
        } else {
            // Error or not found
            optimizationResults.innerHTML = `
                <div class="alert alert-warning mt-3">
                    <h5>Optimization Results Not Available</h5>
                    <p>${data.message}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching optimization results:', error);
        
        const optimizationResults = document.getElementById('optimization-results');
        optimizationResults.innerHTML = `
            <div class="alert alert-danger mt-3">
                <h5>Error Fetching Results</h5>
                <p>There was an error fetching the optimization results: ${error.message}</p>
            </div>
        `;
    } finally {
        // Re-enable the optimization button
        const optimizationBtn = document.getElementById('run-optimization-btn');
        if (optimizationBtn) {
            optimizationBtn.disabled = false;
            optimizationBtn.textContent = 'Run Optimization';
        }
    }
}

// Function to use optimized parameters
async function useOptimizedParameters(strategyType) {
    try {
        // Fetch the latest optimization results
        const response = await fetch(`${API_ENDPOINTS.OPTIMIZATION_RESULTS}/${strategyType}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            const bestParams = data.results.best_params;
            
            // Switch to the Strategies tab
            const strategiesTabEl = document.getElementById('strategies-tab');
            strategiesTabEl.click();
            
            // Select the optimized strategy
            const strategySelect = document.getElementById('strategy-type');
            strategySelect.value = strategyType;
            
            // Trigger the change event to load the parameters
            strategySelect.dispatchEvent(new Event('change'));
            
            // Wait for the parameters to load
            setTimeout(() => {
                // Set the optimized parameters
                for (const [param, value] of Object.entries(bestParams)) {
                    const paramInput = document.getElementById(`strategy-param-${param}`);
                    if (paramInput) {
                        paramInput.value = value;
                    }
                }
                
                showNotification(`Optimized parameters for ${formatMetricName(strategyType)} strategy have been applied.`, 'success');
            }, 500);
        } else {
            showError('Could not load optimization results: ' + data.message);
        }
    } catch (error) {
        console.error('Error using optimized parameters:', error);
        showError('Error using optimized parameters: ' + error.message);
    }
}

// Function to compare strategies
function compareStrategies() {
    const selectedStrategies = Array.from(document.querySelectorAll('#compare-strategies-form input[type="checkbox"]:checked'))
        .map(checkbox => checkbox.value);
        
    if (selectedStrategies.length === 0) {
        showNotification('Please select at least one strategy to compare', 'warning');
        return;
    }
    
    const startDate = document.getElementById('compare-start-date').value;
    const endDate = document.getElementById('compare-end-date').value;
    
    showLoader('Comparing strategies...');
    
    console.log('Calling API: ' + API_ENDPOINTS.COMPARE_STRATEGIES);
    
    fetch(API_ENDPOINTS.COMPARE_STRATEGIES, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            strategy_types: selectedStrategies,
            start_date: startDate,
            end_date: endDate
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => {
                throw new Error(`Validation error: ${JSON.stringify(errorData)}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Compare strategies response:', data);
        hideLoader();
        
        if (!data.success) {
            showNotification(data.message || 'Error comparing strategies', 'error');
            return;
        }
        
        showNotification('Strategies compared successfully', 'success');
        
        // Display comparison results
        const resultsContainer = document.getElementById('compare-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = '';
            
            // Add best strategy highlight
            if (data.best_strategy) {
                const bestStrategy = document.createElement('div');
                bestStrategy.className = 'alert alert-success';
                bestStrategy.innerHTML = `<strong>Best Strategy:</strong> ${data.best_strategy}`;
                resultsContainer.appendChild(bestStrategy);
            }
            
            // Create comparison table
            const table = document.createElement('table');
            table.className = 'table table-striped table-sm';
            
            // Create table header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            
            const metricHeader = document.createElement('th');
            metricHeader.textContent = 'Metric';
            headerRow.appendChild(metricHeader);
            
            // Add a column for each strategy
            for (const strategy of selectedStrategies) {
                const th = document.createElement('th');
                th.textContent = strategy;
                headerRow.appendChild(th);
            }
            
            thead.appendChild(headerRow);
            table.appendChild(thead);
            
            // Create table body
            const tbody = document.createElement('tbody');
            
            // Get all metrics from the first strategy
            if (data.results && Object.keys(data.results).length > 0) {
                const firstStrategy = Object.keys(data.results)[0];
                const metrics = Object.keys(data.results[firstStrategy]);
                
                // Create a row for each metric
                for (const metric of metrics) {
                    const row = document.createElement('tr');
                    
                    const metricCell = document.createElement('td');
                    metricCell.textContent = formatMetricName(metric);
                    row.appendChild(metricCell);
                    
                    // Add the metric value for each strategy
                    for (const strategy of selectedStrategies) {
                        const valueCell = document.createElement('td');
                        
                        if (data.results[strategy] && data.results[strategy][metric] !== undefined) {
                            valueCell.textContent = formatMetricValue(metric, data.results[strategy][metric]);
                        } else {
                            valueCell.textContent = 'N/A';
                        }
                        
                        row.appendChild(valueCell);
                    }
                    
                    tbody.appendChild(row);
                }
            }
            
            table.appendChild(tbody);
            resultsContainer.appendChild(table);
            
            // Display equity curve chart if available
            if (data.chart_image) {
                const chartContainer = document.getElementById('comparison-chart-container');
                if (chartContainer) {
                    chartContainer.innerHTML = '';
                    
                    const chartImg = document.createElement('img');
                    chartImg.src = `data:image/png;base64,${data.chart_image}`;
                    chartImg.alt = 'Strategy Comparison';
                    chartImg.style.width = '100%';
                    chartContainer.appendChild(chartImg);
                    
                    // Make sure the chart container is visible
                    chartContainer.style.display = 'block';
                }
            }
        }
    })
    .catch(error => {
        hideLoader();
        console.error('Error comparing strategies:', error);
        showNotification(`Error comparing strategies: ${error.message}`, 'error');
    });
}

// Initialize the app
document.addEventListener('DOMContentLoaded', async () => {
    // Check backend data status first
    await checkDataStatus();
    
    // Rest of initialization code...
    // Check if we have stored state in sessionStorage
    if (sessionStorage.getItem('dataUploaded') === 'true') {
        dataUploaded = true;
    }
    
    if (sessionStorage.getItem('dataProcessed') === 'true') {
        dataProcessed = true;
    }
    
    // Restore the active tab if saved
    const activeTabId = sessionStorage.getItem('activeTab');
    if (activeTabId && dataProcessed) {
        const tabMap = {
            'data-tab': { tab: dataTab, section: dataSection, title: 'Data Upload' },
            'indicators-tab': { tab: indicatorsTab, section: indicatorsSection, title: 'Technical Indicators' },
            'strategies-tab': { tab: strategiesTab, section: strategiesSection, title: 'Trading Strategies' },
            'backtest-tab': { tab: backtestTab, section: backtestSection, title: 'Backtest' },
            'optimization-tab': { tab: optimizationTab, section: optimizationSection, title: 'Strategy Optimization' },
            'seasonality-tab': { tab: seasonalityTab, section: seasonalitySection, title: 'Seasonality Analysis' },
            'results-tab': { tab: resultsTab, section: resultsSection, title: 'Analysis Results' }
        };
        
        if (tabMap[activeTabId]) {
            const { tab, section, title } = tabMap[activeTabId];
            activateTab(tab, section, title);
            
            // If navigating to strategies tab, load parameters
            if (activeTabId === 'strategies-tab') {
                loadStrategyParameters();
            }
            
            // If navigating to optimization tab, setup parameters
            if (activeTabId === 'optimization-tab') {
                setupOptimizationParameters();
            }
            
            return;
        }
    }
    
    // Default to first tab
    activateTab(dataTab, dataSection, 'Data Upload');
    
    // Add event listeners for the backtest form
    const backtestForm = document.getElementById('backtest-form');
    if (backtestForm) {
        backtestForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Get strategy type and create appropriate parameters
            const strategyType = document.getElementById('backtest-strategy').value;
            const initialCapital = parseFloat(document.getElementById('initial-capital').value || 10000);
            const commission = parseFloat(document.getElementById('commission').value || 0.001);
            const startDate = document.getElementById('backtest-start-date').value;
            const endDate = document.getElementById('backtest-end-date').value;
            
            // Disable the button
            const backTestBtn = document.getElementById('run-backtest-btn');
            backTestBtn.disabled = true;
            backTestBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Running...';
            
            // Get default parameters for the selected strategy
            fetch(`${API_ENDPOINTS.STRATEGY_PARAMETERS}/${strategyType}`)
                .then(response => response.json())
                .then(data => {
                    // Prepare request data using default parameters with the correct structure
                    const requestData = {
                        strategy_config: {
                            strategy_type: strategyType,
                            parameters: data.parameters
                        },
                        backtest_config: {
                            initial_capital: initialCapital,
                            commission: commission,
                            start_date: startDate,
                            end_date: endDate
                        }
                    };
                    
                    console.log('Sending backtest request with data:', requestData);
                    
                    // Call the API
                    return fetch(API_ENDPOINTS.RUN_BACKTEST, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(requestData)
                    });
                })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        throw new Error(data.message || 'Error running backtest');
                    }
                    
                    console.log('Backtest results:', data);
                    
                    // Ensure we save session state
                    sessionStorage.setItem('dataUploaded', 'true');
                    sessionStorage.setItem('dataProcessed', 'true');
                    sessionStorage.setItem('activeTab', 'backtest-tab');
                    dataUploaded = true;
                    dataProcessed = true;
                    
                    // Update backtest results
                    displayBacktestResults(data);
                    
                    // Ensure we stay on the backtest tab
                    activateTab(backtestTab, backtestSection, 'Backtest');
                })
                .catch(error => {
                    console.error('Error running backtest:', error);
                    showError('Error running backtest: ' + error.message);
                })
                .finally(() => {
                    const backTestBtn = document.getElementById('run-backtest-btn');
                    if (backTestBtn) {
                        backTestBtn.disabled = false;
                        backTestBtn.textContent = 'Run Backtest';
                    }
                });
        });
    }
    
    // Add event listener for the optimization form
    const optimizationForm = document.getElementById('optimization-form');
    if (optimizationForm) {
        optimizationForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Set up optimization parameters based on the form values
            setupOptimizationParameters();
            
            // Directly call runOptimization instead of looking for the button
            runOptimization();
        });
    }
    
    // Add event listener for the indicators form
    const indicatorsForm = document.getElementById('indicators-form');
    if (indicatorsForm) {
        indicatorsForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Ensure data is still processed
            if (!dataProcessed) {
                showError('Please upload and process data first.');
                activateTab(dataTab, dataSection, 'Data Upload');
                return;
            }
            
            // Get selected indicators
            const indicatorConfig = {};
            
            // Moving Averages (SMA)
            const smaCheckbox = document.getElementById('sma-checkbox');
            if (smaCheckbox && smaCheckbox.checked) {
                if (!indicatorConfig.moving_averages) {
                    indicatorConfig.moving_averages = {
                        types: []
                    };
                }
                
                indicatorConfig.moving_averages.types.push('sma');
                
                // Extract SMA periods (comma separated values)
                const smaPeriodsStr = document.getElementById('sma-periods').value;
                const smaPeriods = smaPeriodsStr.split(',').map(p => parseInt(p.trim())).filter(p => !isNaN(p) && p > 0);
                indicatorConfig.moving_averages.sma_periods = smaPeriods;
                
                console.log("Adding SMA with periods:", smaPeriods);
            }
            
            // Moving Averages (EMA)
            const emaCheckbox = document.getElementById('ema-checkbox');
            if (emaCheckbox && emaCheckbox.checked) {
                if (!indicatorConfig.moving_averages) {
                    indicatorConfig.moving_averages = {
                        types: []
                    };
                }
                
                indicatorConfig.moving_averages.types.push('ema');
                
                // Extract EMA periods (comma separated values)
                const emaPeriodsStr = document.getElementById('ema-periods').value;
                const emaPeriods = emaPeriodsStr.split(',').map(p => parseInt(p.trim())).filter(p => !isNaN(p) && p > 0);
                indicatorConfig.moving_averages.ema_periods = emaPeriods;
                
                console.log("Adding EMA with periods:", emaPeriods);
            }
            
            // RSI
            const rsiCheckbox = document.getElementById('rsi-checkbox');
            if (rsiCheckbox && rsiCheckbox.checked) {
                const rsiPeriod = document.getElementById('rsi-period');
                indicatorConfig.rsi = {
                    period: rsiPeriod ? parseInt(rsiPeriod.value) : 14
                };
                console.log("Adding RSI with period:", indicatorConfig.rsi.period);
            }
            
            // MACD
            const macdCheckbox = document.getElementById('macd-checkbox');
            if (macdCheckbox && macdCheckbox.checked) {
                const macdFast = document.getElementById('macd-fast');
                const macdSlow = document.getElementById('macd-slow');
                const macdSignal = document.getElementById('macd-signal');
                indicatorConfig.macd = {
                    fast_period: macdFast ? parseInt(macdFast.value) : 12,
                    slow_period: macdSlow ? parseInt(macdSlow.value) : 26,
                    signal_period: macdSignal ? parseInt(macdSignal.value) : 9
                };
                console.log("Adding MACD with parameters:", indicatorConfig.macd);
            }
            
            // Bollinger Bands
            const bbandsCheckbox = document.getElementById('bbands-checkbox');
            if (bbandsCheckbox && bbandsCheckbox.checked) {
                const bbandsPeriod = document.getElementById('bbands-period');
                const bbandsStd = document.getElementById('bbands-std');
                indicatorConfig.bollinger_bands = {
                    window: bbandsPeriod ? parseInt(bbandsPeriod.value) : 20,
                    num_std: bbandsStd ? parseFloat(bbandsStd.value) : 2.0
                };
                console.log("Adding Bollinger Bands with parameters:", indicatorConfig.bollinger_bands);
            }
            
            // Stochastic
            const stochCheckbox = document.getElementById('stoch-checkbox');
            if (stochCheckbox && stochCheckbox.checked) {
                const stochK = document.getElementById('stoch-k');
                const stochD = document.getElementById('stoch-d');
                const stochSlowing = document.getElementById('stoch-slowing');
                indicatorConfig.stochastic = {
                    k_period: stochK ? parseInt(stochK.value) : 14,
                    d_period: stochD ? parseInt(stochD.value) : 3,
                    slowing: stochSlowing ? parseInt(stochSlowing.value) : 3
                };
                console.log("Adding Stochastic with parameters:", indicatorConfig.stochastic);
            }
            
            // Volume
            const volumeCheckbox = document.getElementById('volume-checkbox');
            if (volumeCheckbox && volumeCheckbox.checked) {
                indicatorConfig.volume = true;
                console.log("Adding Volume indicators");
            }
            
            // ATR
            const atrCheckbox = document.getElementById('atr-checkbox');
            if (atrCheckbox && atrCheckbox.checked) {
                const atrPeriod = document.getElementById('atr-period');
                indicatorConfig.atr = {
                    period: atrPeriod ? parseInt(atrPeriod.value) : 14
                };
                console.log("Adding ATR with period:", indicatorConfig.atr.period);
            }
            
            // Check if any indicator is selected
            if (Object.keys(indicatorConfig).length === 0) {
                showError('Please select at least one indicator to add.');
                return;
            }
            
            // Disable the add indicators button
            const addIndicatorsBtn = document.getElementById('add-indicators-btn');
            addIndicatorsBtn.disabled = true;
            addIndicatorsBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding...';
            
            console.log("Sending indicator config:", JSON.stringify(indicatorConfig));
            
            // Call the API
            fetch(API_ENDPOINTS.ADD_INDICATORS, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(indicatorConfig)
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    throw new Error(data.message || 'Error adding indicators');
                }
                
                console.log("API response:", data);
                
                // IMPORTANT: Replace the indicators list entirely rather than merging
                // This ensures previously checked indicators that are now unchecked don't persist
                availableIndicators = data.available_indicators || [];
                console.log("Updated indicators list:", availableIndicators);
                
                // Update the indicator selection dropdowns
                updateIndicatorDropdowns();
                
                // Show success message
                showSuccessMessage('Indicators added successfully!');
                
                // Ensure dataProcessed flag remains true
                dataProcessed = true;
                sessionStorage.setItem('dataProcessed', 'true');
            })
            .catch(error => {
                console.error('Error adding indicators:', error);
                showError('Error adding indicators: ' + error.message);
            })
            .finally(() => {
                // Re-enable the button
                if (addIndicatorsBtn) {
                    addIndicatorsBtn.disabled = false;
                    addIndicatorsBtn.textContent = 'Add Indicators';
                }
            });
        });
    }
    
    // Add event listener for the chart form
    const chartForm = document.getElementById('chart-form');
    if (chartForm) {
        chartForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Ensure data is still processed
            if (!dataProcessed) {
                showError('Please upload and process data first.');
                activateTab(dataTab, dataSection, 'Data Upload');
                return;
            }
            
            // Get all indicators from the respective lists
            const mainIndicatorsSelect = document.getElementById('main-indicators');
            const subplotIndicatorsSelect = document.getElementById('subplot-indicators');
            
            // Get all options (not just selected ones) from each list
            const mainIndicators = Array.from(mainIndicatorsSelect.options).map(opt => opt.value);
            const subplotIndicators = Array.from(subplotIndicatorsSelect.options).map(opt => opt.value);
            
            // Get date range
            const startDate = document.getElementById('chart-start-date').value;
            const endDate = document.getElementById('chart-end-date').value;
            
            // Prepare request data
            const plotConfig = {
                main_indicators: mainIndicators,
                subplot_indicators: subplotIndicators,
                title: 'Price Chart with Selected Indicators',
                start_date: startDate,
                end_date: endDate
            };
            
            // Disable the plot button
            const plotChartBtn = document.getElementById('plot-chart-btn');
            plotChartBtn.disabled = true;
            plotChartBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Plotting...';
            
            // Call the API
            fetch(API_ENDPOINTS.PLOT_INDICATORS, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(plotConfig)
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.message || `Error plotting chart (${response.status})`);
                    });
                }
                return response.json();
            })
            .then(data => {
                // Check if the response indicates success, regardless of the message
                if (!data.success && data.message !== 'Plot created successfully') {
                    throw new Error(data.message || 'Error plotting chart');
                }
                
                // Display the chart
                const chartImage = document.getElementById('chart-image');
                if (data.chart_image) {
                    chartImage.src = `data:image/png;base64,${data.chart_image}`;
                    chartImage.style.display = 'block';
                } else {
                    showError('No chart image data returned from server');
                }
                
                // Display indicator summary if available
                if (data.indicator_summary) {
                    const indicatorSummary = document.getElementById('indicator-summary');
                    indicatorSummary.innerHTML = data.indicator_summary;
                }
                
                // Ensure dataProcessed flag remains true
                dataProcessed = true;
                sessionStorage.setItem('dataProcessed', 'true');
            })
            .catch(error => {
                // Don't log or show "Plot created successfully" as an error
                if (error.message !== 'Plot created successfully') {
                    console.error('Error plotting chart:', error);
                    showError('Error plotting chart: ' + error.message);
                }
            })
            .finally(() => {
                // Re-enable the button
                if (plotChartBtn) {
                    plotChartBtn.disabled = false;
                    plotChartBtn.textContent = 'Plot Chart';
                }
            });
        });
    }
    
    // Add event listener for the strategy comparison form
    const compareStrategiesForm = document.getElementById('compare-strategies-form');
    if (compareStrategiesForm) {
        compareStrategiesForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Ensure data is still processed
            if (!dataProcessed) {
                showError('Please upload and process data first.');
                activateTab(dataTab, dataSection, 'Data Upload');
                return;
            }
            
            // Get selected strategies to compare using the value of the checkboxes
            const selectedStrategies = Array.from(document.querySelectorAll('#compare-strategies-form input[type="checkbox"]:checked'))
                .map(checkbox => checkbox.value);
                
            if (selectedStrategies.length === 0) {
                showNotification('Please select at least one strategy to compare', 'warning');
                return;
            }
            
            // Compare strategies
            compareStrategies();
        });
    }
    
    // Add event listener for the update strategy button
    const updateStrategyBtn = document.getElementById('update-strategy-btn');
    if (updateStrategyBtn) {
        updateStrategyBtn.addEventListener('click', () => {
            // Ensure data is still processed
            if (!dataProcessed) {
                showError('Please upload and process data first.');
                activateTab(dataTab, dataSection, 'Data Upload');
                return;
            }
            
            // Get the strategy type and parameters
            const strategyType = document.getElementById('strategy-type').value;
            
            // Check if parameters have been loaded
            if (!document.getElementById('strategy-parameters').children.length) {
                showError('Strategy parameters not loaded. Please wait or try again.');
                return;
            }
            
            try {
                // Different parameters based on strategy type
                let parameters = {};
                
                if (strategyType === 'trend_following') {
                    parameters = {
                        fast_ma_type: document.getElementById('fast-ma-type').value,
                        fast_ma_period: parseInt(document.getElementById('fast-ma-period').value),
                        slow_ma_type: document.getElementById('slow-ma-type').value,
                        slow_ma_period: parseInt(document.getElementById('slow-ma-period').value)
                    };
                } else if (strategyType === 'mean_reversion') {
                    parameters = {
                        rsi_period: parseInt(document.getElementById('rsi-period').value),
                        oversold: parseInt(document.getElementById('oversold').value),
                        overbought: parseInt(document.getElementById('overbought').value),
                        exit_middle: parseInt(document.getElementById('exit-middle').value)
                    };
                } else if (strategyType === 'breakout') {
                    parameters = {
                        lookback_period: parseInt(document.getElementById('lookback-period').value),
                        volume_threshold: parseFloat(document.getElementById('volume-threshold').value),
                        price_threshold: parseFloat(document.getElementById('price-threshold').value) / 100, // Convert from % to decimal
                        volatility_exit: document.getElementById('volatility-exit').checked,
                        atr_multiplier: parseFloat(document.getElementById('atr-multiplier').value),
                        use_bbands: document.getElementById('use-bbands').checked
                    };
                }
                
                // Update current configuration
                if (!currentConfig.strategies) {
                    currentConfig.strategies = {};
                }
                
                currentConfig.strategies[strategyType] = parameters;
                
                // Show success message
                showSuccessMessage(`${strategyType.replace('_', ' ')} strategy parameters updated.`);
                
                // Ensure dataProcessed flag remains true
                dataProcessed = true;
                sessionStorage.setItem('dataProcessed', 'true');
                
            } catch (error) {
                console.error('Error updating strategy parameters:', error);
                showError('Error updating strategy parameters: ' + error.message);
            }
        });
    }
    
    // Initialize indicator controls
    initializeIndicatorControls();
    
    // Initialize seasonality controls
    initializeSeasonalityControls();
});

// Helper function to show success message
function showSuccessMessage(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'alert alert-success alert-dismissible fade show mt-3';
    successDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Find a good place to show the message
    const currentSection = document.querySelector('.content-section.active');
    if (currentSection) {
        currentSection.appendChild(successDiv);
        
        // Remove the message after 5 seconds
        setTimeout(() => {
            successDiv.remove();
        }, 5000);
    }
}

// Function to update indicator dropdowns for chart plotting
function updateIndicatorDropdowns() {
    const mainIndicatorsSelect = document.getElementById('main-indicators');
    const subplotIndicatorsSelect = document.getElementById('subplot-indicators');
    
    // Clear existing options
    mainIndicatorsSelect.innerHTML = '';
    subplotIndicatorsSelect.innerHTML = '';
    
    console.log("Updating indicator dropdowns with available indicators:", availableIndicators);
    
    // Categorize indicators based on type
    const mainIndicatorTypes = ['sma_', 'ema_', 'bb_', 'typical_price'];
    const subplotIndicatorTypes = ['rsi', 'macd', 'stoch', 'obv', 'vpt', 'volume_', 'atr'];
    
    // Exclude columns that are not indicators
    const excludedItems = ['ticker', 'index'];
    const filteredIndicators = availableIndicators.filter(indicator => 
        !excludedItems.includes(indicator) && 
        indicator !== 'date' && 
        indicator !== 'open' && 
        indicator !== 'high' && 
        indicator !== 'low' && 
        indicator !== 'close' && 
        indicator !== 'volume'
    );
    
    console.log("Filtered indicators (excluding non-indicators):", filteredIndicators);
    
    const categorizedMain = [];
    const categorizedSubplot = [];
    
    // Initialize typical_price for price display
    const hasTypicalPrice = filteredIndicators.some(ind => ind === 'typical_price');
    if (!hasTypicalPrice) {
        categorizedMain.push('typical_price');
    }
    
    filteredIndicators.forEach(indicator => {
        // Decide which dropdown this indicator belongs to
        let isMainIndicator = mainIndicatorTypes.some(prefix => indicator.startsWith(prefix));
        let isSubplotIndicator = subplotIndicatorTypes.some(prefix => indicator.startsWith(prefix) || indicator === prefix);
        
        if (isMainIndicator) {
            categorizedMain.push(indicator);
        } else if (isSubplotIndicator) {
            categorizedSubplot.push(indicator);
        } else {
            // Default to subplot for unknown indicators
            categorizedSubplot.push(indicator);
        }
    });
    
    console.log("Categorized main indicators:", categorizedMain);
    console.log("Categorized subplot indicators:", categorizedSubplot);
    
    // Add categorized indicators to their respective dropdowns
    categorizedMain.forEach(indicator => {
        const option = document.createElement('option');
        option.value = indicator;
        option.textContent = indicator.replace(/_/g, ' ');
        mainIndicatorsSelect.appendChild(option);
    });
    
    categorizedSubplot.forEach(indicator => {
        const option = document.createElement('option');
        option.value = indicator;
        option.textContent = indicator.replace(/_/g, ' ');
        subplotIndicatorsSelect.appendChild(option);
    });
}

// Function to initialize indicator control buttons
function initializeIndicatorControls() {
    // Add event listeners for the indicator control buttons
    document.getElementById('move-to-main').addEventListener('click', function() {
        moveSelectedOptions('subplot-indicators', 'main-indicators');
    });
    
    document.getElementById('move-to-subplot').addEventListener('click', function() {
        moveSelectedOptions('main-indicators', 'subplot-indicators');
    });
    
    document.getElementById('remove-main').addEventListener('click', function() {
        removeSelectedOptions('main-indicators');
    });
    
    document.getElementById('remove-subplot').addEventListener('click', function() {
        removeSelectedOptions('subplot-indicators');
    });
}

// Helper function to move selected options between select elements
function moveSelectedOptions(sourceId, targetId) {
    const sourceSelect = document.getElementById(sourceId);
    const targetSelect = document.getElementById(targetId);
    
    // Get selected options
    const selectedOptions = Array.from(sourceSelect.selectedOptions);
    
    // Move each selected option to the target
    selectedOptions.forEach(option => {
        // Check if this option already exists in the target
        const existingOption = Array.from(targetSelect.options).find(opt => opt.value === option.value);
        if (existingOption) {
            console.log(`Option ${option.value} already exists in target, skipping`);
            return;
        }
        
        // Create a new option for the target
        const newOption = document.createElement('option');
        newOption.value = option.value;
        newOption.textContent = option.textContent;
        
        // Add to target and remove from source
        targetSelect.appendChild(newOption);
        sourceSelect.removeChild(option);
    });
}

// Helper function to remove selected options from a select element
function removeSelectedOptions(selectId) {
    const select = document.getElementById(selectId);
    
    // Get selected options in reverse order (to avoid index issues when removing)
    const selectedOptions = Array.from(select.selectedOptions).reverse();
    
    // Remove each selected option
    selectedOptions.forEach(option => {
        select.removeChild(option);
    });
}

// Function to check backend data status
async function checkDataStatus() {
    try {
        const response = await fetch(API_ENDPOINTS.DATA_STATUS);
        const status = await response.json();
        
        console.log('Backend data status:', status);
        
        // Update frontend state based on backend status
        if (status.uploaded) {
            dataUploaded = true;
            sessionStorage.setItem('dataUploaded', 'true');
            
            // Enable the process button if data is uploaded but not processed
            if (!status.processed) {
                const processBtn = document.getElementById('process-btn');
                if (processBtn) {
                    processBtn.disabled = false;
                }
            }
        }
        
        if (status.processed) {
            dataProcessed = true;
            sessionStorage.setItem('dataProcessed', 'true');
        }
        
        return status;
    } catch (error) {
        console.error('Error checking data status:', error);
        return { uploaded: false, processed: false };
    }
}

// Helper function to format metric names for display
function formatMetricName(metric) {
    // Convert snake_case to Title Case with spaces
    const formatted = metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    return formatted;
}

// Helper function to format metric values based on their type
function formatMetricValue(metric, value) {
    if (typeof value === 'number') {
        // Format percentages with 2 decimal places
        if (metric.includes('return') || metric.includes('drawdown') || metric.includes('volatility') || metric.includes('rate')) {
            return value.toFixed(2) + '%';
        } 
        // Format ratios with 2 decimal places
        else if (metric.includes('ratio')) {
            return value.toFixed(2);
        }
        // Format other numbers with 2 decimal places
        return value.toFixed(2);
    }
    return value;
}

// Show loader with custom message
function showLoader(message = 'Loading...') {
    let loaderEl = document.createElement('div');
    loaderEl.id = 'global-loader';
    loaderEl.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center bg-dark bg-opacity-50';
    loaderEl.style.zIndex = '9999';
    loaderEl.innerHTML = `
        <div class="bg-white p-3 rounded">
            <div class="d-flex align-items-center">
                <div class="spinner-border text-primary me-3"></div>
                <span>${message}</span>
            </div>
        </div>
    `;
    document.body.appendChild(loaderEl);
}

// Hide loader
function hideLoader() {
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.remove();
    }
}

// Show notification message
function showNotification(message, type = 'info') {
    // Create a Bootstrap alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to the current active section
    const currentSection = document.querySelector('.content-section.active');
    if (currentSection) {
        currentSection.prepend(alertDiv);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

// Seasonality Analysis
function initializeSeasonalityControls() {
    // Instead of looking for buttons that don't exist, we'll use the form submission
    const seasonalityForm = document.getElementById('seasonality-form');
    if (seasonalityForm) {
        seasonalityForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const seasonalityType = document.getElementById('seasonality-type').value;
            
            // Convert seasonality_type value to the format expected by the API
            let analysisType;
            switch (seasonalityType) {
                case 'day_of_week':
                    analysisType = 'day-of-week';
                    break;
                case 'monthly':
                    analysisType = 'monthly';
                    break;
                case 'volatility':
                    analysisType = 'volatility';
                    break;
                case 'heatmap':
                    analysisType = 'heatmap';
                    break;
                default:
                    analysisType = 'summary';
            }
            
            runSeasonalityAnalysis(analysisType);
        });
    } else {
        console.warn('Seasonality form not found in the DOM');
    }
}

async function runSeasonalityAnalysis(analysisType) {
    // Show loading state
    showLoader(`Generating ${analysisType.replace('-', ' ')} analysis...`);
    
    // Map analysis type to API endpoint
    const endpointMap = {
        'day-of-week': API_ENDPOINTS.SEASONALITY_DAY_OF_WEEK,
        'monthly': API_ENDPOINTS.SEASONALITY_MONTHLY,
        'volatility': API_ENDPOINTS.SEASONALITY_VOLATILITY,
        'heatmap': API_ENDPOINTS.SEASONALITY_HEATMAP,
        'summary': API_ENDPOINTS.SEASONALITY_SUMMARY
    };
    
    const endpoint = endpointMap[analysisType];
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || 'Failed to perform seasonality analysis');
        }
        
        // Display the results
        displaySeasonalityResults(data, analysisType);
        
    } catch (error) {
        showError(`Seasonality analysis error: ${error.message}`);
        console.error('Seasonality analysis error:', error);
    } finally {
        hideLoader();
    }
}

function displaySeasonalityResults(data, analysisType) {
    const resultsDiv = document.getElementById('seasonality-results');
    if (!resultsDiv) {
        console.error('Seasonality results div not found');
        return;
    }
    
    // Create HTML for the results
    let resultsHTML = '';
    
    // Add the plot image
    resultsHTML += `
        <div class="text-center mb-3">
            <h5>${getSeasonalityTitle(analysisType)}</h5>
            <img src="data:image/png;base64,${data.plot}" class="img-fluid" alt="Seasonality Analysis">
        </div>
    `;
    
    // Add data tables based on analysis type
    if (analysisType === 'heatmap') {
        // No table data for heatmap
        resultsHTML += `<p class="text-muted mt-3">The heatmap visualizes average returns by calendar day. Green indicates positive returns, red indicates negative returns.</p>`;
    } else if (analysisType === 'summary') {
        // Create accordion with all data
        resultsHTML += createSeasonalitySummaryAccordionHTML(data.data);
    } else {
        // Create appropriate table based on analysis type
        resultsHTML += createSeasonalityTableHTML(data.data, analysisType);
    }
    
    // Set the HTML content
    resultsDiv.innerHTML = resultsHTML;
}

// Helper function to get the title for a seasonality analysis type
function getSeasonalityTitle(analysisType) {
    const titles = {
        'day-of-week': 'Day of Week Returns Analysis',
        'monthly': 'Monthly Returns Analysis',
        'volatility': 'Volatility by Day of Week Analysis',
        'heatmap': 'Calendar Returns Heatmap',
        'summary': 'Complete Seasonality Analysis'
    };
    
    return titles[analysisType] || 'Seasonality Analysis';
}

// Create HTML for seasonality table
function createSeasonalityTableHTML(data, analysisType) {
    let tableHtml = '<table class="table table-striped table-sm mt-3">';
    
    // Create table header based on analysis type
    if (analysisType === 'day-of-week') {
        tableHtml += `
            <thead>
                <tr>
                    <th scope="col">Day</th>
                    <th scope="col">Mean Return (%)</th>
                    <th scope="col">Std Dev</th>
                    <th scope="col">Count</th>
                </tr>
            </thead>
            <tbody>
        `;
        
        // Add table rows
        data.forEach(row => {
            tableHtml += `
                <tr>
                    <td>${row.day_of_week}</td>
                    <td class="${row.mean >= 0 ? 'text-success' : 'text-danger'}">${row.mean.toFixed(2)}</td>
                    <td>${row.std.toFixed(2)}</td>
                    <td>${row.count}</td>
                </tr>
            `;
        });
    } else if (analysisType === 'monthly') {
        tableHtml += `
            <thead>
                <tr>
                    <th scope="col">Month</th>
                    <th scope="col">Mean Return (%)</th>
                    <th scope="col">Std Dev</th>
                    <th scope="col">Count</th>
                </tr>
            </thead>
            <tbody>
        `;
        
        // Add table rows
        data.forEach(row => {
            tableHtml += `
                <tr>
                    <td>${row.month_name}</td>
                    <td class="${row.mean >= 0 ? 'text-success' : 'text-danger'}">${row.mean.toFixed(2)}</td>
                    <td>${row.std.toFixed(2)}</td>
                    <td>${row.count}</td>
                </tr>
            `;
        });
    } else if (analysisType === 'volatility') {
        tableHtml += `
            <thead>
                <tr>
                    <th scope="col">Day</th>
                    <th scope="col">Mean Volatility (%)</th>
                    <th scope="col">Std Dev</th>
                    <th scope="col">Count</th>
                </tr>
            </thead>
            <tbody>
        `;
        
        // Add table rows
        data.forEach(row => {
            tableHtml += `
                <tr>
                    <td>${row.day_of_week}</td>
                    <td>${row.mean.toFixed(2)}</td>
                    <td>${row.std.toFixed(2)}</td>
                    <td>${row.count}</td>
                </tr>
            `;
        });
    }
    
    tableHtml += '</tbody></table>';
    
    return tableHtml;
}

// Create HTML for summary accordion
function createSeasonalitySummaryAccordionHTML(data) {
    let accordionHtml = `
        <div class="accordion mt-3" id="seasonalityAccordion">
            <div class="accordion-item">
                <h2 class="accordion-header" id="dowReturnsHeading">
                    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#dowReturnsCollapse" aria-expanded="true" aria-controls="dowReturnsCollapse">
                        Day of Week Returns
                    </button>
                </h2>
                <div id="dowReturnsCollapse" class="accordion-collapse collapse show" aria-labelledby="dowReturnsHeading" data-bs-parent="#seasonalityAccordion">
                    <div class="accordion-body">
                        <table class="table table-striped table-sm">
                            <thead>
                                <tr>
                                    <th scope="col">Day</th>
                                    <th scope="col">Mean Return (%)</th>
                                    <th scope="col">Std Dev</th>
                                    <th scope="col">Count</th>
                                </tr>
                            </thead>
                            <tbody>
    `;
    
    // Add day of week returns rows
    data.day_of_week_returns.forEach(row => {
        accordionHtml += `
                                <tr>
                                    <td>${row.day_of_week}</td>
                                    <td class="${row.mean >= 0 ? 'text-success' : 'text-danger'}">${row.mean.toFixed(2)}</td>
                                    <td>${row.std.toFixed(2)}</td>
                                    <td>${row.count}</td>
                                </tr>
        `;
    });
    
    accordionHtml += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="accordion-item">
                <h2 class="accordion-header" id="monthlyReturnsHeading">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#monthlyReturnsCollapse" aria-expanded="false" aria-controls="monthlyReturnsCollapse">
                        Monthly Returns
                    </button>
                </h2>
                <div id="monthlyReturnsCollapse" class="accordion-collapse collapse" aria-labelledby="monthlyReturnsHeading" data-bs-parent="#seasonalityAccordion">
                    <div class="accordion-body">
                        <table class="table table-striped table-sm">
                            <thead>
                                <tr>
                                    <th scope="col">Month</th>
                                    <th scope="col">Mean Return (%)</th>
                                    <th scope="col">Std Dev</th>
                                    <th scope="col">Count</th>
                                </tr>
                            </thead>
                            <tbody>
    `;
    
    // Add monthly returns rows
    data.monthly_returns.forEach(row => {
        accordionHtml += `
                                <tr>
                                    <td>${row.month_name}</td>
                                    <td class="${row.mean >= 0 ? 'text-success' : 'text-danger'}">${row.mean.toFixed(2)}</td>
                                    <td>${row.std.toFixed(2)}</td>
                                    <td>${row.count}</td>
                                </tr>
        `;
    });
    
    accordionHtml += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="accordion-item">
                <h2 class="accordion-header" id="volatilityHeading">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#volatilityCollapse" aria-expanded="false" aria-controls="volatilityCollapse">
                        Day of Week Volatility
                    </button>
                </h2>
                <div id="volatilityCollapse" class="accordion-collapse collapse" aria-labelledby="volatilityHeading" data-bs-parent="#seasonalityAccordion">
                    <div class="accordion-body">
                        <table class="table table-striped table-sm">
                            <thead>
                                <tr>
                                    <th scope="col">Day</th>
                                    <th scope="col">Mean Volatility (%)</th>
                                    <th scope="col">Std Dev</th>
                                    <th scope="col">Count</th>
                                </tr>
                            </thead>
                            <tbody>
    `;
    
    // Add volatility rows
    data.day_of_week_volatility.forEach(row => {
        accordionHtml += `
                                <tr>
                                    <td>${row.day_of_week}</td>
                                    <td>${row.mean.toFixed(2)}</td>
                                    <td>${row.std.toFixed(2)}</td>
                                    <td>${row.count}</td>
                                </tr>
        `;
    });
    
    accordionHtml += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    return accordionHtml;
}

// ... existing code ...

// Document Ready
document.addEventListener('DOMContentLoaded', () => {
    // ... existing code ...
    
    // Initialize seasonality controls
    initializeSeasonalityControls();
    
    // ... existing code ...
});

// ... existing code ...