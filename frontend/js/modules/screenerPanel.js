// frontend/js/modules/screenerPanel.js

// Import dependencies
import { fetchAvailableStrategies, generateSignals, fetchCachedSignals, updateWeights } from '../utils/api.js';
import { showError, showSuccessMessage, showLoading, hideLoading } from '../utils/ui.js';
import { appState } from '../utils/state.js';

// DOM references
let screenerSection;
let screenerForm;
let strategiesSelect;
let runScreenerBtn;
let screenerInfoMessage;
let screenerLoading;
let screenerResults;
let screenerSummary;
let screenerChart;
let screenerTable;
let screenerPagination;
let weightConfigPanel;
let goalSeekRadios;
let customWeightsContainer;
let sharpeWeightSlider;
let returnWeightSlider;
let drawdownWeightSlider;
let winRateWeightSlider;
let lookbackPeriodSelect;
let sharpeWeightValue;
let returnWeightValue;
let drawdownWeightValue;
let winRateWeightValue;
let useWeightedSignalsToggle;
let includeMlSignalsToggle;

// Module state
const state = {
    strategies: [],
    signals: [],
    currentPage: 1,
    pageSize: 50,
    chartInstance: null,
    // Weight configuration state
    goalSeekMetric: 'sharpe_ratio',
    customWeights: {
        sharpe_ratio: 0.4,
        total_return: 0.3,
        max_drawdown: 0.2,
        win_rate: 0.1
    },
    lookbackPeriod: '1 Year',
    normalizedWeights: {}, // Will hold normalized weight values
    useWeightedSignals: true, // Default to true
    includeMlSignals: false, // Default to false for ML signals
    lastMlResults: null,
};

// Initialize the screener panel
export function initializeScreenerPanel() {
    console.log('Initializing Screener Panel');
    
    // Get DOM references
    screenerSection = document.getElementById('screener-section');
    screenerForm = document.getElementById('screener-form');
    strategiesSelect = document.getElementById('screener-strategies');
    runScreenerBtn = document.getElementById('run-screener-btn');
    screenerInfoMessage = document.getElementById('screener-info-message');
    screenerLoading = document.getElementById('screener-loading');
    screenerResults = document.getElementById('screener-results');
    screenerSummary = document.getElementById('screener-summary');
    screenerChart = document.getElementById('screener-chart');
    screenerTable = document.getElementById('screener-table');
    screenerPagination = document.getElementById('screener-pagination');
    
    // Weight configuration panel elements
    weightConfigPanel = document.getElementById('weight-config-panel');
    goalSeekRadios = document.getElementsByName('goal-seek-metric');
    customWeightsContainer = document.getElementById('custom-weights-container');
    sharpeWeightSlider = document.getElementById('sharpe-weight');
    returnWeightSlider = document.getElementById('return-weight');
    drawdownWeightSlider = document.getElementById('drawdown-weight');
    winRateWeightSlider = document.getElementById('win-rate-weight');
    lookbackPeriodSelect = document.getElementById('lookback-period');
    sharpeWeightValue = document.getElementById('sharpe-weight-value');
    returnWeightValue = document.getElementById('return-weight-value');
    drawdownWeightValue = document.getElementById('drawdown-weight-value');
    winRateWeightValue = document.getElementById('win-rate-weight-value');
    
    // Add the weighted signals toggle to the weight configuration panel
    if (weightConfigPanel) {
        const toggleContainer = document.createElement('div');
        toggleContainer.className = 'mt-3';
        toggleContainer.innerHTML = `
            <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" id="use-weighted-signals" checked>
                <label class="form-check-label" for="use-weighted-signals" title="When enabled, signal scores are weighted by performance metrics">
                    Use Weighted Signals
                </label>
            </div>
        `;
        
        // Insert the toggle container before the last element (which should be the lookback period)
        const cardBody = weightConfigPanel.querySelector('.card-body');
        cardBody.appendChild(toggleContainer);
    }
    
    // Get the weighted signals toggle
    useWeightedSignalsToggle = document.getElementById('use-weighted-signals');
    
    // Get the ML signals toggle
    includeMlSignalsToggle = document.getElementById('include-ml-signals');
    
    // Initialize state from checkbox
    state.useWeightedSignals = useWeightedSignalsToggle ? useWeightedSignalsToggle.checked : true;
    state.includeMlSignals = includeMlSignalsToggle ? includeMlSignalsToggle.checked : false;
    console.log('Initial weighted signals state:', state.useWeightedSignals);
    console.log('Initial ML signals state:', state.includeMlSignals);
    
    // Initialize ML panel
    initializeMlPanel();
    
    // Set up event listeners
    screenerForm.addEventListener('submit', handleScreenerSubmit);
    
    // Set up weight configuration event listeners
    goalSeekRadios.forEach(radio => {
        radio.addEventListener('change', handleGoalSeekChange);
    });
    
    // Add event listeners for weight sliders
    if (sharpeWeightSlider) sharpeWeightSlider.addEventListener('input', updateCustomWeights);
    if (returnWeightSlider) returnWeightSlider.addEventListener('input', updateCustomWeights);
    if (drawdownWeightSlider) drawdownWeightSlider.addEventListener('input', updateCustomWeights);
    if (winRateWeightSlider) winRateWeightSlider.addEventListener('input', updateCustomWeights);
    
    // Set up lookback period change listener
    if (lookbackPeriodSelect) {
        lookbackPeriodSelect.addEventListener('change', handleLookbackPeriodChange);
    }
    
    // Set up weighted signals toggle
    useWeightedSignalsToggle.addEventListener('change', (event) => {
        state.useWeightedSignals = event.target.checked;
        console.log(`Weighted signals ${state.useWeightedSignals ? 'enabled' : 'disabled'}`);
        
        // Re-render the chart and table if we have signals
        if (state.signals && state.signals.length > 0) {
            renderSignalChart(state.signals);
            renderSignalTable(state.signals);
        }
    });
    
    // Set up ML signals toggle
    includeMlSignalsToggle.addEventListener('change', (event) => {
        state.includeMlSignals = event.target.checked;
        console.log(`ML signals ${state.includeMlSignals ? 'enabled' : 'disabled'}`);
        
        // Note: ML signals require re-running the screener
        if (state.signals && state.signals.length > 0) {
            console.log('ML toggle changed. You may need to re-run the screener to see ML signals.');
        }
    });
    
    // Load available strategies
    loadAvailableStrategies();
    
    // Check if there's multiAsset data
    checkMultiAssetData();
    
    // Set up tab activation handler
    document.getElementById('screener-tab').addEventListener('click', () => {
        checkMultiAssetData();
    });
    
    // Initialize weight configuration UI state
    initializeWeightConfig();
    
    // Set up tooltips
    const useWeightedSignalsToggleElement = document.getElementById('use-weighted-signals');
    if (useWeightedSignalsToggleElement) {
        // Use Bootstrap's tooltip if available, otherwise use browser's native title attribute
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            new bootstrap.Tooltip(useWeightedSignalsToggleElement);
        }
    }
}

