@ECHO OFF
REM This script is part of the FE2 Wingman
REM Set up FE2 Wingman as a service if one is not already installed. Otherwise, the existing service will be removed.

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

sc create "FE2 Wingman" binPath= "%~dp0.venv\Scripts\python.exe %~dp0src\service.py" > NUL 2>&1
IF %ERRORLEVEL% EQU 5 (
    ECHO Please run this script with administrator privileges.
)
IF %ERRORLEVEL% EQU 0 (
    ECHO FE2 Wingman service installation successfully completed.
)
IF %ERRORLEVEL% EQU 1073 (
    sc delete "FE2 Wingman"
    ECHO Existing FE2 Wingman service has been removed.
)

PAUSE
EXIT