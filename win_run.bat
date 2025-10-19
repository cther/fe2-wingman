@ECHO OFF
REM This script is part of the FE2 Wingman
REM It creates the virtual python environment and installs all necessary modules.

IF NOT EXIST .venv\ (
  ECHO FE2 Wingman is being prepared...

  py --version 3 > NUL
  IF ERRORLEVEL 1 (
    ECHO Note: Python version 3.10 or higher is required!
    PAUSE
    EXIT
  )

  ECHO * Create .venv
  py -m venv .venv
  
  ECHO * Installing requirements
  .venv\Scripts\python.exe -m pip install --no-cache-dir -r src\requirements-win.txt
  
  ECHO.
  ECHO Preparations completed!
  ECHO.
)

.venv\Scripts\python.exe src\main.py
PAUSE