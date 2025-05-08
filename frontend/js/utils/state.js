// frontend/js/utils/state.js

// Initialize application state
export const appState = {
    dataUploaded: false,
    dataProcessed: false,
    availableIndicators: [],
    selectedStrategy: 'trend_following',
    currentConfig: {},
    optimizationStatusInterval: null,
    currentOptimizationStrategy: null,
    activeTab: null,
    dateRange: {
        startDate: '',
        endDate: ''
    },
    
    // Methods to update state
    setDataUploaded(value) {
        this.dataUploaded = value;
        sessionStorage.setItem('dataUploaded', value);
    },
    
    setDataProcessed(value) {
        this.dataProcessed = value;
        sessionStorage.setItem('dataProcessed', value);
    },
    
    setAvailableIndicators(indicators) {
        this.availableIndicators = indicators;
    },
    
    setSelectedStrategy(strategy) {
        this.selectedStrategy = strategy;
        sessionStorage.setItem('selectedStrategy', strategy);
    },
    
    setCurrentConfig(config) {
        this.currentConfig = config;
    },
    
    setOptimizationStatusInterval(interval) {
        this.optimizationStatusInterval = interval;
    },
    
    setCurrentOptimizationStrategy(strategy) {
        this.currentOptimizationStrategy = strategy;
        sessionStorage.setItem('currentOptimizationStrategy', strategy);
    },
    
    setActiveTab(tabId) {
        this.activeTab = tabId;
        sessionStorage.setItem('activeTab', tabId);
        console.log(`Active tab set to: ${tabId}`);
    },
    
    setDateRange(startDate, endDate) {
        this.dateRange = {
            startDate,
            endDate
        };
        sessionStorage.setItem('dateRangeStart', startDate);
        sessionStorage.setItem('dateRangeEnd', endDate);
        console.log(`Date range set to: ${startDate} - ${endDate}`);
    },
    
    // Load state from session storage
    loadFromSessionStorage() {
        if (sessionStorage.getItem('dataUploaded')) {
            this.dataUploaded = sessionStorage.getItem('dataUploaded') === 'true';
        }
        
        if (sessionStorage.getItem('dataProcessed')) {
            this.dataProcessed = sessionStorage.getItem('dataProcessed') === 'true';
        }
        
        if (sessionStorage.getItem('selectedStrategy')) {
            this.selectedStrategy = sessionStorage.getItem('selectedStrategy');
        }
        
        if (sessionStorage.getItem('currentOptimizationStrategy')) {
            this.currentOptimizationStrategy = sessionStorage.getItem('currentOptimizationStrategy');
        }
        
        if (sessionStorage.getItem('activeTab')) {
            this.activeTab = sessionStorage.getItem('activeTab');
        }
        
        if (sessionStorage.getItem('dateRangeStart') && sessionStorage.getItem('dateRangeEnd')) {
            this.dateRange = {
                startDate: sessionStorage.getItem('dateRangeStart'),
                endDate: sessionStorage.getItem('dateRangeEnd')
            };
        }
    },
    
    // Clear all state
    clearState() {
        this.dataUploaded = false;
        this.dataProcessed = false;
        this.availableIndicators = [];
        this.selectedStrategy = 'trend_following';
        this.currentConfig = {};
        this.currentOptimizationStrategy = null;
        this.activeTab = null;
        this.dateRange = {
            startDate: '',
            endDate: ''
        };
        
        // Clear intervals
        if (this.optimizationStatusInterval) {
            clearInterval(this.optimizationStatusInterval);
            this.optimizationStatusInterval = null;
        }
        
        // Clear session storage
        sessionStorage.removeItem('dataUploaded');
        sessionStorage.removeItem('dataProcessed');
        sessionStorage.removeItem('selectedStrategy');
        sessionStorage.removeItem('currentOptimizationStrategy');
        sessionStorage.removeItem('activeTab');
        sessionStorage.removeItem('dateRangeStart');
        sessionStorage.removeItem('dateRangeEnd');
    }
};

// Initialize state from session storage when the module is loaded
appState.loadFromSessionStorage();