// Initialize weight configuration UI state
function initializeWeightConfig() {
    // Set initial values from appState if available
    if (appState.screeningConfig) {
        state.goalSeekMetric = appState.screeningConfig.goalSeekMetric || state.goalSeekMetric;
        state.customWeights = appState.screeningConfig.customWeights || state.customWeights;
        state.lookbackPeriod = appState.screeningConfig.lookbackPeriod || state.lookbackPeriod;
    }
    
    // Set initial UI state based on the state values
    if (goalSeekRadios) {
        const selectedRadio = Array.from(goalSeekRadios)
            .find(radio => radio.value === state.goalSeekMetric);
        if (selectedRadio) {
            selectedRadio.checked = true;
        }
    }
    
    // Set initial slider values
    if (sharpeWeightSlider) sharpeWeightSlider.value = state.customWeights.sharpe_ratio * 100;
    if (returnWeightSlider) returnWeightSlider.value = state.customWeights.total_return * 100;
    if (drawdownWeightSlider) drawdownWeightSlider.value = state.customWeights.max_drawdown * 100;
    if (winRateWeightSlider) winRateWeightSlider.value = state.customWeights.win_rate * 100;
    
    // Update displayed values
    updateCustomWeights();
    
    // Set lookback period
    if (lookbackPeriodSelect) {
        const option = Array.from(lookbackPeriodSelect.options)
            .find(opt => opt.value === state.lookbackPeriod);
        if (option) {
            lookbackPeriodSelect.value = state.lookbackPeriod;
        }
    }
    
    // Show/hide custom weights container based on the selected goal-seek metric
    toggleCustomWeightsVisibility();
}

// Handle goal-seek metric change
function handleGoalSeekChange(event) {
    state.goalSeekMetric = event.target.value;
    toggleCustomWeightsVisibility();
    
    // Save to appState
    if (!appState.screeningConfig) appState.screeningConfig = {};
    appState.screeningConfig.goalSeekMetric = state.goalSeekMetric;
    
    console.log(`Goal-seek metric changed to: ${state.goalSeekMetric}`);
}

// Handle lookback period change
function handleLookbackPeriodChange(event) {
    state.lookbackPeriod = event.target.value;
    
    // Save to appState
    if (!appState.screeningConfig) appState.screeningConfig = {};
    appState.screeningConfig.lookbackPeriod = state.lookbackPeriod;
    
    console.log(`Lookback period changed to: ${state.lookbackPeriod}`);
}

// Toggle visibility of custom weights container
function toggleCustomWeightsVisibility() {
    if (customWeightsContainer) {
        if (state.goalSeekMetric === 'custom') {
            customWeightsContainer.style.display = 'block';
        } else {
            customWeightsContainer.style.display = 'none';
        }
    }
}

// Update custom weights based on slider values
function updateCustomWeights() {
    // Get current slider values
    const sharpeWeight = sharpeWeightSlider ? parseFloat(sharpeWeightSlider.value) / 100 : state.customWeights.sharpe_ratio;
    const returnWeight = returnWeightSlider ? parseFloat(returnWeightSlider.value) / 100 : state.customWeights.total_return;
    const drawdownWeight = drawdownWeightSlider ? parseFloat(drawdownWeightSlider.value) / 100 : state.customWeights.max_drawdown;
    const winRateWeight = winRateWeightSlider ? parseFloat(winRateWeightSlider.value) / 100 : state.customWeights.win_rate;
    
    // Calculate total weight
    const totalWeight = sharpeWeight + returnWeight + drawdownWeight + winRateWeight;
    
    // Normalize weights to sum to 1
    const normalizedSharpe = totalWeight > 0 ? sharpeWeight / totalWeight : 0.25;
    const normalizedReturn = totalWeight > 0 ? returnWeight / totalWeight : 0.25;
    const normalizedDrawdown = totalWeight > 0 ? drawdownWeight / totalWeight : 0.25;
    const normalizedWinRate = totalWeight > 0 ? winRateWeight / totalWeight : 0.25;
    
    // Update state with original (unnormalized) weights
    state.customWeights = {
        sharpe_ratio: sharpeWeight,
        total_return: returnWeight,
        max_drawdown: drawdownWeight,
        win_rate: winRateWeight
    };
    
    // Save normalized weights
    state.normalizedWeights = {
        sharpe_ratio: normalizedSharpe,
        total_return: normalizedReturn,
        max_drawdown: normalizedDrawdown,
        win_rate: normalizedWinRate
    };
    
    // Update displayed values with normalized weights
    if (sharpeWeightValue) sharpeWeightValue.textContent = (normalizedSharpe * 100).toFixed(1) + '%';
    if (returnWeightValue) returnWeightValue.textContent = (normalizedReturn * 100).toFixed(1) + '%';
    if (drawdownWeightValue) drawdownWeightValue.textContent = (normalizedDrawdown * 100).toFixed(1) + '%';
    if (winRateWeightValue) winRateWeightValue.textContent = (normalizedWinRate * 100).toFixed(1) + '%';
    
    // Save to appState
    if (!appState.screeningConfig) appState.screeningConfig = {};
    appState.screeningConfig.customWeights = state.customWeights;
    
    console.log('Custom weights updated:', state.normalizedWeights);
}

