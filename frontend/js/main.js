// frontend/js/main.js

// Import utility modules
import { appState } from './utils/state.js';
import { activateTab, showError } from './utils/ui.js';

// Import feature modules
import { initializeDataManager, checkDataStatus } from './modules/dataManager.js';
import { initializeIndicatorControls } from './modules/indicatorPanel.js';
import { initializeStrategySelector, buildStrategySelections } from './modules/strategySelector.js';
import { initializeBacktestView } from './modules/backtestView.js';
import { initializeOptimizationPanel } from './modules/optimizationPanel.js';
import { initializeSeasonalityAnalyzer } from './modules/seasonalityAnalyzer.js';
import { initializeResultsViewer } from './modules/resultsViewer.js';
import { initializeConfigManager, fetchCurrentConfig } from './modules/configManager.js';

// DOM references for tabs and sections
const tabLinks = document.querySelectorAll('.nav-link');
const dataTab = document.getElementById('data-tab');
const indicatorsTab = document.getElementById('indicators-tab');
const strategiesTab = document.getElementById('strategies-tab');
const backtestTab = document.getElementById('backtest-tab');
const optimizationTab = document.getElementById('optimization-tab');
const seasonalityTab = document.getElementById('seasonality-tab');
const resultsTab = document.getElementById('results-tab');
const configTab = document.getElementById('config-tab');

// Initialize tab navigation
function initializeTabNavigation() {
    console.log('Initializing tab navigation');
    
    // Bail out if there are no tab links
    if (!tabLinks || !tabLinks.length) {
        console.error('No tab links found');
        return;
    }
    
    // Add direct click handlers to tabs that switch the content immediately
    tabLinks.forEach(tabLink => {
        tabLink.addEventListener('click', function(event) {
            // Prevent default navigation
            event.preventDefault();
            
            const targetId = this.getAttribute('href');
            console.log(`Tab clicked: ${this.id}, target: ${targetId}`);
            
            // Check if we can activate this tab
            if (!canActivateTab(targetId)) {
                console.warn(`Cannot activate tab ${targetId}`);
                return false;
            }
            
            // Update URL hash without triggering hash change event
            const newUrl = window.location.pathname + window.location.search + targetId;
            history.replaceState(null, '', newUrl);
            
            // Activate tab
            toggleTabSection(this, targetId);
            
            return false;
        });
    });
    
    // Handle initial tab based on URL hash or default to data tab
    const hash = window.location.hash;
    if (hash) {
        const tabLink = document.querySelector(`.nav-link[href="${hash}"]`);
        if (tabLink && canActivateTab(hash)) {
            console.log(`Activating initial tab from hash: ${hash}`);
            toggleTabSection(tabLink, hash);
        } else {
            console.warn(`Cannot activate hash tab ${hash}, defaulting to data tab`);
            const dataTabLink = document.getElementById('data-tab');
            if (dataTabLink) {
                toggleTabSection(dataTabLink, '#data-section');
            }
        }
    } else if (appState.activeTab) {
        const activeTabLink = document.querySelector(`.nav-link[href="${appState.activeTab}"]`);
        if (activeTabLink && canActivateTab(appState.activeTab)) {
            console.log(`Activating saved tab: ${appState.activeTab}`);
            toggleTabSection(activeTabLink, appState.activeTab);
        }
    }
}

// Simple function to activate a tab and show its content
function toggleTabSection(tabElement, targetId) {
    // Update UI - remove active class from all tabs
    tabLinks.forEach(tab => tab.classList.remove('active'));
    
    // Add active class to clicked tab
    tabElement.classList.add('active');
    
    // Hide all sections
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => section.classList.remove('active'));
    
    // Show target section
    const targetSection = document.getElementById(targetId.substring(1)); // Remove the # from the id
    if (targetSection) {
        targetSection.classList.add('active');
        
        // Update page title
        const pageTitle = document.getElementById('page-title');
        if (pageTitle) {
            pageTitle.textContent = tabElement.textContent.trim();
        }
        
        // Save active tab to state
        if (appState && typeof appState.setActiveTab === 'function') {
            appState.setActiveTab(targetId);
        } else {
            console.warn('appState.setActiveTab is not available');
        }
        
        // Special handling for strategies tab
        if (targetId === '#strategies-section' && typeof window.loadStrategyParameters === 'function') {
            setTimeout(() => window.loadStrategyParameters(), 100);
        }
    } else {
        console.error(`Target section not found: ${targetId}`);
    }
}

