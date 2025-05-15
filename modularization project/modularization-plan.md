# Frontend Modularization Plan

## Overview
This document outlines a comprehensive step-by-step process for modularizing the monolithic `app.js` file into multiple smaller, maintainable modules. The plan ensures all dependencies are properly managed and circular references are avoided.

## Initial Setup: Modularization Workspace
Before beginning the modularization process, create a dedicated workspace folder to contain all automation scripts and tracking files:

```bash
# Create modularization workspace folder
mkdir "modularization_workspace"

# Copy this plan into the workspace
copy "modularization project\modularization-plan.md" "modularization_workspace\"
```

This dedicated workspace will contain all tracking files, scripts, and temporary files related to the modularization process. After the modularization is complete, this entire folder can be deleted for cleanup.

## Code Structure & Module Mapping
Based on analysis of app.js, the code will be organized as follows:

| Line Range (approx.) | Section | Target Module |
|----------------------|---------|--------------|
| 1-60 | Initial setup, DOM references | main.js |
| 61-120 | Global variables, API endpoints | utils/api.js, utils/state.js |
| 121-200 | Utility functions | utils/ui.js, utils/formatters.js |
| 201-450 | Data upload and processing | modules/dataManager.js |
| 451-650 | Indicator management | modules/indicatorPanel.js |
| 651-950 | Strategy selections and parameters | modules/strategySelector.js |
| 951-1250 | Backtesting functionality | modules/backtestView.js |
| 1251-1550 | Optimization functionality | modules/optimizationPanel.js |
| 1551-1850 | Seasonality analysis | modules/seasonalityAnalyzer.js |
| 1851-2150 | Results handling and comparison | modules/resultsViewer.js |
| 2151-2300 | Configuration management | modules/configManager.js |
| 2301-end | App initialization and event listeners | main.js |

## Function Migration Checklist
This checklist ensures no functions are missed during modularization:

- [ ] showError() → utils/ui.js
- [ ] showLoading() → utils/ui.js
- [ ] formatDate() → utils/formatters.js
- [ ] formatNumber() → utils/formatters.js
- [ ] activateTab() → utils/ui.js
- [ ] updateDataPreview() → modules/dataManager.js
- [ ] uploadForm event handler → modules/dataManager.js
- [ ] arrangeBtn event handler → modules/dataManager.js
- [ ] fetchCurrentConfig() → modules/configManager.js
- [ ] buildStrategySelections() → modules/strategySelector.js
- [ ] loadStrategyParameters() → modules/strategySelector.js
- [ ] updateStrategyParameters() → modules/strategySelector.js
- [ ] formatParamName() → utils/formatters.js
- [ ] setupOptimizationParameters() → modules/optimizationPanel.js
- [ ] debugBacktestResults() → modules/backtestView.js
- [ ] runBacktest() → modules/backtestView.js
- [ ] displayBacktestResults() → modules/backtestView.js
- [ ] runOptimization() → modules/optimizationPanel.js
- [ ] checkOptimizationStatus() → modules/optimizationPanel.js
- [ ] fetchAndDisplayOptimizationResults() → modules/optimizationPanel.js
- [ ] useOptimizedParameters() → modules/optimizationPanel.js
- [ ] compareStrategies() → modules/resultsViewer.js
- [ ] showSuccessMessage() → utils/ui.js
- [ ] updateIndicatorDropdowns() → modules/indicatorPanel.js
- [ ] initializeIndicatorControls() → modules/indicatorPanel.js
- [ ] moveSelectedOptions() → modules/indicatorPanel.js
- [ ] removeSelectedOptions() → modules/indicatorPanel.js
- [ ] checkDataStatus() → modules/dataManager.js
- [ ] formatMetricName() → utils/formatters.js
- [ ] formatMetricValue() → utils/formatters.js
- [ ] showLoader()/showGlobalLoader() → utils/ui.js
- [ ] hideLoader()/hideGlobalLoader() → utils/ui.js
- [ ] showNotification() → utils/ui.js
- [ ] initializeSeasonalityControls() → modules/seasonalityAnalyzer.js
- [ ] runSeasonalityAnalysis() → modules/seasonalityAnalyzer.js
- [ ] displaySeasonalityResults() → modules/seasonalityAnalyzer.js
- [ ] getSeasonalityTitle() → modules/seasonalityAnalyzer.js
- [ ] createSeasonalityTableHTML() → modules/seasonalityAnalyzer.js
- [ ] createSeasonalitySummaryAccordionHTML() → modules/seasonalityAnalyzer.js
- [ ] togglePatternOptions() → modules/seasonalityAnalyzer.js
- [ ] updateCheckboxesFromAvailableIndicators() → modules/indicatorPanel.js