// Check if multi-asset data is available
async function checkMultiAssetData() {
    // Check in appState if we have multi-asset data
    console.log('Checking multi-asset data availability:', {
        multiAssetUploaded: appState.multiAssetUploaded,
        multiAssetData: !!appState.multiAssetData
    });
    
    if (!appState.multiAssetUploaded) {
        console.log('No multi-asset data found. Showing warning message.');
        showScreenerMessage('warning', 'Please upload a multi-sheet Excel file in the Data tab before using the Screener.');
        disableScreener();
    } else {
        console.log('Multi-asset data found. Enabling screener.');
        enableScreener();
    }
    
    // For testing, let's temporarily enable the screener even without data
    // Remove this in production
    console.log('DEBUG: Enabling screener for testing');
    enableScreener();
}

// Load available strategies
async function loadAvailableStrategies() {
    try {
        const response = await fetchAvailableStrategies();
        if (response.strategies && response.strategies.length > 0) {
            state.strategies = response.strategies;
            
            // Clear existing options
            strategiesSelect.innerHTML = '';
            
            // Add new options
            response.strategies.forEach(strategy => {
                const option = document.createElement('option');
                option.value = strategy.type || strategy;
                option.textContent = strategy.name || formatStrategyName(strategy.type || strategy);
                strategiesSelect.appendChild(option);
            });
            
            // Select the first strategy by default
            if (strategiesSelect.options.length > 0) {
                strategiesSelect.options[0].selected = true;
            }
        } else {
            console.error('No strategies found');
            showScreenerMessage('warning', 'No trading strategies available. Please check the system configuration.');
        }
    } catch (error) {
        console.error('Error loading strategies:', error);
        showScreenerMessage('danger', `Error loading strategies: ${error.message}`);
    }
}

// Handle form submission
async function handleScreenerSubmit(event) {
    event.preventDefault();
    
    console.log('handleScreenerSubmit triggered', { 
        multiAssetUploaded: appState.multiAssetUploaded,
        appStateKeys: Object.keys(appState)
    });
    
    // TEMPORARY FIX: Bypass the data check to allow testing
    // This should be removed once multi-asset data loading is properly fixed
    /*
    // Check if multi-asset data is available
    if (!appState.multiAssetUploaded) {
        console.error('No multi-asset data uploaded. Please upload data first.');
        showScreenerMessage('warning', 'Please upload multi-asset data first');
        return;
    }
    */
    
    // Get selected strategies
    const selectedOptions = Array.from(strategiesSelect.selectedOptions);
    if (selectedOptions.length === 0) {
        showScreenerMessage('warning', 'Please select at least one strategy');
        return;
    }
    
    // Create strategy list for the API
    const selectedStrategies = selectedOptions.map(option => {
        // Strategy format: [strategy_type, parameter_type]
        // Use optimized parameters when weighted signals are enabled
        const parameterType = state.useWeightedSignals ? 'optimized' : 'default';
        return [option.value, parameterType];
    });
    
    // Show loading indicator
    screenerLoading.style.display = 'block';
    screenerResults.style.display = 'none';
    screenerInfoMessage.style.display = 'none';
    disableScreener();
    
    try {
        // First, if weighted signals are enabled, calculate weights using weighting engine
        let weightsFile = null;
        
        console.log('Current weighted signals state:', state.useWeightedSignals);
        
        if (state.useWeightedSignals) {
            console.log('Weighted signals enabled - calculating weights...');
            // Prepare weights calculation request
            const weightConfig = {
                strategies: selectedStrategies,
                goal_seek_metric: state.goalSeekMetric,
                lookback_period: state.lookbackPeriod,
                refresh_cache: true  // Force fresh weight calculation
            };
            
            // Add custom weights if using custom metric
            if (state.goalSeekMetric === 'custom') {
                weightConfig.custom_weights = state.normalizedWeights;
            }
            
            console.log('Weight calculation config:', weightConfig);
            
            // Call the API to calculate weights
            const weightResponse = await updateWeights(weightConfig);
            
            console.log('Weight response:', weightResponse);
            
            if (weightResponse.success) {
                // Store the weights file for use in signal generation - extract just the filename
                const fullPath = weightResponse.cached_file;
                weightsFile = fullPath.replace(/\\/g, '/').split('/').pop(); // Extract filename only
                console.log(`Weights calculated and stored in: ${fullPath}`);
                console.log(`Sending weights filename to API: ${weightsFile}`);
            } else {
                console.error('Failed to calculate weights:', weightResponse.message);
                // Continue without weights if weight calculation fails
            }
        } else {
            console.log('Weighted signals disabled - skipping weight calculation');
        }
        
        // Call the API to generate signals
        console.log('Calling generateSignals with:', {
            strategies: selectedStrategies,
            refresh_cache: true,  // Always refresh cache
            weights_file: weightsFile,
            include_ml: state.includeMlSignals
        });

        try {
            const response = await generateSignals({
                strategies: selectedStrategies,
                refresh_cache: true,  // Always force refresh
                weights_file: weightsFile,  // Include weights file if available
                include_ml: state.includeMlSignals  // Include ML signals flag
            });
            
            console.log('generateSignals response:', response);
            
            if (response.success) {
                // If signal generation was successful, fetch the signals from cache
                const cacheFileName = response.cached_file.replace(/\\/g, '/').split('/').pop();
                console.log('Fetching cached signals from:', cacheFileName);
                
                const signalsResponse = await fetchCachedSignals(cacheFileName);
                
                console.log('fetchCachedSignals response:', signalsResponse);
                
                if (signalsResponse.success) {
                    // Store signals in state for pagination
                    state.signals = signalsResponse.signals;
                    
                    // Create proper summary data from the actual signals and generation response
                    const summaryData = {
                        signals_count: signalsResponse.signals.length,
                        buy_signals: signalsResponse.signals.filter(s => s.signal && s.signal.toLowerCase() === 'buy').length,
                        sell_signals: signalsResponse.signals.filter(s => s.signal && s.signal.toLowerCase() === 'sell').length,
                        hold_signals: signalsResponse.signals.filter(s => s.signal && s.signal.toLowerCase() === 'hold').length,
                        asset_count: [...new Set(signalsResponse.signals.map(s => s.asset))].length,
                        strategy_count: [...new Set(signalsResponse.signals.map(s => s.strategy))].length,
                        cached_file: response.cached_file,
                        timestamp: response.timestamp || new Date().toISOString(),
                        has_weights: response.has_weights,
                        has_ml_signals: response.has_ml_signals || signalsResponse.signals.some(s => s.strategy === 'LogisticRegression'),
                        // ML-specific metrics if available
                        ml_avg_accuracy: response.ml_avg_accuracy,
                        ml_signals_count: response.ml_signals_count,
                        ml_buy_signals: response.ml_buy_signals,
                        ml_sell_signals: response.ml_sell_signals,
                        ml_hold_signals: response.ml_hold_signals
                    };
                    
                    // Render signals summary and table
                    renderSignalSummary(summaryData);
                    renderSignalChart(state.signals);
                    renderSignalTable(state.signals);
                    
                    // Show results
                    screenerResults.style.display = 'block';
                } else {
                    console.error('Error in fetchCachedSignals:', signalsResponse);
                    showScreenerMessage('danger', `Error fetching signals: ${signalsResponse.message}`);
                }
            } else {
                console.error('Error in generateSignals:', response);
                showScreenerMessage('danger', `Error generating signals: ${response.message}`);
            }
        } catch (error) {
            console.error('Exception in API call to generateSignals:', error);
            
            // If API is not available, use mock data for demonstration
            if (error.message.includes('Failed to fetch')) {
                const mockSignals = generateMockSignals(selectedOptions.map(opt => opt.value));
                state.signals = mockSignals;
                
                // Render mock data
                renderSignalSummary({
                    signals_count: mockSignals.length,
                    buy_signals: mockSignals.filter(s => s.signal === 'BUY').length,
                    sell_signals: mockSignals.filter(s => s.signal === 'SELL').length,
                    hold_signals: mockSignals.filter(s => s.signal === 'HOLD').length,
                    asset_count: [...new Set(mockSignals.map(s => s.asset))].length,
                    strategy_count: selectedOptions.length,
                    cached_file: 'mock_data',
                    timestamp: new Date().toISOString()
                });
                renderSignalChart(mockSignals);
                renderSignalTable(mockSignals);
                
                // Show results with mock data warning
                screenerResults.style.display = 'block';
                showScreenerMessage('warning', 'Using mock data for demonstration. API connection failed.');
            }
        }
    } catch (error) {
        console.error('Error in screener submission:', error);
        showScreenerMessage('danger', `Error: ${error.message}`);
        
        // If API is not available, use mock data for demonstration
        console.log('Generating mock data for testing');
        const mockSignals = generateMockSignals(selectedOptions.map(opt => opt.value));
        state.signals = mockSignals;
        
        // Render mock data
        renderSignalSummary({
            signals_count: mockSignals.length,
            buy_signals: mockSignals.filter(s => s.signal.toLowerCase() === 'buy').length,
            sell_signals: mockSignals.filter(s => s.signal.toLowerCase() === 'sell').length,
            hold_signals: mockSignals.filter(s => s.signal.toLowerCase() === 'hold').length,
            asset_count: [...new Set(mockSignals.map(s => s.asset))].length,
            strategy_count: selectedOptions.length,
            cached_file: 'mock_data',
            timestamp: new Date().toISOString()
        });
        renderSignalChart(mockSignals);
        renderSignalTable(mockSignals);
        
        // Show results with mock data warning
        screenerResults.style.display = 'block';
        showScreenerMessage('warning', 'Using mock data for demonstration. API connection failed.');
    } finally {
        // Hide loading indicator and re-enable form
        screenerLoading.style.display = 'none';
        enableScreener();
    }
}

