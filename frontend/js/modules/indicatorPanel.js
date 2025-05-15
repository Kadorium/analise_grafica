// frontend/js/modules/indicatorPanel.js

// Import dependencies
import { addIndicators, plotIndicators } from '../utils/api.js';
import { showError, showLoading, showSuccessMessage, showGlobalLoader, hideGlobalLoader } from '../utils/ui.js';
import { appState } from '../utils/state.js';

// DOM references
const indicatorForm = document.getElementById('indicators-form');
const addIndicatorsBtn = document.getElementById('add-indicators-btn');
const chartContainer = document.getElementById('chart-container');
const chartForm = document.getElementById('chart-form');
const plotChartBtn = document.getElementById('plot-chart-btn');
const mainIndicatorsSelect = document.getElementById('main-indicators');
const subplotIndicatorsSelect = document.getElementById('subplot-indicators');
const moveToMainBtn = document.getElementById('move-to-main');
const moveToSubplotBtn = document.getElementById('move-to-subplot');
const removeMainBtn = document.getElementById('remove-main');
const removeSubplotBtn = document.getElementById('remove-subplot');
const selectAllIndicatorsCheckbox = document.getElementById('select-all-indicators');
const groupSelectCheckboxes = document.querySelectorAll('.group-select');

// Add functions to handle the group checkboxes
function handleSelectAllIndicators(e) {
    const isChecked = e.target.checked;
    
    // Find all indicator checkboxes
    const allCheckboxes = indicatorForm.querySelectorAll('input[type="checkbox"]');
    
    // Skip the group header checkboxes and select all checkbox
    allCheckboxes.forEach(checkbox => {
        if (!checkbox.classList.contains('group-select') && checkbox.id !== 'select-all-indicators') {
            checkbox.checked = isChecked;
        }
    });
    
    // Also update the group checkboxes
    groupSelectCheckboxes.forEach(groupCheckbox => {
        groupCheckbox.checked = isChecked;
    });
}

function handleGroupSelect(e) {
    const groupCheckbox = e.target;
    const isChecked = groupCheckbox.checked;
    const group = groupCheckbox.getAttribute('data-group');
    
    // Find checkboxes in this group
    const groupCheckboxes = indicatorForm.querySelectorAll(`.${group}-checkbox`);
    
    // Select or deselect all checkboxes in the group
    groupCheckboxes.forEach(checkbox => {
        checkbox.checked = isChecked;
    });
    
    // Update the "Select All" checkbox state
    updateSelectAllCheckboxState();
}

function updateSelectAllCheckboxState() {
    // Get all individual indicator checkboxes
    const allIndicatorCheckboxes = indicatorForm.querySelectorAll('input[type="checkbox"]:not(.group-select):not(#select-all-indicators)');
    const allChecked = Array.from(allIndicatorCheckboxes).every(checkbox => checkbox.checked);
    const anyChecked = Array.from(allIndicatorCheckboxes).some(checkbox => checkbox.checked);
    
    // Update the select all checkbox
    if (selectAllIndicatorsCheckbox) {
        selectAllIndicatorsCheckbox.checked = allChecked;
        selectAllIndicatorsCheckbox.indeterminate = anyChecked && !allChecked;
    }
}

function updateGroupCheckboxState(group) {
    // Get the group checkbox
    const groupCheckbox = document.getElementById(`select-${group}`);
    if (!groupCheckbox) return;
    
    // Get all checkboxes in this group
    const groupCheckboxes = indicatorForm.querySelectorAll(`.${group}-checkbox`);
    if (groupCheckboxes.length === 0) return;
    
    const allChecked = Array.from(groupCheckboxes).every(checkbox => checkbox.checked);
    const anyChecked = Array.from(groupCheckboxes).some(checkbox => checkbox.checked);
    
    // Update the group checkbox state
    groupCheckbox.checked = allChecked;
    groupCheckbox.indeterminate = anyChecked && !allChecked;
}

function handleIndicatorCheckboxChange(e) {
    const checkbox = e.target;
    
    // Find which group this checkbox belongs to
    const groupClasses = Array.from(checkbox.classList)
        .filter(cls => cls.endsWith('-checkbox'))
        .map(cls => cls.replace('-checkbox', ''));
    
    // Update each group's checkbox state
    groupClasses.forEach(updateGroupCheckboxState);
    
    // Update the "Select All" checkbox state
    updateSelectAllCheckboxState();
}

