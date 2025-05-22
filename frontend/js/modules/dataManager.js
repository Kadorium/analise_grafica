// frontend/js/modules/dataManager.js

// Import dependencies
import { uploadData, processData, fetchDataStatus, arrangeData, uploadMultiAssetData } from '../utils/api.js';
import { showError, showLoading, showSuccessMessage, showGlobalLoader, hideGlobalLoader, hideLoading } from '../utils/ui.js';
import { formatDate } from '../utils/formatters.js';
import { appState } from '../utils/state.js';

// DOM references
const uploadForm = document.getElementById('upload-form');
const csvFileInput = document.getElementById('csv-file');
const uploadProcessBtn = document.getElementById('upload-process-btn');
const dataInfo = document.getElementById('data-info');
const dataPreview = document.getElementById('data-preview');
const arrangeBtn = document.getElementById('arrange-btn');

// Multi-asset DOM references
const multiUploadForm = document.getElementById('multi-upload-form');
const excelFileInput = document.getElementById('excel-file');
const multiUploadProcessBtn = document.getElementById('multi-upload-process-btn');
const multiDataInfo = document.getElementById('multi-data-info');
const multiDataPreview = document.getElementById('multi-data-preview');
const assetSelector = document.getElementById('asset-selector');

// Update all date input fields throughout the application
function updateDateRanges(startDate, endDate) {
    console.log(`Updating date ranges with start: ${startDate}, end: ${endDate}`);
    
    // Format dates if they're not already in YYYY-MM-DD format
    const formattedStartDate = formatDate(startDate);
    const formattedEndDate = formatDate(endDate);
    
    // Update state with the date range
    appState.setDateRange(formattedStartDate, formattedEndDate);
    
    // Get all date input fields
    const startDateInputs = document.querySelectorAll(
        '#chart-start-date, #backtest-start-date, #optimization-start-date, #compare-start-date, #seasonality-start-date'
    );
    
    const endDateInputs = document.querySelectorAll(
        '#chart-end-date, #backtest-end-date, #optimization-end-date, #compare-end-date, #seasonality-end-date'
    );
    
    // Update start date inputs
    startDateInputs.forEach(input => {
        if (input) input.value = formattedStartDate;
    });
    
    // Update end date inputs
    endDateInputs.forEach(input => {
        if (input) input.value = formattedEndDate;
    });
    
    console.log('Date fields updated throughout the application');
}

// Calculate appropriate date range based on data
function calculateDateRange(data) {
    let startDate, endDate;
    
    // Try to extract date range from different response formats
    if (data.date_range) {
        startDate = data.date_range.start;
        endDate = data.date_range.end;
    } else if (data.info && data.info.start_date && data.info.end_date) {
        startDate = data.info.start_date;
        endDate = data.info.end_date;
    } else {
        console.warn('No date range information found in response');
        return;
    }
    
    // Parse dates to ensure they're valid
    const endDateObj = new Date(endDate);
    
    // Calculate a date 5 years before end date
    const fiveYearsBeforeEnd = new Date(endDateObj);
    fiveYearsBeforeEnd.setFullYear(fiveYearsBeforeEnd.getFullYear() - 5);
    
    // Use the later of: start date from data, or 5 years before end date
    const startDateObj = new Date(startDate);
    const effectiveStartDate = startDateObj > fiveYearsBeforeEnd ? startDate : formatDate(fiveYearsBeforeEnd);
    
    return {
        startDate: effectiveStartDate,
        endDate: endDate
    };
}