## Modularization Process

### Phase 1: Setup and Preparation (1 day)

#### Step 1.1: Create Module Directory Structure
```bash
mkdir -p frontend/js/modules
mkdir -p frontend/js/utils
```

#### Step 1.2: Create Module Skeleton Files
```bash
# Create utility modules
touch frontend/js/utils/api.js
touch frontend/js/utils/ui.js
touch frontend/js/utils/formatters.js
touch frontend/js/utils/state.js

# Create feature modules
touch frontend/js/modules/dataManager.js
touch frontend/js/modules/indicatorPanel.js
touch frontend/js/modules/strategySelector.js
touch frontend/js/modules/backtestView.js
touch frontend/js/modules/optimizationPanel.js
touch frontend/js/modules/seasonalityAnalyzer.js
touch frontend/js/modules/resultsViewer.js
touch frontend/js/modules/configManager.js

# Create main entry point
touch frontend/js/main.js
```

#### Step 1.3: Backup Original Code
```bash
cp frontend/js/app.js frontend/js/app.js.backup
```

### Phase 2: Create Utility Modules (1-2 days)

#### Step 2.1: Implement API Module (`utils/api.js`)
- Define API endpoints and fetch wrapper function with error handling
- Create specific API call functions for different endpoints
- Test exports and imports

#### Step 2.2: Implement State Module (`utils/state.js`)
- Create global application state object with tracking for data status, available indicators, etc.
- Add methods to update state and persist to session storage
- Export the state object for use in other modules

#### Step 2.3: Implement UI Module (`utils/ui.js`)
- Implement error handling, loading, success, and notification functions
- Create tab navigation functionality
- Export all UI utility functions

#### Step 2.4: Implement Formatters Module (`utils/formatters.js`)
- Create date, number, and text formatting utilities
- Export all formatter functions

### Phase 3: Create Feature Modules (3-4 days)

#### Step 3.1: Implement DataManager Module (`modules/dataManager.js`)
```javascript
// Import dependencies
import { API_ENDPOINTS, fetchApi, uploadData, processData, fetchDataStatus } from '../utils/api.js';
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

// Data handling functions
export function updateDataPreview(data) {
  // Implementation
}

export async function checkDataStatus() {
  // Implementation
}

// Initialize data controls and event listeners
export function initializeDataManager() {
  // Attach form submit event
  uploadForm.addEventListener('submit', async (e) => {
    // Implementation
  });

  // Attach arrange button event
  arrangeBtn.addEventListener('click', async () => {
    // Implementation
  });
}
```

#### Steps 3.2-3.8: Implement Remaining Feature Modules
Follow the same pattern for each remaining module:
1. Import dependencies
2. Define DOM references
3. Implement module-specific functions
4. Create initialization function to set up event listeners
5. Export public functions

### Phase 4: Create Main Entry Point (1 day)