// Update indicator dropdowns for chart plotting
function updateIndicatorDropdowns() {
    if (!mainIndicatorsSelect || !subplotIndicatorsSelect) return;
    
    // Save current selections before clearing
    const currentMainSelections = Array.from(mainIndicatorsSelect.options).map(opt => opt.value);
    const currentSubplotSelections = Array.from(subplotIndicatorsSelect.options).map(opt => opt.value);
    
    console.log("Current main indicators:", currentMainSelections);
    console.log("Current subplot indicators:", currentSubplotSelections);
    
    // Clear existing options
    mainIndicatorsSelect.innerHTML = '';
    subplotIndicatorsSelect.innerHTML = '';
    
    console.log("Updating indicator dropdowns with available indicators:", appState.availableIndicators);
    
    // Categorize indicators based on type
    const mainIndicatorPrefixes = [
        'sma_', 'ema_', 'bb_', 'typical_price', 
        'supertrend', 'donchian_', 'dc_', 'keltner_', 'kc_',
        'bullish_engulfing', 'bearish_engulfing', 'doji', 'hammer', 'inverted_hammer',
        'morning_star', 'evening_star'
    ];
    
    const subplotIndicatorPrefixes = [
        'rsi', 'macd', 'stoch', 'obv', 'vpt', 'volume_', 'atr',
        'adx', 'plus_di', 'minus_di', 'cci', 'williams_r', 'cmf', 'ad_line'
    ];
    
    // Exclude columns that are not indicators
    const excludedItems = ['ticker', 'index'];
    const filteredIndicators = appState.availableIndicators.filter(indicator => 
        !excludedItems.includes(indicator) && 
        indicator !== 'date' && 
        indicator !== 'open' && 
        indicator !== 'high' && 
        indicator !== 'low' && 
        indicator !== 'close' && 
        indicator !== 'volume'
    );
    
    console.log("Filtered indicators (excluding non-indicators):", filteredIndicators);
    
    // Find new indicators that weren't in any select before
    const allPreviousSelections = [...currentMainSelections, ...currentSubplotSelections];
    const newIndicators = filteredIndicators.filter(ind => !allPreviousSelections.includes(ind));
    
    console.log("New indicators to categorize:", newIndicators);
    
    // Initialize separate arrays for main and subplot indicators
    let categorizedMain = [...currentMainSelections];
    let categorizedSubplot = [...currentSubplotSelections];
    
    // Always ensure typical_price is available for price display
    const hasTypicalPrice = categorizedMain.includes('typical_price') || 
                           filteredIndicators.some(ind => ind === 'typical_price');
    if (!hasTypicalPrice && filteredIndicators.includes('typical_price')) {
        categorizedMain.push('typical_price');
    }
    
    // Categorize only new indicators
    newIndicators.forEach(indicator => {
        // Decide which dropdown this indicator belongs to
        let isMainIndicator = mainIndicatorPrefixes.some(prefix => indicator.startsWith(prefix) || indicator === prefix);
        let isSubplotIndicator = subplotIndicatorPrefixes.some(prefix => indicator.startsWith(prefix) || indicator === prefix);
        
        if (isMainIndicator) {
            categorizedMain.push(indicator);
        } else if (isSubplotIndicator) {
            categorizedSubplot.push(indicator);
        } else {
            // Default to subplot for unknown indicators
            categorizedSubplot.push(indicator);
        }
    });
    
    // Remove duplicates
    categorizedMain = [...new Set(categorizedMain)];
    categorizedSubplot = [...new Set(categorizedSubplot)];
    
    console.log("Categorized main indicators:", categorizedMain);
    console.log("Categorized subplot indicators:", categorizedSubplot);
    
    // Add categorized indicators to their respective dropdowns
    categorizedMain.forEach(indicator => {
        // Only add if the indicator exists in filtered indicators or was already selected
        if (filteredIndicators.includes(indicator) || currentMainSelections.includes(indicator)) {
            const option = document.createElement('option');
            option.value = indicator;
            option.textContent = indicator.replace(/_/g, ' ');
            mainIndicatorsSelect.appendChild(option);
        }
    });
    
    categorizedSubplot.forEach(indicator => {
        // Only add if the indicator exists in filtered indicators or was already selected
        if (filteredIndicators.includes(indicator) || currentSubplotSelections.includes(indicator)) {
            const option = document.createElement('option');
            option.value = indicator;
            option.textContent = indicator.replace(/_/g, ' ');
            subplotIndicatorsSelect.appendChild(option);
        }
    });
}