// Fetch signals from the cached parquet file
async function fetchSignalsFromCache(cacheFile) {
    try {
        // Try to fetch real signals from the API
        if (cacheFile) {
            try {
                const signals = await fetchCachedSignals(cacheFile);
                return signals;
            } catch (apiError) {
                console.error('Error fetching signals from API:', apiError);
                throw apiError; // Let the caller handle this
            }
        } else {
            throw new Error('No cache file provided');
        }
    } catch (error) {
        console.error('Error fetching cached signals:', error);
        throw error;
    }
}

// Generate mock signals for testing (used as fallback)
function generateMockSignals(selectedStrategies) {
    // Convert selected strategies to objects with type/name
    const strategyObjects = selectedStrategies.map(strategy => ({
        type: strategy,
        name: formatStrategyName(strategy)
    }));
    
    // Use a maximum of 10 strategies to avoid overwhelming the UI
    const limitedStrategies = strategyObjects.slice(0, Math.min(strategyObjects.length, 10));
    
    // Use asset list from appState if available, otherwise fall back to default list
    const assets = appState.multiAssetData ? 
        Object.keys(appState.multiAssetData) : 
        ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 'INTC', 'NFLX',
         'BABA', 'PYPL', 'ADBE', 'CRM', 'CSCO', 'IBM', 'ORCL', 'QCOM', 'TXN', 'V'];
    
    const mockSignals = [];
    const signals = ['buy', 'sell', 'hold'];
    const date = new Date().toISOString().split('T')[0];
    
    for (const asset of assets.slice(0, 20)) { // Limit to first 20 assets
        for (const strategy of limitedStrategies) {
            // Generate a random signal
            const randomSignal = signals[Math.floor(Math.random() * signals.length)];
            
            // Generate random metrics for more realistic data
            const sharpe_ratio = (Math.random() * 3 - 0.5).toFixed(2);  // -0.5 to 2.5
            const total_return = (Math.random() * 0.6 - 0.2).toFixed(4);  // -20% to 40%
            const max_drawdown = (Math.random() * 0.3).toFixed(4);  // 0% to 30%
            const win_rate = (Math.random() * 0.6 + 0.2).toFixed(4);  // 20% to 80%
            const num_trades = Math.floor(Math.random() * 100) + 5;  // 5 to 105 trades
            
            // Generate a weighted signal score based on the random signal
            let weighted_signal_score;
            if (randomSignal === 'buy') {
                weighted_signal_score = (Math.random() * 0.7 + 0.3).toFixed(2);  // 0.3 to 1.0
            } else if (randomSignal === 'sell') {
                weighted_signal_score = (-Math.random() * 0.7 - 0.3).toFixed(2);  // -0.3 to -1.0
            } else {
                weighted_signal_score = (Math.random() * 1.0 - 0.5).toFixed(2);  // -0.5 to 0.5
            }
            
            mockSignals.push({
                asset: asset,
                strategy: strategy.type,
                strategy_name: strategy.name,
                parameters: 'optimized',
                signal: randomSignal,
                date: date,
                weighted_signal_score: parseFloat(weighted_signal_score),
                weight: parseFloat((Math.random() * 0.25 + 0.05).toFixed(4)),  // 5% to 30%
                total_return: parseFloat(total_return),
                sharpe_ratio: parseFloat(sharpe_ratio),
                max_drawdown: parseFloat(max_drawdown),
                win_rate: parseFloat(win_rate),
                num_trades: num_trades
            });
        }
    }
    
    console.log(`Generated ${mockSignals.length} mock signals for UI demonstration`);
    return mockSignals;
}

