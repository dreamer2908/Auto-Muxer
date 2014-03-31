@echo off
setlocal
set basefile=%basefile%
set patchedfile=%patchedfile%
set app=xdelta3.exe
set changes=changes.vcdiff

if exist "%patchedfile%" (
    echo Target file already exists. Press enter to continue and overwrite it, or press Ctrl + C to cancel.
	set /P bla=  
)
if exist "%~1" (
    set basefile=%~1
    goto startnow
)
if not exist "%basefile%" goto filenotfound
if not exist "%changes%" goto filenotfound
if not exist "%app%" goto filenotfound

:startnow
echo Attempting to patch %basefile%...
%app% -d -f -s "%basefile%" "%changes%" "%patchedfile%"
echo Done. Press enter to exit.
PAUSE
exit /b

:filenotfound 
echo "The files '%basefile%', '%changes%', and '%app%' must be in the same folder as this script."
pause
exit /b