// Move selected options from one select to another
export function moveSelectedOptions(sourceId, targetId) {
    const sourceSelect = document.getElementById(sourceId);
    const targetSelect = document.getElementById(targetId);
    
    if (!sourceSelect || !targetSelect) return;
    
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

// Remove selected options from a select element
export function removeSelectedOptions(selectId) {
    const select = document.getElementById(selectId);
    
    if (!select) return;
    
    // Get selected options in reverse order (to avoid index issues when removing)
    const selectedOptions = Array.from(select.selectedOptions).reverse();
    
    // Remove each selected option
    selectedOptions.forEach(option => {
        select.removeChild(option);
    });
}

// Initialize indicator control buttons and event listeners
export function initializeIndicatorControls() {
    // Add event listener to "Select All" checkbox
    if (selectAllIndicatorsCheckbox) {
        selectAllIndicatorsCheckbox.addEventListener('change', handleSelectAllIndicators);
    }
    
    // Add event listeners to group select checkboxes
    groupSelectCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', handleGroupSelect);
    });
    
    // Add event listeners to all indicator checkboxes to update group states
    const allIndicatorCheckboxes = indicatorForm.querySelectorAll('input[type="checkbox"]:not(.group-select):not(#select-all-indicators)');
    allIndicatorCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', handleIndicatorCheckboxChange);
    });
    
    // Initialize checkbox states based on current selections
    updateSelectAllCheckboxState();
    ['moving-averages', 'momentum', 'volatility', 'trend', 'volume', 'oscillator', 'patterns'].forEach(updateGroupCheckboxState);
    
    // The existing candlestick patterns checkbox should toggle all individual pattern checkboxes
    const candlestickPatternsCheckbox = document.getElementById('candlestick-patterns-checkbox');
    const patternCheckboxes = document.querySelectorAll('.pattern-checkbox');
    
    if (candlestickPatternsCheckbox) {
        candlestickPatternsCheckbox.addEventListener('change', () => {
            const isChecked = candlestickPatternsCheckbox.checked;
            patternCheckboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            updateGroupCheckboxState('patterns');
        });
    }

    // Indicator form submission
    if (indicatorForm) {
        indicatorForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Disable the add indicators button during processing
            if (addIndicatorsBtn) {
                addIndicatorsBtn.disabled = true;
                addIndicatorsBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding...';
            }
            
            showGlobalLoader('Adding indicators...');
            
            try {
                // Initialize empty indicator config object
                const indicatorConfig = {};
                
                // SMA
                const smaCheckbox = document.getElementById('sma-checkbox');
                if (smaCheckbox && smaCheckbox.checked) {
                    const periodsInput = document.getElementById('sma-periods');
                    const periods = periodsInput && periodsInput.value 
                        ? periodsInput.value.split(',').map(p => parseInt(p.trim())) 
                        : [20, 50, 200];
                    
                    indicatorConfig.sma = {
                        periods: periods
                    };
                }
                
                // EMA
                const emaCheckbox = document.getElementById('ema-checkbox');
                if (emaCheckbox && emaCheckbox.checked) {
                    const periodsInput = document.getElementById('ema-periods');
                    const periods = periodsInput && periodsInput.value 
                        ? periodsInput.value.split(',').map(p => parseInt(p.trim())) 
                        : [12, 26, 50];
                    
                    indicatorConfig.ema = {
                        periods: periods
                    };
                }
                
                // RSI
                const rsiCheckbox = document.getElementById('rsi-checkbox');
                if (rsiCheckbox && rsiCheckbox.checked) {
                    const periodInput = document.getElementById('rsi-period');
                    indicatorConfig.rsi = {
                        period: periodInput && periodInput.value ? parseInt(periodInput.value) : 14
                    };
                }
                
                // MACD
                const macdCheckbox = document.getElementById('macd-checkbox');
                if (macdCheckbox && macdCheckbox.checked) {
                    const fastInput = document.getElementById('macd-fast');
                    const slowInput = document.getElementById('macd-slow');
                    const signalInput = document.getElementById('macd-signal');
                    
                    indicatorConfig.macd = {
                        fast_period: fastInput && fastInput.value ? parseInt(fastInput.value) : 12,
                        slow_period: slowInput && slowInput.value ? parseInt(slowInput.value) : 26,
                        signal_period: signalInput && signalInput.value ? parseInt(signalInput.value) : 9
                    };
                }
                
                // Bollinger Bands
                const bbandsCheckbox = document.getElementById('bbands-checkbox');
                if (bbandsCheckbox && bbandsCheckbox.checked) {
                    const periodInput = document.getElementById('bbands-period');
                    const stdInput = document.getElementById('bbands-std');
                    
                    indicatorConfig.bollinger_bands = {
                        period: periodInput && periodInput.value ? parseInt(periodInput.value) : 20,
                        std_dev: stdInput && stdInput.value ? parseFloat(stdInput.value) : 2
                    };
                }
                
                // Stochastic
                const stochCheckbox = document.getElementById('stoch-checkbox');
                if (stochCheckbox && stochCheckbox.checked) {
                    const kInput = document.getElementById('stoch-k');
                    const dInput = document.getElementById('stoch-d');
                    const slowingInput = document.getElementById('stoch-slowing');
                    
                    indicatorConfig.stochastic = {
                        k_period: kInput && kInput.value ? parseInt(kInput.value) : 14,
                        d_period: dInput && dInput.value ? parseInt(dInput.value) : 3,
                        slowing: slowingInput && slowingInput.value ? parseInt(slowingInput.value) : 3
                    };
                }
                
                // Volume - use direct boolean instead of object with enabled property
                const volumeCheckbox = document.getElementById('volume-checkbox');
                if (volumeCheckbox && volumeCheckbox.checked) {
                    indicatorConfig.volume = true;
                }
                
                // ATR
                const atrCheckbox = document.getElementById('atr-checkbox');
                if (atrCheckbox && atrCheckbox.checked) {
                    const periodInput = document.getElementById('atr-period');
                    indicatorConfig.atr = {
                        period: periodInput && periodInput.value ? parseInt(periodInput.value) : 14
                    };
                }
                
                // ADX
                const adxCheckbox = document.getElementById('adx-checkbox');
                if (adxCheckbox && adxCheckbox.checked) {
                    const periodInput = document.getElementById('adx-period');
                    indicatorConfig.adx = {
                        period: periodInput && periodInput.value ? parseInt(periodInput.value) : 14
                    };
                }
                
                // SuperTrend
                const supertrendCheckbox = document.getElementById('supertrend-checkbox');
                if (supertrendCheckbox && supertrendCheckbox.checked) {
                    const periodInput = document.getElementById('supertrend-atr-period');
                    const multiplierInput = document.getElementById('supertrend-multiplier');
                    
                    indicatorConfig.supertrend = {
                        period: periodInput && periodInput.value ? parseInt(periodInput.value) : 10,
                        multiplier: multiplierInput && multiplierInput.value ? parseFloat(multiplierInput.value) : 3
                    };
                }
                
                // CCI
                const cciCheckbox = document.getElementById('cci-checkbox');
                if (cciCheckbox && cciCheckbox.checked) {
                    const periodInput = document.getElementById('cci-period');
                    indicatorConfig.cci = {
                        period: periodInput && periodInput.value ? parseInt(periodInput.value) : 20
                    };
                }
                
                // Williams %R
                const williamsRCheckbox = document.getElementById('williams-r-checkbox');
                if (williamsRCheckbox && williamsRCheckbox.checked) {
                    const periodInput = document.getElementById('williams-r-period');
                    indicatorConfig.williams_r = {
                        period: periodInput && periodInput.value ? parseInt(periodInput.value) : 14
                    };
                }
                
                // Chaikin Money Flow
                const cmfCheckbox = document.getElementById('cmf-checkbox');
                if (cmfCheckbox && cmfCheckbox.checked) {
                    const periodInput = document.getElementById('cmf-period');
                    indicatorConfig.cmf = {
                        period: periodInput && periodInput.value ? parseInt(periodInput.value) : 20
                    };
                }
                
                // Accumulation Distribution Line
                const adLineCheckbox = document.getElementById('ad-line-checkbox');
                if (adLineCheckbox && adLineCheckbox.checked) {
                    indicatorConfig.ad_line = true;
                }
                
                // Candlestick Patterns
                const candlestickPatternsCheckbox = document.getElementById('candlestick-patterns-checkbox');
                if (candlestickPatternsCheckbox && candlestickPatternsCheckbox.checked) {
                    indicatorConfig.candlestick_patterns = true;
                }
                
                // Donchian Channels
                const donchianCheckbox = document.getElementById('donchian-checkbox');
                if (donchianCheckbox && donchianCheckbox.checked) {
                    const periodInput = document.getElementById('donchian-period');
                    indicatorConfig.donchian_channels = {
                        period: periodInput && periodInput.value ? parseInt(periodInput.value) : 20
                    };
                }
                
                // Keltner Channels
                const keltnerCheckbox = document.getElementById('keltner-checkbox');
                if (keltnerCheckbox && keltnerCheckbox.checked) {
                    const emaInput = document.getElementById('keltner-ema-period');
                    const atrInput = document.getElementById('keltner-atr-period');
                    const multiplierInput = document.getElementById('keltner-multiplier');
                    
                    indicatorConfig.keltner_channels = {
                        ema_period: emaInput && emaInput.value ? parseInt(emaInput.value) : 20,
                        atr_period: atrInput && atrInput.value ? parseInt(atrInput.value) : 10,
                        multiplier: multiplierInput && multiplierInput.value ? parseFloat(multiplierInput.value) : 1.5
                    };
                }
                
                // Check if any indicator is selected
                if (Object.keys(indicatorConfig).length === 0) {
                    showError('Please select at least one indicator to add.');
                    return;
                }
                
                console.log("Sending indicator config:", JSON.stringify(indicatorConfig));
                
                // Add indicators
                const response = await addIndicators(indicatorConfig);
                
                if (response.success) {
                    showSuccessMessage('Indicators added successfully');
                    
                    // Update the app state with the available indicators from response
                    if (response.available_indicators) {
                        appState.availableIndicators = response.available_indicators;
                        console.log("Updated available indicators:", appState.availableIndicators);
                    }
                    
                    // Clear the existing dropdowns
                    if (mainIndicatorsSelect) mainIndicatorsSelect.innerHTML = '';
                    if (subplotIndicatorsSelect) subplotIndicatorsSelect.innerHTML = '';
                    
                    // Update the indicator dropdowns - only add indicators that were checked
                    // First, categorize the indicators based on their types
                    const mainIndicatorPrefixes = [
                        'sma_', 'ema_', 'bb_', 'typical_price', 
                        'supertrend', 'donchian_', 'dc_', 'keltner_', 'kc_',
                        'bullish_engulfing', 'bearish_engulfing', 'doji', 'hammer', 'inverted_hammer',
                        'morning_star', 'evening_star'
                    ];
                    
                    const subplotIndicatorPrefixes = [
                        'rsi', 'macd', 'stoch', 'obv', 'vpt', 'volume_', 'atr',
                        'adx', 'plus_di', 'minus_di', 'cci', 'williams_r', 'cmf', 'ad_line'
                    ];
                    
                    // Check which indicator types were selected in the form
                    const selectedIndicatorTypes = [];
                    if (smaCheckbox && smaCheckbox.checked) selectedIndicatorTypes.push('sma_');
                    if (emaCheckbox && emaCheckbox.checked) selectedIndicatorTypes.push('ema_');
                    if (rsiCheckbox && rsiCheckbox.checked) selectedIndicatorTypes.push('rsi');
                    if (macdCheckbox && macdCheckbox.checked) selectedIndicatorTypes.push('macd');
                    if (bbandsCheckbox && bbandsCheckbox.checked) selectedIndicatorTypes.push('bb_');
                    if (stochCheckbox && stochCheckbox.checked) selectedIndicatorTypes.push('stoch');
                    if (volumeCheckbox && volumeCheckbox.checked) selectedIndicatorTypes.push('volume_', 'obv', 'vpt');
                    if (atrCheckbox && atrCheckbox.checked) selectedIndicatorTypes.push('atr');
                    if (adxCheckbox && adxCheckbox.checked) selectedIndicatorTypes.push('adx', 'plus_di', 'minus_di');
                    if (supertrendCheckbox && supertrendCheckbox.checked) selectedIndicatorTypes.push('supertrend');
                    if (cciCheckbox && cciCheckbox.checked) selectedIndicatorTypes.push('cci');
                    if (williamsRCheckbox && williamsRCheckbox.checked) selectedIndicatorTypes.push('williams_r');
                    if (cmfCheckbox && cmfCheckbox.checked) selectedIndicatorTypes.push('cmf');
                    if (adLineCheckbox && adLineCheckbox.checked) selectedIndicatorTypes.push('ad_line');
                    if (donchianCheckbox && donchianCheckbox.checked) selectedIndicatorTypes.push('donchian_', 'dc_');
                    if (keltnerCheckbox && keltnerCheckbox.checked) selectedIndicatorTypes.push('keltner_', 'kc_');
                    if (candlestickPatternsCheckbox && candlestickPatternsCheckbox.checked) {
                        selectedIndicatorTypes.push('bullish_engulfing', 'bearish_engulfing', 'doji', 
                                                   'hammer', 'inverted_hammer', 'morning_star', 'evening_star');
                    }
                    
                    console.log("Selected indicator types:", selectedIndicatorTypes);
                    
                    // Filter available indicators to only include those that match selected types
                    const filteredIndicators = appState.availableIndicators.filter(indicator => {
                        // Always include typical_price for the main chart
                        if (indicator === 'typical_price') return true;
                        
                        // Check if indicator matches any selected type
                        return selectedIndicatorTypes.some(type => 
                            indicator.startsWith(type) || indicator === type
                        );
                    });
                    
                    console.log("Filtered indicators based on checkbox selection:", filteredIndicators);
                    
                    // If certain indicators were checked but aren't in the filtered list, we need to manually add them
                    // This handles cases where the API doesn't return specific indicators in the available_indicators list
                    
                    // For SMA: Add indicators like sma_20, sma_50, sma_200 if SMA was checked
                    if (smaCheckbox && smaCheckbox.checked) {
                        const periodsInput = document.getElementById('sma-periods');
                        const periods = periodsInput && periodsInput.value 
                            ? periodsInput.value.split(',').map(p => parseInt(p.trim())) 
                            : [20, 50, 200];
                            
                        // Add SMA indicators for each period
                        periods.forEach(period => {
                            const smaIndicator = `sma_${period}`;
                            if (!filteredIndicators.includes(smaIndicator)) {
                                filteredIndicators.push(smaIndicator);
                            }
                        });
                    }
                    
                    // For EMA: Add indicators like ema_12, ema_26, ema_50 if EMA was checked
                    if (emaCheckbox && emaCheckbox.checked) {
                        const periodsInput = document.getElementById('ema-periods');
                        const periods = periodsInput && periodsInput.value 
                            ? periodsInput.value.split(',').map(p => parseInt(p.trim())) 
                            : [12, 26, 50];
                            
                        // Add EMA indicators for each period
                        periods.forEach(period => {
                            const emaIndicator = `ema_${period}`;
                            if (!filteredIndicators.includes(emaIndicator)) {
                                filteredIndicators.push(emaIndicator);
                            }
                        });
                    }
                    
                    // For Accumulation/Distribution Line: Add the indicator if it was checked
                    if (adLineCheckbox && adLineCheckbox.checked && !filteredIndicators.includes('ad_line')) {
                        filteredIndicators.push('ad_line');
                    }
                    
                    console.log("Updated filtered indicators with manually added ones:", filteredIndicators);
                    
                    // Categorize filtered indicators into main chart or subplot
                    const mainIndicators = filteredIndicators.filter(indicator => 
                        mainIndicatorPrefixes.some(type => indicator.startsWith(type) || indicator === type)
                    );
                    
                    const subplotIndicators = filteredIndicators.filter(indicator => 
                        subplotIndicatorPrefixes.some(type => indicator.startsWith(type) || indicator === type)
                    );
                    
                    console.log("Categorized main indicators:", mainIndicators);
                    console.log("Categorized subplot indicators:", subplotIndicators);
                    
                    // Add main indicators to the select
                    mainIndicators.forEach(indicator => {
                        const option = document.createElement('option');
                        option.value = indicator;
                        option.textContent = indicator.replace(/_/g, ' ');
                        mainIndicatorsSelect.appendChild(option);
                    });
                    
                    // Add subplot indicators to the select
                    subplotIndicators.forEach(indicator => {
                        const option = document.createElement('option');
                        option.value = indicator;
                        option.textContent = indicator.replace(/_/g, ' ');
                        subplotIndicatorsSelect.appendChild(option);
                    });
                    
                    // Display chart if available
                    if (response.chart_html && chartContainer) {
                        chartContainer.innerHTML = response.chart_html;
                    }
                } else {
                    showError(response.message || 'Error adding indicators');
                }
            } catch (error) {
                console.error('Error adding indicators:', error);
                showError(error.message || 'Error adding indicators');
            } finally {
                hideGlobalLoader();
                
                // Re-enable the add indicators button
                if (addIndicatorsBtn) {
                    addIndicatorsBtn.disabled = false;
                    addIndicatorsBtn.textContent = 'Add Indicators';
                }
            }
        });
    }
    
    // Chart form submission
    if (chartForm) {
        chartForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            // Get all indicators from the respective lists
            const selectedMainIndicators = Array.from(mainIndicatorsSelect.selectedOptions).map(opt => opt.value);
            const selectedSubplotIndicators = Array.from(subplotIndicatorsSelect.selectedOptions).map(opt => opt.value);
            // If nothing is selected, use all options
            let mainIndicators = selectedMainIndicators.length > 0 ? 
                              selectedMainIndicators : 
                              Array.from(mainIndicatorsSelect.options).map(opt => opt.value);
            let subplotIndicators = selectedSubplotIndicators.length > 0 ? 
                                 selectedSubplotIndicators : 
                                 Array.from(subplotIndicatorsSelect.options).map(opt => opt.value);
            // Combine all selected indicators
            const allIndicators = [...mainIndicators, ...subplotIndicators];
            // Helper: parse indicator name to config
            function buildIndicatorConfig(indicators) {
                const config = {};
                // Moving averages
                const smaPeriods = [];
                const emaPeriods = [];
                indicators.forEach(ind => {
                    if (/^sma_(\d+)$/.test(ind)) {
                        smaPeriods.push(parseInt(ind.match(/^sma_(\d+)$/)[1]));
                    } else if (/^ema_(\d+)$/.test(ind)) {
                        emaPeriods.push(parseInt(ind.match(/^ema_(\d+)$/)[1]));
                    } else if (ind === 'rsi') {
                        config.rsi = { period: 14 };
                    } else if (ind === 'macd' || ind === 'macd_signal' || ind === 'macd_histogram') {
                        config.macd = { fast_period: 12, slow_period: 26, signal_period: 9 };
                    } else if (ind.startsWith('bb_')) {
                        config.bollinger_bands = { window: 20, num_std: 2 };
                    } else if (ind === 'atr' || ind === 'atr_pct') {
                        config.atr = { period: 14 };
                    } else if (ind === 'obv' || ind === 'vpt' || ind.startsWith('volume_')) {
                        config.volume = true;
                    } else if (ind === 'ad_line') {
                        config.ad_line = true;
                    } else if (ind === 'vpt') {
                        config.volume = true;
                    } else if (ind === 'stoch_k' || ind === 'stoch_d') {
                        config.stochastic = { k_period: 14, d_period: 3, slowing: 3 };
                    } else if (ind === 'adx' || ind === 'plus_di' || ind === 'minus_di') {
                        config.adx = { period: 14 };
                    } else if (ind === 'supertrend') {
                        config.supertrend = { atr_period: 10, multiplier: 3 };
                    } else if (ind === 'cci') {
                        config.cci = { period: 20 };
                    } else if (ind === 'williams_r') {
                        config.williams_r = { period: 14 };
                    } else if (ind === 'cmf') {
                        config.cmf = { period: 20 };
                    } else if (ind === 'dc_upper' || ind === 'dc_middle' || ind === 'dc_lower' || ind.startsWith('donchian_')) {
                        config.donchian_channels = { period: 20 };
                    } else if (ind === 'kc_upper' || ind === 'kc_middle' || ind === 'kc_lower' || ind.startsWith('keltner_')) {
                        config.keltner_channels = { ema_period: 20, atr_period: 10, multiplier: 1.5 };
                    } else if ([
                        'bullish_engulfing', 'bearish_engulfing', 'doji', 'hammer', 'inverted_hammer',
                        'morning_star', 'evening_star'
                    ].includes(ind)) {
                        config.candlestick_patterns = true;
                    }
                });
                if (smaPeriods.length > 0 || emaPeriods.length > 0) {
                    config.moving_averages = { types: [], };
                    if (smaPeriods.length > 0) {
                        config.moving_averages.types.push('sma');
                        config.moving_averages.sma_periods = smaPeriods;
                    }
                    if (emaPeriods.length > 0) {
                        config.moving_averages.types.push('ema');
                        config.moving_averages.ema_periods = emaPeriods;
                    }
                }
                return config;
            }
            const indicatorConfig = buildIndicatorConfig(allIndicators);
            // Get date range
            const startDate = document.getElementById('chart-start-date')?.value || '';
            const endDate = document.getElementById('chart-end-date')?.value || '';
            // Disable the plot button
            if (plotChartBtn) {
                plotChartBtn.disabled = true;
                plotChartBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Plotting...';
            }
            try {
                // Add indicators for all selected
                console.log("Adding indicators with configuration:", indicatorConfig);
                const addResponse = await addIndicators(indicatorConfig);
                if (!addResponse.success) {
                    throw new Error(addResponse.message || 'Error adding indicators');
                }
                // Now plot using the available indicators (from server response)
                let availableMainIndicators = [];
                let availableSubplotIndicators = [];
                if (addResponse.available_indicators) {
                    const mainIndicatorPrefixes = [
                        'sma_', 'ema_', 'bb_', 'typical_price', 
                        'supertrend', 'donchian_', 'dc_', 'keltner_', 'kc_',
                        'bullish_engulfing', 'bearish_engulfing', 'doji', 'hammer', 'inverted_hammer',
                        'morning_star', 'evening_star'
                    ];
                    const subplotIndicatorPrefixes = [
                        'rsi', 'macd', 'stoch', 'obv', 'vpt', 'volume_', 'atr',
                        'adx', 'plus_di', 'minus_di', 'cci', 'williams_r', 'cmf', 'ad_line'
                    ];
                    availableMainIndicators = addResponse.available_indicators.filter(indicator => 
                        mainIndicatorPrefixes.some(type => indicator.startsWith(type) || indicator === type)
                    );
                    availableSubplotIndicators = addResponse.available_indicators.filter(indicator => 
                        subplotIndicatorPrefixes.some(type => indicator.startsWith(type) || indicator === type)
                    );
                    if (addResponse.available_indicators.length > 0) {
                        appState.availableIndicators = addResponse.available_indicators;
                    }
                }
                const plotConfig = {
                    main_indicators: availableMainIndicators.length > 0 ? availableMainIndicators : [],
                    subplot_indicators: availableSubplotIndicators.length > 0 ? availableSubplotIndicators : [],
                    title: 'Price Chart with Selected Indicators',
                    start_date: startDate,
                    end_date: endDate
                };
                console.log("Plotting with configuration:", plotConfig);
                const response = await plotIndicators(plotConfig);
                if (!response.success && response.message !== 'Plot created successfully') {
                    throw new Error(response.message || 'Error plotting chart');
                }
                const chartImage = document.getElementById('chart-image');
                if (response.chart_image && chartImage) {
                    chartImage.src = `data:image/png;base64,${response.chart_image}`;
                    chartImage.style.display = 'block';
                } else if (response.chart_html && chartContainer) {
                    chartContainer.innerHTML = response.chart_html;
                } else {
                    showError('No chart data returned from server');
                }
                if (response.indicator_summary) {
                    const indicatorSummary = document.getElementById('indicator-summary');
                    if (indicatorSummary) {
                        indicatorSummary.innerHTML = response.indicator_summary;
                    }
                }
            } catch (error) {
                if (error.message !== 'Plot created successfully') {
                    console.error('Error plotting chart:', error);
                    showError('Error plotting chart: ' + error.message);
                }
                if (chartContainer) chartContainer.innerHTML = '';
            } finally {
                if (plotChartBtn) {
                    plotChartBtn.disabled = false;
                    plotChartBtn.textContent = 'Plot Chart';
                }
            }
        });
    }
    
    // Add event listeners for the indicator control buttons
    if (moveToMainBtn) {
        moveToMainBtn.addEventListener('click', () => {
            moveSelectedOptions('subplot-indicators', 'main-indicators');
        });
    }
    
    if (moveToSubplotBtn) {
        moveToSubplotBtn.addEventListener('click', () => {
            moveSelectedOptions('main-indicators', 'subplot-indicators');
        });
    }
    
    if (removeMainBtn) {
        removeMainBtn.addEventListener('click', () => {
            removeSelectedOptions('main-indicators');
        });
    }
    
    if (removeSubplotBtn) {
        removeSubplotBtn.addEventListener('click', () => {
            removeSelectedOptions('subplot-indicators');
        });
    }
    
    // Initialize the indicator dropdowns
    if (appState.availableIndicators && appState.availableIndicators.length > 0) {
        updateIndicatorDropdowns();
    }
}

// Update checkboxes from available indicators (if using dynamic indicator list)
export function updateCheckboxesFromAvailableIndicators() {
    const container = document.getElementById('indicator-checkboxes');
    
    if (!container || !appState.availableIndicators) return;
    
    // Implementation depends on the application's needs
    // This function could be used to dynamically populate indicator checkboxes
}
