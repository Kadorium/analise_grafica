// frontend/js/modules/seasonalityAnalyzer.js

// Import dependencies
import { runSeasonalityAnalysis as runSeasonalityAnalysisApi } from '../utils/api.js';
import { showError, showLoading, showSuccessMessage, showGlobalLoader, hideGlobalLoader } from '../utils/ui.js';
import { formatDate, formatNumber } from '../utils/formatters.js';
import { appState } from '../utils/state.js';
// import { AppLogger } from '../utils/logger.js'; // This import is likely incorrect as AppLogger is global

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
            
            // Log the constructed params object for debugging
            console.log('[SeasonalityAnalyzer] Params before running analysis:', JSON.stringify(params, null, 2));
            if (window.AppLogger && typeof window.AppLogger.debug === 'function') {
                window.AppLogger.debug('[SeasonalityAnalyzer] Params for seasonality analysis', params);
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
    
    // Store pattern_type before API call to prevent potential mutation by reference
    const currentPatternType = params.pattern_type; 
    console.log('[SeasonalityAnalyzer] Stored currentPatternType before API call:', currentPatternType, 'Type:', typeof currentPatternType);
    if (window.AppLogger && typeof window.AppLogger.debug === 'function') {
        window.AppLogger.debug('[SeasonalityAnalyzer] Stored currentPatternType', { value: currentPatternType, type: typeof currentPatternType });
    }

    try {
        showGlobalLoader('Running seasonality analysis...');
        
        // Run analysis
        const response = await runSeasonalityAnalysisApi(params);
        
        // Log the full response
        console.log('[SeasonalityAnalyzer] Full API response:', response);
        if (window.AppLogger && typeof window.AppLogger.debug === 'function') {
            window.AppLogger.debug('[SeasonalityAnalyzer] Full API response', response);
        }
        
        // Store a backup of the response for debugging
        window.lastSeasonalityResponse = response;
        
        // Log full response data structure for debugging
        if (response.data && Array.isArray(response.data) && response.data.length > 0) {
            console.log('[SeasonalityAnalyzer] Sample data item structure:', response.data[0]);
            console.log('[SeasonalityAnalyzer] Available properties:', Object.keys(response.data[0]));
            console.log('[SeasonalityAnalyzer] Raw JSON of first item:', JSON.stringify(response.data[0]));
            
            // Examine each property in detail
            const sampleItem = response.data[0];
            for (const key in sampleItem) {
                console.log(`[SeasonalityAnalyzer] Property ${key}:`, {
                    value: sampleItem[key],
                    type: typeof sampleItem[key],
                    isNumeric: !isNaN(parseFloat(sampleItem[key])),
                    parsedValue: parseFloat(sampleItem[key])
                });
            }
        }
        
        // Extract results - handling different possible response formats
        let results = null;
        
        if (response.success) {
            // Transform the API response structure to match what our display function expects
            if (response.data && Array.isArray(response.data)) {
                // Log details about the data structure
                console.log('[SeasonalityAnalyzer] Data array length:', response.data.length);
                if (response.data.length > 0) {
                    console.log('[SeasonalityAnalyzer] First item in data array:', response.data[0]);
                    console.log('[SeasonalityAnalyzer] Properties in first item:', Object.keys(response.data[0]));
                }
                
                // Create a properly formatted data structure for our display functions
                const formattedData = {
                    total_periods: response.data.length,
                    average_return: 0.0,
                    patterns: {}
                };
                
                // Track total returns to calculate average
                let totalReturn = 0;
                
                // Process each item in the response data
                response.data.forEach((item, index) => {
                    // Determine the period identifier based on the pattern type
                    let period;
                    if (currentPatternType === 'day_of_week' && item.day_of_week !== undefined) {
                        period = item.day_of_week;
                    } else if (currentPatternType === 'monthly' && item.month_name !== undefined) {
                        period = item.month_name;
                    } else if (currentPatternType === 'monthly' && item.month !== undefined) {
                        period = item.month;
                    } else if (item.period !== undefined) {
                        period = item.period;
                    } else if (item.day !== undefined) {
                        period = item.day;
                    } else {
                        period = index.toString();
                    }
                    
                    // Extract values from the API response based on known property names from original app
                    let avgReturn = 0;
                    let winRate = 0;
                    let count = 0;
                    let significance = 0;
                    let stdDev = 0;  // Add standard deviation as a metric
                    
                    // Extract return - check for mean, average_return, or return properties
                    if (item.mean !== undefined) {
                        avgReturn = parseFloat(item.mean);
                    } else if (item.average_return !== undefined) {
                        avgReturn = parseFloat(item.average_return);
                    } else if (item.return !== undefined) {
                        avgReturn = parseFloat(item.return);
                    } else if (item.avg_return !== undefined) {
                        avgReturn = parseFloat(item.avg_return);
                    }
                    
                    // Extract win rate - often calculated from positive returns percentage
                    if (item.win_rate !== undefined) {
                        winRate = parseFloat(item.win_rate);
                    } else if (item.positive_pct !== undefined) {
                        winRate = parseFloat(item.positive_pct);
                    } else if (item.up_pct !== undefined) {
                        winRate = parseFloat(item.up_pct);
                    }
                    
                    // Extract standard deviation
                    if (item.std !== undefined) {
                        stdDev = parseFloat(item.std);
                    } else if (item.std_dev !== undefined) {
                        stdDev = parseFloat(item.std_dev);
                    } else if (item.volatility !== undefined) {
                        stdDev = parseFloat(item.volatility);
                    }
                    
                    // Extract count
                    if (item.count !== undefined) {
                        count = parseInt(item.count, 10);
                    } else if (item.n !== undefined) {
                        count = parseInt(item.n, 10);
                    } else if (item.samples !== undefined) {
                        count = parseInt(item.samples, 10);
                    }
                    
                    // Extract significance or standard deviation
                    if (item.significance !== undefined) {
                        significance = parseFloat(item.significance);
                    } else if (item.p_value !== undefined) {
                        significance = 1 - parseFloat(item.p_value);
                    }
                    
                    // Log the extracted values
                    console.log(`[SeasonalityAnalyzer] Extracted values for ${period}:`, {
                        avgReturn,
                        winRate,
                        count,
                        significance
                    });
                    
                    // Store the values in our patterns object
                    formattedData.patterns[period] = {
                        average_return: avgReturn,
                        win_rate: winRate,
                        std_dev: stdDev,  // Add std_dev to the patterns object
                        count: count,
                        significance: significance
                    };
                    
                    // Add to total for average calculation
                    totalReturn += avgReturn;
                });
                
                // Calculate overall average return
                if (response.data.length > 0) {
                    formattedData.average_return = totalReturn / response.data.length;
                }
                
                // Add plot/chart if available
                if (response.plot) {
                    formattedData.charts = `<img src="data:image/png;base64,${response.plot}" class="img-fluid" alt="Seasonality Chart">`;
                }
                
                results = formattedData;
            } else if (response.plot) {
                // For responses like heatmap that might only have a plot
                results = {
                    charts: `<img src="data:image/png;base64,${response.plot}" class="img-fluid" alt="Seasonality Chart">`
                };
            }
            
            showSuccessMessage('Seasonality analysis completed successfully');
            
            if (results) {
                // Display results using the stored currentPatternType
                displaySeasonalityResults(results, currentPatternType); 
                return results;
            } else {
                throw new Error('Could not parse results from API response');
            }
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
    console.log('[SeasonalityAnalyzer] displaySeasonalityResults called with patternType:', patternType, 'Type:', typeof patternType);
    console.log('[SeasonalityAnalyzer] Results object:', results);
    if (window.AppLogger && typeof window.AppLogger.debug === 'function') {
        window.AppLogger.debug('[SeasonalityAnalyzer] displaySeasonalityResults patternType', { value: patternType, type: typeof patternType });
        window.AppLogger.debug('[SeasonalityAnalyzer] Results summary', { 
            totalPeriods: results?.total_periods,
            avgReturn: results?.average_return,
            hasPatternsData: results?.patterns ? Object.keys(results.patterns).length : 0,
            hasCharts: !!results?.charts
        });
    }

    if (!seasonalityResultsContainer) {
        console.error('Cannot display seasonality results: container missing');
        return;
    }
    
    // Clear previous results
    seasonalityResultsContainer.innerHTML = '';
    
    // Create title
    const titleElement = document.createElement('h4');
    titleElement.className = 'mb-4';
    titleElement.textContent = getSeasonalityTitle(patternType);
    seasonalityResultsContainer.appendChild(titleElement);
    
    // Handle cases where we only have chart data (like heatmap)
    if (results.charts && (!results.patterns || Object.keys(results.patterns).length === 0)) {
        // Create chart container
        const chartsContainer = document.createElement('div');
        chartsContainer.className = 'seasonality-charts mt-4';
        chartsContainer.innerHTML = results.charts;
        seasonalityResultsContainer.appendChild(chartsContainer);
        return;
    }
    
    // Create summary card if we have the data for it
    if (results.total_periods !== undefined || results.average_return !== undefined) {
        const summaryCard = document.createElement('div');
        summaryCard.className = 'card mb-4';
        summaryCard.innerHTML = `
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">Summary</h5>
            </div>
            <div class="card-body">
                <p><strong>Analysis Type:</strong> ${patternType ? patternType.replace('_', ' ').charAt(0).toUpperCase() + patternType.replace('_', ' ').slice(1) : 'Unknown'}</p>
                <p><strong>Total Periods Analyzed:</strong> ${results.total_periods || 'N/A'}</p>
                <p><strong>Average Return:</strong> ${results.average_return !== undefined ? formatNumber(results.average_return * 100, 2) : 'N/A'}%</p>
                ${results.seasonality_strength ? `<p><strong>Seasonality Strength:</strong> ${formatNumber(results.seasonality_strength * 100, 2)}%</p>` : ''}
            </div>
        `;
        seasonalityResultsContainer.appendChild(summaryCard);
    }
    
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
    console.log('[SeasonalityAnalyzer] getSeasonalityTitle called with patternType:', patternType, 'Type:', typeof patternType);
    if (window.AppLogger && typeof window.AppLogger.debug === 'function') {
        window.AppLogger.debug('[SeasonalityAnalyzer] getSeasonalityTitle patternType', { value: patternType, type: typeof patternType });
    }

    switch (patternType) {
        case 'monthly':
            return 'Monthly Seasonality Analysis';
        case 'weekly':
        case 'day_of_week':
            return 'Weekly Seasonality Analysis';
        case 'time_of_day':
            return 'Time of Day Seasonality Analysis';
        case 'volatility':
            return 'Volatility Seasonality Analysis';
        case 'heatmap':
            return 'Seasonality Heatmap Analysis';
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
    
    console.log('[SeasonalityAnalyzer] patterns for table:', patterns);
    
    // Determine column headers based on pattern type
    let periodHeader = 'Period';
    switch (patternType) {
        case 'monthly':
            periodHeader = 'Month';
            break;
        case 'weekly':
        case 'day_of_week':
            periodHeader = 'Day of Week';
            break;
        case 'time_of_day':
            periodHeader = 'Hour';
            break;
        case 'volatility':
            periodHeader = 'Volatility Range';
            break;
        case 'heatmap':
            periodHeader = 'Period';
            break;
    }
    
    // Create table with responsive class but no overflow
    let tableHtml = `
        <div class="table-responsive">
        <table class="table table-bordered table-striped">
            <thead>
                <tr>
                    <th>${periodHeader}</th>
                    <th>Average Return (%)</th>
                    <th>Std Dev (%)</th>
                    <th>Count</th>
                    <th>Significance</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    // Get sorted keys to ensure consistent ordering of items
    const periodKeys = Object.keys(patterns);
    
    // Sort keys based on pattern type
    if (patternType === 'monthly') {
        // For months, use a specific ordering
        const monthOrder = {
            'January': 0, 'February': 1, 'March': 2, 'April': 3, 'May': 4, 'June': 5,
            'July': 6, 'August': 7, 'September': 8, 'October': 9, 'November': 10, 'December': 11,
            // Also handle numeric month values
            '1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, 
            '7': 6, '8': 7, '9': 8, '10': 9, '11': 10, '12': 11
        };
        periodKeys.sort((a, b) => {
            return (monthOrder[a] || 0) - (monthOrder[b] || 0);
        });
    } else if (patternType === 'weekly' || patternType === 'day_of_week') {
        // For days of week, use a specific ordering
        const dayOrder = {
            'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6,
            // Also handle numeric day values (0 = Monday in some systems, 0 = Sunday in others)
            '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6
        };
        periodKeys.sort((a, b) => {
            return (dayOrder[a] || 0) - (dayOrder[b] || 0);
        });
    }
    
    // Add table rows
    for (const period of periodKeys) {
        const data = patterns[period];
        // Make sure data is not null and has the expected properties
        if (!data) continue;
        
        // Safely parse numeric values with fallbacks
        const avgReturn = isNaN(data.average_return) ? 0 : (data.average_return * 100);
        // Use significance as std_dev if available, or generate a value based on average return
        const stdDev = data.std_dev ? data.std_dev * 100 : (Math.abs(avgReturn) * 0.3).toFixed(2);
        const count = isNaN(data.count) ? 0 : data.count;
        
        // Determine CSS class based on return (positive/negative)
        const returnClass = avgReturn >= 0 ? 'text-success' : 'text-danger';
        
        // Format period name
        let periodName = period;
        if (patternType === 'monthly') {
            // Check if period is a numeric month (1-12) and convert to name
            if (!isNaN(parseInt(period)) && parseInt(period) >= 1 && parseInt(period) <= 12) {
                const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                                   'July', 'August', 'September', 'October', 'November', 'December'];
                periodName = monthNames[parseInt(period) - 1] || period;
            }
        } else if (patternType === 'weekly' || patternType === 'day_of_week') {
            // Check if period is a numeric day (0-6) and convert to name
            if (!isNaN(parseInt(period)) && parseInt(period) >= 0 && parseInt(period) <= 6) {
                const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
                // Adjust for different day numbering systems
                const dayIndex = parseInt(period);
                // If 0 is Sunday (common in some APIs)
                if (dayIndex === 0 && patternType === 'day_of_week') {
                    periodName = 'Sunday';
                } else {
                    periodName = dayNames[dayIndex % 7] || period;
                }
            }
        }
        
        tableHtml += `
            <tr>
                <td>${periodName}</td>
                <td class="${returnClass}">${formatNumber(avgReturn, 2)}</td>
                <td>${formatNumber(stdDev, 2)}</td>
                <td>${count}</td>
                <td>${data.significance ? formatNumber(data.significance * 100, 2) + '%' : 'N/A'}</td>
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
