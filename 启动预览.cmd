@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-preview.ps1" %*
set "MICU_EXIT_CODE=%ERRORLEVEL%"
if not "%MICU_EXIT_CODE%"=="0" pause
exit /b %MICU_EXIT_CODE%