// Check if a tab can be activated based on data status
function canActivateTab(targetTab) {
    console.log(`Checking if can activate tab: ${targetTab}`);
    
    // Always allow navigation to data tab
    if (targetTab === '#data-section') {
        return true;
    }
    
    // For other tabs, check if data is uploaded and processed
    if (!appState.dataUploaded || !appState.dataProcessed) {
        const errorMessage = !appState.dataUploaded ? 
            'Please upload data before accessing this tab' : 
            'Please process data before accessing this tab';
        
        showError(errorMessage);
        
        // Navigate back to data tab
        const dataTabLink = document.getElementById('data-tab');
        if (dataTabLink) setTimeout(() => dataTabLink.click(), 100);
        
        return false;
    }
    
    return true;
}

// Handle hash change in URL
function handleHashChange() {
    const hash = window.location.hash;
    if (!hash) return;
    
    console.log(`Hash changed to: ${hash}`);
    
    // Find the tab link with this href
    const targetTabLink = document.querySelector(`.nav-link[href="${hash}"]`);
    if (!targetTabLink) {
        console.warn(`No tab found with href: ${hash}`);
        return;
    }
    
    // Check if we can activate this tab
    if (!canActivateTab(hash)) {
        console.warn(`Cannot activate tab ${hash} - data requirements not met`);
        return;
    }
    
    // Activate the tab
    toggleTabSection(targetTabLink, hash);
}

// Initialize the application
export function initializeApp() {
    console.log('Initializing application...');
    
    // Initialize data manager
    initializeDataManager();
    
    // Initialize indicator panel
    initializeIndicatorControls();
    
    // Initialize strategy selector
    initializeStrategySelector();
    
    // Initialize backtest view
    initializeBacktestView();
    
    // Initialize optimization panel
    initializeOptimizationPanel();
    
    // Initialize seasonality analyzer
    initializeSeasonalityAnalyzer();
    
    // Initialize results viewer
    initializeResultsViewer();
    
    // Initialize config manager
    initializeConfigManager();
    
    // Add event listener for data upload
    document.addEventListener('data-uploaded', () => {
        console.log('Data uploaded event received, enabling tabs');
        // Enable all tabs that require data
        const tabs = document.querySelectorAll('.nav-link');
        tabs.forEach(tab => {
            if (tab && tab.id !== 'data-tab') {
                tab.classList.remove('disabled');
            }
        });
    });
    
    // Check data status on page load
    checkDataStatus().then(status => {
        if (status.data_processed) {
            console.log('Data already processed, enabling tabs');
            // Enable tabs that require data
            const tabs = document.querySelectorAll('.nav-link');
            tabs.forEach(tab => {
                if (tab && tab.id !== 'data-tab') {
                    tab.classList.remove('disabled');
                }
            });
        }
    });
    
    // Set up tab navigation
    initializeTabNavigation();
    
    // Fetch available strategies for dropdowns
    buildStrategySelections();
    
    // Initialize date fields from appState
    if (appState.dateRange && appState.dateRange.startDate && appState.dateRange.endDate) {
        const startDateInputs = document.querySelectorAll(
            '#chart-start-date, #backtest-start-date, #optimization-start-date, #compare-start-date, #seasonality-start-date'
        );
        
        const endDateInputs = document.querySelectorAll(
            '#chart-end-date, #backtest-end-date, #optimization-end-date, #compare-end-date, #seasonality-end-date'
        );
        
        // Update start date inputs
        startDateInputs.forEach(input => {
            if (input) input.value = appState.dateRange.startDate;
        });
        
        // Update end date inputs
        endDateInputs.forEach(input => {
            if (input) input.value = appState.dateRange.endDate;
        });
        
        console.log(`Date fields initialized from appState: ${appState.dateRange.startDate} - ${appState.dateRange.endDate}`);
    }
    
    // Listen for global events
    setupGlobalEventListeners();
    
    // Force a tab refresh after a short delay to ensure correct display
    setTimeout(() => {
        if (window.location.hash) {
            // Manually trigger hash change to refresh the current tab
            handleHashChange();
        }
    }, 500);
    
    console.log('Application initialized');
}

// Set up global event listeners for cross-module communication
function setupGlobalEventListeners() {
    // Listen for optimization parameter updates
    document.addEventListener('use-optimized-params', (event) => {
        if (event.detail && event.detail.params) {
            // Find where these parameters should be applied
            // For example, apply to strategy parameters
            console.log('Applying optimized parameters:', event.detail.params);
        }
    });
    
    // Listen for strategy selection changes
    document.addEventListener('strategy-changed', (event) => {
        if (event.detail && event.detail.strategy) {
            console.log('Strategy changed to:', event.detail.strategy);
        }
    });
}

// Initialize app on DOM content loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});