// Update data preview table
export function updateDataPreview(data) {
    if (!dataPreview) return;
    
    // Handle different response formats
    const preview = data.data_sample || data.preview || [];
    if (!preview || !preview.length) {
        dataPreview.innerHTML = '<div class="alert alert-info">No data to preview</div>';
        return;
    }
    
    const headers = Object.keys(preview[0]);
    
    let tableHtml = `
        <div class="table-responsive">
            <table class="table table-striped table-bordered">
                <thead>
                    <tr>
                        ${headers.map(header => `<th>${header}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Add rows
    preview.forEach(row => {
        tableHtml += '<tr>';
        headers.forEach(header => {
            let cellValue = row[header];
            
            // Format dates if needed
            if (header.toLowerCase().includes('date') && cellValue) {
                cellValue = formatDate(cellValue);
            }
            
            tableHtml += `<td>${cellValue !== undefined ? cellValue : ''}</td>`;
        });
        tableHtml += '</tr>';
    });
    
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    // Update data info
    if (dataInfo) {
        let infoHtml = '';
        
        if (data.data_shape) {
            infoHtml += `<p><strong>Rows:</strong> ${data.data_shape[0]} | <strong>Columns:</strong> ${data.data_shape[1]}</p>`;
        } else if (data.info && data.info.rows) {
            infoHtml += `<p><strong>Rows:</strong> ${data.info.rows}</p>`;
        }
        
        if (data.date_range) {
            infoHtml += `<p><strong>Date Range:</strong> ${data.date_range.start} to ${data.date_range.end}</p>`;
        } else if (data.info && data.info.start_date && data.info.end_date) {
            infoHtml += `<p><strong>Date Range:</strong> ${formatDate(data.info.start_date)} to ${formatDate(data.info.end_date)}</p>`;
        }
        
        if (data.info && data.info.symbol) {
            infoHtml += `<p><strong>Symbol:</strong> ${data.info.symbol}</p>`;
        }
        
        dataInfo.innerHTML = infoHtml ? 
            `<div class="card mb-3"><div class="card-body"><h5 class="card-title">Data Summary</h5>${infoHtml}</div></div>` : 
            '';
    }
    
    // Update preview
    dataPreview.innerHTML = tableHtml;
    
    // Add success message
    if (data.success || data.message) {
        const message = data.message || 'Data processed successfully';
        if (dataInfo) {
            dataInfo.innerHTML += `<div class="alert alert-success mt-2">${message}</div>`;
        }
    }
    
    // Update date ranges throughout the application if date information is available
    const dateRange = calculateDateRange(data);
    if (dateRange) {
        updateDateRanges(dateRange.startDate, dateRange.endDate);
    }
}

// Update multi-asset data preview
export function updateMultiAssetDataPreview(data) {
    if (!multiDataPreview || !assetSelector) return;
    
    // Update asset selector
    if (data.assets && data.assets.length > 0) {
        let options = '';
        data.assets.forEach(asset => {
            options += `<option value="${asset}">${asset}</option>`;
        });
        assetSelector.innerHTML = options;
        
        // Set up event listener for asset selection
        assetSelector.onchange = function() {
            const selectedAsset = this.value;
            updateSelectedAssetPreview(data.previews[selectedAsset]);
        };
        
        // Show the first asset by default
        const firstAsset = data.assets[0];
        assetSelector.value = firstAsset;
        updateSelectedAssetPreview(data.previews[firstAsset]);
        
        // Enable the screener tab now that we have multi-asset data
        appState.setMultiAssetUploaded(true);
        
        // Create a data summary in multiDataInfo
        if (multiDataInfo) {
            let infoHtml = `
                <div class="alert alert-success">
                    <strong>Multi-Asset Data Loaded:</strong> ${data.assets.length} assets
                </div>
                <p><strong>Date Range:</strong> ${data.date_range.start} to ${data.date_range.end}</p>
            `;
            multiDataInfo.innerHTML = infoHtml;
        }
        
        // Dispatch an event to notify other components that multi-asset data is available
        document.dispatchEvent(new CustomEvent('multi-asset-data-uploaded', { detail: { assetCount: data.assets.length } }));
        
        // Show a success message
        const message = data.message || 'Multi-asset data processed successfully';
        showSuccessMessage(message);
    } else {
        if (multiDataInfo) {
            multiDataInfo.innerHTML = '<div class="alert alert-warning">No assets found in the uploaded file.</div>';
        }
        
        // Clear the preview
        multiDataPreview.innerHTML = '';
    }
}

// Update preview for selected asset
function updateSelectedAssetPreview(assetData) {
    if (!multiDataPreview || !assetData) return;
    
    const preview = assetData || [];
    if (!preview || !preview.length) {
        multiDataPreview.innerHTML = '<div class="alert alert-info">No data to preview</div>';
        return;
    }
    
    const headers = Object.keys(preview[0]);
    
    let tableHtml = `
        <div class="table-responsive">
            <table class="table table-striped table-bordered">
                <thead>
                    <tr>
                        ${headers.map(header => `<th>${header}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Add rows
    preview.forEach(row => {
        tableHtml += '<tr>';
        headers.forEach(header => {
            let cellValue = row[header];
            
            // Format dates if needed
            if (header.toLowerCase().includes('date') && cellValue) {
                cellValue = formatDate(cellValue);
            }
            
            tableHtml += `<td>${cellValue !== undefined ? cellValue : ''}</td>`;
        });
        tableHtml += '</tr>';
    });
    
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    // Update preview
    multiDataPreview.innerHTML = tableHtml;
}