// Render signal summary
function renderSignalSummary(response) {
    // Clear existing content
    screenerSummary.innerHTML = '';
    
    // Create summary card
    const summaryCard = document.createElement('div');
    summaryCard.className = 'card bg-light mb-3';
    
    // Create card header
    const cardHeader = document.createElement('div');
    cardHeader.className = 'card-header d-flex justify-content-between align-items-center';
    cardHeader.innerHTML = `
        <h5 class="mb-0">Signal Summary</h5>
        <span class="badge bg-info">${response.asset_count} Assets × ${response.strategy_count} Strategies</span>
    `;
    
    // Create card body
    const cardBody = document.createElement('div');
    cardBody.className = 'card-body';
    
    // Add total signals info
    cardBody.innerHTML = `
        <p class="card-text">Generated <strong>${response.signals_count}</strong> signals across all assets and strategies.</p>
    `;
    
    // Create raw signals summary
    const rawSignalsDiv = document.createElement('div');
    rawSignalsDiv.className = 'mb-3';
    rawSignalsDiv.innerHTML = `
        <h6>Raw Signals:</h6>
        <div class="d-flex justify-content-between text-center">
            <div class="px-2">
                <span class="badge bg-success">${response.buy_signals}</span>
                <div class="small">Buy</div>
            </div>
            <div class="px-2">
                <span class="badge bg-danger">${response.sell_signals}</span>
                <div class="small">Sell</div>
            </div>
            <div class="px-2">
                <span class="badge bg-secondary">${response.hold_signals}</span>
                <div class="small">Hold</div>
            </div>
        </div>
    `;
    
    // Add raw signals div to card body
    cardBody.appendChild(rawSignalsDiv);
    
    // Check if weighted signals information is available
    const hasWeights = response.has_weights || 
                      response.weighted_buy_signals !== undefined ||
                      (state.signals && state.signals.length > 0 && state.signals[0].weighted_signal_score !== undefined);
                      
    // If weighted signals are available, add weighted signals summary
    if (hasWeights) {
        // If we don't have the weighted signal counts in the response, calculate them from state.signals
        let weightedBuy = response.weighted_buy_signals;
        let weightedSell = response.weighted_sell_signals;
        let weightedHold = response.weighted_hold_signals;
        
        if (weightedBuy === undefined && state.signals && state.signals.length > 0) {
            weightedBuy = state.signals.filter(s => s.weighted_signal_score > 0.5).length;
            weightedSell = state.signals.filter(s => s.weighted_signal_score < -0.5).length;
            weightedHold = state.signals.filter(s => s.weighted_signal_score >= -0.5 && s.weighted_signal_score <= 0.5).length;
        }
        
        const weightedSignalsDiv = document.createElement('div');
        weightedSignalsDiv.className = 'mt-3';
        weightedSignalsDiv.innerHTML = `
            <h6>Weighted Signals:</h6>
            <div class="d-flex justify-content-between text-center">
                <div class="px-2">
                    <span class="badge bg-success">${weightedBuy || 0}</span>
                    <div class="small">Buy (>0.5)</div>
                </div>
                <div class="px-2">
                    <span class="badge bg-danger">${weightedSell || 0}</span>
                    <div class="small">Sell (<-0.5)</div>
                </div>
                <div class="px-2">
                    <span class="badge bg-secondary">${weightedHold || 0}</span>
                    <div class="small">Hold (-0.5 to 0.5)</div>
                </div>
            </div>
            <div class="small text-muted mt-2">
                Weighted signals use performance-based metrics to adjust signal strength. 
                A threshold of +/-0.5 is used to determine the final signal classification.
            </div>
        `;
        
        // Add weighted signals div to card body
        cardBody.appendChild(weightedSignalsDiv);
    }
    
    // Add timestamp
    const timestamp = new Date(response.timestamp).toLocaleString();
    const timestampDiv = document.createElement('div');
    timestampDiv.className = 'mt-3 text-muted small';
    timestampDiv.textContent = `Generated: ${timestamp}`;
    cardBody.appendChild(timestampDiv);
    
    // Assemble the card
    summaryCard.appendChild(cardHeader);
    summaryCard.appendChild(cardBody);
    
    // Add the card to the summary container
    screenerSummary.appendChild(summaryCard);
    
    // Store ML results for panel updates
    if (response.has_ml_signals || response.ml_signals_count > 0) {
        state.lastMlResults = {
            ml_avg_accuracy: response.ml_avg_accuracy,
            ml_signals_count: response.ml_signals_count,
            ml_buy_signals: response.ml_buy_signals,
            ml_sell_signals: response.ml_sell_signals,
            ml_hold_signals: response.ml_hold_signals
        };
        
        // Update ML panel with performance data
        updateMlPanelState();
        updateMlPerformanceDisplay(state.lastMlResults);
    }
}

