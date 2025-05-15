@echo off
echo ===================================================
echo    MARK TESTING AND DEBUGGING PHASE AS COMPLETED
echo ===================================================
echo.

echo Creating completion marker file...
echo completed > tracking\phase6_completed.txt
echo Phase 6 marked as completed.
echo.

echo Running module.bat to update progress tracking...
call module.bat
echo.

echo You can now proceed to Phase 7: Cleanup and Documentation.
echo When Phase 7 is completed, run 'complete_phase7.bat'.
echo =================================================== 