#### Step 4.1: Implement `main.js`
```javascript
// Import all modules
import { appState } from './utils/state.js';
import { activateTab } from './utils/ui.js';
import { initializeDataManager } from './modules/dataManager.js';
import { initializeIndicatorPanel } from './modules/indicatorPanel.js';
import { initializeStrategySelector } from './modules/strategySelector.js';
import { initializeBacktestView } from './modules/backtestView.js';
import { initializeOptimizationPanel } from './modules/optimizationPanel.js';
import { initializeSeasonalityAnalyzer } from './modules/seasonalityAnalyzer.js';
import { initializeResultsViewer } from './modules/resultsViewer.js';
import { initializeConfigManager } from './modules/configManager.js';

// DOM references
const dataTab = document.getElementById('data-tab');
const indicatorsTab = document.getElementById('indicators-tab');
const strategiesTab = document.getElementById('strategies-tab');
const backtestTab = document.getElementById('backtest-tab');
const optimizationTab = document.getElementById('optimization-tab');
const seasonalityTab = document.getElementById('seasonality-tab');
const resultsTab = document.getElementById('results-tab');

const dataSection = document.getElementById('data-section');
const indicatorsSection = document.getElementById('indicators-section');
const strategiesSection = document.getElementById('strategies-section');
const backtestSection = document.getElementById('backtest-section');
const optimizationSection = document.getElementById('optimization-section');
const seasonalitySection = document.getElementById('seasonality-section');
const resultsSection = document.getElementById('results-section');

// Initialize tab navigation
function initializeTabNavigation() {
  // Tab click event handlers with data validation
}

// Initialize application
function initializeApp() {
  // Initialize all modules
  initializeDataManager();
  initializeIndicatorPanel();
  initializeStrategySelector();
  initializeBacktestView();
  initializeOptimizationPanel();
  initializeSeasonalityAnalyzer();
  initializeResultsViewer();
  initializeConfigManager();
  
  // Set up tab navigation
  initializeTabNavigation();
  
  // Restore state from session storage
  const activeTabId = sessionStorage.getItem('activeTab');
  if (activeTabId) {
    document.getElementById(activeTabId).click();
  } else {
    // Default to data tab
    dataTab.click();
  }
}

// Run initialization when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);
```

### Phase 5: Update HTML to Reference Modules (1 day)

#### Step 5.1: Update index.html
Replace the single app.js script reference with:

```html
<script type="module" src="frontend/js/main.js"></script>
```

### Phase 6: Test and Debug (2-3 days)

#### Step 6.1: Browser Testing
- Test each module individually
- Test integration between modules
- Verify all features work as expected

#### Step 6.2: Troubleshooting Common Issues
- **Circular dependencies**: If Module A imports from Module B and vice versa, refactor to avoid this pattern
- **Undefined variables**: Ensure all variables are properly imported
- **Event listener issues**: Verify event listeners are correctly attached
- **API endpoint access**: Ensure API_ENDPOINTS are correctly imported
- **State management**: Check that app state is consistently updated

#### Step 6.3: Performance Optimization
- Check for redundant imports
- Combine small utility modules if necessary
- Check for memory leaks (particularly with event listeners)

### Phase 7: Cleanup and Documentation (1 day)

#### Step 7.1: Remove Backup and Temporary Files
```bash
# Only after successful testing
rm frontend/js/app.js
mv frontend/js/app.js.backup frontend/js/app.js.old
```

#### Step 7.2: Update Documentation
- Update README with modularization information
- Document the module structure and responsibilities

## Error Prevention Checklist

Before starting implementation, verify the following:

- [ ] All DOM elements are properly selected with null checks
- [ ] Circular dependencies are avoided (draw a dependency graph if needed)
- [ ] All event listeners have proper cleanup if needed
- [ ] Function signatures match between modules
- [ ] State is consistently managed and accessed
- [ ] Error handling is consistent across modules
- [ ] All imported modules use the correct relative paths
- [ ] Browser compatibility is maintained

## Emergency Rollback Plan

If critical errors occur after deployment:

1. Revert to the backup:
```bash
cp frontend/js/app.js.backup frontend/js/app.js
```

2. Update the HTML to use the original script:
```html
<script src="frontend/js/app.js"></script>
```

3. Document issues and plan for targeted fixes 

## Automated Progress Tracking

To simplify the modularization process and provide clear guidance for each step, we'll implement an automated progress tracking system using a Windows batch file. This system will help developers (even those without extensive programming knowledge) to follow the process step-by-step.