// Check data status
export async function checkDataStatus() {
    try {
        console.log('Checking data status');
        const response = await fetchDataStatus();
        console.log('Data status response:', response);
        
        if (response.data_uploaded) {
            console.log('Data is uploaded');
            appState.setDataUploaded(true);
            
            // If data is also processed, update that state
            if (response.data_processed) {
                console.log('Data is processed');
                appState.setDataProcessed(true);
                
                // If date range information is available, update date fields
                if (response.date_range || (response.data && response.data.date_range)) {
                    const dateRange = response.date_range || response.data.date_range;
                    updateDateRanges(dateRange.start, dateRange.end);
                }
                
                // Enable all tabs if data is processed
                document.querySelectorAll('.nav-link').forEach(tab => {
                    if (tab && tab.id !== 'data-tab') {
                        tab.classList.remove('disabled');
                    }
                });
                
                // Create an event to notify other components
                const event = new CustomEvent('data-processed');
                document.dispatchEvent(event);
            }
        }
        
        return response;
    } catch (error) {
        console.error('Error checking data status:', error);
        return { data_uploaded: false, data_processed: false };
    }
}

// Initialize the data manager
export function initializeDataManager() {
    console.log('Initializing Data Manager');
    
    // Check data status on init
    checkDataStatus();
    
    // Initialize upload form
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            
            console.log('Upload form submitted');
            showLoading('Processing data...');
            
            const file = csvFileInput.files[0];
            const formData = new FormData();
            
            if (file) {
                formData.append('file', file);
            }
            
            try {
                // Upload the data
                const uploadResponse = await uploadData(formData);
                
                if (!uploadResponse.success && uploadResponse.message) {
                    showError(uploadResponse.message);
                    hideLoading(); // Hide loading indicator on error
                    return;
                }
                
                // Update state
                appState.setDataUploaded(true);
                
                // Update preview with upload response
                updateDataPreview(uploadResponse);
                
                // Now process the data
                const processResponse = await processData();
                
                if (!processResponse.success && processResponse.message) {
                    showError(processResponse.message);
                    hideLoading(); // Hide loading indicator on error
                    return;
                }
                
                // Update state
                appState.setDataProcessed(true);
                
                // Update preview with processed data
                updateDataPreview(processResponse);
                
                // Dispatch event to notify other components
                const event = new CustomEvent('data-processed', { detail: processResponse });
                document.dispatchEvent(event);
                
                // Hide loading indicator
                hideLoading();
                
                // Show success
                showSuccessMessage('Data processed successfully');
            } catch (error) {
                console.error('Error handling data upload:', error);
                showError(`Error processing data: ${error.message}`);
                hideLoading(); // Hide loading indicator on error
            }
        });
    }
    
    // Initialize arrange button
    if (arrangeBtn) {
        arrangeBtn.addEventListener('click', async function() {
            if (!csvFileInput.files[0]) {
                showError('Please select a file to arrange.');
                return;
            }
            
            showLoading('Arranging data...');
            
            const file = csvFileInput.files[0];
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await arrangeData(formData);
                
                if (response.success === false) {
                    showError(response.message);
                    hideLoading(); // Hide loading indicator on error
                    return;
                }
                
                // Update state
                appState.setDataUploaded(true);
                appState.setDataProcessed(true);
                
                // Update preview
                updateDataPreview(response);
                
                // Hide loading indicator
                hideLoading();
                
                // Show success
                showSuccessMessage('Data arranged successfully');
            } catch (error) {
                console.error('Error arranging data:', error);
                showError(`Error arranging data: ${error.message}`);
                hideLoading(); // Hide loading indicator on error
            }
        });
    }
    
    // Initialize multi-asset upload form
    if (multiUploadForm) {
        multiUploadForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            
            console.log('Multi-asset upload form submitted');
            showLoading('Processing multi-asset data...');
            
            const file = excelFileInput.files[0];
            const formData = new FormData();
            
            if (file) {
                formData.append('file', file);
            }
            
            try {
                // Upload the multi-asset data
                const response = await uploadMultiAssetData(formData);
                
                if (!response.success && response.message) {
                    showError(response.message);
                    hideLoading(); // Hide loading indicator on error
                    return;
                }
                
                // Update the multi-asset preview
                updateMultiAssetDataPreview(response);
                
                // Hide loading indicator
                hideLoading();
                
            } catch (error) {
                console.error('Error handling multi-asset data upload:', error);
                showError(`Error processing multi-asset data: ${error.message}`);
                hideLoading(); // Hide loading indicator on error
            }
        });
    }
}
