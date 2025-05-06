// App.js - Main JavaScript file for the Trading Analysis System

// DOM Element References
const dataTab = document.getElementById('data-tab');
const indicatorsTab = document.getElementById('indicators-tab');
const strategiesTab = document.getElementById('strategies-tab');
const backtestTab = document.getElementById('backtest-tab');
const optimizationTab = document.getElementById('optimization-tab');
const resultsTab = document.getElementById('results-tab');

const pageTitle = document.getElementById('page-title');

const dataSection = document.getElementById('data-section');
const indicatorsSection = document.getElementById('indicators-section');
const strategiesSection = document.getElementById('strategies-section');
const backtestSection = document.getElementById('backtest-section');
const optimizationSection = document.getElementById('optimization-section');
const resultsSection = document.getElementById('results-section');

const uploadForm = document.getElementById('upload-form');
const csvFileInput = document.getElementById('csv-file');
const uploadBtn = document.getElementById('upload-btn');
const processBtn = document.getElementById('process-btn');

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
    COMPARE_STRATEGIES: '/api/compare-strategies',
    SAVE_CONFIG: '/api/save-config',
    LOAD_CONFIG: '/api/load-config',
    EXPORT_RESULTS: '/api/export-results',
    CURRENT_CONFIG: '/api/current-config'
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
    [dataTab, indicatorsTab, strategiesTab, backtestTab, optimizationTab, resultsTab].forEach(t => {
        t.classList.remove('active');
    });
    
    [dataSection, indicatorsSection, strategiesSection, backtestSection, optimizationSection, resultsSection].forEach(s => {
        s.classList.remove('active');
    });
    
    // Activate the selected tab and show the corresponding section
    tab.classList.add('active');
    section.classList.add('active');
    pageTitle.textContent = title;
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
        return;
    }
    activateTab(indicatorsTab, indicatorsSection, 'Technical Indicators');
});

strategiesTab.addEventListener('click', (e) => {
    e.preventDefault();
    if (!dataProcessed) {
        showError('Please upload and process data first.');
        return;
    }
    activateTab(strategiesTab, strategiesSection, 'Trading Strategies');
    loadStrategyParameters();
});

backtestTab.addEventListener('click', (e) => {
    e.preventDefault();
    if (!dataProcessed) {
        showError('Please upload and process data first.');
        return;
    }
    activateTab(backtestTab, backtestSection, 'Backtest');
});

optimizationTab.addEventListener('click', (e) => {
    e.preventDefault();
    if (!dataProcessed) {
        showError('Please upload and process data first.');
        return;
    }
    activateTab(optimizationTab, optimizationSection, 'Strategy Optimization');
    setupOptimizationParameters();
});

resultsTab.addEventListener('click', (e) => {
    e.preventDefault();
    const backtestResults = document.getElementById('backtest-results');
    if (backtestResults.innerHTML === '') {
        showError('Please run a backtest first to see results.');
        return;
    }
    activateTab(resultsTab, resultsSection, 'Analysis Results');
});

// Data Upload and Processing
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('csv-file');
    if (!fileInput.files.length) {
        showError('Please select a CSV file to upload.');
        return;
    }
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Uploading...';
        
        const response = await fetch(API_ENDPOINTS.UPLOAD, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error uploading file');
        }
        
        // Update UI with data preview
        updateDataPreview(data);
        
        // Enable the process button
        processBtn.disabled = false;
        dataUploaded = true;
        
    } catch (error) {
        showError(error.message);
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Upload';
    }
});

processBtn.addEventListener('click', async () => {
    if (!dataUploaded) {
        showError('Please upload a CSV file first.');
        return;
    }
    
    try {
        processBtn.disabled = true;
        processBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
        
        const response = await fetch(API_ENDPOINTS.PROCESS_DATA, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error processing data');
        }
        
        // Update UI with processed data preview
        updateDataPreview(data);
        
        // Set data as processed
        dataProcessed = true;
        
        // Show success message
        dataInfo.innerHTML += `<div class="alert alert-success mt-2">Data processed successfully!</div>`;
        
        // Fetch current config
        fetchCurrentConfig();
        
    } catch (error) {
        showError(error.message);
    } finally {
        processBtn.disabled = false;
        processBtn.textContent = 'Process Data';
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

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    // Activate the first tab by default
    activateTab(dataTab, dataSection, 'Data Upload');
}); 