### How the Progress Tracker Works

The batch file (`modularization_workspace/module.bat`) will:

1. Determine which phase of the modularization you're currently working on by checking which files exist
2. Generate detailed instructions for the current phase in text files
3. Update a visual progress bar showing completed and upcoming steps
4. Provide clear, non-technical guidance on what to do next

When you run the batch file, it will automatically assess your progress by checking which files have been created or modified, then provide the appropriate next steps to follow.

### Creating and Using the Progress Tracker

#### Step 1: Create the Batch File
Create a file named `module.bat` in the modularization workspace folder with the following content:

```batch
@echo off
setlocal enabledelayedexpansion

:: Module.bat - Modularization Progress Tracker
:: This batch file helps track progress through the modularization process
:: and provides clear instructions for each stage.

echo ===================================================
echo    FRONTEND MODULARIZATION PROGRESS TRACKER
echo ===================================================
echo.

:: Set up directories for tracking and instructions
if not exist "tracking" mkdir tracking
if not exist "tracking\instructions" mkdir tracking\instructions
set TRACKER_DIR=tracking
set INSTRUCTIONS_DIR=%TRACKER_DIR%\instructions

:: Initialize progress file if it doesn't exist
if not exist "%TRACKER_DIR%\progress.txt" (
    echo Phase 1: Setup and Preparation [NOT STARTED] > "%TRACKER_DIR%\progress.txt"
    echo Phase 2: Create Utility Modules [NOT STARTED] >> "%TRACKER_DIR%\progress.txt"
    echo Phase 3: Create Feature Modules [NOT STARTED] >> "%TRACKER_DIR%\progress.txt"
    echo Phase 4: Create Main Entry Point [NOT STARTED] >> "%TRACKER_DIR%\progress.txt"
    echo Phase 5: Update HTML [NOT STARTED] >> "%TRACKER_DIR%\progress.txt"
    echo Phase 6: Test and Debug [NOT STARTED] >> "%TRACKER_DIR%\progress.txt"
    echo Phase 7: Cleanup and Documentation [NOT STARTED] >> "%TRACKER_DIR%\progress.txt"
)

:: Determine current phase by checking file existence
set CURRENT_PHASE=1

:: Check Phase 1 completion (directories and skeleton files exist)
if exist "..\frontend\js\modules" if exist "..\frontend\js\utils" if exist "..\frontend\js\app.js.backup" (
    call :UpdateProgress 1 "COMPLETED"
    set CURRENT_PHASE=2
) else (
    goto :Phase1Instructions
)

:: Check Phase 2 completion (utility modules exist and have content)
if exist "..\frontend\js\utils\api.js" if exist "..\frontend\js\utils\ui.js" if exist "..\frontend\js\utils\formatters.js" if exist "..\frontend\js\utils\state.js" (
    :: Check if files have actual content (more than 100 bytes)
    for %%F in (api.js ui.js formatters.js state.js) do (
        set FILE_SIZE=0
        for %%A in ("..\frontend\js\utils\%%F") do set FILE_SIZE=%%~zA
        if !FILE_SIZE! LSS 100 goto :Phase2Instructions
    )
    call :UpdateProgress 2 "COMPLETED"
    set CURRENT_PHASE=3
) else (
    goto :Phase2Instructions
)

:: Check Phase 3 completion (feature modules exist and have content)
set PHASE3_COMPLETE=1
for %%F in (dataManager.js indicatorPanel.js strategySelector.js backtestView.js optimizationPanel.js seasonalityAnalyzer.js resultsViewer.js configManager.js) do (
    if not exist "..\frontend\js\modules\%%F" (
        set PHASE3_COMPLETE=0
        goto :Phase3Check
    )
    
    :: Check file size
    set FILE_SIZE=0
    for %%A in ("..\frontend\js\modules\%%F") do set FILE_SIZE=%%~zA
    if !FILE_SIZE! LSS 100 (
        set PHASE3_COMPLETE=0
        goto :Phase3Check
    )
)

:Phase3Check
if %PHASE3_COMPLETE%==1 (
    call :UpdateProgress 3 "COMPLETED"
    set CURRENT_PHASE=4
) else (
    goto :Phase3Instructions
)

:: Check Phase 4 completion (main.js exists and has content)
if exist "..\frontend\js\main.js" (
    set FILE_SIZE=0
    for %%A in ("..\frontend\js\main.js") do set FILE_SIZE=%%~zA
    if !FILE_SIZE! GTR 500 (
        call :UpdateProgress 4 "COMPLETED"
        set CURRENT_PHASE=5
    ) else (
        goto :Phase4Instructions
    )
) else (
    goto :Phase4Instructions
)

:: Check Phase 5 completion (HTML file updated to use modules)
if exist "..\frontend\index.html" (
    findstr /C:"<script type=\"module\" src=\"js/main.js\"></script>" "..\frontend\index.html" >nul
    if not errorlevel 1 (
        call :UpdateProgress 5 "COMPLETED"
        set CURRENT_PHASE=6
    ) else (
        goto :Phase5Instructions
    )
) else (
    goto :Phase5Instructions
)

:: Phase 6 and 7 are subjective, so we'll check for a marker file
if exist "%TRACKER_DIR%\phase6_completed.txt" (
    call :UpdateProgress 6 "COMPLETED"
    set CURRENT_PHASE=7
) else (
    goto :Phase6Instructions
)

if exist "%TRACKER_DIR%\phase7_completed.txt" (
    call :UpdateProgress 7 "COMPLETED"
    set CURRENT_PHASE=8
    goto :AllCompleted
) else (
    goto :Phase7Instructions
)

:: Show instructions for current phase
:Phase1Instructions
call :CreatePhase1Instructions
goto :ShowInstructions

:Phase2Instructions
call :CreatePhase2Instructions
goto :ShowInstructions

:Phase3Instructions
call :CreatePhase3Instructions
goto :ShowInstructions

:Phase4Instructions
call :CreatePhase4Instructions
goto :ShowInstructions

:Phase5Instructions
call :CreatePhase5Instructions
goto :ShowInstructions

:Phase6Instructions
call :CreatePhase6Instructions
goto :ShowInstructions

:Phase7Instructions
call :CreatePhase7Instructions
goto :ShowInstructions

:AllCompleted
echo Congratulations! All phases of the modularization have been completed!
echo The app has been successfully modularized.
echo.
echo You can now safely delete the entire "modularization_workspace" folder
echo as it's no longer needed.
call :ShowProgress
goto :EOF

:ShowInstructions
echo Current Phase: Phase %CURRENT_PHASE%
echo.
echo Instructions have been generated in: %INSTRUCTIONS_DIR%\phase%CURRENT_PHASE%_instructions.txt
echo.
echo Here's what you need to do:
echo ---------------------------------------------------
type "%INSTRUCTIONS_DIR%\phase%CURRENT_PHASE%_instructions.txt"
echo ---------------------------------------------------
echo.
echo Run this batch file again after completing these tasks to get the next set of instructions.
call :ShowProgress
goto :EOF

:: Subroutine to update progress file
:UpdateProgress
setlocal
set PHASE_NUM=%~1
set STATUS=%~2
set TEMP_FILE=%TEMP%\progress_temp.txt
copy /y nul %TEMP_FILE% >nul

for /f "tokens=1* delims=:" %%a in ('type "%TRACKER_DIR%\progress.txt"') do (
    set LINE=%%a: %%b
    echo !LINE! | findstr /C:"Phase %PHASE_NUM%:" >nul
    if not errorlevel 1 (
        echo Phase %PHASE_NUM%: %STATUS% >> %TEMP_FILE%
    ) else (
        echo !LINE! >> %TEMP_FILE%
    )
)

copy /y %TEMP_FILE% "%TRACKER_DIR%\progress.txt" >nul
del %TEMP_FILE%
endlocal
goto :EOF

:: Subroutine to display progress
:ShowProgress
echo.
echo Current Progress:
echo ---------------------------------------------------
type "%TRACKER_DIR%\progress.txt"
echo ---------------------------------------------------
echo.
goto :EOF

:: Create instruction files for each phase
:CreatePhase1Instructions
(
    echo PHASE 1: SETUP AND PREPARATION
    echo.
    echo Follow these steps to set up the modularization structure:
    echo.
    echo 1. Create the module directory structure:
    echo    - Open Command Prompt/PowerShell in your project folder
    echo    - Run these commands to create directories:
    echo        mkdir -p frontend\js\modules
    echo        mkdir -p frontend\js\utils
    echo.
    echo 2. Create empty skeleton files:
    echo    - Run these commands to create empty utility module files:
    echo        type nul ^> frontend\js\utils\api.js
    echo        type nul ^> frontend\js\utils\ui.js
    echo        type nul ^> frontend\js\utils\formatters.js
    echo        type nul ^> frontend\js\utils\state.js
    echo.
    echo    - Run these commands to create empty feature module files:
    echo        type nul ^> frontend\js\modules\dataManager.js
    echo        type nul ^> frontend\js\modules\indicatorPanel.js
    echo        type nul ^> frontend\js\modules\strategySelector.js
    echo        type nul ^> frontend\js\modules\backtestView.js
    echo        type nul ^> frontend\js\modules\optimizationPanel.js
    echo        type nul ^> frontend\js\modules\seasonalityAnalyzer.js
    echo        type nul ^> frontend\js\modules\resultsViewer.js
    echo        type nul ^> frontend\js\modules\configManager.js
    echo.
    echo    - Create the main entry point file:
    echo        type nul ^> frontend\js\main.js
    echo.
    echo 3. Create a backup of the original app.js file:
    echo    - Run this command:
    echo        copy frontend\js\app.js frontend\js\app.js.backup
    echo.
    echo After completing these steps, run the module.bat file again to move to the next phase.
) > "%INSTRUCTIONS_DIR%\phase1_instructions.txt"
goto :EOF

:CreatePhase2Instructions
(
    echo PHASE 2: CREATE UTILITY MODULES
    echo.
    echo Follow these steps to implement the utility modules:
    echo.
    echo 1. Open and edit frontend\js\utils\api.js:
    echo    - Define API_BASE_URL and API_ENDPOINTS
    echo    - Create fetchApi function for making API calls
    echo    - Implement specific API call functions
    echo    - Make sure to export all functions and constants
    echo.
    echo 2. Open and edit frontend\js\utils\state.js:
    echo    - Create appState object with data tracking properties
    echo    - Add methods to update state
    echo    - Add session storage integration
    echo    - Export the state object
    echo.
    echo 3. Open and edit frontend\js\utils\ui.js:
    echo    - Implement showError function
    echo    - Implement showLoading function
    echo    - Implement activateTab function
    echo    - Add other UI helper functions
    echo    - Export all functions
    echo.
    echo 4. Open and edit frontend\js\utils\formatters.js:
    echo    - Implement formatDate function
    echo    - Implement formatNumber function
    echo    - Implement formatMetricName function
    echo    - Implement formatMetricValue function
    echo    - Implement formatParamName function
    echo    - Export all functions
    echo.
    echo Use the Function Migration Checklist in the modularization-plan.md 
    echo to make sure you've moved all the necessary functions.
    echo.
    echo After completing these steps, run the module.bat file again to move to the next phase.
) > "%INSTRUCTIONS_DIR%\phase2_instructions.txt"
goto :EOF

:CreatePhase3Instructions
(
    echo PHASE 3: CREATE FEATURE MODULES
    echo.
    echo Follow these steps to implement the feature modules:
    echo.
    echo For each module, follow this general pattern:
    echo 1. Import dependencies from utility modules
    echo 2. Define DOM references
    echo 3. Implement module-specific functions
    echo 4. Create an initialization function
    echo 5. Export public functions and the initialization function
    echo.
    echo Implement these modules one by one:
    echo.
    echo 1. frontend\js\modules\dataManager.js:
    echo    - Import from api.js, ui.js, formatters.js, state.js
    echo    - Implement updateDataPreview function
    echo    - Implement checkDataStatus function
    echo    - Create initialization function for event listeners
    echo.
    echo 2. frontend\js\modules\indicatorPanel.js:
    echo    - Implement updateIndicatorDropdowns function
    echo    - Implement moveSelectedOptions function
    echo    - Implement removeSelectedOptions function
    echo    - Implement initializeIndicatorControls function
    echo    - Implement updateCheckboxesFromAvailableIndicators function
    echo.
    echo 3. frontend\js\modules\strategySelector.js:
    echo    - Implement buildStrategySelections function
    echo    - Implement loadStrategyParameters function
    echo    - Implement updateStrategyParameters function
    echo.
    echo 4. frontend\js\modules\backtestView.js:
    echo    - Implement debugBacktestResults function
    echo    - Implement runBacktest function
    echo    - Implement displayBacktestResults function
    echo.
    echo 5. frontend\js\modules\optimizationPanel.js:
    echo    - Implement setupOptimizationParameters function
    echo    - Implement runOptimization function
    echo    - Implement checkOptimizationStatus function
    echo    - Implement fetchAndDisplayOptimizationResults function
    echo    - Implement useOptimizedParameters function
    echo.
    echo 6. frontend\js\modules\seasonalityAnalyzer.js:
    echo    - Implement initializeSeasonalityControls function
    echo    - Implement runSeasonalityAnalysis function
    echo    - Implement displaySeasonalityResults function
    echo    - Implement getSeasonalityTitle function
    echo    - Implement createSeasonalityTableHTML function
    echo    - Implement createSeasonalitySummaryAccordionHTML function
    echo    - Implement togglePatternOptions function
    echo.
    echo 7. frontend\js\modules\resultsViewer.js:
    echo    - Implement compareStrategies function
    echo.
    echo 8. frontend\js\modules\configManager.js:
    echo    - Implement fetchCurrentConfig function
    echo.
    echo Use the Function Migration Checklist in the modularization-plan.md 
    echo to make sure you've moved all the necessary functions.
    echo.
    echo After completing these steps, run the module.bat file again to move to the next phase.
) > "%INSTRUCTIONS_DIR%\phase3_instructions.txt"
goto :EOF

:CreatePhase4Instructions
(
    echo PHASE 4: CREATE MAIN ENTRY POINT
    echo.
    echo Follow these steps to implement the main entry point:
    echo.
    echo 1. Open and edit frontend\js\main.js:
    echo    - Import all modules:
    echo        * utils/state.js
    echo        * utils/ui.js
    echo        * modules/dataManager.js
    echo        * modules/indicatorPanel.js
    echo        * modules/strategySelector.js
    echo        * modules/backtestView.js
    echo        * modules/optimizationPanel.js
    echo        * modules/seasonalityAnalyzer.js
    echo        * modules/resultsViewer.js
    echo        * modules/configManager.js
    echo.
    echo    - Define DOM references for tabs and sections
    echo.
    echo    - Create initializeTabNavigation function:
    echo        * Add click event listeners to all tabs
    echo        * Include data validation checks before switching tabs
    echo.
    echo    - Create initializeApp function:
    echo        * Call initialization functions from all modules
    echo        * Set up tab navigation
    echo        * Restore state from session storage
    echo.
    echo    - Add DOMContentLoaded event listener to run initializeApp
    echo.
    echo Make sure the main.js file coordinates the initialization of all modules
    echo and manages the application's starting state.
    echo.
    echo After completing these steps, run the module.bat file again to move to the next phase.
) > "%INSTRUCTIONS_DIR%\phase4_instructions.txt"
goto :EOF

:CreatePhase5Instructions
(
    echo PHASE 5: UPDATE HTML
    echo.
    echo Follow these steps to update the HTML to use the new modular system:
    echo.
    echo 1. Open frontend\index.html in a text editor
    echo.
    echo 2. Find the script tag that loads app.js, which might look like:
    echo    ^<script src="js/app.js"^>^</script^>
    echo.
    echo 3. Replace it with:
    echo    ^<script type="module" src="js/main.js"^>^</script^>
    echo.
    echo 4. Save the file
    echo.
    echo This change tells the browser to load main.js as a JavaScript module,
    echo which enables the import/export statements used in our modular system.
    echo.
    echo After completing these steps, run the module.bat file again to move to the next phase.
) > "%INSTRUCTIONS_DIR%\phase5_instructions.txt"
goto :EOF

:CreatePhase6Instructions
(
    echo PHASE 6: TEST AND DEBUG
    echo.
    echo Follow these steps to test the modularized application:
    echo.
    echo 1. Open the application in a browser
    echo.
    echo 2. Test each feature one by one:
    echo    - Data upload and processing
    echo    - Indicator selection
    echo    - Strategy selection and parameters
    echo    - Backtesting
    echo    - Optimization
    echo    - Seasonality analysis
    echo    - Results viewing
    echo.
    echo 3. Check the browser console for errors
    echo.
    echo 4. Fix any issues you find:
    echo    - Check for circular dependencies
    echo    - Verify all variables are properly imported
    echo    - Check that event listeners are correctly attached
    echo    - Ensure API_ENDPOINTS are correctly imported
    echo    - Verify state is consistently updated
    echo.
    echo 5. After thorough testing, create a marker file to indicate completion:
    echo    echo completed > "%TRACKER_DIR%\phase6_completed.txt"
    echo.
    echo After completing these steps, run the module.bat file again to move to the next phase.
) > "%INSTRUCTIONS_DIR%\phase6_instructions.txt"
goto :EOF

:CreatePhase7Instructions
(
    echo PHASE 7: CLEANUP AND DOCUMENTATION
    echo.
    echo Follow these steps to finalize the modularization:
    echo.
    echo 1. Remove backup and temporary files (only after successful testing):
    echo    del frontend\js\app.js
    echo    rename frontend\js\app.js.backup frontend\js\app.js.old
    echo.
    echo 2. Update documentation:
    echo    - Add information about the modular structure to README.md
    echo    - Document the responsibility of each module
    echo.
    echo 3. Perform final checks:
    echo    - Verify no console errors
    echo    - Check for any memory leaks (especially with event listeners)
    echo    - Ensure all features work correctly
    echo.
    echo 4. After completing all steps, create a marker file to indicate completion:
    echo    echo completed > "%TRACKER_DIR%\phase7_completed.txt"
    echo.
    echo Congratulations! After this phase, the modularization will be complete!
    echo Run this batch file again to see your overall progress.
) > "%INSTRUCTIONS_DIR%\phase7_instructions.txt"
goto :EOF
```

#### Step 2: How to Use the Progress Tracker

1. **Double-click the `modularization_workspace/module.bat` file** whenever you want to check your progress or get instructions for the current stage.

2. The tracker will:
   - Show which phase you're currently in
   - Display detailed instructions in the console
   - Generate a text file with step-by-step guidance
   - Update a progress report showing completed and upcoming phases

3. **Follow the instructions** provided for the current phase

4. **Run the batch file again** after completing each set of tasks to get the next set of instructions

#### Benefits of the Progress Tracker

- **No programming knowledge required** - Clear, step-by-step instructions
- **Visual progress tracking** - Shows exactly where you are in the process
- **Automatic detection** - Determines your current stage by checking file existence
- **Detailed guidance** - Creates custom instruction files for each phase
- **Error prevention** - Ensures each phase is properly completed before moving on

This batch file can be especially helpful for team members who may be less familiar with JavaScript modularization but need to understand or contribute to the process.

## Final Cleanup

After completing all modularization steps and verifying that the application works correctly with the new modular structure, you can remove all modularization-related files:

```bash
# Delete the entire modularization workspace folder
rmdir /s /q modularization_workspace
```

This will remove all tracking files, instruction documents, and batch scripts that were used during the modularization process, leaving only your clean, modularized application code. 