// frontend/js/modules/seasonalityAnalyzer.js

// Import dependencies
import { runSeasonalityAnalysis as runSeasonalityAnalysisApi } from '../utils/api.js';
import { showError, showLoading, showSuccessMessage, showGlobalLoader, hideGlobalLoader } from '../utils/ui.js';
import { formatDate, formatNumber } from '../utils/formatters.js';
import { appState } from '../utils/state.js';

// DOM references
const seasonalityForm = document.getElementById('seasonality-form');
const seasonalityResultsContainer = document.getElementById('seasonality-results');
const patternTypeSelect = document.getElementById('pattern-type');
const monthlyPatternOptions = document.getElementById('monthly-pattern-options');
const weeklyPatternOptions = document.getElementById('weekly-pattern-options');
const timePatternOptions = document.getElementById('time-pattern-options');

// Initialize seasonality controls
export function initializeSeasonalityControls() {
    // Add event listeners for pattern type selection
    if (patternTypeSelect) {
        patternTypeSelect.addEventListener('change', () => {
            togglePatternOptions(patternTypeSelect.value);
        });
        
        // Initialize with default value
        togglePatternOptions(patternTypeSelect.value);
    }
    
    // Add form submit event listener
    if (seasonalityForm) {
        seasonalityForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Get form values
            const formData = new FormData(seasonalityForm);
            const params = {};
            
            // Convert form data to params object
            for (const [key, value] of formData.entries()) {
                if (key.startsWith('is_') && value === 'on') {
                    // Handle checkboxes
                    params[key] = true;
                } else if (!isNaN(value) && value !== '') {
                    // Convert numeric values
                    params[key] = parseFloat(value);
                } else {
                    params[key] = value;
                }
            }
            
            // Run seasonality analysis
            await runSeasonalityAnalysis(params);
        });
    }
}

// Toggle pattern options based on selected pattern type
export function togglePatternOptions(patternType) {
    if (monthlyPatternOptions) {
        monthlyPatternOptions.style.display = patternType === 'monthly' ? 'block' : 'none';
    }
    
    if (weeklyPatternOptions) {
        weeklyPatternOptions.style.display = patternType === 'weekly' ? 'block' : 'none';
    }
    
    if (timePatternOptions) {
        timePatternOptions.style.display = patternType === 'time_of_day' ? 'block' : 'none';
    }
}

// Run seasonality analysis
export async function runSeasonalityAnalysis(params = {}) {
    if (!appState.dataProcessed) {
        showError('Please upload and process data first');
        return null;
    }
    
    try {
        showGlobalLoader('Running seasonality analysis...');
        
        // Run analysis
        const response = await runSeasonalityAnalysisApi(params);
        
        if (response.success) {
            showSuccessMessage('Seasonality analysis completed successfully');
            
            // Display results
            displaySeasonalityResults(response.results, params.pattern_type);
            
            return response.results;
        } else {
            throw new Error(response.error || 'Error running seasonality analysis');
        }
    } catch (error) {
        showError(error.message || 'Failed to run seasonality analysis');
        return null;
    } finally {
        hideGlobalLoader();
    }
}

// Display seasonality results
export function displaySeasonalityResults(results, patternType) {
    if (!seasonalityResultsContainer || !results) {
        console.error('Cannot display seasonality results: container or results missing');
        return;
    }
    
    // Clear previous results
    seasonalityResultsContainer.innerHTML = '';
    
    // Create title
    const titleElement = document.createElement('h4');
    titleElement.className = 'mb-4';
    titleElement.textContent = getSeasonalityTitle(patternType);
    seasonalityResultsContainer.appendChild(titleElement);
    
    // Create summary card
    const summaryCard = document.createElement('div');
    summaryCard.className = 'card mb-4';
    summaryCard.innerHTML = `
        <div class="card-header bg-primary text-white">
            <h5 class="mb-0">Summary</h5>
        </div>
        <div class="card-body">
            <p><strong>Analysis Type:</strong> ${patternType ? patternType.replace('_', ' ').charAt(0).toUpperCase() + patternType.replace('_', ' ').slice(1) : 'Unknown'}</p>
            <p><strong>Total Periods Analyzed:</strong> ${results.total_periods || 'N/A'}</p>
            <p><strong>Average Return:</strong> ${formatNumber(results.average_return * 100, 2)}%</p>
            ${results.seasonality_strength ? `<p><strong>Seasonality Strength:</strong> ${formatNumber(results.seasonality_strength * 100, 2)}%</p>` : ''}
        </div>
    `;
    seasonalityResultsContainer.appendChild(summaryCard);
    
    // Add detailed results table
    if (results.patterns && Object.keys(results.patterns).length > 0) {
        const tableContainer = document.createElement('div');
        tableContainer.className = 'table-responsive';
        tableContainer.innerHTML = createSeasonalityTableHTML(results.patterns, patternType);
        seasonalityResultsContainer.appendChild(tableContainer);
    }
    
    // Add charts if available
    if (results.charts) {
        const chartsContainer = document.createElement('div');
        chartsContainer.className = 'seasonality-charts mt-4';
        chartsContainer.innerHTML = results.charts;
        seasonalityResultsContainer.appendChild(chartsContainer);
    }
    
    // Add detailed breakdown accordion if available
    if (results.detailed_patterns && Object.keys(results.detailed_patterns).length > 0) {
        const accordionContainer = document.createElement('div');
        accordionContainer.className = 'mt-4';
        accordionContainer.innerHTML = createSeasonalitySummaryAccordionHTML(results.detailed_patterns, patternType);
        seasonalityResultsContainer.appendChild(accordionContainer);
    }
}

