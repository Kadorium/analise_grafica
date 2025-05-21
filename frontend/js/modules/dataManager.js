// frontend/js/modules/dataManager.js

// Import dependencies
import { uploadData, processData, fetchDataStatus, arrangeData, uploadMultiAssetData } from '../utils/api.js';
import { showError, showLoading, showSuccessMessage, showGlobalLoader, hideGlobalLoader } from '../utils/ui.js';
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
    }
    
    // Update multi-data info
    if (multiDataInfo) {
        let infoHtml = '';
        
        if (data.assets) {
            infoHtml += `<p><strong>Number of Assets:</strong> ${data.assets.length}</p>`;
            infoHtml += `<p><strong>Assets:</strong> ${data.assets.join(', ')}</p>`;
        }
        
        if (data.date_range) {
            infoHtml += `<p><strong>Overall Date Range:</strong> ${data.date_range.start} to ${data.date_range.end}</p>`;
        }
        
        multiDataInfo.innerHTML = infoHtml ? 
            `<div class="card mb-3"><div class="card-body"><h5 class="card-title">Multi-Asset Summary</h5>${infoHtml}</div></div>` : 
            '';
    }
    
    // Add success message
    if (data.success || data.message) {
        const message = data.message || 'Multi-asset data processed successfully';
        if (multiDataInfo) {
            multiDataInfo.innerHTML += `<div class="alert alert-success mt-2">${message}</div>`;
        }
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

// Initialize data controls and event listeners
export function initializeDataManager() {
    // Check data status on init
    checkDataStatus();
    
    // Attach form submit event for single asset upload
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            console.log('Upload form submitted');
            const formData = new FormData();
            let fileNameForLog = "default_file.csv"; // Default file logging

            if (csvFileInput && csvFileInput.files.length > 0) {
                const file = csvFileInput.files[0];
                formData.append('file', file);
                fileNameForLog = file.name;
                console.log('Uploading selected file:', fileNameForLog);
            } else {
                // No file selected - append empty string to ensure proper multipart structure
                // The backend will use the default file
                formData.append('file', '');
                console.log('No file selected, using default file on server');
            }
            
            // Show loading state
            if (uploadProcessBtn) uploadProcessBtn.disabled = true;
            if (dataPreview) showLoading(dataPreview);
            
            try {
                // --- UPLOAD PHASE ---
                console.log('Starting upload phase');
                const uploadResponse = await uploadData(formData);
                console.log('Upload response:', uploadResponse);
                
                if (uploadResponse && (uploadResponse.success || uploadResponse.data_sample || uploadResponse.preview)) {
                    updateDataPreview(uploadResponse);
                    
                    // Set flag indicating data was uploaded
                    appState.setDataUploaded(true);
                    
                    // --- PROCESS PHASE ---
                    console.log('Starting process phase');
                    const processResponse = await processData();
                    console.log('Process response:', processResponse);
                    
                    if (processResponse && (processResponse.success !== false)) {
                        // Update UI with processing results
                        updateDataPreview(processResponse);
                        
                        // Set flag indicating data was processed
                        appState.setDataProcessed(true);
                        
                        // Enable all tabs
                        document.querySelectorAll('.nav-link').forEach(tab => {
                            if (tab && tab.id !== 'data-tab') {
                                tab.classList.remove('disabled');
                            }
                        });
                        
                        // Fire event for other components to react
                        const event = new CustomEvent('data-processed');
                        document.dispatchEvent(event);
                        
                        // Show success message
                        showSuccessMessage('Data uploaded and processed successfully!');
                    } else {
                        // Handle processing error
                        const errorMessage = processResponse && processResponse.message 
                            ? processResponse.message 
                            : 'Failed to process data. Please check the file format.';
                        
                        showError(errorMessage);
                    }
                } else {
                    // Handle upload error
                    const errorMessage = uploadResponse && uploadResponse.message 
                        ? uploadResponse.message 
                        : 'Failed to upload file. Please try again.';
                    
                    showError(errorMessage);
                }
            } catch (error) {
                console.error('Error in data upload/process:', error);
                showError('An error occurred: ' + (error.message || 'Unknown error'));
            } finally {
                // Re-enable button
                if (uploadProcessBtn) uploadProcessBtn.disabled = false;
            }
        });
    }
    
    // Attach form submit event for multi-asset upload
    if (multiUploadForm) {
        multiUploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            console.log('Multi-asset upload form submitted');
            const formData = new FormData();
            let fileNameForLog = "test multidata.xlsx"; // Default file name
            
            if (excelFileInput && excelFileInput.files.length > 0) {
                const file = excelFileInput.files[0];
                formData.append('file', file);
                fileNameForLog = file.name;
                console.log('Uploading selected file:', fileNameForLog);
            } else {
                // No file selected - append empty string to ensure proper multipart structure
                // The backend will use the default file
                formData.append('file', '');
                console.log('No file selected, using default multi-asset file on server');
            }
            
            // Show loading state
            if (multiUploadProcessBtn) multiUploadProcessBtn.disabled = true;
            if (multiDataPreview) showLoading(multiDataPreview);
            
            try {
                // Call the API to upload and process the multi-asset Excel file
                console.log('Starting multi-asset upload and process');
                const response = await uploadMultiAssetData(formData);
                console.log('Multi-asset upload response:', response);
                
                if (response && response.success !== false) {
                    // Update the multi-asset data preview
                    updateMultiAssetDataPreview(response);
                    
                    // Show success message
                    showSuccessMessage('Multi-asset data uploaded and processed successfully!');
                    
                    // Note: We don't set appState.setDataUploaded/Processed here
                    // as that's still controlled by the single asset flow
                    // This keeps the multi-asset data separate from the main workflow
                } else {
                    // Handle error
                    const errorMessage = response && response.message 
                        ? response.message 
                        : 'Failed to upload multi-asset file. Please check the file format.';
                    
                    showError(errorMessage);
                }
            } catch (error) {
                console.error('Error in multi-asset data upload/process:', error);
                showError('An error occurred: ' + (error.message || 'Unknown error'));
            } finally {
                // Re-enable button
                if (multiUploadProcessBtn) multiUploadProcessBtn.disabled = false;
            }
        });
    }
    
    // Attach arrange data button event
    if (arrangeBtn) {
        arrangeBtn.addEventListener('click', async () => {
            if (!csvFileInput || !csvFileInput.files.length) {
                showError('Please select a file to arrange');
                return;
            }
            
            const file = csvFileInput.files[0];
            const formData = new FormData();
            formData.append('file', file);
            
            // Show loading state
            arrangeBtn.disabled = true;
            showGlobalLoader('Arranging data...');
            
            try {
                const response = await arrangeData(formData);
                console.log('Arrange response:', response);
                
                if (response && (response.success !== false)) {
                    // Update UI with arranged results
                    updateDataPreview(response);
                    showSuccessMessage('Data arranged successfully!');
                    
                    // Set flags for data state
                    appState.setDataUploaded(true);
                    appState.setDataProcessed(true);
                    
                    // Enable all tabs
                    document.querySelectorAll('.nav-link').forEach(tab => {
                        if (tab && tab.id !== 'data-tab') {
                            tab.classList.remove('disabled');
                        }
                    });
                    
                    // Fire event for other components to react
                    const event = new CustomEvent('data-processed');
                    document.dispatchEvent(event);
                } else {
                    const errorMessage = response && response.message 
                        ? response.message 
                        : 'Failed to arrange data. Please check the file format.';
                    
                    showError(errorMessage);
                }
            } catch (error) {
                console.error('Error in data arrange:', error);
                showError('An error occurred: ' + (error.message || 'Unknown error'));
            } finally {
                // Re-enable button and hide loader
                arrangeBtn.disabled = false;
                hideGlobalLoader();
            }
        });
    }
}
