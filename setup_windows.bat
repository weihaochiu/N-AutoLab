@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating local Python 3.11 virtual environment in .venv ...
    py -3.11 -c "import sys; sys.exit(not (3, 11).__le__(sys.version_info[:2]))" >nul 2>nul
    if not errorlevel 1 (
        py -3.11 -m venv .venv
        if errorlevel 1 goto :error
    ) else (
        python -c "import sys; sys.exit(not (3, 11).__le__(sys.version_info[:2]))" >nul 2>nul
        if errorlevel 1 (
            echo ERROR: Python 3.11 or newer was not found through "py -3.11" or "python".
            goto :error
        )
        python -m venv .venv
        if errorlevel 1 goto :error
    )
) else (
    echo Reusing existing local virtual environment .venv ...
)

echo Installing N-AutoLab development dependencies locally ...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m pip install -e ".[dev]"
if errorlevel 1 goto :error

echo.
echo Setup complete. No global Python packages were changed.
echo Run tests with: .venv\Scripts\python.exe -m pytest
pause
exit /b 0

:error
echo.
echo Setup failed. Review the output above.
pause
exit /b 1
