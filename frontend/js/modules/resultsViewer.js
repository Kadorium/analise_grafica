// frontend/js/modules/resultsViewer.js

// Import dependencies
import { compareStrategies as compareStrategiesApi } from '../utils/api.js';
import { showError, showLoading, showSuccessMessage, showGlobalLoader, hideGlobalLoader } from '../utils/ui.js';
import { formatDate, formatNumber } from '../utils/formatters.js';
import { appState } from '../utils/state.js';

// Temporary placeholder for fetchResultsHistory until browser cache refreshes
const fetchResultsHistory = async () => {
    console.log("Temporary fetchResultsHistory placeholder function called");
    return { results: [] };
};

// DOM references
const compareStrategiesForm = document.getElementById('compare-strategies-form');
const resultsComparisonContainer = document.getElementById('results-comparison');
const resultsHistoryContainer = document.getElementById('results-history');
const strategySelectContainer = document.getElementById('strategy-select-container');

// Compare strategies
export async function compareStrategies(params = {}) {
    if (!appState.dataProcessed) {
        showError('Please upload and process data first');
        return null;
    }
    
    try {
        showGlobalLoader('Comparing strategies...');
        
        // Run comparison
        const response = await compareStrategiesApi(params);
        
        if (response.success) {
            showSuccessMessage('Strategy comparison completed');
            
            // Display comparison results
            displayComparisonResults(response.results);
            
            return response.results;
        } else {
            throw new Error(response.error || 'Error comparing strategies');
        }
    } catch (error) {
        showError(error.message || 'Failed to compare strategies');
        return null;
    } finally {
        hideGlobalLoader();
    }
}

// Display comparison results
function displayComparisonResults(results) {
    if (!resultsComparisonContainer || !results) return;
    
    // Clear previous results
    resultsComparisonContainer.innerHTML = '';
    
    // Create comparison table
    let comparisonHtml = `
        <div class="card mb-4">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">Strategy Comparison Results</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-bordered table-striped">
                        <thead>
                            <tr>
                                <th>Metric</th>
                                ${results.strategies.map(strategy => 
                                    `<th>${strategy.name || 'Strategy ' + strategy.id}</th>`
                                ).join('')}
                            </tr>
                        </thead>
                        <tbody>
    `;
    
    // Add metrics rows
    if (results.metrics && results.metrics.length > 0) {
        results.metrics.forEach(metric => {
            comparisonHtml += `
                <tr>
                    <td>${metric.name}</td>
                    ${results.strategies.map(strategy => {
                        const value = strategy.metrics[metric.id];
                        let formattedValue = value;
                        
                        // Format based on metric type
                        if (typeof value === 'number') {
                            if (metric.is_percentage) {
                                formattedValue = formatNumber(value * 100, 2) + '%';
                            } else {
                                formattedValue = formatNumber(value);
                            }
                        }
                        
                        // Add class for highlighting
                        let cellClass = '';
                        if (metric.higher_is_better && value === Math.max(...results.strategies.map(s => s.metrics[metric.id]))) {
                            cellClass = 'table-success';
                        } else if (!metric.higher_is_better && value === Math.min(...results.strategies.map(s => s.metrics[metric.id]))) {
                            cellClass = 'table-success';
                        }
                        
                        return `<td class="${cellClass}">${formattedValue}</td>`;
                    }).join('')}
                </tr>
            `;
        });
    }
    
    comparisonHtml += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    // Add comparison charts if available
    if (results.comparison_charts) {
        comparisonHtml += `
            <div class="comparison-charts">
                ${results.comparison_charts}
            </div>
        `;
    }
    
    resultsComparisonContainer.innerHTML = comparisonHtml;
}

// Load results history
async function loadResultsHistory() {
    if (!resultsHistoryContainer) return;
    
    try {
        showLoading(resultsHistoryContainer);
        
        // Fetch results history
        const response = await fetchResultsHistory();
        
        if (response.results && response.results.length > 0) {
            displayResultsHistory(response.results);
        } else {
            resultsHistoryContainer.innerHTML = '<div class="alert alert-info">No previous results found</div>';
        }
    } catch (error) {
        showError(error.message || 'Failed to load results history');
        resultsHistoryContainer.innerHTML = '';
    }
}

