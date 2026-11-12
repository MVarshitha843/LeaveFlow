@echo off
echo ========================================================
echo       Running LeaveFlow Pytest Verification Suite
echo ========================================================
echo.
backend\venv\Scripts\python.exe -m pytest backend/tests -v
echo.
pause
