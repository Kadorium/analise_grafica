// frontend/js/utils/state.js

// Initialize application state
export const appState = {
    dataUploaded: false,
    dataProcessed: false,
    availableIndicators: [],
    selectedStrategy: 'trend_following',
    strategyParameters: {},
    currentConfig: {},
    optimizationStatusInterval: null,
    currentOptimizationStrategy: null,
    optimizationJobId: null,
    optimizationResults: null,
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
    
    setStrategyParameters(parameters) {
        this.strategyParameters = parameters;
        sessionStorage.setItem('strategyParameters', JSON.stringify(parameters));
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
    
    setOptimizationJobId(jobId) {
        this.optimizationJobId = jobId;
        sessionStorage.setItem('optimizationJobId', jobId);
    },
    
    setOptimizationResults(results) {
        this.optimizationResults = results;
        try {
            sessionStorage.setItem('optimizationResults', JSON.stringify(results));
        } catch (e) {
            console.error('Error storing optimization results in session storage:', e);
            // Results might be too large for sessionStorage, store a simplified version
            const simplifiedResults = {
                strategy_type: results.strategy_type,
                metric: results.metric,
                best_params: results.best_params,
                best_performance: results.best_performance,
                top_results: results.top_results ? results.top_results.slice(0, 3) : []
            };
            sessionStorage.setItem('optimizationResults', JSON.stringify(simplifiedResults));
        }
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
        
        if (sessionStorage.getItem('strategyParameters')) {
            try {
                this.strategyParameters = JSON.parse(sessionStorage.getItem('strategyParameters'));
            } catch (e) {
                console.error('Error parsing strategy parameters from session storage:', e);
                this.strategyParameters = {};
            }
        }
        
        if (sessionStorage.getItem('currentOptimizationStrategy')) {
            this.currentOptimizationStrategy = sessionStorage.getItem('currentOptimizationStrategy');
        }
        
        if (sessionStorage.getItem('optimizationJobId')) {
            this.optimizationJobId = sessionStorage.getItem('optimizationJobId');
        }
        
        if (sessionStorage.getItem('optimizationResults')) {
            try {
                this.optimizationResults = JSON.parse(sessionStorage.getItem('optimizationResults'));
            } catch (e) {
                console.error('Error parsing optimization results from session storage:', e);
                this.optimizationResults = null;
            }
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
        this.strategyParameters = {};
        this.currentConfig = {};
        this.currentOptimizationStrategy = null;
        this.optimizationJobId = null;
        this.optimizationResults = null;
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
        sessionStorage.removeItem('strategyParameters');
        sessionStorage.removeItem('currentOptimizationStrategy');
        sessionStorage.removeItem('optimizationJobId');
        sessionStorage.removeItem('optimizationResults');
        sessionStorage.removeItem('activeTab');
        sessionStorage.removeItem('dateRangeStart');
        sessionStorage.removeItem('dateRangeEnd');
    }
};

// Initialize state from session storage when the module is loaded
appState.loadFromSessionStorage();
