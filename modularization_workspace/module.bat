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