// Get title for seasonality results
export function getSeasonalityTitle(patternType) {
    switch (patternType) {
        case 'monthly':
            return 'Monthly Seasonality Analysis';
        case 'weekly':
            return 'Weekly Seasonality Analysis';
        case 'time_of_day':
            return 'Time of Day Seasonality Analysis';
        case 'custom':
            return 'Custom Seasonality Analysis';
        default:
            return 'Seasonality Analysis Results';
    }
}

// Create seasonality table HTML
export function createSeasonalityTableHTML(patterns, patternType) {
    if (!patterns || Object.keys(patterns).length === 0) {
        return '<div class="alert alert-info">No pattern data available</div>';
    }
    
    // Determine column headers based on pattern type
    let periodHeader = 'Period';
    switch (patternType) {
        case 'monthly':
            periodHeader = 'Month';
            break;
        case 'weekly':
            periodHeader = 'Day of Week';
            break;
        case 'time_of_day':
            periodHeader = 'Hour';
            break;
    }
    
    // Create table
    let tableHtml = `
        <table class="table table-bordered table-striped">
            <thead>
                <tr>
                    <th>${periodHeader}</th>
                    <th>Average Return (%)</th>
                    <th>Win Rate (%)</th>
                    <th>Count</th>
                    <th>Significance</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    // Add table rows
    for (const [period, data] of Object.entries(patterns)) {
        const avgReturn = data.average_return * 100;
        const winRate = data.win_rate * 100;
        
        // Determine CSS class based on return (positive/negative)
        const returnClass = avgReturn >= 0 ? 'text-success' : 'text-danger';
        
        // Format period name
        let periodName = period;
        if (patternType === 'monthly') {
            // Convert month number to name
            const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                               'July', 'August', 'September', 'October', 'November', 'December'];
            periodName = monthNames[parseInt(period) - 1] || period;
        } else if (patternType === 'weekly') {
            // Convert day number to name
            const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            periodName = dayNames[parseInt(period)] || period;
        }
        
        tableHtml += `
            <tr>
                <td>${periodName}</td>
                <td class="${returnClass}">${formatNumber(avgReturn, 2)}</td>
                <td>${formatNumber(winRate, 2)}</td>
                <td>${data.count}</td>
                <td>${data.significance ? formatNumber(data.significance * 100, 2) + '%' : 'N/A'}</td>
            </tr>
        `;
    }
    
    tableHtml += `
            </tbody>
        </table>
    `;
    
    return tableHtml;
}

// Create accordion for detailed seasonality breakdown
export function createSeasonalitySummaryAccordionHTML(detailedPatterns, patternType) {
    if (!detailedPatterns || Object.keys(detailedPatterns).length === 0) {
        return '';
    }
    
    let accordionHtml = `
        <div class="accordion" id="seasonalityDetailAccordion">
            <div class="accordion-item">
                <h2 class="accordion-header" id="detailedBreakdownHeading">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                            data-bs-target="#detailedBreakdownCollapse" aria-expanded="false" 
                            aria-controls="detailedBreakdownCollapse">
                        Detailed Breakdown
                    </button>
                </h2>
                <div id="detailedBreakdownCollapse" class="accordion-collapse collapse" 
                     aria-labelledby="detailedBreakdownHeading" data-bs-parent="#seasonalityDetailAccordion">
                    <div class="accordion-body">
                        <div class="table-responsive">
                            <table class="table table-sm table-bordered">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Period</th>
                                        <th>Return (%)</th>
                                    </tr>
                                </thead>
                                <tbody>
    `;
    
    // Add each detailed record
    for (const record of detailedPatterns) {
        const returnValue = record.return * 100;
        const returnClass = returnValue >= 0 ? 'text-success' : 'text-danger';
        
        accordionHtml += `
                                    <tr>
                                        <td>${formatDate(record.date)}</td>
                                        <td>${record.period}</td>
                                        <td class="${returnClass}">${formatNumber(returnValue, 2)}</td>
                                    </tr>
        `;
    }
    
    accordionHtml += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    return accordionHtml;
}

// Initialize module
export function initializeSeasonalityAnalyzer() {
    initializeSeasonalityControls();
}
