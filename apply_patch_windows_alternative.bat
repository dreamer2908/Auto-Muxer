@echo off
setlocal
set app=xdelta3.exe
set changes=changes.vcdiff

if exist "%~1" (
    echo Attempting to patch %~1...
    %app% -d -f -s "%~1" "%changes%"
) else (
    echo Attempting to patch...
    %app% -d -f "%changes%"
)
echo Done. Press enter to exit.
pause
exit /b