// Render signal chart
function renderSignalChart(signals) {
    // Add null/undefined checks
    if (!signals || !Array.isArray(signals) || signals.length === 0) {
        console.warn('renderSignalChart: Invalid or empty signals array', signals);
        return;
    }
    
    // Get the canvas element
    const chartCanvas = document.getElementById('screener-chart');
    if (!chartCanvas) {
        console.error('Screener chart canvas not found');
        return;
    }
    
    // Log to help with debugging
    console.log('Rendering signal chart with data:', {
        signalCount: signals.length,
        useWeightedSignals: state.useWeightedSignals,
        hasWeightedScores: signals.some(s => s.weighted_signal_score !== undefined),
        hasMlSignals: signals.some(s => s.strategy === 'LogisticRegression')
    });
    
    // Destroy existing chart if it exists
    if (window.signalChart) {
        window.signalChart.destroy();
    }
    
    // Determine whether to use raw signals or weighted scores
    let buyCount, sellCount, holdCount;
    
    if (state.useWeightedSignals && signals.some(s => s.weighted_signal_score !== undefined)) {
        // Count based on weighted signal scores
        buyCount = signals.filter(s => s.weighted_signal_score > 0.5).length;
        sellCount = signals.filter(s => s.weighted_signal_score < -0.5).length;
        holdCount = signals.filter(s => s.weighted_signal_score >= -0.5 && s.weighted_signal_score <= 0.5).length;
    } else {
        // Count based on raw signals
        buyCount = signals.filter(s => s.signal.toLowerCase() === 'buy').length;
        sellCount = signals.filter(s => s.signal.toLowerCase() === 'sell').length;
        holdCount = signals.filter(s => s.signal.toLowerCase() === 'hold').length;
    }
    
    // Calculate percentages
    const total = signals.length;
    const buyPercent = ((buyCount / total) * 100).toFixed(1);
    const sellPercent = ((sellCount / total) * 100).toFixed(1);
    const holdPercent = ((holdCount / total) * 100).toFixed(1);
    
    // Create the chart
    try {
        // Check if Chart is available
        if (typeof Chart === 'undefined') {
            console.error('Chart.js is not loaded. Cannot render signal chart.');
            return;
        }
        
        // Create chart title
        const hasMlSignals = signals.some(s => s.strategy === 'LogisticRegression');
        let chartTitle = state.useWeightedSignals ? 'Weighted Signal Distribution' : 'Raw Signal Distribution';
        if (hasMlSignals) {
            chartTitle += ' (includes ML signals)';
        }
        
        window.signalChart = new Chart(chartCanvas, {
            type: 'bar',
            data: {
                labels: [
                    `Buy (${buyPercent}%)`, 
                    `Sell (${sellPercent}%)`, 
                    `Hold (${holdPercent}%)`
                ],
                datasets: [{
                    label: state.useWeightedSignals ? 'Weighted Signals' : 'Raw Signals',
                    data: [buyCount, sellCount, holdCount],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.7)',    // Green for Buy
                        'rgba(220, 53, 69, 0.7)',    // Red for Sell
                        'rgba(108, 117, 125, 0.7)'   // Gray for Hold
                    ],
                    borderColor: [
                        'rgba(40, 167, 69, 1)',
                        'rgba(220, 53, 69, 1)',
                        'rgba(108, 117, 125, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Signals'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: chartTitle
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y;
                                const percentage = [buyPercent, sellPercent, holdPercent][context.dataIndex];
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        console.log('Signal chart created successfully');
    } catch (error) {
        console.error('Error creating signal chart:', error);
    }
}

// Render signal table
function renderSignalTable(signals) {
    // Add null/undefined checks
    if (!signals || !Array.isArray(signals) || signals.length === 0) {
        console.warn('renderSignalTable: Invalid or empty signals array', signals);
        // Clear the table and show a message
        if (screenerTable && screenerTable.querySelector('tbody')) {
            screenerTable.querySelector('tbody').innerHTML = '<tr><td colspan="13" class="text-center text-muted">No signals to display</td></tr>';
        }
        return;
    }
    
    // Calculate total pages
    const totalPages = Math.ceil(signals.length / state.pageSize);
    
    // Ensure current page is valid
    if (state.currentPage > totalPages) {
        state.currentPage = 1;
    }
    
    // Calculate starting and ending indices for the current page
    const startIndex = (state.currentPage - 1) * state.pageSize;
    const endIndex = Math.min(startIndex + state.pageSize, signals.length);
    
    // Get signals for the current page
    const pageSignals = signals.slice(startIndex, endIndex);
    
    // Clear existing table content
    screenerTable.querySelector('tbody').innerHTML = '';
    
    // Update table header to include weighted signal score
    const headerRow = screenerTable.querySelector('thead tr');
    if (headerRow) {
        // Check if we need to add the weighted score column
        if (!headerRow.innerHTML.includes('Weighted Score')) {
            // Update header row with weighted score column
            headerRow.innerHTML = `
                <th>Asset</th>
                <th>Strategy</th>
                <th>Parameters</th>
                <th>Raw Signal</th>
                <th>Weighted Score</th>
                <th>Date</th>
                <th>Weight</th>
                <th>Total Return</th>
                <th>Sharpe Ratio</th>
                <th>Max Drawdown</th>
                <th>Win Rate</th>
                <th>Trades</th>
                <th>Accuracy</th>
            `;
        }
    }
    
    // Add rows for each signal
    pageSignals.forEach(signal => {
        const row = document.createElement('tr');
        
        // Format metrics for display
        const weight = signal.weight !== undefined ? (signal.weight * 100).toFixed(2) + '%' : 'N/A';
        const totalReturn = signal.total_return !== undefined ? (signal.total_return * 100).toFixed(2) + '%' : 'N/A';
        const sharpeRatio = signal.sharpe_ratio !== undefined ? signal.sharpe_ratio.toFixed(2) : 'N/A';
        const maxDrawdown = signal.max_drawdown !== undefined ? (signal.max_drawdown * 100).toFixed(2) + '%' : 'N/A';
        const winRate = signal.win_rate !== undefined ? (signal.win_rate * 100).toFixed(2) + '%' : 'N/A';
        const numTrades = signal.num_trades !== undefined ? signal.num_trades : 'N/A';
        
        // Format weighted signal score
        const weightedScore = signal.weighted_signal_score !== undefined ? 
            signal.weighted_signal_score.toFixed(2) : 'N/A';
        
        // Format accuracy (only for ML signals)
        const accuracy = signal.accuracy !== undefined && signal.strategy === 'LogisticRegression' ? 
            (signal.accuracy * 100).toFixed(1) + '%' : 'N/A';
        
        // Add cells for each data point
        row.innerHTML = `
            <td>${signal.asset}</td>
            <td>${signal.strategy_name || formatStrategyName(signal.strategy)}</td>
            <td>${formatParameterType(signal.parameters)}</td>
            <td><span class="badge ${getBadgeClass(signal.signal)}">${signal.signal.toUpperCase()}</span></td>
            <td class="${getWeightedScoreClass(signal.weighted_signal_score)}">${weightedScore}</td>
            <td>${signal.date}</td>
            <td>${weight}</td>
            <td class="${getMetricClass(signal.total_return)}">${totalReturn}</td>
            <td class="${getMetricClass(signal.sharpe_ratio, true)}">${sharpeRatio}</td>
            <td class="${getMetricClass(signal.max_drawdown, false, true)}">${maxDrawdown}</td>
            <td class="${getMetricClass(signal.win_rate)}">${winRate}</td>
            <td>${numTrades}</td>
            <td class="${getAccuracyClass(signal.accuracy, signal.strategy)}">${accuracy}</td>
        `;
        
        screenerTable.querySelector('tbody').appendChild(row);
    });
    
    // Render pagination
    renderPagination(totalPages);
}

// Render pagination controls
function renderPagination(totalPages) {
    // Clear existing pagination
    screenerPagination.innerHTML = '';
    
    // Don't show pagination if only one page
    if (totalPages <= 1) {
        return;
    }
    
    // Add "Previous" button
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${state.currentPage === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a>`;
    prevLi.addEventListener('click', (e) => {
        e.preventDefault();
        if (state.currentPage > 1) {
            state.currentPage--;
            renderSignalTable(state.signals);
        }
    });
    screenerPagination.appendChild(prevLi);
    
    // Add page number buttons (show up to 5 pages centered around the current page)
    const startPage = Math.max(1, state.currentPage - 2);
    const endPage = Math.min(totalPages, startPage + 4);
    
    for (let i = startPage; i <= endPage; i++) {
        const pageLi = document.createElement('li');
        pageLi.className = `page-item ${i === state.currentPage ? 'active' : ''}`;
        pageLi.innerHTML = `<a class="page-link" href="#">${i}</a>`;
        pageLi.addEventListener('click', (e) => {
            e.preventDefault();
            state.currentPage = i;
            renderSignalTable(state.signals);
        });
        screenerPagination.appendChild(pageLi);
    }
    
    // Add "Next" button
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${state.currentPage === totalPages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" aria-label="Next"><span aria-hidden="true">&raquo;</span></a>`;
    nextLi.addEventListener('click', (e) => {
        e.preventDefault();
        if (state.currentPage < totalPages) {
            state.currentPage++;
            renderSignalTable(state.signals);
        }
    });
    screenerPagination.appendChild(nextLi);
}

// Show a message in the screener info area
function showScreenerMessage(type, message) {
    screenerInfoMessage.className = `alert alert-${type}`;
    screenerInfoMessage.innerHTML = `<i class="bi bi-info-circle-fill"></i> ${message}`;
    screenerInfoMessage.style.display = 'block';
}

// Format strategy name for display
function formatStrategyName(strategyKey) {
    return strategyKey
        .replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Format parameter type for display
function formatParameterType(paramType) {
    return paramType.charAt(0).toUpperCase() + paramType.slice(1);
}

// Get badge class based on signal
function getBadgeClass(signal) {
    switch(signal.toLowerCase()) {
        case 'buy': return 'bg-success';
        case 'sell': return 'bg-danger';
        case 'hold': return 'bg-secondary';
        default: return 'bg-secondary';
    }
}

// Get CSS class for metric value display
function getMetricClass(value, isRatio = false, isNegativeGood = false) {
    if (value === undefined || value === null) return '';
    
    // For metrics where negative is good (like drawdown), invert the logic
    if (isNegativeGood) value = -value;
    
    // For ratio metrics like Sharpe, different thresholds
    if (isRatio) {
        if (value > 1.5) return 'text-success fw-bold';
        if (value > 0.5) return 'text-success';
        if (value > 0) return 'text-warning';
        return 'text-danger';
    }
    
    // For percentage metrics
    if (value > 0.2) return 'text-success fw-bold';
    if (value > 0.05) return 'text-success';
    if (value > 0) return 'text-warning';
    return 'text-danger';
}

// Get CSS class for weighted signal score
function getWeightedScoreClass(score) {
    if (score === undefined || score === null) return '';
    
    if (score > 0.75) return 'text-success fw-bold';
    if (score > 0.25) return 'text-success';
    if (score > -0.25) return 'text-warning';
    if (score > -0.75) return 'text-danger';
    return 'text-danger fw-bold';
}

// Get CSS class for accuracy
function getAccuracyClass(accuracy, strategy) {
    if (strategy !== 'LogisticRegression' || accuracy === undefined) {
        return '';
    }
    
    if (accuracy > 0.7) return 'text-success fw-bold';
    if (accuracy > 0.5) return 'text-success';
    if (accuracy > 0.3) return 'text-warning';
    return 'text-danger';
}

// Disable screener functionality
function disableScreener() {
    strategiesSelect.disabled = true;
    runScreenerBtn.disabled = true;
}

// Enable screener functionality
function enableScreener() {
    strategiesSelect.disabled = false;
    runScreenerBtn.disabled = false;
}

// Initialize ML panel
function initializeMlPanel() {
    // Get ML panel elements
    const mlPanel = document.getElementById('ml-config-panel');
    const mlToggle = document.getElementById('include-ml-signals');
    const mlIndicatorsCount = document.getElementById('ml-indicators-count');
    const mlPerformanceSection = document.getElementById('ml-performance');
    
    if (!mlPanel || !mlToggle) {
        console.warn('ML panel elements not found');
        return;
    }
    
    // Set up ML toggle event listener
    mlToggle.addEventListener('change', (event) => {
        state.includeMlSignals = event.target.checked;
        console.log(`ML signals ${state.includeMlSignals ? 'enabled' : 'disabled'}`);
        
        // Update panel state
        updateMlPanelState();
        
        // Save to appState
        if (!appState.screeningConfig) appState.screeningConfig = {};
        appState.screeningConfig.includeMlSignals = state.includeMlSignals;
        
        // Show message about re-running screener
        if (state.signals && state.signals.length > 0) {
            showScreenerMessage('info', 'ML toggle changed. Re-run the screener to apply changes.');
        }
    });
    
    // Initialize indicator count
    updateMlIndicatorCount();
    
    // Set initial panel state
    updateMlPanelState();
    
    console.log('ML panel initialized');
}

// Update ML panel state based on toggle
function updateMlPanelState() {
    const mlPerformanceSection = document.getElementById('ml-performance');
    const mlPanel = document.getElementById('ml-config-panel');
    
    if (!mlPanel) return;
    
    // Update panel appearance based on ML toggle state
    if (state.includeMlSignals) {
        mlPanel.classList.add('ml-enabled');
        if (mlPerformanceSection && state.lastMlResults) {
            mlPerformanceSection.style.display = 'block';
            updateMlPerformanceDisplay(state.lastMlResults);
        }
    } else {
        mlPanel.classList.remove('ml-enabled');
        if (mlPerformanceSection) {
            mlPerformanceSection.style.display = 'none';
        }
    }
}

// Update ML indicator count
function updateMlIndicatorCount() {
    const mlIndicatorsCount = document.getElementById('ml-indicators-count');
    if (!mlIndicatorsCount) return;
    
    // Detailed indicators that are used for ML feature engineering
    const mlFeatures = {
        priceFeatures: ['Open', 'High', 'Low', 'Close', 'Lagged Returns (1-5 days)'],
        volumeFeatures: ['Volume', 'Volume Change', 'Volume MA Ratio'],
        trendIndicators: ['SMA (20,50)', 'EMA (12,26)', 'MACD (12,26,9)', 'ADX (14)'],
        momentumIndicators: ['RSI (14)', 'Stochastic (%K,%D)', 'Williams %R (14)'],
        volatilityIndicators: ['Bollinger Bands (20,2)', 'ATR (14)']
    };
    
    const totalFeatures = Object.values(mlFeatures).flat().length;
    
    mlIndicatorsCount.textContent = `${totalFeatures} features`;
    mlIndicatorsCount.title = `ML features include: ${Object.values(mlFeatures).flat().join(', ')}`;
    
    // Add click handler for detailed view
    mlIndicatorsCount.style.cursor = 'pointer';
    mlIndicatorsCount.onclick = () => showMlFeatureDetails(mlFeatures);
}

// Show detailed ML feature information
function showMlFeatureDetails(mlFeatures) {
    // Create a modal or detailed view showing ML features
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'ml-features-modal';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-info text-white">
                    <h5 class="modal-title">
                        <i class="bi bi-cpu-fill"></i> ML Feature Engineering Details
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        ${Object.entries(mlFeatures).map(([category, features]) => `
                            <div class="col-md-6 mb-3">
                                <div class="card">
                                    <div class="card-header">
                                        <h6 class="mb-0">${category.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}</h6>
                                    </div>
                                    <div class="card-body">
                                        <ul class="list-unstyled">
                                            ${features.map(feature => `<li><i class="bi bi-check-circle text-success"></i> ${feature}</li>`).join('')}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <div class="alert alert-info">
                        <strong>Feature Engineering Process:</strong>
                        <ol>
                            <li>Price data is normalized using StandardScaler</li>
                            <li>Lagged returns (1-5 days) are calculated for momentum</li>
                            <li>Technical indicators are computed with standard parameters</li>
                            <li>Volume features are derived from volume and price relationships</li>
                            <li>Features with high correlation (>0.95) are removed</li>
                            <li>Missing values are forward-filled then backward-filled</li>
                        </ol>
                    </div>
                    <div class="alert alert-warning">
                        <strong>Model Configuration:</strong>
                        <ul>
                            <li><strong>Algorithm:</strong> Scikit-learn LogisticRegression with L2 regularization</li>
                            <li><strong>Training:</strong> Time-aware 70/30 split (no future leakage)</li>
                            <li><strong>Signal Logic:</strong> Probability >60% = Buy/Sell, else Hold</li>
                            <li><strong>Minimum Data:</strong> 100 data points required for training</li>
                            <li><strong>Caching:</strong> Models and signals cached for performance</li>
                        </ul>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to page
    document.body.appendChild(modal);
    
    // Show modal
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
    
    // Remove modal from DOM after hiding
    modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
    });
}

// Update ML performance display
function updateMlPerformanceDisplay(mlResults) {
    const avgAccuracyElement = document.getElementById('ml-avg-accuracy');
    const successfulModelsElement = document.getElementById('ml-successful-models');
    const mlBuyCountElement = document.getElementById('ml-buy-count');
    const mlSellCountElement = document.getElementById('ml-sell-count');
    const mlHoldCountElement = document.getElementById('ml-hold-count');
    
    if (!mlResults) return;
    
    // Calculate metrics from ML results
    let totalAccuracy = 0;
    let successfulModels = 0;
    let buyCount = 0;
    let sellCount = 0;
    let holdCount = 0;
    
    if (mlResults.ml_avg_accuracy !== undefined) {
        // Use provided aggregated metrics
        if (avgAccuracyElement) {
            const accuracy = mlResults.ml_avg_accuracy;
            avgAccuracyElement.textContent = `${(accuracy * 100).toFixed(1)}%`;
            avgAccuracyElement.className = `badge ${getAccuracyBadgeClass(accuracy)}`;
        }
        
        if (successfulModelsElement) {
            successfulModelsElement.textContent = `${mlResults.ml_signals_count || 0}`;
        }
        
        if (mlBuyCountElement) mlBuyCountElement.textContent = mlResults.ml_buy_signals || 0;
        if (mlSellCountElement) mlSellCountElement.textContent = mlResults.ml_sell_signals || 0;
        if (mlHoldCountElement) mlHoldCountElement.textContent = mlResults.ml_hold_signals || 0;
    } else if (Array.isArray(mlResults)) {
        // Calculate from signal array
        mlResults.forEach(signal => {
            if (signal.strategy === 'LogisticRegression' && signal.accuracy > 0) {
                totalAccuracy += signal.accuracy;
                successfulModels++;
                
                if (signal.signal === 'buy') buyCount++;
                else if (signal.signal === 'sell') sellCount++;
                else holdCount++;
            }
        });
        
        const avgAccuracy = successfulModels > 0 ? totalAccuracy / successfulModels : 0;
        
        if (avgAccuracyElement) {
            avgAccuracyElement.textContent = `${(avgAccuracy * 100).toFixed(1)}%`;
            avgAccuracyElement.className = `badge ${getAccuracyBadgeClass(avgAccuracy)}`;
        }
        
        if (successfulModelsElement) successfulModelsElement.textContent = `${successfulModels}`;
        if (mlBuyCountElement) mlBuyCountElement.textContent = buyCount;
        if (mlSellCountElement) mlSellCountElement.textContent = sellCount;
        if (mlHoldCountElement) mlHoldCountElement.textContent = holdCount;
    }
}

// Get accuracy badge class for color coding
function getAccuracyBadgeClass(accuracy) {
    if (accuracy >= 0.7) return 'bg-success';
    if (accuracy >= 0.6) return 'bg-warning';
    return 'bg-danger';
} 