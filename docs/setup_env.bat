@echo off
REM Setup script for Windows Command Prompt

set PYTHONPATH=%CD%

echo ✓ PYTHONPATH set to: %PYTHONPATH%
echo.
echo You can now run:
echo   python main.py analyze YOUR_USERNAME
echo   python scripts/verify/verify_setup.py
echo.
