@echo off
setlocal

REM === CONFIGURE THESE TWO LINES IF YOUR PATHS DIFFER ===
set ORACLE_HOME_32=C:\Oracle\Ora12_32\client
set APP_DIR=%~dp0

REM Ensure the ODAC native bin (oci.dll, etc.) is first on PATH
set PATH=%ORACLE_HOME_32%\bin;%PATH%

REM Ensure the managed ODP.NET (2.x) is local next to datamgr.exe
if not exist "%APP_DIR%Oracle.DataAccess.dll" (
  echo [INFO] Copying Oracle.DataAccess.dll (2.122.1.0) next to datamgr.exe...
  copy /Y "%ORACLE_HOME_32%\odp.net\bin\2.x\Oracle.DataAccess.dll" "%APP_DIR%"
)

REM Optional: log environment for quick troubleshooting
echo --- PATH (first 5 entries) ---
for /f "tokens=1* delims=;" %%A in ("%PATH%") do (
  echo   %%A
  goto :afterpath
)
:afterpath
echo ORACLE_HOME=%ORACLE_HOME_32%
echo TNS_ADMIN=%TNS_ADMIN%

REM Launch the app
echo Starting datamgr.exe...
start "" "%APP_DIR%datamgr.exe"

endlocal