// Display results history
function displayResultsHistory(historyResults) {
    if (!resultsHistoryContainer || !historyResults) return;
    
    // Create history table
    let historyHtml = `
        <div class="table-responsive">
            <table class="table table-bordered table-striped">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Strategy</th>
                        <th>Net Profit</th>
                        <th>Win Rate</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Add each history item
    historyResults.forEach(item => {
        historyHtml += `
            <tr>
                <td>${formatDate(item.date)}</td>
                <td>${item.strategy_name || 'Strategy ' + item.strategy_id}</td>
                <td class="${item.net_profit >= 0 ? 'text-success' : 'text-danger'}">${formatNumber(item.net_profit)}</td>
                <td>${formatNumber(item.win_rate * 100, 2)}%</td>
                <td>
                    <button class="btn btn-sm btn-primary view-result-btn" data-result-id="${item.id}">
                        View
                    </button>
                </td>
            </tr>
        `;
    });
    
    historyHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    resultsHistoryContainer.innerHTML = historyHtml;
    
    // Add event listeners to view buttons
    const viewButtons = resultsHistoryContainer.querySelectorAll('.view-result-btn');
    viewButtons.forEach(button => {
        button.addEventListener('click', () => {
            const resultId = button.dataset.resultId;
            viewResultDetails(resultId);
        });
    });
}

// View result details
function viewResultDetails(resultId) {
    // This would typically open a modal or navigate to a details page
    console.log(`Viewing result details for ID: ${resultId}`);
    
    // Example implementation: show a modal
    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        // If using Bootstrap 5
        const modalElement = document.getElementById('result-details-modal');
        if (modalElement) {
            const resultModal = new bootstrap.Modal(modalElement);
            
            // Here we would fetch the specific result details and populate the modal
            // For now, just show the modal
            resultModal.show();
        }
    }
}

// Add strategy to comparison
function addStrategyToComparison() {
    if (!strategySelectContainer) return;
    
    // Create new strategy select
    const selectIndex = strategySelectContainer.querySelectorAll('.strategy-select').length + 1;
    
    const newSelectGroup = document.createElement('div');
    newSelectGroup.className = 'mb-3 strategy-select-group';
    
    // Create a row for the select and remove button
    newSelectGroup.innerHTML = `
        <div class="input-group">
            <select class="form-select strategy-select" name="strategy_${selectIndex}" required>
                <option value="">Select Strategy ${selectIndex}</option>
                ${appState.availableStrategies.map(strategy => 
                    `<option value="${strategy.id || strategy}">${strategy.name || strategy}</option>`
                ).join('')}
            </select>
            <button type="button" class="btn btn-danger remove-strategy-btn">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    `;
    
    strategySelectContainer.appendChild(newSelectGroup);
    
    // Add event listener to remove button
    const removeButton = newSelectGroup.querySelector('.remove-strategy-btn');
    if (removeButton) {
        removeButton.addEventListener('click', function() {
            strategySelectContainer.removeChild(newSelectGroup);
        });
    }
}

// Initialize results viewer
export function initializeResultsViewer() {
    // Load results history
    loadResultsHistory();
    
    // Add strategy comparison form handler
    if (compareStrategiesForm) {
        compareStrategiesForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Get selected strategies
            const strategySelects = compareStrategiesForm.querySelectorAll('.strategy-select');
            const strategies = [];
            
            strategySelects.forEach(select => {
                if (select.value) {
                    strategies.push(select.value);
                }
            });
            
            if (strategies.length < 2) {
                showError('Please select at least two strategies to compare');
                return;
            }
            
            // Run comparison
            await compareStrategies({ strategies });
        });
        
        // Add "Add Strategy" button handler
        const addStrategyBtn = document.getElementById('add-strategy-btn');
        if (addStrategyBtn) {
            addStrategyBtn.addEventListener('click', addStrategyToComparison);
        }
        
        // Initialize with two strategy selects
        addStrategyToComparison();
        addStrategyToComparison();
    }
}
